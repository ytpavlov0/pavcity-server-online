"""One locksmith for property/vehicle keys, with durable retry receipts.

Owners can revoke an offline holder by character record, rather than reusing a
temporary server ID. Copying still requires the actual recipient beside them.
"""
import json
import re
import time


def install(api):
    if getattr(api, 'keys74_installed', False):
        return api
    import gameplay_v29.pn_economy as economy
    import gameplay_v29.pn_roleplay as rp
    import gameplay_v29.pn_admin as staff
    import gameplay_v29.pn_multiplayer as mp
    import gameplay_v29.pn_commands as commands
    w, previous = api.world, api.dispatch
    old_command = commands.command
    definitions = {
        'property': ('pn_properties', 'pn_property_keys', 'property_id'),
        'vehicle': ('pn_vehicles', 'pn_vehicle_access', 'vehicle_id'),
    }
    with api.database() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS pn_key_receipts74(
          user_id INTEGER NOT NULL, request_id TEXT NOT NULL, digest TEXT NOT NULL,
          result TEXT NOT NULL, PRIMARY KEY(user_id,request_id))''')

    def actor(token, values):
        uid = api.authenticated61(token)
        p, s = api.PRESENCE.get(token), api.GTA_STATE.get(token)
        if not uid or not p or uid != p['user_id']:
            raise ValueError('Önce karakterinle şehre gir.')
        api.require_client61(token, values)
        w.live(p, s)
        if time.time() - p.get('last_seen', 0) > 20 or time.time() - s.get('last_seen', 0) > 20:
            raise ValueError('Konumun güncel değil; bağlantını bekle.')
        if p.get('dimension') or s.get('vehicle_id') or w.occupation(p['char_id'])[0]:
            raise ValueError('Anahtar işlemini dışarıda ve yaya yap.')
        if (p.get('property45_used') or {}).get('phase') == 'pending' or p.get('inventory_action') or p.get('recon72') or staff.jail(p['char_id']):
            raise ValueError('Önce devam eden işlemi veya kısıtlamayı bitir.')
        return uid, p, s

    def integer(value):
        if type(value) is not int or not 0 < value <= 2147483647:
            raise ValueError('Geçerli kayıt numarası seç.')
        return value

    def view(p, s):
        assets = []
        with api.database() as db:
            for kind, (table, access, fk) in definitions.items():
                for row in db.execute('SELECT * FROM ' + table + ' WHERE owner=? ORDER BY id', (p['char_id'],)):
                    holders = [dict(char_id=r['char_id'], name=r['name']) for r in db.execute(
                        'SELECT a.char_id,COALESCE(c.name || \' \' || c.surname,\'Karakter #\' || a.char_id) name FROM ' + access +
                        ' a LEFT JOIN characters c ON c.id=a.char_id WHERE a.' + fk + '=? AND a.char_id<>? ORDER BY a.char_id',
                        (row['id'], p['char_id']))]
                    label = row['name'] if kind == 'property' else row['model'].upper() + ' · ' + row['plate']
                    assets.append(dict(kind=kind, id=row['id'], name=label, holders=holders))
        players = []
        for t, q in api.PRESENCE.items():
            qs = api.GTA_STATE.get(t)
            if q['char_id'] == p['char_id'] or not qs or q.get('dimension') or q.get('health', 200) <= 100:
                continue
            if time.time() - q.get('last_seen', 0) > 10 or time.time() - qs.get('last_seen', 0) > 10:
                continue
            if qs.get('vehicle_id') or w.occupation(q['char_id'])[0] or q.get('recon72'):
                continue
            if w.near(s, qs, 3):
                players.append(dict(id=q['server_id'], char_id=q['char_id'], name=q['name']))
        at_shop = any(w.near(s, v, v['radius']) for v in economy.STORES if v['kind'] == 'locksmith')
        return dict(success=True, assets=assets, players=players, price=2500, at_shop=at_shop,
                    locksmith=next(dict(v) for v in economy.STORES if v['kind'] == 'locksmith'))

    def action(uid, p, s, values, verb):
        if verb == 'list':
            return view(p, s)
        if verb not in ('copy', 'revoke'):
            raise ValueError('Anahtar işlemi bulunamadı.')
        kind = values.get('kind')
        if kind not in definitions:
            raise ValueError('Araç veya mülk seç.')
        table, access, fk = definitions[kind]
        asset_id, target = integer(values.get('id')), integer(values.get('char_id'))
        if target == p['char_id']:
            raise ValueError('Sahibin kendi anahtarı zaten var.')
        rid = values.get('request_id')
        if not isinstance(rid, str) or not re.fullmatch('[a-zA-Z0-9_-]{16,80}', rid):
            raise ValueError('İşlem kimliği gerekli; ekranı yeniden aç.')
        digest = json.dumps([p['char_id'], kind, asset_id, target, verb], separators=(',', ':'))
        with api.database() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT owner FROM ' + table + ' WHERE id=?', (asset_id,)).fetchone()
            if not row or row['owner'] != p['char_id']:
                raise ValueError('Anahtar yönetimi yalnız sahibine açık.')
            receipt = db.execute('SELECT * FROM pn_key_receipts74 WHERE user_id=? AND request_id=?', (uid, rid)).fetchone()
            if receipt:
                if receipt['digest'] != digest:
                    raise ValueError('İşlem kimliği başka bir anahtar işleminde kullanıldı.')
                return {**json.loads(receipt['result']), 'replayed': True}
            exists = db.execute('SELECT 1 FROM ' + access + ' WHERE ' + fk + '=? AND char_id=?', (asset_id, target)).fetchone()
            if verb == 'copy':
                economy.at('locksmith', p, s)
                # The character identity is bound to the chosen server slot. A
                # disconnected/recycled slot cannot receive somebody else's key.
                nearby = view(p, s)['players']
                if not any(q['char_id'] == target and q['id'] == values.get('server_id') for q in nearby):
                    raise ValueError('Anahtarı alacak kişi 3 metre içinde, yaya ve çevrimiçi olmalı.')
                if not exists:
                    if db.execute('SELECT count(*) FROM ' + access + ' WHERE ' + fk + '=? AND char_id<>?', (asset_id, p['char_id'])).fetchone()[0] >= 20:
                        raise ValueError('En fazla 20 kopya. Önce eski bir anahtarı iptal et.')
                    rp.debit(db, 'pn_wallet', 'user_id', uid, 2500)
                    db.execute('INSERT INTO ' + access + ' VALUES(?,?)', (asset_id, target))
                notice = 'Bu kişide zaten anahtar var; ücret kesilmedi.' if exists else 'Anahtar çoğaltıldı · $2.500.'
            else:
                db.execute('DELETE FROM ' + access + ' WHERE ' + fk + '=? AND char_id=?', (asset_id, target))
                notice = 'Anahtar iptal edildi. Eski kopya kapıyı açamaz.' if exists else 'Bu anahtar zaten iptal edilmiş.'
            result = dict(success=True, notice=notice, charged=2500 if verb == 'copy' and not exists else 0)
            w.audit(db, uid, 'key74-' + verb, dict(kind=kind, id=asset_id, target=target, charged=result['charged']))
            db.execute('INSERT INTO pn_key_receipts74 VALUES(?,?,?,?)', (uid, rid, digest, json.dumps(result)))
        result['money'] = w.wallet(uid)
        return result

    def dispatch(path, values, token):
        if not path.startswith('/api/key74/'):
            return previous(path, values, token)
        with api.LOCK:
            uid, p, s = actor(token, values)
            mp.rate(token, 'key74', .3)
            result = action(uid, p, s, values, path.rsplit('/', 1)[-1])
            # A receipt never replaces the latest wallet balance.
            if 'charged' in result:
                result['money'] = w.wallet(uid)
            return result, None

    def command(cmd, args, uid, p, s, peers):
        if cmd in ('/anahtarlar', '/anahtarci'):
            w.live(p, s)
            data = view(p, s)
            rows = [[('Mülk' if a['kind'] == 'property' else 'Araç') + ' #' + str(a['id']), a['name'] + ' · ' + str(len(a['holders'])) + ' kopya'] for a in data['assets']]
            rows += [['Anahtarcı', 'Haritadaki anahtar simgesi · $2.500 / kopya'], ['Kopyalama', 'Anahtarcı paneli · alıcı 3 m içinde yaya olmalı'], ['İptal', 'Panelden çevrim dışı kişilerin anahtarı da iptal edilir']]
            return dict(success=True, info=dict(title='Araç ve mülk anahtarları', rows=rows))
        return old_command(cmd, args, uid, p, s, peers)

    commands.command = command
    api.dispatch = dispatch
    api.keys74_installed = True
    return api
