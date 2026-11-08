"""162: traffic vehicles stuck at the cap ("Trafik araçları dolu; kısa süre sonra tekrar dene.", 31 Oct).

pn_traffic.register keeps at most 256 adopted ambient cars (owner=0) and deletes one only when its `updated` is older than
1 h. But pn_world.public() re-saves every active car it shows to a nearby player every 3 s, which refreshes `updated`;
cars parked where players gather never aged, so the table sat at 256/256 (244 touched in the last 5 min, only 15
registrations in the last hour) and nobody could take a traffic car.

Now, when a registration finds the table at the cap, the least recently USED ambient cars are removed first, down to
TARGET: never one with anybody in a seat, never a job car, never one driven/ridden in the last RECENT seconds, and
first only cars with no connected player within FAR m, then (if that is not enough) within NEAR m. "Used" = had an
occupant at a sync (tracked in memory from clean_seats, which every sync runs); cars unused since this process started
count as oldest, lowest id first. Removal is the same as the old 1 h expiry (pn_vehicles + pn_vehicle_access rows) plus
the in-memory caches. Stats: api.features162_stats."""
import importlib,time,math
CAP=256;TARGET=224;RECENT=600;FAR=150;NEAR=40
def install(api):
 if getattr(api,'features162_installed',False):return api
 package=api.__package__;world=api.world;traffic=importlib.import_module(package+'.pn_traffic')
 STATS={'evictions':0,'evict_runs':0,'evict_short':0,'tracked':0};USED={}
 old_clean=world.clean_seats
 def clean_seats(presences):
  r=old_clean(presences);now=time.time()
  for vid,_ in list(world.SEATS):USED[vid]=now
  STATS['tracked']=len(USED);return r
 world.clean_seats=clean_seats
 def players():
  now=time.time();out=[]
  for s in list(api.GTA_STATE.values()):
   try:
    if now-s.get('last_seen',0)<30:out.append((float(s['x']),float(s['y']),float(s['z'])))
   except Exception:pass
  return out
 def evict(db):
  n=db.execute('SELECT COUNT(*) FROM pn_vehicles WHERE owner=0').fetchone()[0]
  if n<CAP:return 0
  STATS['evict_runs']+=1;now=time.time();occupied={vid for vid,_ in list(world.SEATS)};who=players()
  jobs={r[0] for r in db.execute('SELECT vehicle_id FROM pn_job_vehicles').fetchall()}
  cand=[]
  for row in db.execute('SELECT id,state FROM pn_vehicles WHERE owner=0').fetchall():
   vid=row[0]
   if vid in occupied or vid in jobs or now-USED.get(vid,0)<RECENT:continue
   f=world.VEHICLE_CACHE.get(vid)
   if f is None:
    try:f=world.json.loads(row[1])
    except Exception:f={}
   x,y,z=float(f.get('x',0)),float(f.get('y',0)),float(f.get('z',0))
   d=min((math.dist((x,y,z),q)for q in who),default=1e9)
   cand.append((USED.get(vid,0),vid,d))
  cand.sort()
  need=n-TARGET;gone=[]
  for limit in(FAR,NEAR):
   for used,vid,d in cand:
    if len(gone)>=need:break
    if d>=limit and vid not in gone:gone.append(vid)
  for vid in gone:
   db.execute('DELETE FROM pn_vehicles WHERE id=? AND owner=0',(vid,));db.execute('DELETE FROM pn_vehicle_access WHERE vehicle_id=?',(vid,))
   world.VEHICLE_CACHE.pop(vid,None);world.SAVED_AT.pop(vid,None);USED.pop(vid,None)
  if len(gone)<need:STATS['evict_short']+=1
  STATS['evictions']+=len(gone);return len(gone)
 # older layers keep their own reference to pn_traffic.register (city72, vehicle_policy82), so the eviction runs at the
 # top-level entry every request goes through, just before the registration
 old_dispatch=api.dispatch
 def dispatch(path,*a,**k):
  if isinstance(path,str)and path.endswith('/traffic-register'):
   try:
    with api.LOCK:
     with world.database() as db:evict(db)
   except Exception as e:STATS['last_error']=repr(e)[:160]
  return old_dispatch(path,*a,**k)
 api.dispatch=dispatch
 api.features162_evict=evict;api.features162_used=USED;api.features162_stats=STATS;api.features162_installed=True;return api
