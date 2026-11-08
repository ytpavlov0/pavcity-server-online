"""188: vehicle lifecycle (roads no longer fill up with abandoned cars).
- Unowned cars (NPC cars players took, admin spawns) that nobody has used for 30 minutes are removed. Job, faction,
  shared NPC-route, donation and for-sale cars are never touched.
- An owned car nobody has used for 60 minutes goes back to its paid /park spot; without a paid spot it is towed to
  the city car park (Şehir Otoparkı) and can be taken out at any garage.
- "Used" = somebody sat in it. A car is only moved or removed while it is empty, standing still and nobody is
  within 25 m; at most a few changes every 10 s.
- /park: the owner or a key holder, also from inside the car (the spot is the car's current position, $250 once
  per spot).
- The old 35-minute return of vehicles61/64 is switched off (it sent unparked cars back to where they first appeared).
- coast188: for 10 s after leaving the driver seat, the last driver may report the car's pose while it still rolls
  (players saw the car stop where they jumped out, and F found "no car nearby" next to it)."""
import json,math,sys,time
NPC_IDLE=30*60;OWN_IDLE=60*60;TICK=10.0;NEAR=25.0;MAX_ACTIONS=4;FEE=250;COAST=10.0
IMPOUND=dict(id=4,name='Şehir Otoparkı',x=409.3,y=-1623.0,z=29.3,heading=230)
STATS={'npc_removed':0,'returned':0,'impounded':0,'parks':0,'coast':0,'coast_refused':0}
def finite(*v):return all(type(x)in(int,float)and math.isfinite(x)for x in v)
def install(api,clock=time.time):
 if getattr(api,'vehicles188_installed',False):return api
 w=api.world;import importlib;staff=importlib.import_module(api.__package__+'.pn_admin')
 v64=next((m for m in list(sys.modules.values())if getattr(m,'__file__','')and str(m.__file__).replace('\\','/').endswith('vehicles64.py')and hasattr(m,'GARAGES')),None)
 if v64 is not None:
  if not any(g['id']==IMPOUND['id']for g in v64.GARAGES):v64.GARAGES.append(dict(IMPOUND))
  v64.INTERVAL=10**9
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_vehicle_use188(vehicle_id INTEGER PRIMARY KEY,used REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_vehicle_home61(vehicle_id INTEGER PRIMARY KEY,anchor TEXT NOT NULL,paid INTEGER NOT NULL DEFAULT 0,due REAL NOT NULL,garage INTEGER NOT NULL DEFAULT 0)')
  db.execute('UPDATE pn_vehicle_home61 SET due=? WHERE due<?',(clock()+10**9,clock()+10**8))
 last=[0.0];DRIVER={}  # vid -> (char_id, last time seated as driver)
 def fields(row):return dict(w.VEHICLE_CACHE.get(row['id'],json.loads(row['state'])))
 def occupied():return {v for v,seat in w.SEATS}
 def stopped(s):
  try:return math.hypot(float(s.get('vx',0)),float(s.get('vy',0)),float(s.get('vz',0)))<1
  except(TypeError,ValueError):return False
 def people_near(s):
  for t,p in list(api.PRESENCE.items()):
   q=api.GTA_STATE.get(t)
   if q and p.get('dimension',0)==0 and clock()-q.get('last_seen',0)<60 and finite(q.get('x'),q.get('y'))and finite(s.get('x'),s.get('y'))and math.hypot(q['x']-s['x'],q['y']-s['y'])<NEAR:return True
  return False
 PROTECTED=("SELECT vehicle_id FROM pn_job_vehicles UNION SELECT vehicle_id FROM pn_faction_vehicles UNION SELECT vehicle_id FROM pn_ambient188 "
  "UNION SELECT vehicle_id FROM pn_donate_vehicles WHERE vehicle_id IS NOT NULL UNION SELECT vehicle_id FROM pn_vehicle_sale84 WHERE status='pending'")
 def protected_ids(db):
  ids=set()
  for q in PROTECTED.split(' UNION '):
   try:ids|={r[0]for r in db.execute(q)}
   except Exception:pass
  try:ids|={r[0]for r in db.execute('SELECT vehicle_id FROM pn_faction_fleet69')}
  except Exception:pass
  return ids
 def drivers():
  """Every sync, no lock needed (reads a snapshot of the seat table)."""
  now=clock()
  for(vid,seat),info in list(w.SEATS.items()):
   if seat==-1 and isinstance(info,dict)and info.get('char_id'):DRIVER[vid]=(info['char_id'],now)
 def due():return clock()-last[0]>=TICK
 def tick():
  drivers();now=clock()
  if now-last[0]<TICK:return
  last[0]=now;busy=occupied();acted=0
  with api.database()as db:
   for vid in busy:db.execute('INSERT INTO pn_vehicle_use188 VALUES(?,?) ON CONFLICT(vehicle_id) DO UPDATE SET used=excluded.used',(vid,now))
   # cars seen for the first time start their idle clock now (no mass removal right after an update)
   db.execute('INSERT OR IGNORE INTO pn_vehicle_use188 SELECT id,? FROM pn_vehicles WHERE active=1',(now,))
   rows=db.execute('SELECT v.*,u.used,h.anchor,h.paid FROM pn_vehicles v JOIN pn_vehicle_use188 u ON u.vehicle_id=v.id LEFT JOIN pn_vehicle_home61 h ON h.vehicle_id=v.id '
    'WHERE v.active=1 AND ((v.owner=0 AND u.used<?) OR (v.owner>0 AND u.used<?)) ORDER BY u.used LIMIT 40',(now-NPC_IDLE,now-OWN_IDLE)).fetchall()
   if not rows:return
   keep=protected_ids(db)
   for r in rows:
    if acted>=MAX_ACTIONS:break
    vid=r['id']
    if vid in busy or vid in keep:continue
    s=fields(r)
    if not stopped(s)or people_near(s):continue
    if r['owner']==0:
     for table in('pn_vehicle_access','pn_vehicle_home61','pn_vehicle_use188','pn_vehicle_rotation79'):
      try:db.execute('DELETE FROM '+table+' WHERE vehicle_id=?',(vid,))
      except Exception:pass
     db.execute('DELETE FROM pn_vehicles WHERE id=? AND owner=0',(vid,))
     w.audit(db,0,'vehicle-idle-remove188',dict(vehicle_id=vid,model=r['model']));w.VEHICLE_CACHE.pop(vid,None);w.SAVED_AT.pop(vid,None)
     STATS['npc_removed']+=1;acted+=1;continue
    anchor=None
    try:anchor=json.loads(r['anchor'])if r['anchor']and r['paid']else None
    except ValueError:anchor=None
    if anchor and finite(*(anchor.get(k)for k in('x','y','z','heading'))):
     if math.hypot(s.get('x',0)-anchor['x'],s.get('y',0)-anchor['y'])>4:
      new=dict(s);new.update({k:anchor[k]for k in('x','y','z','heading')});new.update(rx=0,ry=0,rz=anchor['heading'],vx=0,vy=0,vz=0,engine=False,doors=0,pose_epoch=int(s.get('pose_epoch',0))+1)
      db.execute('UPDATE pn_vehicles SET state=?,updated=? WHERE id=?',(json.dumps(new),now,vid));w.VEHICLE_CACHE[vid]=new;w.SAVED_AT[vid]=now
      w.audit(db,0,'vehicle-idle-return188',dict(vehicle_id=vid));STATS['returned']+=1;acted+=1
     db.execute('UPDATE pn_vehicle_use188 SET used=? WHERE vehicle_id=?',(now,vid))
    else:
     new=dict(s,engine=False,vx=0,vy=0,vz=0)
     db.execute('UPDATE pn_vehicles SET state=?,active=0,updated=? WHERE id=?',(json.dumps(new),now,vid))
     db.execute('INSERT INTO pn_vehicle_home61(vehicle_id,anchor,due,garage) VALUES(?,?,?,?) ON CONFLICT(vehicle_id) DO UPDATE SET garage=excluded.garage',
      (vid,json.dumps({k:float(s.get(k,0))for k in('x','y','z','heading')}),now+10**9,IMPOUND['id']))
     db.execute('UPDATE pn_vehicle_use188 SET used=? WHERE vehicle_id=?',(now,vid))
     w.audit(db,0,'vehicle-impound188',dict(vehicle_id=vid,owner=r['owner']));w.VEHICLE_CACHE.pop(vid,None);w.SAVED_AT.pop(vid,None)
     STATS['impounded']+=1;acted+=1
 def park(uid,p,state,args):
  w.live(p,state)
  if p.get('dimension',0):raise ValueError('Park yalnız dışarıda yapılır.')
  vid,seat=w.occupation(p['char_id'])
  if args:vid=staff.number(args[0],1,2147483647)
  if not vid:
   near=[r for r in w.rows(state)if w.near(state,fields(r),7)]
   if not near:raise ValueError('Aracının içinde ol ya da yanına yaklaş (7 m).')
   vid=min(near,key=lambda r:sum((fields(r)[k]-state[k])**2 for k in('x','y','z')))['id']
  row=w.vehicle(vid);s=fields(row)
  with api.database()as db:
   holder=row['owner']==p['char_id']or bool(db.execute('SELECT 1 FROM pn_vehicle_access WHERE vehicle_id=? AND char_id=?',(vid,p['char_id'])).fetchone())
  if not holder:raise ValueError('Yalnız sahibi olduğun veya anahtarı sende olan aracı park edebilirsin.')
  if row['owner']==0:raise ValueError('Sahipsiz araçlar park edilemez.')
  if not row['active']:raise ValueError('Araç garajda.')
  inside=w.occupation(p['char_id'])[0]==vid
  if not inside and not w.near(state,s,7):raise ValueError('Aracın yanına yaklaş (7 m).')
  if not stopped(s):raise ValueError('Önce aracı durdur.')
  pose={k:float(s.get(k,0))for k in('x','y','z','heading')}
  if not finite(*pose.values()):raise ValueError('Araç konumu henüz hazır değil.')
  with api.database()as db:
   old=db.execute('SELECT * FROM pn_vehicle_home61 WHERE vehicle_id=?',(vid,)).fetchone()
   if old and old['paid']:
    try:a=json.loads(old['anchor'])
    except ValueError:a={}
    if finite(a.get('x'),a.get('y'))and math.hypot(a['x']-pose['x'],a['y']-pose['y'])<2:return dict(success=True,notice='Bu park yeri zaten kayıtlı; ücret alınmadı.')
   if db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(FEE,uid,FEE)).rowcount!=1:raise ValueError('Park yeri için $%d gerekli.'%FEE)
   db.execute('INSERT INTO pn_vehicle_home61(vehicle_id,anchor,paid,due,garage) VALUES(?,?,1,?,0) ON CONFLICT(vehicle_id) DO UPDATE SET anchor=excluded.anchor,paid=1,due=excluded.due,garage=0',(vid,json.dumps(pose),clock()+10**9))
   db.execute('INSERT INTO pn_vehicle_use188 VALUES(?,?) ON CONFLICT(vehicle_id) DO UPDATE SET used=excluded.used',(vid,clock()))
   if not inside:
    new=dict(s,engine=False,vx=0,vy=0,vz=0);db.execute('UPDATE pn_vehicles SET state=?,locked=1,updated=? WHERE id=?',(json.dumps(new),clock(),vid));w.VEHICLE_CACHE[vid]=new;w.SAVED_AT[vid]=clock()
   w.audit(db,uid,'vehicle-park188',dict(vehicle_id=vid,fee=FEE,inside=inside))
  STATS['parks']+=1
  return dict(success=True,notice='Araç #%d bu konuma park edildi ($%d). 1 saat kullanılmazsa buraya döner.'%(vid,FEE))
 def coast(p,state,data):
  """Pose of the car this player drove until <= 10 s ago, while nobody else drives it."""
  try:vid=int(data.get('id'))
  except(TypeError,ValueError):return
  d=DRIVER.get(vid);now=clock()
  if not d or d[0]!=p['char_id']or now-d[1]>COAST or (vid,-1)in w.SEATS or w.occupation(p['char_id'])[0]:STATS['coast_refused']+=1;return
  vals=[data.get(k)for k in('x','y','z','heading','vx','vy','vz')]
  if not finite(*vals):STATS['coast_refused']+=1;return
  x,y,z,h,vx,vy,vz=(float(v)for v in vals)
  s=w.VEHICLE_CACHE.get(vid)
  if s is None or not finite(s.get('x'),s.get('y'),s.get('z')):return
  dt=max(.05,now-s.get('coast188_at',d[1]))
  if math.hypot(vx,vy,vz)>90 or math.dist((x,y,z),(s['x'],s['y'],s['z']))>90*dt+10:STATS['coast_refused']+=1;return
  new=dict(s,x=x,y=y,z=z,heading=h%360,rz=h%360,vx=vx,vy=vy,vz=vz,coast188_at=now);w.VEHICLE_CACHE[vid]=new
  if now-w.SAVED_AT.get(vid,0)>=3:w.persist_vehicle(vid)
  STATS['coast']+=1
 api.vehicles188_tick=tick;api.vehicles188_drivers=drivers;api.vehicles188_due=due;api.vehicles188_park=park;api.vehicles188_coast=coast;api.vehicles188_installed=True
 return api
