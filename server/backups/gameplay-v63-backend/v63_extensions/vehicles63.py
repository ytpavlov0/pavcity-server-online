"""One garage retrieval path and durable administrator fleet suppression."""
import importlib,json,secrets,time

def install(api):
 if getattr(api,'vehicles63_installed',False):return api
 previous=api.dispatch;w=api.world;city=importlib.import_module(api.__package__+'.pn_city')
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_fleet_deleted63(job TEXT NOT NULL,slot INTEGER NOT NULL,vehicle_id INTEGER NOT NULL,deleted REAL NOT NULL,PRIMARY KEY(job,slot))')
 def ensure_fleet(db):
  for job,(model,*_)in city.JOB_PARKS.items():
   for slot in range(3):
    if db.execute('SELECT 1 FROM pn_fleet_deleted63 WHERE job=? AND slot=?',(job,slot)).fetchone()or db.execute('SELECT 1 FROM pn_job_vehicles WHERE job=? AND slot=?',(job,slot)).fetchone():continue
    vid=db.execute('INSERT INTO pn_vehicles(owner,model,plate,locked,active,state,updated) VALUES(0,?,?,1,1,?,?)',(model,'JOB'+secrets.token_hex(2).upper(),json.dumps(city.parked(job,slot)),time.time())).lastrowid
    db.execute('INSERT INTO pn_job_vehicles(job,slot,vehicle_id) VALUES(?,?,?)',(job,slot,vid))
 city.ensure_fleet=ensure_fleet
 def dispatch(path,payload,token):
  with api.LOCK:
   # Legacy PC/mobile callers receive exactly the same ownership, marker,
   # active-state and full customization-preserving checks as the new menu.
   if path=='/api/vehicles/retrieve':return previous('/api/garage61/retrieve',payload,token)
   args=str(payload.get('message','')).strip().split()if path=='/api/chat/send'else[]
   deleting=path=='/api/garage61/delete'or bool(args and args[0].lower()=='/delveh')
   if not deleting:return previous(path,payload,token)
   uid=api.authenticated61(token);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
   if not uid or not p or not s:return previous(path,payload,token)
   api.require_client61(token,payload)
   # Do not inspect/mutate a fleet slot until the normal administrator guard passes.
   if not w.admin(uid)or not p.get('admin_duty'):return previous(path,payload,token)
   raw=payload.get('id',0)if not args else(args[1]if len(args)==2 else 0)
   vid=int(raw)
   if not vid:
    nearby=[r for r in w.rows(s)if w.near(s,w.VEHICLE_CACHE.get(r['id'],json.loads(r['state'])),7)]
    if nearby:vid=min(nearby,key=lambda r:sum((w.VEHICLE_CACHE.get(r['id'],json.loads(r['state']))[k]-s[k])**2 for k in ('x','y','z')))['id']
   with api.database()as db:
    fleet=db.execute('SELECT *FROM pn_job_vehicles WHERE vehicle_id=?',(vid,)).fetchone()
    if fleet and fleet['borrower']:raise ValueError('Bu araç aktif mesleğe tahsisli. Önce görev tamamlanmalı veya iptal edilmeli.')
    result,cookie=previous(path,payload,token)
    if result.get('success')and fleet:
     db.execute('INSERT OR REPLACE INTO pn_fleet_deleted63 VALUES(?,?,?,?)',(fleet['job'],fleet['slot'],vid,time.time()))
    return result,cookie
 api.dispatch=dispatch;api.vehicles63_installed=True
 return api
