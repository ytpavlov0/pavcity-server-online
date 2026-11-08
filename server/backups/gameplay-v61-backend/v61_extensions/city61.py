"""Account lease, bank payroll and call text. Uses the existing authenticated API."""
import hashlib
import importlib
import secrets
import time


def install(api, clock=time.time):
    if getattr(api, 'city61_installed', False):
        return api
    world = api.world
    city = importlib.import_module(api.__package__ + '.pn_city')
    phone = importlib.import_module(api.__package__ + '.pn_phone')
    multi = importlib.import_module(api.__package__ + '.pn_multiplayer')
    previous = api.dispatch
    with api.database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pn_payroll61(user_id INTEGER PRIMARY KEY,seconds REAL NOT NULL DEFAULT 0,period INTEGER NOT NULL DEFAULT 0,code TEXT,amount INTEGER NOT NULL DEFAULT 0,expires REAL NOT NULL DEFAULT 0,paid_period INTEGER NOT NULL DEFAULT 0)')
    ticks = {}

    def authenticated(token):
        session = api.SESSIONS.get(token)
        if session and session['expires'] > clock():
            return session['user_id']
        if token:
            with api.database() as db:
                row = db.execute('SELECT user_id FROM pn_sessions WHERE hash=? AND expires>?', (hashlib.sha256(token.encode()).hexdigest(), clock())).fetchone()
            if row:
                return row['user_id']
        return None

    def deposit(db, uid, p, row):
        if row['paid_period'] >= row['period']:
            return
        db.execute('INSERT OR IGNORE INTO pn_bank VALUES(?,0)', (uid,))
        db.execute('UPDATE pn_bank SET balance=balance+? WHERE user_id=?', (row['amount'], uid))
        db.execute('INSERT INTO pn_rp_ledger(user_id,char_id,kind,amount,detail,created) VALUES(?,?,?,?,?,?)', (uid, p['char_id'], 'hourly61', row['amount'], 'Saatlik devlet ödemesi · dönem ' + str(row['period']), clock()))
        db.execute('UPDATE pn_payroll61 SET paid_period=period,code=NULL,expires=0 WHERE user_id=?', (uid,))

    def payroll(uid, p, accrue=False, confirm=None):
        now = clock()
        with api.database() as db:
            db.execute('INSERT OR IGNORE INTO pn_payroll61(user_id) VALUES(?)', (uid,))
            row = dict(db.execute('SELECT * FROM pn_payroll61 WHERE user_id=?', (uid,)).fetchone())
            if confirm is not None:
                if not row['code'] or row['expires'] < now or not secrets.compare_digest(str(confirm), row['code']):
                    raise ValueError('Onay kodu yanlış veya süresi doldu. /maas ile güncel kodu gör.')
                deposit(db, uid, p, row)
                row.update(paid_period=row['period'], code=None, expires=0)
            if accrue:
                last = ticks.get(uid)
                ticks[uid] = now
                # Only adjacent authenticated online heartbeats count. No offline pay.
                delta = now-last if last is not None and 0 <= now-last <= 20 else 0
                if not row['code']:
                    row['seconds'] += delta
                profile = city.profile(db, uid)
                vip = int(profile.get('vip', 0))
                if row['seconds'] >= 3600 and not row['code']:
                    member = db.execute('SELECT f.kind,r.salary FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id LEFT JOIN pn_faction_ranks r ON r.faction_id=m.faction_id AND r.rank=m.rank WHERE m.char_id=?', (p['char_id'],)).fetchone()
                    legal = member and member['kind'] in ('police', 'medical', 'legal', 'government')
                    salary = max(500, min(2500, int(member['salary'] or 1000))) if legal else 500
                    row.update(seconds=0, period=row['period']+1, code=str(secrets.randbelow(9000)+1000), amount=salary+500*vip, expires=now+900)
                elif row['code'] and row['expires'] < now:
                    row.update(code=str(secrets.randbelow(9000)+1000), expires=now+900)
                db.execute('UPDATE pn_payroll61 SET seconds=?,period=?,code=?,amount=?,expires=? WHERE user_id=?', (row['seconds'], row['period'], row['code'], row['amount'], row['expires'], uid))
                if vip and row['code']:
                    deposit(db, uid, p, row)
                    row.update(paid_period=row['period'], code=None, expires=0)
            return dict(period=row['period'], code=row['code'], amount=row['amount'], paid=row['paid_period']==row['period'] and row['period']>0, remaining=max(0, int(3600-row['seconds'])), expires=row['expires'])

    def dispatch(path, payload, token):
        with api.LOCK:
            uid = authenticated(token)
            if path in ('/api/gta/join', '/api/lobby/join') and uid:
                current=api.PRESENCE.get(token)
                instance=payload.get('client61')
                if instance is not None and (not isinstance(instance,str) or not 16<=len(instance)<=64):
                    raise ValueError('Geçersiz istemci oturumu.')
                if current and clock()-current['last_seen']<30 and (current['char_id']!=payload.get('char_id') or current.get('client61') and current['client61']!=instance):
                    raise ValueError('Bu hesap zaten başka oyun oturumunda. Önce karakterden çık; bağlantı koptuysa 30 saniye bekle.')
                for key, peer in list(api.PRESENCE.items()):
                    if key == token or peer.get('user_id') != uid:
                        continue
                    if clock()-peer['last_seen'] < 30:
                        raise ValueError('Bu hesap zaten oyunda. Diğer cihazdan çıkış yap; bağlantı koptuysa 30 saniye bekle.')
                    if key in api.GTA_STATE:
                        multi.save(peer, api.GTA_STATE[key], True)
                    world.release(peer['char_id'])
                    api.PRESENCE.pop(key, None)
                    api.GTA_STATE.pop(key, None)
            p = api.PRESENCE.get(token)
            if p and p.get('client61') and path not in ('/api/gta/join','/api/lobby/join') and not path.startswith(('/api/auth/','/api/character/')) and payload.get('client61')!=p['client61']:
                raise ValueError('Bu oyun oturumu başka sekmeye ait. Aynı hesapla tek oturum kullan.')
            if path == '/api/chat/send' and uid and p:
                parts = str(payload.get('message', '')).strip().split(None, 1)
                command = parts[0].lower() if parts else ''
                if command in ('/onayla', '/maas'):
                    world.live(p, api.GTA_STATE.get(token))
                    status = payroll(uid, p, confirm=parts[1] if command=='/onayla' and len(parts)>1 else None)
                    if command=='/onayla' and len(parts)<2:
                        raise ValueError('Kullanım: /onayla 1234')
                    notice = f"Saatlik ${status['amount']:,} banka hesabına yatırıldı." if status['paid'] else f"Saatlik ödemen hazır: /onayla {status['code']}" if status['code'] else f"Sonraki ödeme için {status['remaining']//60} dakika çevrim içi kal."
                    return dict(success=True, notice=notice, payroll61=status), None
                if command == '/p':
                    peer_id = phone.call_peer(p['char_id'])
                    peer = next((q for q in api.PRESENCE.values() if q['char_id']==peer_id and clock()-q['last_seen']<20), None)
                    if not peer:
                        raise ValueError('Önce karşı tarafın cevapladığı bir telefon görüşmesi başlat.')
                    if len(parts)<2 or not parts[1].strip():
                        raise ValueError('Kullanım: /p mesaj')
                    payload = {**payload, 'message': f"/pm {peer['server_id']} [Telefon] {parts[1][:190]}"}
            result, cookie = previous(path, payload, token)
            p = api.PRESENCE.get(token)
            if result.get('success') and p and path in ('/api/gta/join','/api/lobby/join') and payload.get('client61'):
                p['client61']=payload['client61']
            if result.get('success') and uid and p and path == '/api/gta/sync':
                # Bank/SQL payroll updates at most once per five seconds per account.
                cached = p.get('payroll61_cache')
                if not cached or clock()-cached[0]>=5:
                    cached = (clock(), payroll(uid, p, accrue=True))
                    p['payroll61_cache'] = cached
                result['payroll61'] = cached[1]
            if path in ('/api/lobby/leave', '/api/auth/logout') and uid:
                ticks.pop(uid, None)
            return result, cookie

    def guard(token,payload):
        p=api.PRESENCE.get(token)
        if p and p.get('client61') and payload.get('client61')!=p['client61']:
            raise ValueError('Bu oyun oturumu başka sekmeye ait. Aynı hesapla tek oturum kullan.')

    api.dispatch = dispatch
    api.city61_installed = True
    api.payroll61 = payroll
    api.authenticated61 = authenticated
    api.require_client61 = guard
    return api
