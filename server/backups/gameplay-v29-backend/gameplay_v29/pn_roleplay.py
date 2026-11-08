"""SQLite RP economy and character factions. Caller holds session_api.LOCK.

Identity, prices, permissions, mission progress and rewards are server selected.
Coordinates still come from native client samples: this is not server physics.
Money changes and repeat receipts commit in the same SQLite transaction.
"""
import hashlib
import json
import math
import re
import secrets
import time
import gameplay_v29.pn_world as world
BANKS = [dict(x=150.0, y=-1040.0, z=29.4), dict(x=-1212.9, y=-330.8, z=37.8), dict(x=314.2, y=-278.9, z=54.2)]
JOB_HUB = dict(x=78.4, y=111.8, z=81.2)
DEPOT = dict(x=1201.0, y=-1276.0, z=35.2)
JOBS = {'courier': dict(name='Kurye', legal=True, reward=1200, seconds=25, hub=JOB_HUB, points=[dict(x=-42.8, y=-58.9, z=63.5), dict(x=-501.8, y=-670.5, z=33.2), dict(x=290.1, y=-1071.3, z=29.4)]), 'recycling': dict(name='Geri dönüşüm', legal=True, reward=850, seconds=15, hub=DEPOT, points=[dict(x=1144.2, y=-1647.6, z=36.4), dict(x=1098.1, y=-2000.4, z=31.0)]), 'contraband': dict(name='Kaçak sevkiyat', legal=False, reward=2400, seconds=45, hub=dict(x=918.9, y=-1261.6, z=25.5), points=[dict(x=489.8, y=-1524.4, z=29.3), dict(x=-219.4, y=-1500.3, z=31.2)])}
JOBS['assassin'] = dict(name='Tetikçilik · RP sözleşmesi', legal=False, reward=8000, seconds=60, hub=dict(x=-1171.0, y=-1572.0, z=4.4), points=[])
JOBS['harvest'] = dict(name='Kaçak ürün toplama', legal=False, reward=2800, seconds=30, hub=dict(x=156.0, y=-2203.0, z=4.7), points=[dict(x=241.5, y=-2157.1, z=13.3), dict(x=121.9, y=-2121.1, z=16.1)])
JOBS['grapes'] = dict(name='Bağcılık · Üzüm toplama ve satış', legal=True, reward=1800, seconds=25, hub=dict(x=-1887.3, y=2034.6, z=140.8), points=[dict(x=-1838.3, y=2055.5, z=140.9), dict(x=-1808.0, y=2065.2, z=138.5), dict(x=-1901.4, y=2081.4, z=140.4)])
JOBS['herbs'] = dict(name='Kaçak ürün · Toplama ve teslimat', legal=False, reward=3600, seconds=40, hub=dict(x=2224.1, y=5577.4, z=53.8), points=[dict(x=2210.6, y=5576.2, z=53.8), dict(x=2200.1, y=5588.4, z=53.8), dict(x=1535.7, y=2231.1, z=77.7)])
JOBS['grapes']['points'] = JOBS['grapes']['points'][:2]
JOBS['grapes']['finish'] = dict(x=-1901.4, y=2081.4, z=140.4)
JOBS['herbs']['points'] = JOBS['herbs']['points'][:2]
JOBS['herbs']['finish'] = dict(x=1535.7, y=2231.1, z=77.7)
TYPES = {'legal', 'illegal', 'police', 'medical'}
WEAPON_SHOPS = [dict(x=18.4, y=-1115.3, z=29.8), dict(x=249.6, y=-47.4, z=69.9)]
MARKETS = [dict(x=25.7, y=-1347.3, z=29.5), dict(x=-48.5, y=-1757.9, z=29.4)]

def services():
    entries = [('bank', 'Fleeca Banka', 108, b) for b in BANKS] + [('job', j['name'], 478, j['hub']) for j in JOBS.values()] + [('weapons', 'Ammu-Nation', 110, b) for b in WEAPON_SHOPS] + [('market', 'Market', 52, b) for b in MARKETS]
    result = [dict(id=1001 + i, kind=k, name=n, sprite=s, color=2, radius=5, **point) for i, (k, n, s, point) in enumerate(entries)]
    for service in result:
        if service['kind'] == 'job':
            service['job'] = next((k for k, j in JOBS.items() if j['name'] == service['name']))
    return result + __import__('gameplay_v29.pn_economy', fromlist=['*']).STORES + __import__('gameplay_v29.pn_economy', fromlist=['*']).FUEL_STATIONS

def schema(db):
    for sql in ('CREATE TABLE IF NOT EXISTS pn_bank(user_id INTEGER PRIMARY KEY,balance INTEGER NOT NULL DEFAULT 0 CHECK(balance>=0))', 'CREATE TABLE IF NOT EXISTS pn_rp_receipts(user_id INTEGER NOT NULL,key TEXT NOT NULL,digest TEXT NOT NULL,result TEXT NOT NULL,created REAL NOT NULL,PRIMARY KEY(user_id,key))', "CREATE TABLE IF NOT EXISTS pn_factions(id INTEGER PRIMARY KEY,name TEXT NOT NULL COLLATE NOCASE UNIQUE,tag TEXT NOT NULL COLLATE NOCASE UNIQUE,kind TEXT NOT NULL,level INTEGER NOT NULL DEFAULT 1,bank INTEGER NOT NULL DEFAULT 0 CHECK(bank>=0),motd TEXT NOT NULL DEFAULT '',created REAL NOT NULL)", 'CREATE TABLE IF NOT EXISTS pn_faction_members(char_id INTEGER PRIMARY KEY,faction_id INTEGER NOT NULL,rank INTEGER NOT NULL CHECK(rank BETWEEN 1 AND 20),leader INTEGER NOT NULL CHECK(leader IN(0,1)),joined REAL NOT NULL)', 'CREATE INDEX IF NOT EXISTS pn_faction_members_fac ON pn_faction_members(faction_id)', 'CREATE TABLE IF NOT EXISTS pn_faction_ranks(faction_id INTEGER NOT NULL,rank INTEGER NOT NULL,title TEXT NOT NULL,salary INTEGER NOT NULL DEFAULT 0 CHECK(salary>=0),PRIMARY KEY(faction_id,rank))', 'CREATE TABLE IF NOT EXISTS pn_faction_invites(id TEXT PRIMARY KEY,faction_id INTEGER NOT NULL,char_id INTEGER NOT NULL,expires REAL NOT NULL)', 'CREATE TABLE IF NOT EXISTS pn_faction_vehicles(vehicle_id INTEGER PRIMARY KEY,faction_id INTEGER NOT NULL,giver INTEGER NOT NULL)', 'CREATE TABLE IF NOT EXISTS pn_faction_duty(id INTEGER PRIMARY KEY,faction_id INTEGER NOT NULL,name TEXT NOT NULL,x REAL NOT NULL,y REAL NOT NULL,z REAL NOT NULL,min_rank INTEGER NOT NULL,armor INTEGER NOT NULL CHECK(armor BETWEEN 0 AND 100))', 'CREATE TABLE IF NOT EXISTS pn_job_runs(id TEXT PRIMARY KEY,char_id INTEGER NOT NULL,job TEXT NOT NULL,step INTEGER NOT NULL DEFAULT 0,started REAL NOT NULL,step_at REAL NOT NULL,completed REAL,paid INTEGER NOT NULL DEFAULT 0)', 'CREATE UNIQUE INDEX IF NOT EXISTS pn_job_active ON pn_job_runs(char_id) WHERE completed IS NULL', 'CREATE TABLE IF NOT EXISTS pn_contract_optin(char_id INTEGER PRIMARY KEY,enabled INTEGER NOT NULL CHECK(enabled IN(0,1)))', 'CREATE TABLE IF NOT EXISTS pn_contract_targets(run TEXT PRIMARY KEY,target INTEGER NOT NULL,life INTEGER NOT NULL)', 'CREATE TABLE IF NOT EXISTS pn_combat_events(id INTEGER PRIMARY KEY,target INTEGER NOT NULL,life INTEGER NOT NULL,attacker INTEGER NOT NULL,created REAL NOT NULL)', 'CREATE TABLE IF NOT EXISTS pn_rp_ledger(id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,char_id INTEGER NOT NULL,kind TEXT NOT NULL,amount INTEGER NOT NULL,detail TEXT NOT NULL,created REAL NOT NULL)'):
        db.execute(sql)

def amount(value):
    if type(value) is not int or not 1 <= value <= 10000000:
        raise ValueError('Tutar 1–10.000.000 arasında tam sayı olmalı.')
    return value

def integer(value, lo=1, hi=2147483647):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError('Geçersiz kimlik veya rütbe.')
    return value

def label(value, lo, hi):
    if not isinstance(value, str) or not lo <= len(value.strip()) <= hi or any((ord(c) < 32 for c in value)):
        raise ValueError('Geçersiz metin.')
    return value.strip()

def membership(db, cid):
    return db.execute('SELECT m.*,f.name,f.tag,f.kind,f.level,f.bank,f.motd FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id WHERE char_id=?', (cid,)).fetchone()

def lead(db, cid):
    m = membership(db, cid)
    if not m or not m['leader']:
        raise ValueError('Bu işlem birlik liderine açık.')
    return m

def vehicle_access(vid, cid):
    with world.database() as db:
        return bool(db.execute('SELECT 1 FROM pn_faction_vehicles v JOIN pn_faction_members m ON m.faction_id=v.faction_id WHERE v.vehicle_id=? AND m.char_id=?', (vid, cid)).fetchone())

def release_shared_seat(db, cid, fid, releases):
    vid, _ = world.occupation(cid)
    if vid and db.execute('SELECT 1 FROM pn_faction_vehicles f JOIN pn_vehicles v ON v.id=f.vehicle_id WHERE f.vehicle_id=? AND f.faction_id=? AND v.owner!=?', (vid, fid, cid)).fetchone():
        releases.append(cid)

def near(state, point, radius=5):
    return state and math.dist([state[k] for k in ('x', 'y', 'z')], [point[k] for k in ('x', 'y', 'z')]) <= radius

def ledger(db, uid, cid, kind, n, detail):
    db.execute('INSERT INTO pn_rp_ledger(user_id,char_id,kind,amount,detail,created) VALUES(?,?,?,?,?,?)', (uid, cid, kind, n, json.dumps(detail), time.time()))
    world.audit(db, uid, kind, dict(char_id=cid, amount=n, **detail))

def debit(db, table, key, uid, n):
    if not db.execute(f'UPDATE {table} SET balance=balance-? WHERE {key}=? AND balance>=?', (n, uid, n)).rowcount:
        raise ValueError('Yeterli bakiye yok.')

def bank_view(db, uid):
    db.execute('INSERT OR IGNORE INTO pn_bank(user_id) VALUES(?)', (uid,))
    return dict(cash=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?', (uid,)).fetchone()[0], bank=db.execute('SELECT balance FROM pn_bank WHERE user_id=?', (uid,)).fetchone()[0])

def faction_view(db, cid):
    m = membership(db, cid)
    invites = [dict(r) for r in db.execute('SELECT i.id,f.name,f.tag,i.expires FROM pn_faction_invites i JOIN pn_factions f ON f.id=i.faction_id WHERE i.char_id=? AND i.expires>?', (cid, time.time()))]
    if not m:
        return dict(member=None, invites=invites)
    fid = m['faction_id']
    return dict(member=dict(m), invites=invites, ranks=[dict(r) for r in db.execute('SELECT rank,title,salary FROM pn_faction_ranks WHERE faction_id=? ORDER BY rank', (fid,))], members=[dict(r) for r in db.execute('SELECT m.char_id,c.name,c.surname,m.rank,m.leader FROM pn_faction_members m JOIN characters c ON c.id=m.char_id WHERE faction_id=? ORDER BY leader DESC,rank,char_id', (fid,))], duty=[dict(r) for r in db.execute('SELECT * FROM pn_faction_duty WHERE faction_id=?', (fid,))], vehicles=[dict(r) for r in db.execute('SELECT v.id,v.owner,v.model,v.plate,v.active FROM pn_faction_vehicles f JOIN pn_vehicles v ON v.id=f.vehicle_id WHERE f.faction_id=?', (fid,))])

def dispatch(path, uid, token, payload, p, state, presences):
    world.live(p, state)
    action = path.rsplit('/', 1)[-1]
    group = path.split('/')[2]
    cid = p['char_id']
    now = time.time()
    from gameplay_v29.pn_multiplayer import rate
    read = action in ('list', 'status')
    releases = []
    with world.database() as db:
        schema(db)
        bank_view(db, uid)
        key = payload.get('request_id')
        digest = None
        if not read:
            if not isinstance(key, str) or not re.fullmatch('[A-Za-z0-9_-]{12,80}', key):
                raise ValueError('İşlem kimliği gerekli.')
            digest = hashlib.sha256(json.dumps([cid, path, {k: v for k, v in payload.items() if k != 'request_id'}], sort_keys=True, allow_nan=False).encode()).hexdigest()
            previous = db.execute('SELECT digest,result FROM pn_rp_receipts WHERE user_id=? AND key=?', (uid, key)).fetchone()
            if previous:
                if previous['digest'] != digest:
                    raise ValueError('İşlem kimliği başka bir işlemde kullanılmış.')
                return json.loads(previous['result'])
            rate(token, 'rp-' + group, 0.25)
        if group == 'bank':
            result = bank_action(db, action, uid, cid, payload, state)
        elif group == 'factions':
            result = faction_action(db, action, uid, cid, payload, p, state, presences, releases)
        elif group == 'jobs':
            result = job_action(db, action, uid, cid, payload, state, p)
        else:
            raise ValueError('İşlem bulunamadı.')
        result = dict(success=True, **result)
        if not read:
            db.execute('INSERT INTO pn_rp_receipts VALUES(?,?,?,?,?)', (uid, key, digest, json.dumps(result), now))
    for released in set(releases):
        world.release(released)
    return result

def bank_action(db, action, uid, cid, payload, state):
    if state.get('vehicle_id') or state.get('dimension', 0) or (not any((near(state, b, 5) for b in BANKS))):
        raise ValueError('Banka NPC yanına yaya yaklaş.')
    if action == 'list':
        return dict(**bank_view(db, uid), locations=BANKS, transactions=[dict(r) for r in db.execute("SELECT kind,amount,created,detail FROM pn_rp_ledger WHERE user_id=? AND kind LIKE 'bank-%' ORDER BY id DESC LIMIT 30", (uid,))])
    if not any((near(state, b) for b in BANKS)):
        raise ValueError('Bankaya veya ATM noktasına yaklaş.')
    n = amount(payload.get('amount'))
    if action == 'deposit':
        debit(db, 'pn_wallet', 'user_id', uid, n)
        db.execute('UPDATE pn_bank SET balance=balance+? WHERE user_id=?', (n, uid))
    elif action == 'withdraw':
        debit(db, 'pn_bank', 'user_id', uid, n)
        db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?', (n, uid))
    elif action == 'transfer':
        target = integer(payload.get('char_id'))
        row = db.execute('SELECT user_id FROM characters WHERE id=? AND id NOT IN(SELECT char_id FROM pn_character_archive)', (target,)).fetchone()
        if not row or row['user_id'] == uid:
            raise ValueError('Başka bir oyuncunun aktif karakter ID’sini yaz.')
        bank_view(db, row['user_id'])
        debit(db, 'pn_bank', 'user_id', uid, n)
        db.execute('UPDATE pn_bank SET balance=balance+? WHERE user_id=?', (n, row['user_id']))
        ledger(db, row['user_id'], target, 'bank-received', n, dict(sender=cid))
    else:
        raise ValueError('Banka işlemi bulunamadı.')
    ledger(db, uid, cid, 'bank-' + action, n, dict(target=payload.get('char_id') if action == 'transfer' else None))
    return dict(**bank_view(db, uid), notice='Banka işlemi tamamlandı.')

def faction_action(db, action, uid, cid, v, p, state, presences, releases):
    m = membership(db, cid)
    if action == 'list':
        return dict(faction=faction_view(db, cid), on_duty=bool(p.get('faction_duty')))
    if action == 'create':
        if m:
            raise ValueError('Önce mevcut birliğinden ayrıl.')
        name = label(v.get('name'), 4, 36)
        tag = label(v.get('tag'), 2, 8).upper()
        kind = v.get('kind')
        if kind not in TYPES:
            raise ValueError('Geçersiz birlik türü.')
        if not re.fullmatch('[A-Z0-9ÇĞİÖŞÜ]+', tag):
            raise ValueError('Etiket harf veya rakam olmalı.')
        if kind in ('police', 'medical'):
            import gameplay_v29.pn_admin as pn_admin
            if pn_admin.rank(uid) < 4:
                raise ValueError('Resmî birlikleri kurucu oluşturabilir.')
        if db.execute('SELECT 1 FROM pn_factions WHERE name=? OR tag=?', (name, tag)).fetchone():
            raise ValueError('Birlik adı veya etiketi kullanılıyor.')
        debit(db, 'pn_wallet', 'user_id', uid, 50000)
        fid = db.execute('INSERT INTO pn_factions(name,tag,kind,created) VALUES(?,?,?,?)', (name, tag, kind, time.time())).lastrowid
        db.execute('INSERT INTO pn_faction_members VALUES(?,?,1,1,?)', (cid, fid, time.time()))
        db.executemany('INSERT INTO pn_faction_ranks VALUES(?,?,?,0)', [(fid, i, 'Lider' if i == 1 else 'Rütbe ' + str(i)) for i in range(1, 21)])
        ledger(db, uid, cid, 'faction-create', 50000, dict(faction=fid))
    elif action == 'accept':
        if m:
            raise ValueError('Zaten bir birliktesin.')
        invite = db.execute('SELECT * FROM pn_faction_invites WHERE id=? AND char_id=? AND expires>?', (str(v.get('invite', '')), cid, time.time())).fetchone()
        if not invite:
            raise ValueError('Davet bulunamadı veya süresi doldu.')
        count = db.execute('SELECT count(*) FROM pn_faction_members WHERE faction_id=?', (invite['faction_id'],)).fetchone()[0]
        level = db.execute('SELECT level FROM pn_factions WHERE id=?', (invite['faction_id'],)).fetchone()[0]
        if count >= level * 10:
            raise ValueError('Birlik üye sınırına ulaştı.')
        db.execute('INSERT INTO pn_faction_members VALUES(?,?,20,0,?)', (cid, invite['faction_id'], time.time()))
        db.execute('DELETE FROM pn_faction_invites WHERE char_id=?', (cid,))
    elif action == 'leave':
        if not m:
            raise ValueError('Birlik üyesi değilsin.')
        if m['leader']:
            raise ValueError('Ayrılmadan önce liderliği başka bir üyeye devret.')
        release_shared_seat(db, cid, m['faction_id'], releases)
        db.execute('DELETE FROM pn_faction_members WHERE char_id=?', (cid,))
        p.pop('faction_duty', None)
    elif action == 'vehicle-share':
        if not m:
            raise ValueError('Birlik üyesi değilsin.')
        vid = integer(v.get('vehicle_id'))
        car = db.execute('SELECT owner FROM pn_vehicles WHERE id=?', (vid,)).fetchone()
        if not car or car['owner'] != cid:
            raise ValueError('Yalnız kendi aracını paylaşabilirsin.')
        existing = db.execute('SELECT faction_id FROM pn_faction_vehicles WHERE vehicle_id=?', (vid,)).fetchone()
        if existing:
            raise ValueError('Bu araç zaten birliğe paylaşılmış.')
        db.execute('INSERT INTO pn_faction_vehicles VALUES(?,?,?)', (vid, m['faction_id'], cid))
    elif action == 'vehicle-unshare':
        vid = integer(v.get('vehicle_id'))
        shared = db.execute('SELECT * FROM pn_faction_vehicles WHERE vehicle_id=?', (vid,)).fetchone()
        if not shared or not (shared['giver'] == cid or (m and m['leader'] and (m['faction_id'] == shared['faction_id']))):
            raise ValueError('Paylaşımı araç sahibi veya birlik lideri kaldırabilir.')
        for peer in presences.values():
            if peer['char_id'] != shared['giver'] and world.occupation(peer['char_id'])[0] == vid:
                releases.append(peer['char_id'])
        db.execute('DELETE FROM pn_faction_vehicles WHERE vehicle_id=?', (vid,))
    elif action == 'duty':
        from gameplay_v29.pn_multiplayer import rate
        rate(str(uid), 'faction-duty', 5)
        if p.get('faction_duty'):
            p.pop('faction_duty', None)
            p.pop('duty_started', None)
            p['armor'] = min(p.get('armor', 0), p.pop('duty_original_armor', 0))
            state['armor'] = p['armor']
        else:
            point = db.execute('SELECT * FROM pn_faction_duty WHERE id=?', (integer(v.get('point')),)).fetchone()
            if not m or not point or point['faction_id'] != m['faction_id'] or (m['rank'] > point['min_rank']):
                raise ValueError('Görev noktası veya rütben uygun değil.')
            if not near(state, point, 3) or p.get('health', 0) <= 100 or state.get('vehicle_id'):
                raise ValueError('Görev noktasında, hayatta ve yaya olmalısın.')
            p['faction_duty'] = point['id']
            p['duty_started'] = time.time()
            p['duty_original_armor'] = p.get('armor', 0)
            p['armor'] = max(p.get('armor', 0), point['armor'])
            state['armor'] = p['armor']
    elif action == 'payday':
        point = db.execute('SELECT faction_id,min_rank FROM pn_faction_duty WHERE id=?', (p.get('faction_duty', 0),)).fetchone()
        if not m or not point or point['faction_id'] != m['faction_id'] or (m['rank'] > point['min_rank']) or (time.time() - p.get('duty_started', time.time()) < 300):
            raise ValueError('Maaş için yetkili görevde 5 dakika çalışmalısın.')
        n = db.execute('SELECT salary FROM pn_faction_ranks WHERE faction_id=? AND rank=?', (m['faction_id'], m['rank'])).fetchone()[0]
        if not n:
            raise ValueError('Bu rütbe için maaş tanımlanmamış.')
        if not db.execute('UPDATE pn_factions SET bank=bank-? WHERE id=? AND bank>=?', (n, m['faction_id'], n)).rowcount:
            raise ValueError('Birlik kasası maaş için yetersiz.')
        db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?', (n, uid))
        p['duty_started'] = time.time()
        ledger(db, uid, cid, 'faction-payday', n, dict(faction=m['faction_id']))
    elif action in ('deposit', 'withdraw'):
        if not m:
            raise ValueError('Birlik üyesi değilsin.')
        n = amount(v.get('amount'))
        fid = m['faction_id']
        if action == 'deposit':
            debit(db, 'pn_wallet', 'user_id', uid, n)
            db.execute('UPDATE pn_factions SET bank=bank+? WHERE id=?', (n, fid))
        else:
            lead(db, cid)
            if not db.execute('UPDATE pn_factions SET bank=bank-? WHERE id=? AND bank>=?', (n, fid, n)).rowcount:
                raise ValueError('Birlik kasası yetersiz.')
            db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?', (n, uid))
        ledger(db, uid, cid, 'faction-' + action, n, dict(faction=fid))
    else:
        m = lead(db, cid)
        fid = m['faction_id']
        if action == 'invite':
            target = world.resolve_player_id(v.get('server_id'), presences)
            if membership(db, target):
                raise ValueError('Oyuncu zaten bir birlikte.')
            if db.execute('SELECT count(*) FROM pn_faction_invites WHERE faction_id=? AND expires>?', (fid, time.time())).fetchone()[0] >= 20:
                raise ValueError('Davet sınırı dolu.')
            db.execute('DELETE FROM pn_faction_invites WHERE char_id=? AND faction_id=?', (target, fid))
            db.execute('INSERT INTO pn_faction_invites VALUES(?,?,?,?)', (secrets.token_urlsafe(18), fid, target, time.time() + 300))
        elif action in ('rank', 'kick', 'transfer-leader'):
            target = integer(v.get('char_id'))
            member = membership(db, target)
            if not member or member['faction_id'] != fid or target == cid or member['leader']:
                raise ValueError('Bu üye için işlem yapılamaz.')
            if action == 'rank':
                db.execute('UPDATE pn_faction_members SET rank=? WHERE char_id=?', (integer(v.get('rank'), 1, 20), target))
            elif action == 'kick':
                release_shared_seat(db, target, fid, releases)
                db.execute('DELETE FROM pn_faction_members WHERE char_id=?', (target,))
                for peer in presences.values():
                    if peer['char_id'] == target:
                        peer.pop('faction_duty', None)
            else:
                db.execute('UPDATE pn_faction_members SET leader=CASE WHEN char_id=? THEN 1 ELSE 0 END WHERE faction_id=?', (target, fid))
        elif action == 'motd':
            db.execute('UPDATE pn_factions SET motd=? WHERE id=?', (label(v.get('text'), 0, 300), fid))
        elif action == 'rank-config':
            db.execute('UPDATE pn_faction_ranks SET title=?,salary=? WHERE faction_id=? AND rank=?', (label(v.get('title'), 2, 32), integer(v.get('salary', 0), 0, 10000), fid, integer(v.get('rank'), 1, 20)))
        elif action == 'level':
            if m['level'] >= 5:
                raise ValueError('Birlik en yüksek seviyede.')
            cost = m['level'] * 100000
            if not db.execute('UPDATE pn_factions SET bank=bank-?,level=level+1 WHERE id=? AND bank>=?', (cost, fid, cost)).rowcount:
                raise ValueError('Seviye ücreti için kasa yetersiz.')
            ledger(db, uid, cid, 'faction-level', cost, dict(faction=fid))
        elif action == 'duty-create':
            if m['kind'] not in ('police', 'medical', 'legal'):
                raise ValueError('Bu birlik türü resmî görev noktası kullanamaz.')
            if db.execute('SELECT count(*) FROM pn_faction_duty WHERE faction_id=?', (fid,)).fetchone()[0] >= 8:
                raise ValueError('Görev noktası sınırı 8.')
            armor = integer(v.get('armor', 0), 0, 100)
            if armor and m['kind'] != 'police':
                raise ValueError('Zırhlı görev paketi yalnızca polis birliğine açık.')
            db.execute('INSERT INTO pn_faction_duty(faction_id,name,x,y,z,min_rank,armor) VALUES(?,?,?,?,?,?,?)', (fid, label(v.get('name'), 2, 40), state['x'], state['y'], state['z'], integer(v.get('min_rank'), 1, 20), armor))
        elif action == 'duty-delete':
            db.execute('DELETE FROM pn_faction_duty WHERE id=? AND faction_id=?', (integer(v.get('point')), fid))
        else:
            raise ValueError('Birlik işlemi bulunamadı.')
    world.audit(db, uid, 'faction-' + action, dict(char_id=cid))
    return dict(faction=faction_view(db, cid), on_duty=bool(p.get('faction_duty')), money=bank_view(db, uid)['cash'], notice='Birlik işlemi tamamlandı.')

def job_view(row, target_state=None):
    if not row:
        return None
    job = JOBS[row['job']]
    step = row['step']
    target = job['points'][step] if step < len(job['points']) else job.get('finish', job['hub'])
    if row['job'] == 'assassin':
        target = target_state if step == 0 and target_state else job.get('finish', job['hub'])
    returning = step >= len(job['points']) and (not (row['job'] == 'assassin' and step == 0))
    cargo = row['job'] == 'courier'
    gather = row['job'] in ('grapes', 'herbs')
    title = ('Satış noktasına git · Ürünleri sat' if gather else 'Depoya dön · Ücreti al') if returning else ('Teslimat ' if cargo else 'Toplama noktası ' if gather else 'Durak ') + str(step + 1) + ' / ' + str(len(job['points']))
    instruction = ('GPS işaretindeki alıcıya git, dur ve E tuşunu basılı tut.' if gather else 'Başlangıçtaki görevliye dön, dur ve E tuşunu basılı tut.') if returning else 'GPS işaretine git, dur ve E tuşunu basılı tut. Teslimatı araç içinden de yapabilirsin.' if cargo else 'GPS işaretine git ve E tuşunu basılı tut.'
    if row['job'] == 'assassin':
        title = 'Sözleşme hedefi' if step == 0 else 'Görevliye dön'
        instruction = 'Görev panelindeki RP sözleşme adımını izle.'
    with world.database() as db:
        loan = db.execute('SELECT j.vehicle_id,v.model,v.plate,v.state FROM pn_job_vehicles j JOIN pn_vehicles v ON v.id=j.vehicle_id WHERE j.borrower=?', (row['char_id'],)).fetchone()
    vehicle = None
    if loan:
        position = world.VEHICLE_CACHE.get(loan['vehicle_id'], json.loads(loan['state']))
        vehicle = dict(id=loan['vehicle_id'], model=loan['model'], plate=loan['plate'], **{k: position[k] for k in ('x', 'y', 'z')})
    return dict(id=row['id'], job=row['job'], name=job['name'], step=step, total=2 if row['job'] == 'assassin' else len(job['points']) + 1, target={k: target[k] for k in ('x', 'y', 'z')}, ready_at=row['step_at'] + job['seconds'], reward=job['reward'], legal=job['legal'], step_title=title, instruction=instruction, phase='return' if returning else 'delivery' if cargo else 'work', cargo_remaining=max(0, len(job['points']) - step) if cargo else None, vehicle=vehicle)

def combat_event(target, life, attacker):
    with world.database() as db:
        opted = db.execute('SELECT enabled FROM pn_contract_optin WHERE char_id=?', (target,)).fetchone()
        if opted and opted['enabled']:
            db.execute('INSERT INTO pn_combat_events(target,life,attacker,created) VALUES(?,?,?,?)', (target, life, attacker, time.time()))

def contract_progress(db, row, cid):
    if not row or row['job'] != 'assassin':
        return (row, None)
    assignment = db.execute('SELECT * FROM pn_contract_targets WHERE run=?', (row['id'],)).fetchone()
    if not assignment:
        return (row, None)
    event = db.execute('SELECT 1 FROM pn_combat_events WHERE target=? AND life=? AND attacker=? AND created>=?', (assignment['target'], assignment['life'], cid, row['started'])).fetchone()
    if event and row['step'] == 0:
        db.execute('UPDATE pn_job_runs SET step=1 WHERE id=?', (row['id'],))
        row = db.execute('SELECT * FROM pn_job_runs WHERE id=?', (row['id'],)).fetchone()
    if row['step'] == 0:
        from gameplay_v29.session_api import PRESENCE, GTA_STATE
        opted = db.execute('SELECT enabled FROM pn_contract_optin WHERE char_id=?', (assignment['target'],)).fetchone()
        peer = next((v for v in PRESENCE.values() if v['char_id'] == assignment['target'] and time.time() - v['last_seen'] < 10), None)
        if peer and (not opted or not opted['enabled'] or peer.get('life_id', 0) != assignment['life']):
            db.execute('UPDATE pn_job_runs SET completed=? WHERE id=?', (time.time(), row['id']))
            return (None, None)
        state = next((s for s in GTA_STATE.values() if s['char_id'] == assignment['target'] and time.time() - s['last_seen'] < 10), None)
        return (row, state)
    return (row, None)

def job_action(db, action, uid, cid, v, state, p):
    import gameplay_v29.pn_city as pn_city
    row = db.execute('SELECT * FROM pn_job_runs WHERE char_id=? AND completed IS NULL', (cid,)).fetchone()
    now = time.time()
    row, target_state = contract_progress(db, row, cid)
    opted = db.execute('SELECT enabled FROM pn_contract_optin WHERE char_id=?', (cid,)).fetchone()
    if action in ('list', 'status'):
        return dict(jobs=[dict(key=k, **j) for k, j in JOBS.items()], active=job_view(row, target_state), contract_optin=bool(opted and opted['enabled']))
    if action == 'contract-optin':
        if type(v.get('enabled')) is not bool:
            raise ValueError('Geçersiz sözleşme tercihi.')
        db.execute('INSERT INTO pn_contract_optin VALUES(?,?) ON CONFLICT(char_id) DO UPDATE SET enabled=excluded.enabled', (cid, int(v['enabled'])))
        return dict(contract_optin=v['enabled'], notice='RP sözleşme katılımı güncellendi.')
    if action != 'cancel' and (p.get('health', 0) <= 100 or p.get('fly') or p.get('admin_duty')):
        raise ValueError('Çalışmak için hayatta ve normal oyun modunda olmalısın.')
    if action == 'start':
        if row:
            raise ValueError('Zaten bir görevin var.')
        key = v.get('job')
        job = JOBS.get(key)
        if p.get('dimension', 0) or not job or (not near(state, job['hub'])):
            raise ValueError('Mesleğin başlangıç noktasına yaklaş.')
        latest = db.execute('SELECT max(completed) FROM pn_job_runs WHERE char_id=? AND paid>0', (cid,)).fetchone()[0]
        if latest and now - latest < 30:
            raise ValueError('Yeni iş için 30 saniye bekle.')
        run = secrets.token_urlsafe(18)
        assignment = None
        if key == 'assassin':
            from gameplay_v29.session_api import PRESENCE
            import gameplay_v29.pn_admin as pn_admin
            opted_ids = {r['char_id'] for r in db.execute('SELECT char_id FROM pn_contract_optin WHERE enabled=1')}
            eligible = [v for v in PRESENCE.values() if v.get('world') == 'gta' and v['char_id'] in opted_ids and (v['char_id'] != cid) and (time.time() - v['last_seen'] < 10) and (v.get('health', 0) > 100) and (not v.get('fly')) and (not v.get('godmode')) and (pn_admin.rank(v['user_id']) == 0)]
            if not eligible:
                raise ValueError('RP sözleşmesine katılan uygun oyuncu yok.')
            assignment = secrets.choice(eligible)
        db.execute('INSERT INTO pn_job_runs(id,char_id,job,started,step_at) VALUES(?,?,?,?,?)', (run, cid, key, now, now))
        pn_city.borrow_job_car(db, key, cid)
        if assignment:
            db.execute('INSERT INTO pn_contract_targets VALUES(?,?,?)', (run, assignment['char_id'], assignment.get('life_id', 0)))
    elif action == 'cancel':
        if not row:
            raise ValueError('Aktif görev yok.')
        db.execute('UPDATE pn_job_runs SET completed=? WHERE id=?', (now, row['id']))
        pn_city.return_job_car(db, cid)
    elif action == 'complete-step':
        if not row or row['id'] != v.get('run'):
            raise ValueError('Görev bulunamadı.')
        current = job_view(row, target_state)
        job = JOBS[row['job']]
        if now - row['started'] > 3600:
            raise ValueError('Görev süresi doldu; iptal edip yeniden başla.')
        if p.get('dimension', 0) or not near(state, current['target'], 5):
            raise ValueError('GPS işaretindeki görev noktasına 5 metre yaklaş.')
        if now < current['ready_at']:
            raise ValueError('Teslimat hazırlığı sürüyor: ' + str(math.ceil(current['ready_at'] - now)) + ' saniye bekle.')
        if state.get('speed', 0) > 1:
            raise ValueError('Teslimat için önce tamamen dur.')
        if row['job'] == 'assassin' and row['step'] == 0:
            raise ValueError('Sözleşme için sunucunun doğruladığı hedef sonucu gerekli.')
        if row['job'] in ('grapes', 'herbs'):
            import gameplay_v29.pn_inventory as pn_inventory, gameplay_v29.pn_containers as pn_containers, gameplay_v29.pn_economy as pn_economy
            item = 'grape' if row['job'] == 'grapes' else 'herb'
            updated = json.loads(json.dumps(pn_inventory.load(p)))
            stock = updated.setdefault('stock', {})
            need = len(job['points']) * 2
            if row['step'] < len(job['points']):
                if stock.get(item, 0) + 2 > 20 or pn_containers.weight(pn_containers.personal(p)) + 0.6 > (1000 if world.admin(uid) else 30):
                    raise ValueError('Toplamak için çantanda yer aç.')
                stock[item] = stock.get(item, 0) + 2
            else:
                if stock.get(item, 0) < need:
                    raise ValueError('Teslim edilecek ürün çantanda eksik.')
                stock[item] -= need
                if stock[item] <= 0:
                    stock.pop(item, None)
            version = pn_economy.stock_save(db, p, updated)
            p['loadout'] = updated
            p['loadout_version'] = version
        if row['step'] < len(job['points']) and row['job'] != 'assassin':
            db.execute('UPDATE pn_job_runs SET step=step+1,step_at=? WHERE id=?', (now, row['id']))
        else:
            if not db.execute('UPDATE pn_job_runs SET paid=?,completed=? WHERE id=? AND completed IS NULL AND paid=0', (job['reward'], now, row['id'])).rowcount:
                raise ValueError('Bu görev zaten ödendi.')
            db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?', (job['reward'], uid))
            ledger(db, uid, cid, 'job-reward', job['reward'], dict(job=row['job'], run=row['id']))
            pn_city.return_job_car(db, cid)
    else:
        raise ValueError('Meslek işlemi bulunamadı.')
    current = db.execute('SELECT * FROM pn_job_runs WHERE char_id=? AND completed IS NULL', (cid,)).fetchone()
    current, target_state = contract_progress(db, current, cid)
    notice = 'Meslekten ayrıldın. Atanan araç ve anahtarı iade edildi.' if action == 'cancel' else 'Görev tamamlandı. $' + str(JOBS[row['job']]['reward']) + ' hesabına eklendi.' if not current else JOBS[current['job']]['name'] + ' başladı. GPS ve görev kartındaki adımları izle; /meslekayril ile bırakabilirsin.' if action == 'start' else 'Durak tamamlandı. Sıradaki hedef GPS’e işlendi.'
    return dict(active=job_view(current, target_state), money=bank_view(db, uid)['cash'], notice=notice)
