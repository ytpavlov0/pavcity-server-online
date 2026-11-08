"""Adopt a nearby ambient vehicle and validate lockpicking on the server.

Ambient physics originate on a client, just like the existing driving samples.
Adoption does not grant ownership or move an existing registered vehicle.
"""
import json, math, re, secrets, time
import gameplay_v29.pn_world as world
ROAD_MODELS = set('schwarzer peyote picador minivan minivan2 utillitruck utillitruck2 utillitruck3 journey tiptruck tiptruck2 rhapsody panto radi voodoo dukes2 manana manana2 primo2 sabregt2 slamvan slamvan2 gburrito gburrito2 rumpo2 rumpo3 buffalo3 schafter3 schafter4 schafter5 schafter6 stretch tampa brioso asea2 rapidgt3 futo2 hakuchou innovation cruiser fixter scorcher bmx tribike tribike2 tribike3 trflat stockade stockade3 barracks barracks2 barracks3 flatbed guardian insurgent insurgent2 technical'.split()) | set('emperor emperor2 stanier washington ingot intruder dilettante premier fugitive tailgater oracle oracle2 sentinel sentinel2 issi2 felon felon2 zion zion2 dominator dukes gauntlet buccaneer baller2 cavalcade cavalcade2 gresley rocoto habanero landstalker patriot serrano dubsta dubsta2 huntley asterope regina stratum ruiner sabregt stalion tornado tornado2 tornado3 vigero voodoo2 bagger bati2 blazer daemon double hexer nemesis pcj ruffian sanchez2 vader bison bison2 bison3 bobcatxl burrito burrito2 burrito3 pony pony2 rumpo speedo speedo2 surfer surfer2 youga mule mule2 mule3 benson boxville boxville2 boxville3 boxville4 pounder phantom hauler packer taxi bus coach airbus rentalbus police3 police4 policeb fbi fbi2 sheriff sheriff2 firetruk trash trash2 towtruck towtruck2 dump bulldozer caddy caddy2 forklift tractor tractor2 tractor3 sadler sandking sandking2 rebel rebel2 rancherxl mesa mesa2 mesa3 blista2 blista3 carbonizzare carbonrs f620 fusilade futo jester massacro rapidgt rapidgt2 surano ninef ninef2 coquette buffalo2 feltzer2 entityxf vacca bullet voltic cheetah'.split()) | world.SPAWN_MODELS

def joaat(name):
    h = 0
    for c in name.lower():
        h = h + ord(c) & 4294967295
        h = h + (h << 10) & 4294967295
        h ^= h >> 6
    h = h + (h << 3) & 4294967295
    h ^= h >> 11
    return h + (h << 15) & 4294967295
HASHES = {joaat(model): model for model in ROAD_MODELS}

def has_key(vid, cid):
    with world.database() as db:
        return db.execute('SELECT 1 FROM pn_vehicle_access WHERE vehicle_id=? AND char_id=?', (vid, cid)).fetchone() is not None

def grant_key(db, vid, cid):
    db.execute('INSERT OR IGNORE INTO pn_vehicle_access VALUES(?,?)', (vid, cid))

def register(uid, token, payload, p, state):
    from gameplay_v29.pn_multiplayer import rate
    if world.occupation(p['char_id'])[0]:
        raise ValueError('Önce mevcut aracından in.')
    raw = payload.get('model_hash')
    if type(raw) is not int or not 0 <= raw <= 4294967295 or raw not in HASHES:
        raise ValueError('Bu trafik aracının modeli desteklenmiyor.')
    model = HASHES[raw]
    plate = str(payload.get('plate', '')).strip().upper()
    if not re.fullmatch('[A-Z0-9 ]{1,8}', plate):
        raise ValueError('Trafik aracının plakası okunamadı.')
    fields = {}
    for k in ('x', 'y', 'z', 'heading', 'body'):
        value = payload.get(k)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or (not math.isfinite(value)):
            raise ValueError('Geçersiz trafik aracı konumu.')
        fields[k] = float(value)
    if abs(fields['x']) > 16000 or abs(fields['y']) > 16000 or (not -1700 < fields['z'] < 2700) or (not world.near(state, fields, 7)):
        raise ValueError('Trafik aracına yaklaş (7 m).')
    locked = payload.get('locked')
    seats = payload.get('seats')
    if type(locked) is not bool or type(seats) is not int or (not 1 <= seats <= 8):
        raise ValueError('Geçersiz trafik aracı bilgisi.')
    rate(token, 'traffic-register', 0.8)
    with world.database() as db:
        row = db.execute('SELECT * FROM pn_vehicles WHERE plate=?', (plate,)).fetchone()
        if row:
            if not row['active'] or row['model'] != model or (not world.near(state, world.public(row), 7)):
                raise ValueError('Bu plakada başka bir araç kaydı var.')
            job = db.execute('SELECT borrower FROM pn_job_vehicles WHERE vehicle_id=?', (row['id'],)).fetchone()
            if row['owner'] == 0 and (not job) and (payload.get('ambient_driver') is True):
                db.execute('UPDATE pn_vehicles SET locked=0 WHERE id=?', (row['id'],))
                row = db.execute('SELECT * FROM pn_vehicles WHERE id=?', (row['id'],)).fetchone()
            return {'success': True, 'vehicle': world.public(row)}
        occupied = {vid for vid, seat in world.SEATS}
        expired = db.execute('SELECT id FROM pn_vehicles WHERE owner=0 AND updated<? AND id NOT IN (SELECT vehicle_id FROM pn_job_vehicles)', (time.time() - 3600,)).fetchall()
        for row in expired:
            if row['id'] not in occupied:
                db.execute('DELETE FROM pn_vehicles WHERE id=?', (row['id'],))
                db.execute('DELETE FROM pn_vehicle_access WHERE vehicle_id=?', (row['id'],))
        if db.execute('SELECT COUNT(*) FROM pn_vehicles WHERE owner=0').fetchone()[0] >= 256:
            raise ValueError('Trafik araçları dolu; kısa süre sonra tekrar dene.')
        if payload.get('ambient_driver') is True:
            locked = False
        fields.update(body=max(0, min(1000, fields['body'])), rx=0, ry=0, rz=fields['heading'], vx=0, vy=0, vz=0, engine=payload.get('ambient_driver') is True, fuel=70, km=0, street=True, seats=seats)
        vid = db.execute('INSERT INTO pn_vehicles(owner,model,plate,locked,state,updated) VALUES(0,?,?,?,?,?)', (model, plate, int(locked), json.dumps(fields), time.time())).lastrowid
        world.audit(db, uid, 'traffic-register', {'id': vid, 'model': model})
    return {'success': True, 'vehicle': world.public(world.vehicle(vid))}

def challenge_view(attempt):
    now = time.time()
    done = attempt['step'] == len(attempt['keys'])
    return {'success': True, 'id': attempt['id'], 'challenge': attempt['challenge'], 'step': attempt['step'], 'total': len(attempt['keys']), 'completed': done, 'key': None if done else attempt['keys'][attempt['step']], 'ready_in_ms': max(0, math.ceil((attempt['ready_at'] - now) * 1000)), 'timeout_ms': max(0, math.ceil((attempt['deadline'] - now) * 1000))}

def lockpick(action, uid, token, payload, p, state, row):
    from gameplay_v29.pn_multiplayer import rate
    vid = row['id']
    now = time.time()
    if action == 'break-cancel':
        attempt = world.BREAK_INS.get(token)
        if attempt and attempt['id'] == vid and secrets.compare_digest(attempt['challenge'], str(payload.get('challenge', ''))):
            world.BREAK_INS.pop(token, None)
        return {'success': True}
    if world.occupation(p['char_id'])[0]:
        raise ValueError('Maymuncuk için araçtan in.')
    if not world.near(state, world.public(row), 5):
        world.BREAK_INS.pop(token, None)
        raise ValueError('Kilitten uzaklaştın (5 m).')
    if action == 'break-start':
        if not row['locked']:
            raise ValueError('Kapı zaten açık.')
        rate(token, 'break-attempt', 5)
        for key, a in list(world.BREAK_INS.items()):
            if now - a['start'] > 30:
                world.BREAK_INS.pop(key, None)
        attempt = {'id': vid, 'char_id': p['char_id'], 'life_id': p.get('life_id', 0), 'challenge': secrets.token_urlsafe(24), 'keys': [secrets.choice(('left', 'right')) for _ in range(6)], 'step': 0, 'start': now, 'ready_at': now + 0.25, 'deadline': now + 2.7}
        world.BREAK_INS[token] = attempt
        return challenge_view(attempt)
    attempt = world.BREAK_INS.get(token)
    if not attempt or attempt['id'] != vid or attempt['char_id'] != p['char_id'] or (attempt['life_id'] != p.get('life_id', 0)) or (not secrets.compare_digest(attempt['challenge'], str(payload.get('challenge', '')))) or (now - attempt['start'] > 25):
        world.BREAK_INS.pop(token, None)
        raise ValueError('Maymuncuk denemesi sona erdi.')
    if action == 'break-step':
        if attempt['step'] >= len(attempt['keys']) or type(payload.get('step')) is not int or payload['step'] != attempt['step'] or (payload.get('key') != attempt['keys'][attempt['step']]) or (not attempt['ready_at'] <= now <= attempt['deadline']):
            world.BREAK_INS.pop(token, None)
            raise ValueError('Yanlış yön veya zamanlama. Kilit açılmadı.')
        attempt['step'] += 1
        attempt.update(ready_at=now + 0.25, deadline=now + 2.7)
        return challenge_view(attempt)
    if action == 'break-finish':
        world.BREAK_INS.pop(token, None)
        if attempt['step'] != len(attempt['keys']):
            raise ValueError('Önce tüm maymuncuk adımlarını tamamla.')
        with world.database() as db:
            db.execute('UPDATE pn_vehicles SET locked=0 WHERE id=?', (vid,))
            grant_key(db, vid, p['char_id'])
            world.audit(db, uid, 'lockpick', {'id': vid, 'steps': attempt['step']})
        return {'success': True, 'vehicle': world.public(world.vehicle(vid)), 'notice': 'Kilit açıldı. Aracı kullanabilirsin.'}
    raise ValueError('Geçersiz maymuncuk işlemi.')
