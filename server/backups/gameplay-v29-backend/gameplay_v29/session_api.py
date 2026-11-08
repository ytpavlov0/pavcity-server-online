"""Authenticated account and character API for the browser launcher."""
import hashlib
import secrets
import time
import threading
import math
from contextlib import contextmanager
import online_engine as engine
import gameplay_v29.pn_multiplayer as multiplayer
import gameplay_v29.pn_world as world
import gameplay_v29.pn_admin as staff
import gameplay_v29.pn_storage as pn_storage
LOCK = threading.RLock()
SESSIONS = {}
PRESENCE = {}
GTA_STATE = {}

def allocate_player_id(excluding=None):
    used = {p['server_id'] for k, p in PRESENCE.items() if k != excluding and p.get('world') == 'gta' and ('server_id' in p)}
    for sid in range(1, 4097):
        if sid not in used:
            return sid
    raise ValueError('Sunucu oyuncu kapasitesine ulaştı.')

@contextmanager
def database():
    with pn_storage.database() as db:
        yield db

def password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 200000).hex()
    return f'pbkdf2${salt}${digest}'

def check_password(password, stored):
    if stored.startswith('pbkdf2$'):
        _, salt, digest = stored.split('$')
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 200000).hex()
        return secrets.compare_digest(actual, digest)
    return secrets.compare_digest(engine.hash_pw(password), stored)

def account(user_id):
    with database() as db:
        user = db.execute('SELECT id, username FROM users WHERE id=?', (user_id,)).fetchone()
        characters = [dict(r) for r in db.execute('SELECT * FROM characters WHERE user_id=? AND id NOT IN (SELECT char_id FROM pn_character_archive)', (user_id,))]
        archived = [dict(r) for r in db.execute('SELECT c.id,c.name,c.surname,a.archived FROM characters c JOIN pn_character_archive a ON a.char_id=c.id WHERE c.user_id=? ORDER BY a.archived DESC', (user_id,))]
    for ch in characters:
        ch.update(world.character(ch['id']))
    return {'success': True, 'user_id': user['id'], 'username': user['username'], 'characters': characters, 'archived_characters': archived, 'admin': world.admin(user_id), 'rank': staff.rank(user_id), 'money': world.wallet(user_id)}

def dispatch(path, payload, token):
    with LOCK, pn_storage.request():
        now = time.time()
        for key in list(SESSIONS):
            if SESSIONS[key]['expires'] < now:
                if key in GTA_STATE and key in PRESENCE:
                    multiplayer.save(PRESENCE[key], GTA_STATE[key], True)
                if key in PRESENCE:
                    world.release(PRESENCE[key]['char_id'])
                SESSIONS.pop(key)
                PRESENCE.pop(key, None)
                GTA_STATE.pop(key, None)
        for key, p in list(PRESENCE.items()):
            if now - p['last_seen'] > 120:
                if key in GTA_STATE:
                    multiplayer.save(p, GTA_STATE[key], True)
                world.release(p['char_id'])
                PRESENCE.pop(key, None)
                GTA_STATE.pop(key, None)
        if path in ('/api/auth/register', '/api/auth/login'):
            username = str(payload.get('username', '')).strip()
            password = str(payload.get('password', ''))
            if not 3 <= len(username) <= 32 or not 3 <= len(password) <= 128:
                raise ValueError('Kullanıcı adı 3–32, şifre 3–128 karakter olmalı.')
            with database() as db:
                multiplayer.schema(db)
                row = db.execute('SELECT users.* FROM users JOIN pn_identity p ON p.owner=users.id WHERE p.kind=? AND p.key=?', ('account', multiplayer.identity(username))).fetchone()
                if path.endswith('register'):
                    if len(password) < 8:
                        raise ValueError('Yeni hesap şifresi en az 8 karakter olmalı.')
                    if row:
                        raise ValueError('Bu kullanıcı adı kullanılıyor.')
                    uid = db.execute('INSERT INTO users(username,password_hash,created_at) VALUES(?,?,?)', (username, password_hash(password), now)).lastrowid
                    multiplayer.reserve(db, 'account', username, uid)
                else:
                    exact = db.execute('SELECT * FROM users WHERE username=? COLLATE BINARY', (username,)).fetchone()
                    matched = None
                    checked = set()
                    for candidate in (exact, row):
                        if candidate and candidate['id'] not in checked:
                            checked.add(candidate['id'])
                            if check_password(password, candidate['password_hash']):
                                matched = candidate
                                break
                    if not matched:
                        raise ValueError('Kullanıcı adı veya şifre hatalı.')
                    row = matched
                    uid = row['id']
                    if not row['password_hash'].startswith('pbkdf2$'):
                        db.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash(password), uid))
            staff.check(uid)
            new_token = secrets.token_urlsafe(32)
            SESSIONS[new_token] = {'user_id': uid, 'expires': now + 86400}
            with database() as db:
                db.execute('DELETE FROM pn_sessions WHERE expires<?', (now,))
                db.execute('INSERT INTO pn_sessions VALUES(?,?,?)', (hashlib.sha256(new_token.encode()).hexdigest(), uid, now + 86400))
            return (account(uid), new_token)
        session = SESSIONS.get(token)
        if not session and token:
            with database() as db:
                multiplayer.schema(db)
                row = db.execute('SELECT user_id,expires FROM pn_sessions WHERE hash=? AND expires>?', (hashlib.sha256(token.encode()).hexdigest(), now)).fetchone()
            if row:
                session = dict(row)
                SESSIONS[token] = session
        if not session:
            return ({'success': False, 'error': 'Oturum sona erdi. Tekrar giriş yapın.'}, None)
        uid = session['user_id']
        if path != '/api/auth/logout':
            staff.check(uid)
        if path.startswith(('/api/account/', '/api/properties/')) or path == '/api/services/open':
            import gameplay_v29.pn_city as pn_city
            return (pn_city.dispatch(path, uid, token, payload, PRESENCE.get(token), GTA_STATE.get(token), PRESENCE), None)
        if path != '/api/auth/logout' and session['expires'] - now < 43200:
            session['expires'] = now + 86400
            session['renew_cookie'] = True
            with database() as db:
                db.execute('UPDATE pn_sessions SET expires=? WHERE hash=?', (session['expires'], hashlib.sha256(token.encode()).hexdigest()))
        if any((path.startswith('/api/' + g + '/') for g in ('shops', 'keys', 'tuning', 'clothes'))):
            import gameplay_v29.pn_economy as pn_economy
            return (pn_economy.dispatch(path, uid, token, payload, PRESENCE.get(token), GTA_STATE.get(token), PRESENCE), None)
        if path.startswith('/api/social/'):
            import gameplay_v29.pn_social as pn_social
            return (pn_social.dispatch(path, uid, token, payload, PRESENCE.get(token), GTA_STATE.get(token)), None)
        if path.startswith('/api/reports/'):
            return (staff.reports(path, uid, token, payload, PRESENCE.get(token)), None)
        if path == '/api/auth/me':
            return (account(uid), None)
        if path == '/api/auth/logout':
            if token in GTA_STATE:
                multiplayer.save(PRESENCE[token], GTA_STATE[token], True)
            if token in PRESENCE:
                world.release(PRESENCE[token]['char_id'])
            SESSIONS.pop(token, None)
            with database() as db:
                db.execute('DELETE FROM pn_sessions WHERE hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
            PRESENCE.pop(token, None)
            GTA_STATE.pop(token, None)
            return ({'success': True}, '')
        if path == '/api/character/create':
            look = world.appearance(payload.get('appearance'))
            name = str(payload.get('name', '')).strip()
            surname = str(payload.get('surname', '')).strip()
            if not all((2 <= len(v) <= 24 and all((c.isalpha() or c in " '-" for c in v)) for v in (name, surname))):
                raise ValueError('Ad ve soyad 2–24 karakter olmalı; harf kullanın.')
            with database() as db:
                count = db.execute('SELECT COUNT(*) FROM characters WHERE user_id=? AND id NOT IN (SELECT char_id FROM pn_character_archive)', (uid,)).fetchone()[0]
                if count >= 3:
                    raise ValueError('En fazla 3 karakter oluşturabilirsiniz.')
                import gameplay_v29.pn_commands as pn_commands
                code = payload.get('country')
                if code and code not in pn_commands.COUNTRIES:
                    raise ValueError('Geçersiz ülke.')
                cid = db.execute('INSERT INTO characters(user_id,name,surname,role,created_at) VALUES(?,?,?,?,?)', (uid, name, surname, 'Sivil', now)).lastrowid
                pn_commands.country(cid, code or __import__('secrets').choice([c for c in pn_commands.COUNTRIES if c != 'other']))
                multiplayer.reserve(db, 'character', name + ' ' + surname, cid)
                character = dict(db.execute('SELECT * FROM characters WHERE id=?', (cid,)).fetchone())
                db.execute('INSERT INTO pn_character VALUES(?,?,1)', (cid, __import__('json').dumps(look)))
            character.update(world.character(cid))
            return ({'success': True, 'character': character}, None)
        if path in ('/api/character/archive', '/api/character/restore'):
            cid = int(payload.get('char_id', 0))
            with database() as db:
                if not db.execute('SELECT 1 FROM characters WHERE id=? AND user_id=?', (cid, uid)).fetchone():
                    raise ValueError('Karakter bulunamadı.')
                if any((p['char_id'] == cid and now - p['last_seen'] < 120 for p in PRESENCE.values())):
                    raise ValueError('Karakter bağlıyken kaldırılamaz. Önce karakter seçimine dön.')
                if path.endswith('archive'):
                    member = db.execute('SELECT leader FROM pn_faction_members WHERE char_id=?', (cid,)).fetchone()
                    if member and member['leader']:
                        raise ValueError('Birlik liderliğini devretmeden karakterini kaldıramazsın.')
                    db.execute('DELETE FROM pn_faction_members WHERE char_id=?', (cid,))
                    db.execute('DELETE FROM pn_faction_invites WHERE char_id=?', (cid,))
                    db.execute('INSERT OR IGNORE INTO pn_character_archive VALUES(?,?,?)', (cid, uid, now))
                else:
                    if db.execute('SELECT COUNT(*) FROM characters WHERE user_id=? AND id NOT IN (SELECT char_id FROM pn_character_archive)', (uid,)).fetchone()[0] >= 3:
                        raise ValueError('Geri yüklemek için boş karakter slotu gerekli.')
                    db.execute('DELETE FROM pn_character_archive WHERE char_id=? AND user_id=?', (cid, uid))
                world.audit(db, uid, path.rsplit('/', 1)[-1], {'char_id': cid})
            return (account(uid), None)
        if path == '/api/character/appearance':
            cid = int(payload.get('char_id', 0))
            with database() as db:
                if not db.execute('SELECT 1 FROM characters WHERE id=? AND user_id=? AND id NOT IN (SELECT char_id FROM pn_character_archive)', (cid, uid)).fetchone():
                    raise ValueError('Karakter bulunamadı.')
            p = PRESENCE.get(token)
            state = GTA_STATE.get(token)
            if p and state:
                if p['char_id'] != cid or p.get('health', 200) <= 100 or world.occupation(cid)[0] or (not world.at_barber(state)):
                    raise ValueError('Görünümünü değiştirmek için hayatta, yaya ve berberde olmalısın.')
            data = world.save_appearance(cid, payload.get('appearance'))
            for p in PRESENCE.values():
                if p['char_id'] == cid:
                    p.update(data)
            return ({'success': True, **data}, None)
        if path in ('/api/lobby/join', '/api/gta/join'):
            cid = int(payload.get('char_id', 0))
            with database() as db:
                ch = db.execute('SELECT * FROM characters WHERE id=? AND user_id=? AND id NOT IN (SELECT char_id FROM pn_character_archive)', (cid, uid)).fetchone()
            if not ch:
                raise ValueError('Karakter bulunamadı.')
            if any((p['char_id'] == cid and k != token and (now - p['last_seen'] < 20) for k, p in PRESENCE.items())):
                raise ValueError('Bu karakter başka cihazda bağlı. Başka bir karakter seçin.')
            for key, p in list(PRESENCE.items()):
                if key != token and p['char_id'] == cid:
                    if key in GTA_STATE:
                        multiplayer.save(p, GTA_STATE[key], True)
                    world.release(cid)
                    PRESENCE.pop(key, None)
                    GTA_STATE.pop(key, None)
            sid = allocate_player_id(token) if path == '/api/gta/join' else 0
            if token in PRESENCE and PRESENCE[token]['char_id'] == cid and (PRESENCE[token].get('world') == 'gta'):
                sid = PRESENCE[token]['server_id']
            if token in GTA_STATE:
                multiplayer.save(PRESENCE[token], GTA_STATE[token], True)
            if token in PRESENCE:
                world.release(PRESENCE[token]['char_id'])
            PRESENCE[token] = {'char_id': cid, 'name': ch['name'] + ' ' + ch['surname'], 'last_seen': now, 'x': cid % 8 * 2, 'z': 0, 'world': 'gta' if path == '/api/gta/join' else 'test', 'user_id': uid, 'server_id': sid, **world.character(cid)}
            GTA_STATE.pop(token, None)
            if path == '/api/gta/join':
                spawn = multiplayer.initial(dict(ch))
                if spawn['health'] <= 100:
                    spawn.update(world.HOSPITAL_SPAWN, health=200, armor=0)
                elif abs(spawn['x'] - 310.2) < 0.35 and abs(spawn['y'] + 590.1) < 0.35 and (abs(spawn['z'] - 43.2) < 0.35) or (abs(spawn['x'] - 329) < 6 and abs(spawn['y'] + 579.5) < 6 and (25 < spawn['z'] < 34)):
                    spawn.update(world.HOSPITAL_SPAWN)
                if staff.jail(cid):
                    spawn.update(staff.JAIL)
                PRESENCE[token]['health'] = spawn['health']
                PRESENCE[token]['armor'] = spawn['armor']
                PRESENCE[token].update({key: spawn[key] for key in ('hunger', 'thirst', 'food', 'water')})
                PRESENCE[token]['needs_at'] = now
                PRESENCE[token]['life_id'] = 0
                return ({'success': True, 'spawn': spawn, 'life_id': 0, 'server_id': sid, **world.character(cid), 'admin': world.admin(uid), 'can_spawn': staff.rank(uid) >= 2, 'money': world.wallet(uid)}, None)
            return ({'success': True}, None)
        if path == '/api/lobby/leave':
            if token in GTA_STATE:
                multiplayer.save(PRESENCE[token], GTA_STATE[token], True)
            if token in PRESENCE:
                world.release(PRESENCE[token]['char_id'])
            PRESENCE.pop(token, None)
            GTA_STATE.pop(token, None)
            return ({'success': True}, None)
        if path == '/api/gta/checkpoint':
            p = PRESENCE.get(token)
            state = GTA_STATE.get(token)
            if not p or not state or p.get('world') != 'gta':
                raise ValueError('Etkin karakter kaydı bulunamadı.')
            if payload.get('char_id') != p['char_id'] or payload.get('life_id') != p.get('life_id', 0):
                raise ValueError('Eski karakter veya can kaydı.')
            import gameplay_v29.pn_inventory as pn_inventory
            pn_inventory.sample(p, payload)
            armor = payload.get('armor')
            health = payload.get('health')
            if type(armor) in (int, float) and math.isfinite(armor) and (payload.get('armor_applied') == payload.get('armor_version')) and (payload.get('armor_target') == p.get('armor', 0)) and (now >= p.get('armor_ready_at', 0)):
                p['armor'] = max(0, min(p.get('armor', 0), armor))
            if type(health) in (int, float) and math.isfinite(health) and (0 <= health <= p.get('health', 200)) and (not p.get('godmode')) and (now - p.get('respawned_at', 0) > 0.7):
                p['health'] = health
                state['health'] = health
            multiplayer.save(p, state, True)
            return ({'success': True}, None)
        if path == '/api/gta/sync':
            presence = PRESENCE.get(token)
            if not presence or presence.get('world') != 'gta':
                raise ValueError('Önce GTA oturumuna katılın.')
            fields = {key: float(payload.get(key, presence.get('health', 200) if key == 'health' else 0)) for key in ('x', 'y', 'z', 'heading', 'speed', 'health')}
            if not all((math.isfinite(v) for v in fields.values())) or abs(fields['x']) > 16000 or abs(fields['y']) > 16000 or (not -1700 < fields['z'] < 2700):
                raise ValueError('Geçersiz GTA koordinatı.')
            if 'x' not in payload or 'y' not in payload or 'z' not in payload:
                raise ValueError('Oyun motorunun gerçek koordinatı gerekli.')
            presence['last_seen'] = now
            return (multiplayer.update(token, payload, fields, presence, GTA_STATE, PRESENCE), None)
        if path == '/api/gta/voice':
            return (multiplayer.voice(token, payload, PRESENCE.get(token), GTA_STATE.get(token)), None)
        if path == '/api/gta/voice/poll':
            return (multiplayer.voice_poll(payload, PRESENCE.get(token), GTA_STATE.get(token)), None)
        if any((path.startswith('/api/' + group + '/') for group in ('bank', 'factions', 'jobs'))):
            import gameplay_v29.pn_roleplay as pn_roleplay
            return (pn_roleplay.dispatch(path, uid, token, payload, PRESENCE.get(token), GTA_STATE.get(token), PRESENCE), None)
        if path == '/api/gta/consume':
            return (multiplayer.consume(token, payload, PRESENCE.get(token), GTA_STATE.get(token)), None)
        if path.startswith('/api/inventory/'):
            import gameplay_v29.pn_inventory as pn_inventory
            return (pn_inventory.dispatch(path, uid, token, payload, PRESENCE.get(token), GTA_STATE.get(token)), None)
        if path.startswith('/api/interactions/'):
            import gameplay_v29.pn_interactions as pn_interactions
            return (pn_interactions.dispatch(path, uid, token, payload, PRESENCE.get(token), GTA_STATE.get(token), PRESENCE, GTA_STATE), None)
        if path == '/api/services/treat':
            p = PRESENCE.get(token)
            state = GTA_STATE.get(token)
            world.live(p, state)
            if world.occupation(p['char_id'])[0] or not any((world.near(state, s, 4) for s in world.HOSPITALS)):
                raise ValueError('Tedavi için yaya olarak hastane girişine yaklaş (4 m).')
            if p['health'] >= 200:
                raise ValueError('Canın zaten dolu.')
            with database() as db:
                if not db.execute('UPDATE pn_wallet SET balance=balance-2500 WHERE user_id=? AND balance>=2500', (uid,)).rowcount:
                    raise ValueError('Tedavi için $2.500 gerekli.')
                world.audit(db, uid, 'hospital-treatment', {'char_id': p['char_id'], 'price': 2500})
            p['health'] = 200
            p['respawned_at'] = now
            p['life_id'] = p.get('life_id', 0) + 1
            state['health'] = 200
            p['respawn_spawn'] = {k: state[k] for k in ('x', 'y', 'z', 'heading', 'health')}
            p['respawn_spawn']['armor'] = p.get('armor', 0)
            multiplayer.save(p, state, True)
            return ({'success': True, 'spawn': p['respawn_spawn'], 'life_id': p['life_id'], 'money': world.wallet(uid), 'notice': 'Tedavi tamamlandı. Canın yenilendi.'}, None)
        if path.startswith('/api/vehicles/'):
            return (world.dispatch(path, uid, token, payload, PRESENCE.get(token), GTA_STATE.get(token), PRESENCE), None)
        if path.startswith('/api/storage/'):
            import gameplay_v29.pn_containers as pn_containers
            return (pn_containers.dispatch(path, uid, token, payload, PRESENCE.get(token), GTA_STATE.get(token), PRESENCE, GTA_STATE), None)
        if path.startswith('/api/phone/'):
            import gameplay_v29.pn_phone as pn_phone
            return (pn_phone.dispatch(path, uid, token, payload, PRESENCE.get(token), GTA_STATE.get(token), PRESENCE), None)
        if path == '/api/character/country':
            import gameplay_v29.pn_commands as pn_commands
            p = PRESENCE.get(token)
            if not p:
                raise ValueError('Önce karakterinle şehre bağlan.')
            code = payload.get('country')
            return (dict(success=True, countries=pn_commands.COUNTRIES, country=pn_commands.country(p['char_id'], code)), None)
        if path == '/api/gta/respawn':
            presence = PRESENCE.get(token)
            state = GTA_STATE.get(token)
            if not presence or not state or presence.get('health', 200) > 100:
                raise ValueError('Karakterin hayatta.')
            if now - presence.get('dead_at', now) < 5:
                raise ValueError('Yeniden doğmak için 5 saniye bekle.')
            spawn = {**world.HOSPITAL_SPAWN, 'health': 200, 'armor': 0}
            if staff.jail(presence['char_id']):
                spawn.update(staff.JAIL)
            presence['armor'] = 0
            presence['dimension'] = 0
            import gameplay_v29.pn_interactions as pn_interactions
            pn_interactions.release(presence['char_id'])
            world.release(presence['char_id'])
            presence['health'] = 200
            presence['respawned_at'] = now
            presence.pop('dead_at', None)
            presence['life_id'] = presence.get('life_id', 0) + 1
            presence['respawn_spawn'] = dict(spawn)
            state.update(spawn)
            state.update(vehicle_id=0, seat=-2, carried_by=0, speed=0, vx=0, vy=0, vz=0, flags=0, dimension=0)
            multiplayer.save(presence, state, True)
            return ({'success': True, 'spawn': spawn, 'life_id': presence['life_id']}, None)
        if path == '/api/gta/roster':
            players = [{k: p.get(k) for k in ('char_id', 'server_id', 'name', 'admin_duty', 'speaking_until')} for p in multiplayer.active(GTA_STATE)]
            return ({'success': True, 'players': players, 'count': len(players)}, None)
        if path == '/api/gta/presence':
            presence = PRESENCE.get(token)
            if not presence or presence.get('world') != 'gta':
                raise ValueError('GTA oturumu bulunamadı.')
            presence['last_seen'] = now
            return ({'success': True}, None)
        if path == '/api/lobby/heartbeat':
            if token not in PRESENCE:
                raise ValueError('Önce lobiye katılın.')
            p = PRESENCE[token]
            x, z = (float(payload.get('x', p['x'])), float(payload.get('z', p['z'])))
            if not math.isfinite(x) or not math.isfinite(z):
                raise ValueError('Geçersiz konum.')
            limit = 12 * min(2, max(0.1, now - p['last_seen']))
            distance = math.hypot(x - p['x'], z - p['z'])
            if distance > limit:
                factor = limit / distance
                x, z = (p['x'] + (x - p['x']) * factor, p['z'] + (z - p['z']) * factor)
            p.update(x=max(-100, min(100, x)), z=max(-100, min(100, z)), last_seen=now)
            players = [p for p in PRESENCE.values() if now - p['last_seen'] < 20 and p.get('world') == 'test']
            return ({'success': True, 'players': players, 'messages': engine.get_recent_chat()}, None)
        if path == '/api/chat/send':
            p = PRESENCE.get(token)
            if not p:
                raise ValueError('Önce lobiye katılın.')
            if p.get('world') == 'gta':
                import gameplay_v29.pn_city as pn_city
                words = str(payload.get('message', '')).split()
                import gameplay_v29.pn_commands as pn_commands
                result = pn_commands.command(words[0].lower(), words[1:], uid, p, GTA_STATE[token], PRESENCE) if words else None
                if result is None:
                    result = pn_city.admin_command(words[0].lower(), words[1:], uid, p, GTA_STATE[token], PRESENCE) if words else None
                if result:
                    return (result, None)
                result = staff.command(uid, token, payload, p, PRESENCE, GTA_STATE)
                if result:
                    return (result, None)
                result = world.command(uid, token, payload, p, PRESENCE)
                if result:
                    return (result, None)
                return (multiplayer.chat(token, payload, p, GTA_STATE.get(token)), None)
            msg = str(payload.get('message', '')).strip()
            if not 1 <= len(msg) <= 200:
                raise ValueError('Mesaj 1–200 karakter olmalı.')
            return (engine.add_chat(p['char_id'], p['name'], 'Sivil', msg, 'ooc'), None)
        return ({'success': False, 'error': 'API yolu bulunamadı.'}, None)
