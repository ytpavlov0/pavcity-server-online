"""187: the shared ambient NPC tick (ambient43, every 80 ms under api.LOCK) tested every walking NPC against every
player and every cached vehicle in the city, for the current point and each 50 ms sub-step, after copying every
vehicle's state dict into a fresh obstacle list. With 60 players that was ~60 ms per tick, ~75 % of the server.

Same rules, same results: obstacles go into a 16 m grid once per tick and each NPC only tests the obstacles of the
grid cells within reach (7.3 m blocking radius + the distance it can move this tick). An obstacle farther away can
never satisfy the blocking test (0 < along < 7, side < 1.9), so the blocked/advanced outcome is unchanged.

Installed by swapping the 'tick' cell of ambient43's dispatch closure; the selection phase and everything else run
the original code paths."""
import gc,json,math,types
G=16.0
def find():
 for f in gc.get_objects():
  if isinstance(f,types.FunctionType)and f.__name__=='dispatch'and f.__code__.co_filename.replace('\\','/').endswith('ambient43.py')and'tick'in f.__code__.co_freevars:
   return f
 return None
def cells_of(fn):return dict(zip(fn.__code__.co_freevars,(c.cell_contents for c in fn.__closure__)))
def make(old):
 c=cells_of(old);last_tick=c['last_tick'];valid_people=c['valid_people'];last_select=c['last_select'];routes=c['routes'];car_traffic_enabled=c['car_traffic_enabled'];ensure=c['ensure'];agents=c['agents'];world=c['world']
 boxes={id(r):tuple((min(p[k]for p in r.points),max(p[k]for p in r.points))for k in range(3))for r in routes}
 def box_near(route,s):
  try:q=(s['x'],s['y'],s['z'])
  except KeyError:return True
  if not all(type(v)in(int,float)and math.isfinite(v)for v in q):return True
  d2=0.
  for v,(lo,hi)in zip(q,boxes[id(route)]):
   e=lo-v if v<lo else v-hi if v>hi else 0.;d2+=e*e
  return d2<=141.**2
 def tick(now):
  elapsed=now-last_tick[0]
  if elapsed<.08:return
  dt=min(1.,max(0.,elapsed));last_tick[0]=now;people=valid_people(now)
  if now-last_select[0]>2:
   last_select[0]=now;wanted=set()
   for token,p,s in people:
    for kind,limit in ([('car',2),('ped',4)]if car_traffic_enabled else [('ped',4)]):
     # a route whose bounding box is more than 140 m away is dropped by the distance>140 test below anyway, and it
     # sorts after every nearer route, so leaving it out keeps the same picks (stable sort, same order otherwise)
     nearest=sorted(((route.nearest([s[k]for k in ('x','y','z')]),route)for route in routes if route.kind==kind and box_near(route,s)),key=lambda item:item[0][0])
     for (distance,phase),route in nearest[:limit]:
      if distance>140:continue
      wanted.add(route.id);ensure(route,(phase+(22 if kind=='car'else 8))%route.length,now)
   for key,agent in list(agents.items()):
    if key not in wanted and now-agent['seen']>60:
     if agent['route'].kind=='car'and not any(v==agent['vehicle']for v,seat in world.SEATS):
      row=world.vehicle(agent['vehicle']);fields=dict(world.VEHICLE_CACHE.get(row['id'],json.loads(row['state'])))
      if not fields.get('ambient188_taken'):
       fields.update(vx=0,vy=0,vz=0,speed=0,ambient188_paused=True);world.VEHICLE_CACHE[row['id']]=fields;world.persist_vehicle(row['id'])
     agents.pop(key)
  grid={}
  def put(x,y,z,oid):
   # non-finite positions never block (every comparison with nan/inf is False)
   if math.isfinite(x)and math.isfinite(y)and math.isfinite(z):grid.setdefault((math.floor(x/G),math.floor(y/G)),[]).append((x,y,z,oid))
  if agents:
   for _,p,s in people:
    if not s.get('vehicle_id'):put(s['x'],s['y'],s['z'],s.get('id'))
   for vid,fields in list(world.VEHICLE_CACHE.items()):
    if all(math.isfinite(fields.get(k,math.nan))for k in ('x','y','z')):put(fields['x'],fields['y'],fields['z'],vid)
  for key,agent in list(agents.items()):
   route=agent['route'];current=route.sample(agent['phase']);offset=agent.get('offset',1.)
   if route.kind=='car':
    try:row=world.vehicle(agent['vehicle'])
    except ValueError:agents.pop(key);continue
    if not row['active']:agents.pop(key);continue
    fields=dict(world.VEHICLE_CACHE.get(agent['vehicle'],json.loads(row['state'])))
    if any(v==agent['vehicle']for v,seat in world.SEATS)or row['owner']!=0 or fields.get('ambient188_taken')or fields.get('body',1000)<350:
     fields.update(ambient188_taken=True,vx=0,vy=0,vz=0,speed=0);world.VEHICLE_CACHE[agent['vehicle']]=fields;world.persist_vehicle(agent['vehicle']);agents.pop(key);continue
   fx=current['vx']/route.speed;fy=current['vy']/route.speed
   reach=7.3+route.speed*dt+.5;mine=agent.get('vehicle');near=[]
   for gx in range(math.floor((current['x']-reach)/G),math.floor((current['x']+reach)/G)+1):
    for gy in range(math.floor((current['y']-reach)/G),math.floor((current['y']+reach)/G)+1):
     for o in grid.get((gx,gy),()):
      if o[3]!=mine:near.append(o)
   long_=7 if route.kind=='car'else 1.3;wide=1.9 if route.kind=='car'else .75
   def hit(pt):
    px,py,pz=pt['x'],pt['y'],pt['z']
    for ox,oy,oz,_ in near:
     dx=ox-px;dy=oy-py;along=dx*fx+dy*fy;side=abs(dx*fy-dy*fx)
     if abs(oz-pz-offset)<2.2 and 0<along<long_ and side<wide:return True
    return False
   blocked=hit(current)
   # Sweep bounded substeps so a slow poll cannot tunnel through an obstacle.
   remaining=dt
   while not blocked and remaining>1e-9:
    step=min(.05,remaining);probe=route.sample(agent['phase']+step*route.speed)
    blocked=hit(probe)
    if not blocked:agent['phase']=(agent['phase']+step*route.speed)%route.length
    remaining-=step
   point=route.sample(agent['phase']);point['z']+=offset
   if blocked:point.update(vx=0,vy=0,vz=0,speed=0)
   agent['point']=point
   if route.kind=='car':
    fields.update(**point,rz=point['heading'],engine=fields.get('fuel',80)>0,ambient188=True,ambient188_paused=False);world.VEHICLE_CACHE[agent['vehicle']]=fields
 tick.ambient187=True
 return tick
def install(api):
 if getattr(api,'ambient187_installed',False):return True
 fn=find()
 if fn is None:return False
 i=fn.__code__.co_freevars.index('tick');old=fn.__closure__[i].cell_contents
 if getattr(old,'ambient187',False):api.ambient187_installed=True;return True
 api.ambient187_old_tick=old;fn.__closure__[i].cell_contents=make(old);api.ambient187_installed=True
 return True
