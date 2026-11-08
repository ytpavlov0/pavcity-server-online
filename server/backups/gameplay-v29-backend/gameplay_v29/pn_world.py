"""Server-owned identity, wallet, vehicles and seat reservations.

Vehicle physics remain client sampled; money, ownership, locks and seats are
validated on this server. Caller must hold session_api.LOCK.
"""
import json
import math
import re
import secrets
import time
from contextlib import contextmanager
import online_engine as engine
SEATS = {}
BREAK_INS = {}
VEHICLE_CACHE = {}
SAVED_AT = {}
CATALOG = {'blista': 18000, 'asea': 25000, 'primo': 32000, 'sultan': 85000, 'buffalo': 110000, 'baller': 125000, 'schafter2': 160000, 'zentorno': 725000, 'adder': 950000, 'bati': 45000, 'faggio': 8000}
BARBERS = [{'x': -814.3, 'y': -183.8, 'z': 37.6}, {'x': 136.8, 'y': -1708.4, 'z': 29.3}, {'x': -1282.4, 'y': -1116.8, 'z': 7.0}]
SPAWN_MODELS = set(CATALOG) | {'t20', 'infernus', 'turismor', 'kuruma', 'police', 'police2', 'ambulance', 'bus', 'sanchez', 'banshee', 'comet2', 'i8', 'skyline'}
DONATE_MODELS = {'i8': dict(name='BMW i8 · 2015', category='İndirilen model', accent='#79cfff', author='[YCA]Aige', source='https://www.gta5-mods.com/vehicles/2015-bmw-i8', custom=True), 'skyline': dict(name='Nissan Skyline GT-R R34', category='İndirilen model', accent='#ba9aff', author='YCA-y97y', source='https://www.gta5-mods.com/vehicles/nissan-skyline-gt-r-bnr34-yca-y97y', custom=True), 't20': dict(name='Progen T20', category='Super', accent='#b5ef67'), 'turismor': dict(name='Grotti Turismo R', category='Super', accent='#ffb46e'), 'zentorno': dict(name='Pegassi Zentorno', category='Super', accent='#ba9aff'), 'adder': dict(name='Truffade Adder', category='Super', accent='#8dcfff'), 'banshee': dict(name='Bravado Banshee', category='Sport', accent='#ff91aa'), 'comet2': dict(name='Pfister Comet', category='Sport', accent='#f2db80')}
HOSPITALS = [{'x': 293.7, 'y': -601.5, 'z': 43.2}, {'x': 310.2, 'y': -590.1, 'z': 43.2}, {'x': 329.0, 'y': -579.5, 'z': 28.8}, {'x': 1839.6, 'y': 3672.9, 'z': 34.3}, {'x': -247.8, 'y': 6331.2, 'z': 32.4}]
DEALERS = [{'x': -56.5, 'y': -1096.3, 'z': 26.4}]
SERVICES = [dict(id=i + 1, kind=kind, name=name, sprite=sprite, color=color, radius=radius, **location) for i, (kind, name, sprite, color, radius, location) in enumerate([('barber', 'Berber', 71, 2, 3, s) for s in BARBERS] + [('hospital', 'Hastane', 61, 1, 4, s) for s in HOSPITALS] + [('dealer', 'PAV Motors', 225, 2, 5, s) for s in DEALERS])]

def at_barber(state):
    return any((near(state, shop, 3) for shop in BARBERS))

def spawn_location(state, model='sultan', excluding=0):
    """Avoid stacking managed cars while native collision/ground loads."""
    with database() as db:
        existing = db.execute("SELECT id,model,state FROM pn_vehicles WHERE active=1 AND abs(json_extract(state,'$.x')-?)<50 AND abs(json_extract(state,'$.y')-?)<50", (state['x'], state['y'])).fetchall()
    blockers = [(r['model'], VEHICLE_CACHE.get(r['id'], json.loads(r['state']))) for r in existing if r['id'] != excluding]
    heading = math.radians(state['heading'])
    for radius in (4, 10, 16, 22):
        for angle in (0, 45, -45, 90, -90, 135, -135, 180):
            yaw = heading + math.radians(angle)
            point = dict(x=state['x'] - math.sin(yaw) * radius, y=state['y'] + math.cos(yaw) * radius, z=state['z'] + 0.3)
            if all((abs(v.get('z', point['z']) - point['z']) > 4 or math.hypot(v['x'] - point['x'], v['y'] - point['y']) >= (10 if model == 'bus' or other == 'bus' else 5.5) for other, v in blockers)):
                return point
    raise ValueError('Yakında boş araç alanı yok. Biraz ilerleyip tekrar dene.')

@contextmanager
def database():
    import gameplay_v29.pn_storage as pn_storage
    with pn_storage.database() as db:
        yield db

def schema(db):
    for query in ('CREATE TABLE IF NOT EXISTS pn_admin(singleton INTEGER PRIMARY KEY CHECK(singleton=1),user_id INTEGER NOT NULL UNIQUE)', 'CREATE TABLE IF NOT EXISTS pn_wallet(user_id INTEGER PRIMARY KEY,balance INTEGER NOT NULL CHECK(balance>=0))', 'CREATE TABLE IF NOT EXISTS pn_character(char_id INTEGER PRIMARY KEY,appearance TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1)', 'CREATE TABLE IF NOT EXISTS pn_vehicles(id INTEGER PRIMARY KEY AUTOINCREMENT,owner INTEGER NOT NULL,model TEXT NOT NULL,plate TEXT NOT NULL UNIQUE,locked INTEGER NOT NULL DEFAULT 0,active INTEGER NOT NULL DEFAULT 1,state TEXT NOT NULL,updated REAL NOT NULL)', 'CREATE TABLE IF NOT EXISTS pn_vehicle_access(vehicle_id INTEGER NOT NULL,char_id INTEGER NOT NULL,PRIMARY KEY(vehicle_id,char_id))', 'CREATE INDEX IF NOT EXISTS pn_vehicle_owner ON pn_vehicles(owner)', "CREATE INDEX IF NOT EXISTS pn_vehicle_xy ON pn_vehicles(active,json_extract(state,'$.x'),json_extract(state,'$.y'))", 'CREATE TABLE IF NOT EXISTS pn_audit(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,action TEXT NOT NULL,detail TEXT NOT NULL,created REAL NOT NULL)', 'CREATE TABLE IF NOT EXISTS pn_loadout(char_id INTEGER PRIMARY KEY,state TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1)', 'CREATE TABLE IF NOT EXISTS pn_donate_vehicles(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,model TEXT NOT NULL,granted_by INTEGER NOT NULL,created REAL NOT NULL,vehicle_id INTEGER UNIQUE,claimed_char INTEGER,claimed_at REAL,revoked_at REAL)', 'CREATE INDEX IF NOT EXISTS pn_donate_owner ON pn_donate_vehicles(user_id,id)'):
        db.execute(query)
    db.execute('INSERT OR IGNORE INTO pn_wallet SELECT id,5000 FROM users')
    import gameplay_v29.pn_admin as pn_admin
    pn_admin.schema(db)

def admin(uid):
    import gameplay_v29.pn_admin as pn_admin
    return pn_admin.rank(uid) >= 2

def wallet(uid):
    with database() as db:
        db.execute('INSERT OR IGNORE INTO pn_wallet VALUES(?,5000)', (uid,))
        return db.execute('SELECT balance FROM pn_wallet WHERE user_id=?', (uid,)).fetchone()[0]

def appearance(raw=None):
    raw = raw or {}
    if not isinstance(raw, dict):
        raise ValueError('Geçersiz karakter görünümü.')

    def integer(key, default, lo, hi):
        value = raw.get(key, default)
        if isinstance(value, bool) or not isinstance(value, int) or (not lo <= value <= hi):
            raise ValueError('Geçersiz görünüm: ' + key)
        return value

    def number(key, default, lo, hi):
        value = raw.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (float, int)) or (not math.isfinite(value)) or (not lo <= value <= hi):
            raise ValueError('Geçersiz görünüm: ' + key)
        return value
    gender = raw.get('gender', 'male')
    if gender not in ('male', 'female'):
        raise ValueError('Kadın veya erkek seç.')
    result = {'gender': gender, 'mother': integer('mother', 21, 0, 45), 'father': integer('father', 0, 0, 45), 'skinMother': integer('skinMother', 21, 0, 45), 'skinFather': integer('skinFather', 0, 0, 45), 'faceMix': number('faceMix', 0.5, 0, 1), 'skinMix': number('skinMix', 0.5, 0, 1), 'hair': integer('hair', 0, 0, 35), 'hairColor': integer('hairColor', 0, 0, 63), 'top': integer('top', 0, 0, 150), 'pants': integer('pants', 0, 0, 100), 'shoes': integer('shoes', 0, 0, 70), 'torso': integer('torso', 0, 0, 15), 'undershirt': integer('undershirt', 15, 0, 100), 'eye': integer('eye', 0, 0, 31), 'beard': integer('beard', -1, -1, 28), 'eyebrow': integer('eyebrow', 0, 0, 33), 'texture': integer('texture', 0, 0, 10)}
    features = raw.get('features', [0] * 20)
    if not isinstance(features, list) or len(features) != 20 or any((isinstance(v, bool) or not isinstance(v, (int, float)) or (not math.isfinite(v)) or (not -1 <= v <= 1) for v in features)):
        raise ValueError('Geçersiz yüz ayarı.')
    result['features'] = features
    return result

def character(cid):
    with database() as db:
        row = db.execute('SELECT * FROM pn_character WHERE char_id=?', (cid,)).fetchone()
    return {'appearance': json.loads(row['appearance']) if row else appearance(), 'appearance_version': row['version'] if row else 1, 'country': __import__('gameplay_v29.pn_commands', fromlist=['*']).country(cid)}

def save_appearance(cid, raw):
    data = appearance(raw)
    with database() as db:
        db.execute('INSERT INTO pn_character VALUES(?,?,1) ON CONFLICT(char_id) DO UPDATE SET appearance=excluded.appearance,version=pn_character.version+1', (cid, json.dumps(data)))
    return character(cid)

def audit(db, uid, action, detail):
    db.execute('INSERT INTO pn_audit(user_id,action,detail,created) VALUES(?,?,?,?)', (uid, action, json.dumps(detail, ensure_ascii=False), time.time()))

def resolve_player_id(value, presences):
    try:
        sid = int(value)
    except (ValueError, TypeError):
        raise ValueError('Geçerli oyuncu ID yaz.')
    peer = next((p for p in presences.values() if p.get('world') == 'gta' and p.get('server_id') == sid), None)
    if not peer:
        raise ValueError('Bu ID ile bağlı oyuncu bulunamadı. TAB listesini kontrol et.')
    return peer['char_id']

def command(uid, token, payload, presence, presences):
    text = str(payload.get('message', '')).strip()
    parts = text.split()
    if not parts:
        return None
    command = parts[0].lower()
    if command not in ('/aduty', '/changename'):
        return None
    if not admin(uid):
        raise ValueError('Bu komut yalnızca yöneticiye açık.')
    if command == '/aduty':
        if len(parts) != 1:
            raise ValueError('Kullanım: /aduty')
        presence['admin_duty'] = not presence.get('admin_duty', False)
        return {'success': True, 'notice': 'Yönetici görevi ' + ('açıldı.' if presence['admin_duty'] else 'kapatıldı.')}
    if len(parts) != 4:
        raise ValueError('Kullanım: /changename ID Ad Soyad')
    cid = resolve_player_id(parts[1], presences)
    name, surname = parts[2:]
    if not all((2 <= len(v) <= 24 and all((c.isalpha() or c in " '-" for c in v)) for v in (name, surname))):
        raise ValueError('Geçerli ad ve soyad yaz.')
    from gameplay_v29.pn_multiplayer import reserve, identity
    with database() as db:
        old = db.execute('SELECT name,surname FROM characters WHERE id=?', (cid,)).fetchone()
        if not old:
            raise ValueError('Karakter bulunamadı.')
        reserve(db, 'character', name + ' ' + surname, cid)
        oldkey = identity(old['name'] + ' ' + old['surname'])
        newkey = identity(name + ' ' + surname)
        if oldkey != newkey:
            db.execute('DELETE FROM pn_identity WHERE kind=? AND key=? AND owner=?', ('character', oldkey, cid))
        db.execute('UPDATE characters SET name=?,surname=? WHERE id=?', (name, surname, cid))
        audit(db, uid, 'changename', {'id': cid, 'old': dict(old), 'new': name + ' ' + surname})
    for p in presences.values():
        if p['char_id'] == cid:
            p['name'] = name + ' ' + surname
    return {'success': True, 'notice': f'Oyuncu #{parts[1]}: {name} {surname}'}

def live(p, state):
    if not p or not state or p.get('health', 200) <= 100:
        raise ValueError('Bu işlem için hayatta ve oyunda olmalısın.')

def near(a, b, limit=7):
    return math.sqrt(sum(((a[k] - b[k]) ** 2 for k in ('x', 'y', 'z')))) <= limit

def rows(state):
    x, y, z = (state['x'], state['y'], state['z'])
    with database() as db:
        candidates = {r['id']: dict(r) for r in db.execute("SELECT * FROM pn_vehicles WHERE active=1 AND json_extract(state,'$.x') BETWEEN ? AND ? AND json_extract(state,'$.y') BETWEEN ? AND ? ORDER BY (json_extract(state,'$.x')-?)*(json_extract(state,'$.x')-?)+(json_extract(state,'$.y')-?)*(json_extract(state,'$.y')-?)+(json_extract(state,'$.z')-?)*(json_extract(state,'$.z')-?),id DESC LIMIT 96", (x - 650, x + 650, y - 650, y + 650, x, x, y, y, z, z))}
        for vid, position in VEHICLE_CACHE.items():
            if near(state, position, 400) and vid not in candidates:
                row = db.execute('SELECT * FROM pn_vehicles WHERE id=? AND active=1', (vid,)).fetchone()
                if row:
                    candidates[vid] = dict(row)
    return list(candidates.values())

def vehicle(vid):
    with database() as db:
        row = db.execute('SELECT * FROM pn_vehicles WHERE id=?', (vid,)).fetchone()
    if not row:
        raise ValueError('Araç bulunamadı.')
    return dict(row)

def remove_seat(key):
    entry = SEATS.pop(key, None)
    if entry is None:
        return
    vid, seat = key
    if seat == -1:
        fields = dict(VEHICLE_CACHE.get(vid, json.loads(vehicle(vid)['state'])))
        fields.update(vx=0, vy=0, vz=0)
        VEHICLE_CACHE[vid] = fields
        persist_vehicle(vid)
    if (vid, -1) not in SEATS:
        VEHICLE_CACHE.pop(vid, None)
        SAVED_AT.pop(vid, None)

def release(cid):
    import gameplay_v29.pn_interactions as pn_interactions
    pn_interactions.release(cid)
    for key in list(SEATS):
        if SEATS[key]['char_id'] == cid:
            remove_seat(key)

def clean_seats(presences):
    now = time.time()
    connected = {p['char_id'] for p in presences.values() if now - p['last_seen'] < 10 and p.get('health', 200) > 100}
    for key, entry in list(SEATS.items()):
        if entry['char_id'] not in connected or now - entry['time'] > 12:
            remove_seat(key)

def recover_vehicles():
    """On server startup no driver reservations survive; retain parked positions."""
    if SEATS:
        raise RuntimeError('Vehicle recovery requires an idle startup.')
    with database() as db:
        for row in db.execute('SELECT id,model,state FROM pn_vehicles WHERE active=1').fetchall():
            if row['model'] not in __import__('gameplay_v29.pn_traffic', fromlist=['*']).ROAD_MODELS:
                db.execute('UPDATE pn_vehicles SET active=0 WHERE id=?', (row['id'],))
                continue
            fields = json.loads(row['state'])
            if fields.get('engine') or any((fields.get(k, 0) for k in ('vx', 'vy', 'vz'))):
                fields.update(vx=0, vy=0, vz=0)
                db.execute('UPDATE pn_vehicles SET state=?,updated=? WHERE id=?', (json.dumps(fields), time.time(), row['id']))
    VEHICLE_CACHE.clear()
    SAVED_AT.clear()
HOSPITAL_SPAWN = {'x': 293.7, 'y': -601.5, 'z': 43.2, 'heading': 70, 'safe_ground': True}

def occupation(cid):
    return next(((vid, seat) for (vid, seat), p in SEATS.items() if p['char_id'] == cid), (0, -2))

def public(row):
    fields = dict(VEHICLE_CACHE.get(row['id'], json.loads(row['state'])))
    now = time.time()
    fuel_at = fields.setdefault('fuel_at', row['updated'])
    elapsed = int(max(0, min(86400, now - fuel_at)))
    if fields.get('engine'):
        fields['fuel'] = max(0, fields.get('fuel', 100) - elapsed * 0.002)
        if fields['fuel'] <= 0:
            fields['engine'] = False
    if elapsed:
        fields['fuel_at'] = now
    VEHICLE_CACHE[row['id']] = fields
    SAVED_AT.setdefault(row['id'], row['updated'])
    if row['active'] and now - SAVED_AT.get(row['id'], now) >= 3:
        persist_vehicle(row['id'])
    return dict(id=row['id'], owner=row['owner'], owner_label='NPC' if row['owner'] == 0 else 'Oyuncu #' + str(row['owner']), model=row['model'], plate=row['plate'], locked=bool(row['locked']), **fields)

def view(uid, p, state, presences):
    clean_seats(presences)
    vehicles = [public(row) for row in rows(state)]
    vehicles = sorted((v for v in vehicles if near(state, v, 400)), key=lambda v: (sum(((v[k] - state[k]) ** 2 for k in ('x', 'y', 'z'))), -v['id']))[:48]
    for v in vehicles:
        v['driver'] = SEATS.get((v['id'], -1), {}).get('char_id', 0)
    if vehicles:
        with database() as db:
            placeholders = ','.join(('?' for _ in vehicles))
            shared = {r['vehicle_id']: r for r in db.execute('SELECT l.vehicle_id,f.id,f.name,f.tag FROM pn_faction_vehicles l JOIN pn_factions f ON f.id=l.faction_id WHERE l.vehicle_id IN (' + placeholders + ')', [v['id'] for v in vehicles])}
            jobs = {r['vehicle_id']: r for r in db.execute('SELECT vehicle_id,job,borrower FROM pn_job_vehicles WHERE vehicle_id IN (' + placeholders + ')', [v['id'] for v in vehicles])}
        for v in vehicles:
            if v['id'] in jobs:
                job = jobs[v['id']]
                v.update(job=job['job'], job_assigned=job['borrower'] == p['char_id'], owner_label='Meslek aracı')
            if v['id'] in shared:
                faction = shared[v['id']]
                v['faction_id'] = faction['id']
                v['owner_label'] = '[' + faction['tag'] + '] ' + faction['name']
    vid, seat = occupation(p['char_id'])
    import gameplay_v29.pn_admin as pn_admin
    import gameplay_v29.pn_roleplay as pn_roleplay
    import gameplay_v29.pn_city as pn_city
    return {'vehicles': vehicles if not p.get('dimension', 0) else [], 'vehicle_id': vid, 'seat': seat, 'money': wallet(uid), 'admin': admin(uid), 'owner': pn_admin.rank(uid) == 4, 'can_spawn': pn_admin.rank(uid) >= 2, 'admin_duty': p.get('admin_duty', False) and (not p.get('hide_admin')), 'barbers': BARBERS, 'services': SERVICES + pn_roleplay.services() if not p.get('dimension', 0) else [], **pn_city.view(uid, p, state)}

def donate_action(action, uid, payload, p):
    """Account entitlement -> exactly one vehicle, delivered to the chosen character.

    The row and garage insert share a transaction; replay does not mint a car.
    Delivery stays parked until the owner explicitly retrieves it from the garage.
    """
    if action == 'donate-list':
        with database() as db:
            rows = [dict(r) for r in db.execute('SELECT d.id,d.model,d.created,d.vehicle_id,d.claimed_char,d.claimed_at,d.revoked_at,v.plate,c.name,c.surname FROM pn_donate_vehicles d LEFT JOIN pn_vehicles v ON v.id=d.vehicle_id LEFT JOIN characters c ON c.id=d.claimed_char WHERE d.user_id=? ORDER BY d.id DESC LIMIT 100', (uid,))]
        for r in rows:
            r['status'] = 'revoked' if r.pop('revoked_at') else 'claimed' if r['vehicle_id'] else 'pending'
            r['character_name'] = ((r.pop('name') or '') + ' ' + (r.pop('surname') or '')).strip()
        return dict(success=True, catalog=[dict(model=k, **v) for k, v in DONATE_MODELS.items()], grants=rows)
    grant_id = payload.get('id')
    if type(grant_id) is not int or grant_id < 1:
        raise ValueError('Geçerli teslimat numarası seç.')
    cid = p['char_id']
    with database() as db:
        row = db.execute('SELECT * FROM pn_donate_vehicles WHERE id=? AND user_id=?', (grant_id, uid)).fetchone()
        if not row:
            raise ValueError('Bu teslimat hesabına ait değil.')
        if row['revoked_at']:
            raise ValueError('Bu teslimat kurucu tarafından iptal edilmiş.')
        if row['vehicle_id']:
            return dict(success=True, vehicle_id=row['vehicle_id'], already_claimed=True, notice='Bu teslimat daha önce garaja kaydedildi. Yeni araç üretilmedi.')
        model = row['model']
        if model not in DONATE_MODELS:
            raise ValueError('Bu araç şu anda teslim edilemiyor.')
        if db.execute('SELECT COUNT(*) FROM pn_vehicles WHERE owner=?', (cid,)).fetchone()[0] >= 20:
            raise ValueError('Garajın dolu (20 araç). Teslimat hesabında bekliyor.')
        position = dict(x=-45.5, y=-1097.2, z=26.4, heading=70, rx=0, ry=0, rz=70, vx=0, vy=0, vz=0, body=1000, engine=False, fuel=100, km=0)
        plate = 'DN' + secrets.token_hex(3).upper()
        now = time.time()
        vid = db.execute('INSERT INTO pn_vehicles(owner,model,plate,locked,active,state,updated) VALUES(?,?,?,1,0,?,?)', (cid, model, plate, json.dumps(position), now)).lastrowid
        db.execute('UPDATE pn_donate_vehicles SET vehicle_id=?,claimed_char=?,claimed_at=? WHERE id=?', (vid, cid, now, grant_id))
        audit(db, uid, 'donate-claim', dict(grant=grant_id, vehicle=vid, char_id=cid, model=model))
    return dict(success=True, vehicle_id=vid, already_claimed=False, notice=DONATE_MODELS[model]['name'] + ' garajına kaydedildi. Araçlarım ekranından çıkarabilirsin.')

def dispatch(path, uid, token, payload, p, state, presences):
    if path == '/api/vehicles/catalog':
        import gameplay_v29.pn_admin as pn_admin
        return {'success': True, 'catalog': [{'model': m, 'price': price} for m, price in CATALOG.items()], 'money': wallet(uid), 'admin': admin(uid), 'can_spawn': pn_admin.rank(uid) >= 2}
    live(p, state)
    clean_seats(presences)
    cid = p['char_id']
    is_admin = admin(uid)
    action = path.rsplit('/', 1)[-1]
    if action in ('donate-list', 'donate-claim'):
        return donate_action(action, uid, payload, p)
    if action in ('refuel-info', 'refuel'):
        from gameplay_v29.pn_economy import refuel
        return refuel(action, uid, token, payload, p, state)
    import gameplay_v29.pn_traffic as traffic
    if action == 'traffic-register':
        return traffic.register(uid, token, payload, p, state)
    from gameplay_v29.pn_multiplayer import rate
    if action in ('buy', 'spawn'):
        import gameplay_v29.pn_admin as pn_admin
        is_owner = pn_admin.rank(uid) == 4
        if action == 'spawn' and (not is_admin):
            raise ValueError('Ücretsiz araç üretme yönetici yetkisi gerektirir.')
        model = str(payload.get('model', '')).lower()
        if model not in SPAWN_MODELS or (action == 'buy' and model not in CATALOG):
            raise ValueError('Geçersiz araç modeli. /galeri aç veya /veh sultan kullan; “model” örnek yer tutucudur.')
        rate(token, 'vehicle-buy', 1)
        cost = 0 if action == 'spawn' else CATALOG.get(model)
        if cost is None:
            raise ValueError('Bu araç satılık değil; yönetici /veh komutunu kullanabilir.')
        position = dict(**spawn_location(state, model), heading=state['heading'], rx=0, ry=0, rz=state['heading'], vx=0, vy=0, vz=0, body=1000, engine=False, fuel=100, km=0)
        with database() as db:
            count = db.execute('SELECT COUNT(*) FROM pn_vehicles WHERE owner=?', (cid,)).fetchone()[0]
            if count >= 20 and (not is_owner):
                raise ValueError('Garaj sınırı: 20 araç.')
            changed = db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?', (cost, uid, cost)).rowcount
            if not changed:
                raise ValueError('Yeterli paran yok.')
            plate = 'PN' + secrets.token_hex(3).upper()
            vid = db.execute('INSERT INTO pn_vehicles(owner,model,plate,state,updated) VALUES(?,?,?,?,?)', (cid, model, plate, json.dumps(position), time.time())).lastrowid
            audit(db, uid, action, {'id': vid, 'model': model, 'price': cost})
        return {'success': True, 'vehicle': public(vehicle(vid)), 'money': wallet(uid), 'notice': f'{model.upper()} · {plate} · ${cost:,}'}
    if action == 'garage':
        with database() as db:
            owned = [dict(r) for r in db.execute('SELECT * FROM pn_vehicles WHERE owner=?', (cid,))]
        with database() as db:
            donate_ids = {r['vehicle_id'] for r in db.execute('SELECT vehicle_id FROM pn_donate_vehicles WHERE user_id=? AND vehicle_id IS NOT NULL', (uid,))}
        return {'success': True, 'vehicles': [dict(id=r['id'], model=r['model'], plate=r['plate'], active=bool(r['active']), locked=bool(r['locked']), available=r['model'] in SPAWN_MODELS, donate=r['id'] in donate_ids, km=public(r).get('km', 0), fuel=public(r).get('fuel', 100)) for r in owned]}
    if action == 'exit':
        if p.get('seatbelt') and occupation(cid)[0]:
            raise ValueError('Önce kemerini çıkar (U).')
        release(cid)
        return {'success': True, 'vehicle_id': 0, 'seat': -2}
    try:
        vid = int(payload.get('id', 0))
    except (ValueError, TypeError):
        raise ValueError('Geçerli araç ID yaz.')
    row = vehicle(vid)
    data = public(row)
    owner = row['owner'] == cid or is_admin
    if action == 'belt':
        if occupation(cid)[0] != vid:
            raise ValueError('Kemer için bu araçta oturmalısın.')
        if row['model'] in ('bati', 'faggio'):
            raise ValueError('Bu araçta emniyet kemeri yok.')
        p['seatbelt'] = not p.get('seatbelt', False)
        return dict(success=True, seatbelt=p['seatbelt'], notice='Emniyet kemeri ' + ('bağlandı.' if p['seatbelt'] else 'çıkarıldı.'))
    if action == 'indicator':
        if occupation(cid) != (vid, -1):
            raise ValueError('Sinyali yalnız sürücü değiştirebilir.')
        signal = payload.get('signal')
        if signal not in ('off', 'left', 'right', 'hazard'):
            raise ValueError('Geçersiz sinyal.')
        fields = dict(VEHICLE_CACHE.get(vid, data))
        fields['indicators'] = signal
        VEHICLE_CACHE[vid] = fields
        persist_vehicle(vid)
        return dict(success=True, vehicle=public(vehicle(vid)), notice='Sinyal: ' + {'off': 'kapalı', 'left': 'sol', 'right': 'sağ', 'hazard': 'dörtlü'}[signal])
    if action == 'lights':
        if occupation(cid) != (vid, -1):
            raise ValueError('Farları yalnız sürücü değiştirebilir.')
        rate(token, 'vehicle-lights', 0.2)
        fields = dict(VEHICLE_CACHE.get(vid, data))
        fields['lights'] = (fields.get('lights', 0) + 1) % 3
        VEHICLE_CACHE[vid] = fields
        persist_vehicle(vid)
        return dict(success=True, vehicle=public(vehicle(vid)), notice='Farlar: ' + ['kapalı', 'kısa', 'uzun'][fields['lights']])
    with database() as db:
        job_car = db.execute('SELECT borrower FROM pn_job_vehicles WHERE vehicle_id=?', (vid,)).fetchone()
    if job_car and job_car['borrower'] != cid and (not is_admin):
        raise ValueError('Bu meslek aracı sana atanmadı. Önce ilgili mesleğe başla.')
    import gameplay_v29.pn_roleplay as pn_roleplay
    shared_key = pn_roleplay.vehicle_access(vid, cid)
    job_key = bool(job_car and job_car['borrower'] == cid)
    key = owner or shared_key or job_key or traffic.has_key(vid, cid)
    if action == 'entry-access':
        if not row['active'] or not near(state, data):
            raise ValueError('Araca yaklaşmalısın (7 m).')
        return dict(success=True, has_key=bool(key), may_lockpick=not key and (not job_car), job_vehicle=bool(job_car))
    if row['model'] not in __import__('gameplay_v29.pn_traffic', fromlist=['*']).ROAD_MODELS:
        raise ValueError('Bu eski kayıttaki araç modeli geçersiz; galeriden desteklenen bir model seç.')
    if action == 'engine':
        if occupation(cid) != (vid, -1):
            raise ValueError('Motoru yalnız sürücü açabilir.')
        if not key and row['owner'] != 0:
            raise ValueError('Motor anahtarın yok; önce kilidi maymuncukla aç.')
        if data.get('fuel', 100) <= 0:
            raise ValueError('Yakıt bitti.')
        rate(token, 'vehicle-engine', 0.5)
        fields = dict(VEHICLE_CACHE.get(vid, json.loads(row['state'])))
        fields['engine'] = not fields.get('engine', False)
        fields['fuel_at'] = time.time()
        VEHICLE_CACHE[vid] = fields
        persist_vehicle(vid)
        return {'success': True, 'vehicle': public(vehicle(vid)), 'notice': 'Motor ' + ('çalıştırıldı.' if fields['engine'] else 'durduruldu.')}
    if action == 'retrieve':
        if not owner and (not shared_key):
            raise ValueError('Bu araç sana veya birliğine ait değil.')
        if any((v == vid for v, s in SEATS)):
            raise ValueError('Araç kullanımda.')
        if row['active']:
            return {'success': True, 'vehicle': data, 'notice': f'Araç #{vid} zaten dünyada: {data['x']:.0f}, {data['y']:.0f}'}
        data.update(**spawn_location(state, row['model'], vid), heading=state['heading'], rx=0, ry=0, rz=state['heading'], vx=0, vy=0, vz=0)
        fields = {k: data[k] for k in ('x', 'y', 'z', 'heading', 'rx', 'ry', 'rz', 'vx', 'vy', 'vz', 'body')}
        fields.update(engine=False, fuel=data.get('fuel', 100), km=data.get('km', 0), mods=data.get('mods', {}))
        with database() as db:
            db.execute('UPDATE pn_vehicles SET active=1,state=?,updated=? WHERE id=?', (json.dumps(fields), time.time(), vid))
        VEHICLE_CACHE[vid] = fields
        SAVED_AT[vid] = time.time()
        return {'success': True, 'vehicle': public(vehicle(vid)), 'notice': f'Araç #{vid} garajdan çıkarıldı.'}
    if not row['active'] or not near(state, data):
        raise ValueError('Araca yaklaşmalısın (7 m).')
    if action == 'park':
        if not owner and (not shared_key):
            raise ValueError('Bu araç sana veya birliğine ait değil.')
        if any((v == vid for v, s in SEATS)):
            raise ValueError('Önce herkes araçtan insin.')
        fields = dict(VEHICLE_CACHE.get(vid, json.loads(row['state'])))
        fields.update(engine=False, vx=0, vy=0, vz=0)
        with database() as db:
            db.execute('UPDATE pn_vehicles SET active=0,state=?,updated=? WHERE id=?', (json.dumps(fields), time.time(), vid))
        VEHICLE_CACHE[vid] = fields
        SAVED_AT[vid] = time.time()
        return {'success': True, 'removed_vehicle': vid, 'notice': 'Araç garaja kaydedildi.'}
    if action == 'lock':
        if not (row['owner'] == cid or shared_key or job_key or traffic.has_key(vid, cid) or (is_admin and p.get('admin_duty'))):
            raise ValueError('Araç anahtarın veya açık yönetici görevin yok.')
        rate(token, 'vehicle-lock', 0.5)
        with database() as db:
            db.execute('UPDATE pn_vehicles SET locked=? WHERE id=?', (int(not row['locked']), vid))
        from gameplay_v29.pn_multiplayer import emote
        emote(p, state, 'aracını ' + ('kilitledi.' if not row['locked'] else 'kilidini açtı.'))
        return {'success': True, 'notice': 'Kapılar ' + ('kilitlendi.' if not row['locked'] else 'açıldı.')}
    if action in ('window', 'door'):
        index = payload.get('index')
        opened = payload.get('open')
        if type(index) is not int or not 0 <= index < (4 if action == 'window' else 6) or type(opened) is not bool:
            raise ValueError('Geçersiz kapı / cam seçimi.')
        occupied = occupation(cid)
        if not key and occupied[0] != vid:
            raise ValueError('Araç anahtarın veya koltuğun yok.')
        if row['locked'] and occupied[0] != vid:
            raise ValueError('Önce kilidi aç.')
        if not key and (action == 'door' or (occupied[1] != -1 and index != occupied[1] + 1)):
            raise ValueError('Yalnız kendi camını kontrol edebilirsin.')
        fields = dict(VEHICLE_CACHE.get(vid, json.loads(row['state'])))
        mask = fields.get(action + 's', 0)
        fields[action + 's'] = mask | 1 << index if opened else mask & ~(1 << index)
        VEHICLE_CACHE[vid] = fields
        persist_vehicle(vid)
        from gameplay_v29.pn_multiplayer import emote
        emote(p, state, ('camını' if action == 'window' else 'kapısını') + (' açtı.' if opened else ' kapattı.'))
        return {'success': True, 'vehicle': public(vehicle(vid)), 'notice': ('Cam' if action == 'window' else 'Kapı') + (' açıldı.' if opened else ' kapatıldı.')}
    if action == 'enter':
        allowed = tuple(range(-1, data['seats'] - 1)) if data.get('street') else (-1, 0) if row['model'] in ('blista', 'zentorno', 'adder', 'bati', 'faggio', 't20', 'turismor', 'banshee', 'comet2', 'i8', 'skyline') else (-1, 0, 1, 2)
        current = occupation(cid)
        requested = payload.get('seat')
        if requested is not None and (type(requested) is not int or requested not in allowed):
            raise ValueError('Bu araçta uygun boş koltuk yok.')
        if current[0] == vid and (requested is None or requested == current[1]):
            SEATS[current]['time'] = time.time()
            return {'success': True, 'vehicle_id': vid, 'seat': current[1]}
        seat = requested if requested is not None else next((s for s in allowed if (vid, s) not in SEATS), -2)
        if seat not in allowed:
            raise ValueError('Bu araçta uygun boş koltuk yok.')
        if row['locked']:
            if not key:
                raise ValueError('Kapılar kilitli. Anahtar sahibi /kilit ile açabilir.')
            with database() as db:
                db.execute('UPDATE pn_vehicles SET locked=0 WHERE id=?', (vid,))
        if (vid, seat) in SEATS and SEATS[vid, seat]['char_id'] != cid:
            raise ValueError('Bu koltuk dolu.')
        release(cid)
        SEATS[vid, seat] = {'char_id': cid, 'time': time.time()}
        if row['owner'] == 0 and seat == -1 and (not job_car):
            with database() as db:
                traffic.grant_key(db, vid, cid)
        return {'success': True, 'vehicle_id': vid, 'seat': seat, 'vehicle': public(vehicle(vid))}
    if action in ('break-start', 'break-step', 'break-finish', 'break-cancel'):
        if job_car:
            raise ValueError('Meslek araçlarında maymuncuk kullanılmaz. Sana atanan aracın anahtarı meslek süresince geçerlidir.')
        return traffic.lockpick(action, uid, token, payload, p, state, row)
    raise ValueError('Araç işlemi bulunamadı.')

def validate_sample(p, state, payload):
    vid, seat = occupation(p['char_id'])
    data = payload.get('vehicle_sample')
    if not vid or seat != -1 or (not isinstance(data, dict)) or (data.get('id') != vid):
        return None
    fields = {k: float(data.get(k, 0)) for k in ('x', 'y', 'z', 'heading', 'rx', 'ry', 'rz', 'vx', 'vy', 'vz', 'body')}
    if not all((math.isfinite(v) for v in fields.values())) or abs(fields['x']) > 16000 or abs(fields['y']) > 16000 or (not -1700 < fields['z'] < 2700) or any((abs(fields[k]) > 250 for k in ('vx', 'vy', 'vz'))):
        raise ValueError('Geçersiz araç konumu.')
    if not near(state, fields, 12):
        raise ValueError('Araç sürücüden çok uzakta.')
    fields['body'] = max(0, min(1000, fields['body']))
    old = public(vehicle(vid))
    elapsed = max(0, min(3, time.time() - SEATS[vid, seat].get('sample_at', time.time())))
    distance = min(math.sqrt(sum(((fields[k] - old[k]) ** 2 for k in ('x', 'y', 'z')))), math.sqrt(sum((fields[k] ** 2 for k in ('vx', 'vy', 'vz')))) * elapsed + 2)
    fields.update(**{k: old[k] for k in ('street', 'seats', 'pose_epoch', 'repair_epoch', 'indicators', 'fuel_at', 'mods', 'lights') if k in old}, windows=old.get('windows', 0), doors=old.get('doors', 0), engine=bool(old.get('engine', False)), km=old.get('km', 0) + distance / 1000, fuel=max(0, old.get('fuel', 100) - (distance * 4e-05 if old.get('engine') else 0)))
    if fields['fuel'] <= 0:
        fields['engine'] = False
    return fields

def persist_vehicle(vid):
    if vid not in VEHICLE_CACHE:
        return
    with database() as db:
        db.execute('UPDATE pn_vehicles SET state=?,updated=? WHERE id=? AND active=1', (json.dumps(VEHICLE_CACHE[vid]), time.time(), vid))
    SAVED_AT[vid] = time.time()

def sample(p, state, payload):
    vid, seat = occupation(p['char_id'])
    state.update(vehicle_id=vid, seat=seat)
    if not vid:
        return
    SEATS[vid, seat]['time'] = time.time()
    if seat != -1:
        return
    fields = validate_sample(p, state, payload)
    if fields is None:
        return
    VEHICLE_CACHE[vid] = fields
    SEATS[vid, seat]['sample_at'] = time.time()
    if time.time() - SAVED_AT.get(vid, 0) >= 3:
        persist_vehicle(vid)
