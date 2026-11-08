"""Bounded multiplayer services. Caller holds session_api.LOCK.

Gameplay damage uses client native hit reports plus server distance/cooldown
checks. It is not an authoritative physics simulation or a complete anti-cheat.
Voice is transient PCM relayed by this VDS, without third-party STUN/TURN.
"""
import base64
import binascii
import json
import math
import time
import unicodedata
import secrets
from collections import deque
from contextlib import contextmanager, nullcontext
import online_engine as engine
CHAT_RADIUS = {'local': 25, 'me': 20, 'do': 20, 'ooc': 40}
VOICE_RADIUS = 30
VOICE = deque(maxlen=512)
voice_sequence = 0
VOICE_EPOCH = secrets.token_hex(8)
RATES = {}

@contextmanager
def database():
    import gameplay_v29.pn_storage as pn_storage
    with pn_storage.database() as db:
        yield db

def identity(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().replace('̇', '').replace('ı', 'i').split())

def schema(db):
    import gameplay_v29.pn_world as pn_world
    pn_world.schema(db)
    import gameplay_v29.pn_roleplay as pn_roleplay
    pn_roleplay.schema(db)
    import gameplay_v29.pn_city as pn_city
    pn_city.schema(db)
    import gameplay_v29.pn_commands as pn_commands, gameplay_v29.pn_containers as pn_containers, gameplay_v29.pn_phone as pn_phone
    pn_commands.schema(db)
    pn_containers.schema(db)
    pn_phone.schema(db)
    import gameplay_v29.pn_economy as pn_economy, gameplay_v29.pn_support as pn_support, gameplay_v29.pn_social as pn_social
    pn_economy.schema(db)
    pn_support.schema(db)
    pn_social.schema(db)
    db.execute('CREATE TABLE IF NOT EXISTS pn_identity(kind TEXT,key TEXT,owner INTEGER,PRIMARY KEY(kind,key))')
    db.execute('CREATE TABLE IF NOT EXISTS pn_saved(char_id INTEGER PRIMARY KEY,state TEXT NOT NULL,updated REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_chat(id INTEGER PRIMARY KEY AUTOINCREMENT,char_id INTEGER,name TEXT,body TEXT,scope TEXT,x REAL,y REAL,z REAL,created REAL)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_chat_recent ON pn_chat(created)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_private_chat(id INTEGER PRIMARY KEY,sender INTEGER NOT NULL,target INTEGER NOT NULL,name TEXT NOT NULL,target_name TEXT NOT NULL,body TEXT NOT NULL,created REAL NOT NULL)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_private_recent ON pn_private_chat(target,created)')
    if 'admin' not in [r[1] for r in db.execute('PRAGMA table_info(pn_chat)')]:
        db.execute('ALTER TABLE pn_chat ADD COLUMN admin INTEGER NOT NULL DEFAULT 0')
    if 'dimension' not in [r[1] for r in db.execute('PRAGMA table_info(pn_chat)')]:
        db.execute('ALTER TABLE pn_chat ADD COLUMN dimension INTEGER NOT NULL DEFAULT 0')
    db.execute('CREATE TABLE IF NOT EXISTS pn_sessions(hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL,expires REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_character_archive(char_id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,archived REAL NOT NULL)')
    for row in db.execute('SELECT id,username FROM users ORDER BY id').fetchall():
        db.execute('INSERT OR IGNORE INTO pn_identity VALUES(?,?,?)', ('account', identity(row['username']), row['id']))
    for row in db.execute('SELECT id,name,surname FROM characters ORDER BY id').fetchall():
        db.execute('INSERT OR IGNORE INTO pn_identity VALUES(?,?,?)', ('character', identity(row['name'] + ' ' + row['surname']), row['id']))

def reserve(db, kind, label, owner):
    key = identity(label)
    row = db.execute('SELECT owner FROM pn_identity WHERE kind=? AND key=?', (kind, key)).fetchone()
    if row and row['owner'] != owner:
        raise ValueError('Bu kullanıcı adı zaten alınmış.' if kind == 'account' else 'Bu karakterin ad ve soyadı zaten alınmış.')
    db.execute('INSERT OR IGNORE INTO pn_identity VALUES(?,?,?)', (kind, key, owner))

def initial(character):
    with database() as db:
        schema(db)
        row = db.execute('SELECT state FROM pn_saved WHERE char_id=?', (character['id'],)).fetchone()
    saved = json.loads(row['state']) if row else {}
    state = {key: saved.get(key, character.get('pos_' + key, default)) for key, default in [('x', 215.7), ('y', -920.3), ('z', 30.6), ('heading', 0), ('health', 200)]}
    state.update(hunger=max(0, min(100, float(saved.get('hunger', 100)))), thirst=max(0, min(100, float(saved.get('thirst', 100)))), food=max(0, int(saved.get('food', 3))), water=max(0, int(saved.get('water', 3))))
    state['armor'] = max(0, min(100, int(saved.get('armor', 0))))
    if saved.get('dimension'):
        with database() as db:
            door = db.execute('SELECT x,y,z,heading FROM pn_properties WHERE id=?', (saved['dimension'],)).fetchone()
        if door:
            state.update(dict(door))
    return state

def save(presence, state, force=False, connection=None):
    now = time.time()
    if not force and now - presence.get('saved_at', 0) < 3:
        return
    presence['saved_at'] = now
    values = {key: state[key] for key in ('x', 'y', 'z', 'heading', 'health')}
    values.update({key: presence.get(key, default) for key, default in [('hunger', 100), ('thirst', 100), ('food', 3), ('water', 3)]})
    values['armor'] = presence.get('armor', 0)
    values['dimension'] = presence.get('dimension', 0)
    with database() if connection is None else nullcontext(connection) as db:
        db.execute('INSERT INTO pn_saved VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,updated=excluded.updated', (presence['char_id'], json.dumps(values), now))
        db.execute('UPDATE characters SET pos_x=?,pos_y=?,pos_z=? WHERE id=?', (state['x'], state['y'], state['z'], presence['char_id']))

def distance(a, b):
    return math.sqrt(sum(((a[k] - b[k]) ** 2 for k in ('x', 'y', 'z'))))

def active(states, now=None):
    now = now or time.time()
    return [p for p in states.values() if now - p['last_seen'] < 10]

def emote(p, state, body):
    with database() as db:
        db.execute('INSERT INTO pn_chat(char_id,name,body,scope,x,y,z,created,dimension) VALUES(?,?,?,?,?,?,?,?,?)', (p['char_id'], p['name'], body, 'me', state['x'], state['y'], state['z'], time.time(), p.get('dimension', 0)))

def messages(state):
    if not state:
        return []
    with database() as db:
        rows = db.execute('SELECT * FROM pn_chat WHERE created>? ORDER BY id DESC LIMIT 100', (time.time() - 300,)).fetchall()
        private = db.execute('SELECT * FROM pn_private_chat WHERE created>? AND (sender=? OR target=?) ORDER BY id DESC LIMIT 50', (time.time() - 300, state['char_id'], state['char_id'])).fetchall()
    result = [dict(m) for m in reversed(rows) if m['scope'] in CHAT_RADIUS and m['dimension'] == state.get('dimension', 0) and (distance(state, m) <= CHAT_RADIUS[m['scope']])]
    result.extend((dict(m, scope='pm', char_id=m['sender'], admin=0) for m in private))
    return sorted(result, key=lambda m: m['id'])[-100:]

def rate(token, key, interval):
    now = time.time()
    pair = (token, key)
    if now - RATES.get(pair, 0) < interval:
        raise ValueError('Çok hızlı işlem gönderiyorsun.')
    RATES[pair] = now
    if len(RATES) > 1000:
        for stale in list(RATES):
            if now - RATES[stale] > 60:
                RATES.pop(stale, None)

def chat(token, payload, presence, state):
    if not state:
        raise ValueError('Sohbet için önce GTA dünyasına girin.')
    raw = str(payload.get('message', '')).strip()
    if raw.lower().startswith('/pm '):
        from gameplay_v29.session_api import PRESENCE
        pieces = raw.split(None, 2)
        if len(pieces) != 3 or not 1 <= len(pieces[2].strip()) <= 200:
            raise ValueError('Kullanım: /pm ID mesaj')
        import gameplay_v29.pn_world as pn_world
        cid = pn_world.resolve_player_id(pieces[1], PRESENCE)
        peer = next((v for v in PRESENCE.values() if v['char_id'] == cid and time.time() - v['last_seen'] < 20), None)
        if not peer:
            raise ValueError('Oyuncu şu anda çevrim içi değil.')
        if cid == presence['char_id']:
            raise ValueError('Kendine özel mesaj gönderemezsin.')
        rate(token, 'chat', 0.6)
        presence['activity_at'] = time.time()
        with database() as db:
            mid = db.execute("INSERT INTO pn_chat(char_id,name,body,scope,x,y,z,created) VALUES(?,?,'','local',0,0,0,0)", (presence['char_id'], presence['name'])).lastrowid
            db.execute('DELETE FROM pn_chat WHERE id=?', (mid,))
            db.execute('INSERT INTO pn_private_chat VALUES(?,?,?,?,?,?,?)', (mid, presence['char_id'], cid, presence['name'], peer['name'], pieces[2].strip(), time.time()))
            db.execute('DELETE FROM pn_private_chat WHERE created<?', (time.time() - 86400,))
        return {'success': True, 'notice': peer['name'] + ' için özel mesaj gönderildi.'}
    scope = 'ooc' if payload.get('scope') == 'ooc' else 'local'
    if raw.startswith('/'):
        pieces = raw[1:].split(None, 1)
        command = pieces[0] if pieces else ''
        raw = pieces[1] if len(pieces) > 1 else ''
        scope = {'me': 'me', 'do': 'do', 'b': 'ooc', 'ooc': 'ooc'}.get(command.lower())
        if not scope:
            raise ValueError('Bilinmeyen komut. /yardim yaz; / ile komut önerilerini aç.')
    if scope not in CHAT_RADIUS or not 1 <= len(raw.strip()) <= 200:
        raise ValueError('Mesaj 1–200 karakter olmalı.')
    rate(token, 'chat', 0.6)
    presence['activity_at'] = time.time()
    with database() as db:
        db.execute('INSERT INTO pn_chat(char_id,name,body,scope,x,y,z,created,admin,dimension) VALUES(?,?,?,?,?,?,?,?,?,?)', (presence['char_id'], presence['name'], raw.strip(), scope, state['x'], state['y'], state['z'], time.time(), int(presence.get('admin_duty', False) and (not presence.get('hide_admin'))), presence.get('dimension', 0)))
        db.execute('DELETE FROM pn_chat WHERE created<?', (time.time() - 86400,))
    return {'success': True}

def voice(token, payload, presence, state):
    global voice_sequence
    if not state:
        raise ValueError('Ses için önce GTA dünyasına girin.')
    data = payload.get('audio', '')
    if not isinstance(data, str) or len(data) > 11000:
        raise ValueError('Geçersiz ses paketi.')
    try:
        raw = base64.b64decode(data, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError('Geçersiz ses paketi.')
    if not 320 <= len(raw) <= 8000 or len(raw) % 2:
        raise ValueError('Geçersiz PCM paketi.')
    rate(token, 'voice', 0.09)
    voice_sequence += 1
    presence['activity_at'] = time.time()
    VOICE.append(dict(seq=voice_sequence, char_id=presence['char_id'], audio=data, time=time.time(), x=state['x'], y=state['y'], z=state['z'], dimension=presence.get('dimension', 0)))
    state['speaking_until'] = time.time() + 0.7
    return {'success': True}

def audio(state, cursor):
    now = time.time()
    while VOICE and now - VOICE[0]['time'] > 2:
        VOICE.popleft()
    from gameplay_v29.pn_phone import call_peer
    call = call_peer(state['char_id'])
    return [dict(v, age=max(0, now - v['time']), **{'x': state['x'], 'y': state['y'], 'z': state['z'], 'phone': True} if v['char_id'] == call else {}) for v in VOICE if v['seq'] > cursor and v['char_id'] != state['char_id'] and (v['char_id'] == call or (v.get('dimension', 0) == state.get('dimension', 0) and distance(state, v) <= VOICE_RADIUS))][-64:]

def voice_poll(payload, presence, state):
    import gameplay_v29.pn_world as pn_world
    pn_world.live(presence, state)
    cursor = payload.get('cursor', 0)
    if type(cursor) is not int or not 0 <= cursor <= 2 ** 53:
        raise ValueError('Geçersiz ses sırası.')
    return {'success': True, 'voice': audio(state, cursor), 'voice_cursor': voice_sequence, 'voice_epoch': VOICE_EPOCH, 'server_time': time.time()}

def needs(presence, now=None):
    now = time.time() if now is None else now
    elapsed = max(0, min(5, now - presence.get('needs_at', now)))
    presence['needs_at'] = now
    if presence.get('health', 200) > 100:
        presence['hunger'] = max(0, presence.get('hunger', 100) - elapsed / 60)
        presence['thirst'] = max(0, presence.get('thirst', 100) - elapsed / 40)
    return {key: presence.get(key, default) for key, default in [('hunger', 100), ('thirst', 100), ('food', 3), ('water', 3)]}

def consume(token, payload, presence, state):
    if not presence or not state or presence.get('health', 200) <= 100:
        raise ValueError('Tüketmek için hayatta ve oyunda olmalısın.')
    item = payload.get('item')
    if item not in ('food', 'water'):
        raise ValueError('Geçersiz eşya.')
    if presence.get(item, 3) <= 0:
        raise ValueError('Çantanda bu eşya kalmadı.')
    rate(token, 'consume', 2)
    needs(presence)
    presence[item] = presence.get(item, 3) - 1
    key = 'hunger' if item == 'food' else 'thirst'
    presence[key] = min(100, presence.get(key, 100) + (30 if item == 'food' else 35))
    presence['activity_at'] = time.time()
    presence['activity'] = dict(kind=item, until=time.time() + 3)
    save(presence, state, True)
    with database() as db:
        db.execute('INSERT INTO pn_chat(char_id,name,body,scope,x,y,z,created,dimension) VALUES(?,?,?,?,?,?,?,?,?)', (presence['char_id'], presence['name'], 'yemeğini yedi.' if item == 'food' else 'suyunu içti.', 'me', state['x'], state['y'], state['z'], time.time(), presence.get('dimension', 0)))
    return {'success': True, 'needs': needs(presence)}

def update(token, payload, fields, presence, states, presences):
    now = time.time()
    old = states.get(token)
    life = presence.get('life_id', 0)
    supplied = payload.get('life_id', life)
    if type(supplied) is not int or supplied < 0 or supplied > life:
        raise ValueError('Geçersiz yaşam sürümü.')
    if supplied != life and old:
        old['last_seen'] = now
        return snapshot(presence, old, states, presences, presence.get('hit_sequence', 0), max(0, int(payload.get('voice_cursor', 0))), presence.get('respawn_spawn'), payload.get('separate_voice') is not True)
    import gameplay_v29.pn_inventory as pn_inventory
    loadout = pn_inventory.view(presence, False)
    fields['weapon'] = loadout['weapon']
    selected = next((k for k, v in pn_inventory.WEAPONS.items() if v['slot'] == loadout['selected']), None)
    fields['weapon_tint'] = loadout.get('tints', {}).get(selected, 0)
    shot_budget = loadout['ammo'] if loadout['weapon'] != pn_inventory.UNARMED else 0
    accepted_shots = 0
    fields['flags'] = int(payload.get('flags', 0)) & 255
    import gameplay_v29.pn_interactions as pn_interactions, gameplay_v29.pn_admin as pn_admin
    presence['godmode'] = bool(presence.get('godmode') and pn_admin.rank(presence['user_id']) >= 2)
    fields['fly'] = bool(presence.get('fly') and pn_admin.rank(presence['user_id']) >= 2)
    pn_interactions.clean(presences)
    pn_interactions.constrain(presence, fields, states)
    for key in ('vx', 'vy', 'vz', 'aim_x', 'aim_y', 'aim_z'):
        value = float(payload.get(key, 0))
        if not math.isfinite(value) or abs(value) > 20000:
            raise ValueError('Geçersiz hareket durumu.')
        fields[key] = value
    hits = payload.get('hits', [])
    if not isinstance(hits, list) or len(hits) > 8:
        raise ValueError('Geçersiz vuruş paketi.')
    if any((not isinstance(h, dict) or not isinstance(h.get('seq'), int) or (not isinstance(h.get('target'), int)) or (h.get('kind') not in ('melee', 'shoot')) for h in hits)):
        raise ValueError('Geçersiz vuruş paketi.')
    cursor = max(0, int(payload.get('voice_cursor', 0)))
    import gameplay_v29.pn_world as pn_world
    import gameplay_v29.pn_admin as pn_admin
    teleport = pn_admin.constraints(presence, fields)
    pn_world.clean_seats(presences)
    pn_world.validate_sample(presence, fields, payload)
    armor = float(payload.get('armor', presence.get('armor', 0)))
    if not math.isfinite(armor):
        raise ValueError('Geçersiz zırh.')
    hp = presence.get('health', 200)
    old_hp = hp
    if not presence.get('godmode') and now - presence.get('respawned_at', 0) > 0.7 and (0 <= fields['health'] < hp):
        hp = fields['health']
    presence['health'] = max(0, min(200, hp))
    armor_ack = 'armor_version' not in payload or (payload.get('armor_applied') == payload['armor_version'] and payload.get('armor_target') == presence.get('armor', 0))
    old_armor = presence.get('armor', 0)
    if now >= presence.get('armor_ready_at', 0) and armor_ack:
        presence['armor'] = max(0, min(old_armor, armor))
    fields['armor'] = presence['armor']
    if presence['health'] <= 100:
        presence.setdefault('dead_at', now)
    fields['health'] = presence['health']
    last = presence.get('hit_sequence', 0)
    for hit in hits:
        seq = int(hit.get('seq', 0))
        if seq <= last:
            continue
        last = seq
        victim = next((pair for pair in states.items() if pair[1]['char_id'] == int(hit.get('target', 0)) and now - pair[1]['last_seen'] < 10), None)
        if not victim or victim[0] == token or presence['health'] <= 100:
            continue
        melee = hit.get('kind') == 'melee'
        limit = 3 if melee else 200
        if not melee and shot_budget <= 0:
            continue
        if distance(fields, victim[1]) > limit or now - presence.get('last_hit_time', 0) < 0.16:
            continue
        presence['last_hit_time'] = now
        target_presence = presences.get(victim[0])
        if not target_presence:
            continue
        if target_presence.get('dimension', 0) != presence.get('dimension', 0):
            continue
        if (target_presence.get('fly') or target_presence.get('godmode')) and pn_admin.rank(target_presence['user_id']) >= 2:
            continue
        if not melee:
            shot_budget -= 1
            accepted_shots += 1
        damage = 20 if melee else 25
        if not melee:
            absorbed = min(damage, target_presence.get('armor', 0))
            target_presence['armor'] = target_presence.get('armor', 0) - absorbed
            damage -= absorbed
            victim[1]['armor'] = target_presence['armor']
        target_presence['health'] = max(0, target_presence.get('health', 200) - damage)
        victim[1]['health'] = target_presence['health']
        target_presence['damage_sequence'] = target_presence.get('damage_sequence', 0) + 1
        target_presence['damage_kind'] = 1 if melee else 2
        if target_presence['health'] <= 100:
            target_presence.setdefault('dead_at', now)
            import gameplay_v29.pn_roleplay as pn_roleplay
            pn_roleplay.combat_event(target_presence['char_id'], target_presence.get('life_id', 0), presence['char_id'])
    presence['hit_sequence'] = last
    fields['speaking_until'] = old.get('speaking_until', 0) if old else 0
    activity = payload.get('activity')
    if old is None or (old and distance(fields, old) > 0.15) or activity != presence.get('input_activity'):
        presence['activity_at'] = now
    presence['input_activity'] = activity if type(activity) is int else 0
    fields['afk_seconds'] = max(0, int(now - presence.get('activity_at', now)))
    fields['dimension'] = presence.get('dimension', 0)
    fields['seatbelt'] = bool(presence.get('seatbelt') and pn_world.occupation(presence['char_id'])[0])
    if not fields['seatbelt']:
        presence['seatbelt'] = False
    fields['activity'] = presence.get('activity') if presence.get('activity', {}).get('until', 0) > now else None
    import gameplay_v29.pn_city as pn_city
    fields.update(pn_city.public_profile(presence['user_id']))
    fields['country'] = __import__('gameplay_v29.pn_commands', fromlist=['*']).country(presence['char_id'])
    fields.update(char_id=presence['char_id'], server_id=presence['server_id'], name=presence['name'], last_seen=now)
    target = int(payload.get('melee_target', 0))
    target_state = next((s for s in states.values() if s['char_id'] == target and now - s['last_seen'] < 10 and (s.get('health', 200) > 100)), None)
    fields['melee_target'] = target if fields['flags'] & 32 and target_state and (target != presence['char_id']) and (distance(fields, target_state) < 4) else 0
    fields.update(appearance=presence['appearance'], appearance_version=presence['appearance_version'], admin_duty=presence.get('admin_duty', False) and (not presence.get('hide_admin')), damage_sequence=presence.get('damage_sequence', 0), damage_kind=presence.get('damage_kind', 0))
    pn_world.sample(presence, fields, payload)
    import gameplay_v29.pn_inventory as pn_inventory
    pn_inventory.sample(presence, payload)
    if accepted_shots:
        key = next((k for k, v in pn_inventory.WEAPONS.items() if v['hash'] == loadout['weapon']))
        remaining = max(0, loadout['ammo'] - accepted_shots)
        if presence['loadout']['owned'].get(key, 0) > remaining:
            presence['loadout']['owned'][key] = remaining
            pn_inventory.persist(presence)
    states[token] = fields
    vitals = needs(presence, now)
    save(presence, fields, force=old_hp != presence['health'] or old_armor != presence.get('armor', 0))
    return snapshot(presence, fields, states, presences, last, cursor, teleport, payload.get('separate_voice') is not True)

def snapshot(presence, fields, states, presences, last, cursor, teleport=None, include_voice=True):
    import gameplay_v29.pn_world as pn_world, gameplay_v29.pn_admin as pn_admin, gameplay_v29.pn_inventory as pn_inventory
    import gameplay_v29.pn_interactions as pn_interactions
    pn_interactions.clean(presences)
    fields['carried_by'] = pn_interactions.CARRY.get(fields['char_id'], 0)
    population = active(states)
    peers = sorted((p for p in population if p['char_id'] != fields['char_id'] and p.get('dimension', 0) == fields.get('dimension', 0) and (distance(fields, p) < 350)), key=lambda p: distance(fields, p))[:32]
    peers = [dict(p, carried_by=pn_interactions.CARRY.get(p['char_id'], 0)) for p in peers]
    delay = max(0, 5 - (time.time() - presence.get('dead_at', time.time()))) if presence['health'] <= 100 else 0
    return {'success': True, 'life_id': presence.get('life_id', 0), 'respawn_delay': delay, 'loadout': pn_inventory.view(presence, False), 'players': [fields] + peers, 'player_count': len(population), 'messages': messages(fields), 'voice': audio(fields, cursor) if include_voice else [], 'voice_cursor': voice_sequence, 'health': presence['health'], 'armor': presence['armor'], 'teleport': teleport, 'fly': bool(presence.get('fly') and pn_admin.rank(presence['user_id']) >= 2), 'godmode': bool(presence.get('godmode') and pn_admin.rank(presence['user_id']) >= 2), 'jail_until': (pn_admin.jail(presence['char_id']) or {}).get('until', 0), 'hit_ack': last, 'needs': needs(presence), **pn_world.view(presence['user_id'], presence, fields, presences)}
with database() as _db:
    schema(_db)
