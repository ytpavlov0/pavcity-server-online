"""Paid return anchors, garage custody and bounded empty-car recovery."""
import json
import math
import time

GARAGES = [dict(id=1, name='Legion Garajı', x=215.8, y=-810.1, z=30.7, heading=160),
           dict(id=2, name='Vespucci Garajı', x=-1184.8, y=-1510.1, z=4.4, heading=125),
           dict(id=3, name='Sandy Garajı', x=1737.6, y=3710.2, z=34.1, heading=20)]
INTERVAL = 35*60


def stopped64(state):
    try:
        vx, vy, vz, rx, ry = (float(state.get(k, 0)) for k in ('vx', 'vy', 'vz', 'rx', 'ry'))
        if not all(math.isfinite(n) for n in (vx, vy, vz, rx, ry)):
            return False
        up = math.cos(math.radians(rx % 360)) * math.cos(math.radians(ry % 360))
        return math.hypot(vx, vy, vz) < 1 and up > math.cos(math.radians(30))
    except (ValueError, TypeError, OverflowError):
        return False


def install(api, clock=time.time):
    if getattr(api, 'vehicles61_installed', False):
        return api
    w = api.world
    previous = api.dispatch
    with api.database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pn_vehicle_home61(vehicle_id INTEGER PRIMARY KEY,anchor TEXT NOT NULL,paid INTEGER NOT NULL DEFAULT 0,due REAL NOT NULL,garage INTEGER NOT NULL DEFAULT 0)')
        db.execute('CREATE INDEX IF NOT EXISTS pn_vehicle_due61 ON pn_vehicle_home61(due)')
    last_tick = [-1e30]

    def fields(row):
        return dict(w.VEHICLE_CACHE.get(row['id'], json.loads(row['state'])))

    def occupied(vid):
        return any(v == vid for v, seat in w.SEATS)

    def pose(s):
        return {k: float(s.get(k, 0)) for k in ('x', 'y', 'z', 'heading')}

    def save(db, row, s, active=1):
        db.execute('UPDATE pn_vehicles SET state=?,active=?,updated=? WHERE id=?', (json.dumps(s), active, clock(), row['id']))

    def stopped(s):
        return stopped64(s)

    def empty_state(s, at=None):
        s = dict(s)
        if at:
            s.update(at)
        s.update(rx=0, ry=0, rz=s.get('heading', 0), vx=0, vy=0, vz=0, engine=False, doors=0, pose_epoch=int(s.get('pose_epoch', 0))+1)
        return s

    def seed(db):
        # Existing cars retain their first known location; new cars are captured
        # by the same transaction immediately after creation/retrieval.
        db.execute("INSERT OR IGNORE INTO pn_vehicle_home61(vehicle_id,anchor,due) SELECT id,json_object('x',json_extract(state,'$.x'),'y',json_extract(state,'$.y'),'z',json_extract(state,'$.z'),'heading',coalesce(json_extract(state,'$.heading'),0)),?+(id%61)*5 FROM pn_vehicles WHERE owner>0", (clock()+INTERVAL,))

    def maintenance():
        now = clock()
        if now-last_tick[0] < 5:
            return
        last_tick[0] = now
        changed = None
        with api.database() as db:
            seed(db)
            rows = db.execute('SELECT h.*,v.* FROM pn_vehicle_home61 h JOIN pn_vehicles v ON v.id=h.vehicle_id WHERE h.due<=? AND v.active=1 ORDER BY h.due LIMIT 8', (now,)).fetchall()
            for raw in rows:
                row = dict(raw); vid = row['id']; s = fields(row); target = json.loads(row['anchor'])
                db.execute('UPDATE pn_vehicle_home61 SET due=? WHERE vehicle_id=?', (now+60, vid))
                if not all(isinstance(target.get(k), (int,float)) and math.isfinite(target[k]) for k in ('x','y','z','heading')):
                    continue
                if occupied(vid) or not stopped(s):
                    continue
                if db.execute('SELECT 1 FROM pn_job_vehicles WHERE vehicle_id=?', (vid,)).fetchone():
                    continue
                if any(now-p['last_seen']<30 and (w.near(api.GTA_STATE.get(t, s), s, 25) or w.near(api.GTA_STATE.get(t, s), target, 25)) for t, p in api.PRESENCE.items() if p.get('dimension', 0)==0):
                    continue
                nearby = db.execute("SELECT id,state FROM pn_vehicles WHERE active=1 AND id<>? AND json_extract(state,'$.x') BETWEEN ? AND ? AND json_extract(state,'$.y') BETWEEN ? AND ?", (vid, target['x']-12, target['x']+12, target['y']-12, target['y']+12)).fetchall()
                if any(w.near(w.VEHICLE_CACHE.get(v['id'], json.loads(v['state'])), target, 7) for v in nearby):
                    continue
                new = empty_state(s, target); save(db, row, new)
                db.execute('UPDATE pn_vehicle_home61 SET due=? WHERE vehicle_id=?', (now+INTERVAL, vid))
                w.audit(db, 0, 'vehicle-return61', {'vehicle_id': vid})
                changed = (vid, new)
                break  # at most one return per five seconds, never a world reset
        if changed:
            w.VEHICLE_CACHE[changed[0]] = changed[1]
            w.SAVED_AT[changed[0]] = now

    def action(uid, p, state, verb, payload):
        w.live(p, state)
        if p.get('dimension', 0):
            raise ValueError('Bu işlem dışarıdaki araçlar içindir.')
        garage = next((g for g in GARAGES if w.near(state, g, 25)), None)
        if verb=='list':
            with api.database() as db:
                rows = [dict(r) for r in db.execute('SELECT v.id,v.model,v.plate,v.active,h.garage FROM pn_vehicles v LEFT JOIN pn_vehicle_home61 h ON h.vehicle_id=v.id WHERE v.owner=? ORDER BY v.id', (p['char_id'],))]
            return dict(success=True, garages=GARAGES, nearby=garage, vehicles=rows, park_fee=250)
        vid = int(payload.get('id', 0))
        if not vid:
            candidates = [r for r in w.rows(state) if w.near(state, fields(r), 7)]
            if verb!='delete':
                candidates = [r for r in candidates if r['owner']==p['char_id']]
            if not candidates:
                raise ValueError('Yakında uygun araç yok. Araç ID belirtebilirsin.')
            vid = min(candidates, key=lambda r: sum((fields(r)[k]-state[k])**2 for k in ('x','y','z')))['id']
        row = w.vehicle(vid); s = fields(row)
        if verb=='delete':
            if not w.admin(uid) or not p.get('admin_duty'):
                raise ValueError('/delveh için yönetici görevinde olmalısın.')
        elif row['owner']!=p['char_id']:
            raise ValueError('Yalnız kendi aracını park edebilir veya garaja koyabilirsin.')
        if occupied(vid):
            raise ValueError('Araçtaki herkes inmeli; devam eden binme işlemi de bitmeli.')
        if verb in ('park', 'store') and (not row['active'] or not w.near(state, s, 7) or not stopped(s)):
            raise ValueError('Duran, düz ve boş aracının yanına yaklaş (7 m).')
        if verb in ('store', 'retrieve') and not garage:
            raise ValueError('Garaj işaretine yaklaş (25 m). /garaj ile konumunu gör.')
        with api.database() as db:
            if verb=='delete':
                for table in ('pn_vehicle_access','pn_job_vehicles','pn_faction_vehicles','pn_vehicle_home61'):
                    db.execute('DELETE FROM '+table+' WHERE vehicle_id=?', (vid,))
                db.execute('UPDATE pn_donate_vehicles SET revoked_at=? WHERE vehicle_id=?', (clock(),vid))
                db.execute('DELETE FROM pn_vehicles WHERE id=?', (vid,))
                w.audit(db, uid, 'vehicle-delete61', {'vehicle_id':vid, 'model':row['model'], 'plate':row['plate']})
                result = dict(success=True, notice=f'Araç #{vid} kalıcı olarak silindi.')
                new = None
            elif verb=='park':
                seed(db)
                old = db.execute('SELECT * FROM pn_vehicle_home61 WHERE vehicle_id=?', (vid,)).fetchone()
                if old and old['paid'] and w.near(json.loads(old['anchor']), s, 2):
                    return dict(success=True, notice='Bu park noktası zaten kayıtlı; ücret tekrar alınmadı.')
                if db.execute('UPDATE pn_wallet SET balance=balance-250 WHERE user_id=? AND balance>=250', (uid,)).rowcount!=1:
                    raise ValueError('Park noktası için $250 gerekli.')
                db.execute('UPDATE pn_vehicle_home61 SET anchor=?,paid=1,due=?,garage=0 WHERE vehicle_id=?', (json.dumps(pose(s)),clock()+INTERVAL,vid))
                # Recording a park position must never straighten or teleport a car.
                new = dict(s, engine=False, vx=0, vy=0, vz=0); save(db,row,new)
                db.execute('UPDATE pn_vehicles SET locked=1 WHERE id=?', (vid,))
                w.audit(db, uid, 'vehicle-park61', {'vehicle_id':vid,'fee':250})
                result = dict(success=True, notice='Park noktası $250 karşılığında kaydedildi. Boş araç bu noktaya döner.')
            elif verb=='store':
                seed(db); new = dict(s,engine=False,vx=0,vy=0,vz=0)
                save(db,row,new,0);db.execute('UPDATE pn_vehicle_home61 SET garage=? WHERE vehicle_id=?',(garage['id'],vid))
                result = dict(success=True,notice=f'Araç #{vid} {garage["name"]} içine kaldırıldı.')
            elif verb=='retrieve':
                if row['active']:
                    raise ValueError('Araç zaten dışarıda; önce mevcut aracını kullan veya garaja koy.')
                if row['model'] in ('t20','kuruma') or row['model'] not in w.SPAWN_MODELS:
                    raise ValueError('Bu aracın model paketi yüklü değil; garaj kaydı korunuyor.')
                at = w.spawn_location(garage, row['model'], vid)
                new = empty_state(s, dict(at,heading=garage['heading']));save(db,row,new)
                db.execute('UPDATE pn_vehicle_home61 SET due=?,garage=0 WHERE vehicle_id=?',(clock()+INTERVAL,vid))
                result = dict(success=True,notice=f'Araç #{vid} garajdan çıkarıldı.')
            else:
                raise ValueError('Geçersiz garaj işlemi.')
        if new is None or verb=='store':
            w.VEHICLE_CACHE.pop(vid,None);w.SAVED_AT.pop(vid,None)
        else:
            w.VEHICLE_CACHE[vid]=new;w.SAVED_AT[vid]=clock()
        if verb=='retrieve':
            result['vehicle']=w.public(w.vehicle(vid))
        return result

    def dispatch(path,payload,token):
        with api.LOCK:
            uid=api.authenticated61(token);p=api.PRESENCE.get(token);state=api.GTA_STATE.get(token)
            if uid and p and state:
                if path.startswith('/api/garage61/') or path in ('/api/chat/send','/api/vehicles/park'):
                    api.require_client61(token,payload)
                if path.startswith('/api/garage61/'):
                    return action(uid,p,state,path.rsplit('/',1)[-1],payload),None
                if path=='/api/chat/send':
                    args=str(payload.get('message','')).strip().split()
                    if args and args[0].lower() in ('/delveh','/park'):
                        if len(args)>2:
                            raise ValueError('Kullanım: '+args[0]+' [araç ID]')
                        return action(uid,p,state,'delete' if args[0].lower()=='/delveh' else 'park',{'id':int(args[1]) if len(args)>1 else 0}),None
                if path=='/api/vehicles/park':
                    return action(uid,p,state,'park',payload),None
            result,cookie=previous(path,payload,token)
            if result.get('success') and path in ('/api/vehicles/buy','/api/vehicles/spawn','/api/vehicles/retrieve'):
                with api.database() as db:seed(db)
            if result.get('success') and path=='/api/gta/sync':
                maintenance()
            return result,cookie

    api.dispatch=dispatch
    api.vehicle_maintenance61=maintenance
    api.vehicles61_installed=True
    return api
