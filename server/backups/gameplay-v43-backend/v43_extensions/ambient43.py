"""Explicit-install, bounded shared traffic on original verified road/ped paths.

NPCs are a separate identity stream. Real cars use the existing server vehicle
IDs and seat authority; a player taking the driver seat permanently ends AI.
No worker thread, user grant, client destination or import-time database work.
"""
from pathlib import Path
import bisect,hashlib,json,math,time,zlib
clock=time.time
ROOT=Path(__file__).resolve().parents[2]
NPC_MODEL='a_m_y_business_01'

class Route:
 def __init__(self,row):
  self.id=row['id'];self.kind=row['kind'];self.points=row['points'];self.speed=row['speed'];self.cumulative=[0.]
  if self.kind not in ('car','ped')or not 2<=len(self.points)<=1024 or not .5<=self.speed<=10:raise ValueError('Invalid ambient route')
  for i,p in enumerate(self.points):
   if len(p)!=3 or not all(type(v)in(int,float)and math.isfinite(v)and abs(v)<16000 for v in p):raise ValueError('Invalid ambient point')
   self.cumulative.append(self.cumulative[-1]+math.dist(p,self.points[(i+1)%len(self.points)]))
  self.length=self.cumulative[-1]
  if self.length<10:raise ValueError('Short ambient route')
  self.fingerprint=self.kind+':'+','.join(sorted(set(row['nodes'])))
 def sample(self,phase):
  distance=phase%self.length;i=min(len(self.points)-1,bisect.bisect_right(self.cumulative,distance)-1);a=self.points[i];b=self.points[(i+1)%len(self.points)];length=self.cumulative[i+1]-self.cumulative[i];t=(distance-self.cumulative[i])/max(.001,length);dx=b[0]-a[0];dy=b[1]-a[1];flat=math.hypot(dx,dy)
  return dict(x=a[0]+dx*t,y=a[1]+dy*t,z=a[2]+(b[2]-a[2])*t,heading=math.degrees(math.atan2(-dx,dy))%360,vx=dx/max(flat,.001)*self.speed,vy=dy/max(flat,.001)*self.speed,vz=0,speed=self.speed)
 def nearest(self,p):
  best=(math.inf,0.)
  for i,a in enumerate(self.points):
   b=self.points[(i+1)%len(self.points)];d=[b[k]-a[k]for k in range(3)];square=sum(v*v for v in d);t=max(0.,min(1.,sum((p[k]-a[k])*d[k]for k in range(3))/max(square,.001)));distance=math.sqrt(sum((p[k]-a[k]-d[k]*t)**2 for k in range(3)))
   if distance<best[0]:best=(distance,self.cumulative[i]+math.sqrt(square)*t)
  return best

def install(api,routes_path=None,models_path=None,car_traffic_enabled=False):
 if getattr(api,'ambient188_installed',False):return api
 routes_path=Path(routes_path or ROOT/'backups/ambient188/routes.json');models_path=Path(models_path or ROOT/'backups/ambient188/models.json');data=json.loads(routes_path.read_text());models=json.loads(models_path.read_text())
 if data.get('version')!=188 or not 1<=len(data.get('routes',[]))<=200:raise ValueError('Invalid ambient catalog')
 unique={}
 for row in data['routes']:
  route=Route(row);unique.setdefault(route.fingerprint,route)
 routes=list(unique.values());world=api.world;original=api.dispatch;agents={};last_tick=[clock()];last_select=[-math.inf]
 with api.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_ambient188(route TEXT PRIMARY KEY,vehicle_id INTEGER UNIQUE NOT NULL)')
 original_rows=world.rows
 def visible_rows(state):
  rows=original_rows(state)
  if car_traffic_enabled:return rows
  with api.database()as db:keys={r[0]for r in db.execute('SELECT DISTINCT vehicle_id FROM pn_vehicle_access')}
  occupied={vid for vid,seat in world.SEATS}
  def keep(row):
   fields=world.VEHICLE_CACHE.get(row['id'])or json.loads(row['state'])
   return row['owner']!=0 or not fields.get('ambient188')or fields.get('ambient188_taken')or row['id']in occupied or row['id']in keys
  return [row for row in rows if keep(row)]
 world.rows=visible_rows
 def valid_people(now):
  return [(token,p,s)for token,s in api.GTA_STATE.items()if (p:=api.PRESENCE.get(token))and p.get('world')=='gta'and not p.get('dimension',0)and p.get('health',200)>100 and now-s.get('last_seen',0)<20]
 def ensure(route,phase,now):
  if route.id in agents:agents[route.id]['seen']=now;return
  if sum(a['route'].kind==route.kind for a in agents.values())>=(18 if route.kind=='car'else 28):return
  agent=dict(route=route,phase=phase,seen=now,id=1500000000+zlib.crc32(route.id.encode())%10000000)
  if route.kind=='car':
   point=route.sample(phase);model=('asea','primo')[zlib.crc32(route.id.encode())%2];point['z']+=models[model]['originOffset'];fields=dict(**point,rx=0,ry=0,rz=point['heading'],body=1000,engine=True,fuel=80,km=0,street=True,seats=4,ambient188=True,pose_epoch=0,repair_epoch=0)
   with api.database()as db:
    saved=db.execute('SELECT vehicle_id FROM pn_ambient188 WHERE route=?',(route.id,)).fetchone();row=db.execute('SELECT * FROM pn_vehicles WHERE id=?',(saved[0],)).fetchone()if saved else None
    if row and(row['owner']!=0 or not row['active']or db.execute('SELECT 1 FROM pn_vehicle_access WHERE vehicle_id=? LIMIT 1',(row['id'],)).fetchone()):return
    if row:
     old=world.public(row)
     if old.get('ambient188_taken'):return
     # Resume an existing unoccupied NPC car from its nearest route point.
     if any(vid==row['id']for vid,seat in world.SEATS):return
     agent['phase']=route.nearest([old[k]for k in ('x','y','z')])[1];vid=row['id']
    else:
     plate='A'+hashlib.sha256(route.id.encode()).hexdigest()[:7].upper();vid=db.execute('INSERT INTO pn_vehicles(owner,model,plate,locked,active,state,updated) VALUES(0,?,?,0,1,?,?)',(model,plate,json.dumps(fields),now)).lastrowid;db.execute('INSERT OR REPLACE INTO pn_ambient188 VALUES(?,?)',(route.id,vid))
   agent.update(vehicle=vid,model=model,offset=models[model]['originOffset'])
  agents[route.id]=agent
 def tick(now):
  elapsed=now-last_tick[0]
  if elapsed<.08:return
  dt=min(1.,max(0.,elapsed));last_tick[0]=now;people=valid_people(now)
  if now-last_select[0]>2:
   last_select[0]=now;wanted=set()
   for token,p,s in people:
    for kind,limit in ([('car',2),('ped',4)]if car_traffic_enabled else [('ped',4)]):
     nearest=sorted(((route.nearest([s[k]for k in ('x','y','z')]),route)for route in routes if route.kind==kind),key=lambda item:item[0][0])
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
  obstacles=[{**s,'kind':'person'}for _,p,s in people if not s.get('vehicle_id')]
  obstacles.extend({**fields,'id':vid,'kind':'car'}for vid,fields in list(world.VEHICLE_CACHE.items())if all(math.isfinite(fields.get(k,math.nan))for k in ('x','y','z')))
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
   blocked=False
   for obstacle in obstacles:
    if obstacle.get('id')==agent.get('vehicle'):continue
    dx=obstacle['x']-current['x'];dy=obstacle['y']-current['y'];along=dx*fx+dy*fy;side=abs(dx*fy-dy*fx)
    if abs(obstacle['z']-current['z']-offset)<2.2 and 0<along<(7 if route.kind=='car'else 1.3)and side<(1.9 if route.kind=='car'else .75):blocked=True;break
   # Sweep bounded substeps so a slow poll cannot tunnel through an obstacle.
   remaining=dt
   while not blocked and remaining>1e-9:
    step=min(.05,remaining);probe=route.sample(agent['phase']+step*route.speed)
    for obstacle in obstacles:
     if obstacle.get('id')==agent.get('vehicle'):continue
     dx=obstacle['x']-probe['x'];dy=obstacle['y']-probe['y'];along=dx*fx+dy*fy;side=abs(dx*fy-dy*fx)
     if abs(obstacle['z']-probe['z']-offset)<2.2 and 0<along<(7 if route.kind=='car'else 1.3)and side<(1.9 if route.kind=='car'else .75):blocked=True;break
    if not blocked:agent['phase']=(agent['phase']+step*route.speed)%route.length
    remaining-=step
   point=route.sample(agent['phase']);point['z']+=offset
   if blocked:point.update(vx=0,vy=0,vz=0,speed=0)
   agent['point']=point
   if route.kind=='car':
    fields.update(**point,rz=point['heading'],engine=fields.get('fuel',80)>0,ambient188=True,ambient188_paused=False);world.VEHICLE_CACHE[agent['vehicle']]=fields
 def view(p,s,now):
  if p.get('dimension',0):return dict(version=188,peds=[],cars=[])
  nearby=sorted((a for a in agents.values()if a.get('point')and math.dist([s[k]for k in ('x','y','z')],[a['point'][k]for k in ('x','y','z')])<150),key=lambda a:math.hypot(a['point']['x']-s['x'],a['point']['y']-s['y']))
  peds=[];cars=[]
  for a in nearby:
   point=a['point']
   if a['route'].kind=='car':
    cars.append(a['vehicle']);peds.append(dict(**point,id=a['id'],model=NPC_MODEL,vehicle_id=a['vehicle'],seat=-1))
   elif sum(not p['vehicle_id']for p in peds)<6:peds.append(dict(**point,id=a['id'],model=NPC_MODEL,vehicle_id=0,seat=-2))
  return dict(version=188,peds=peds[:10],cars=cars[:6],server_time=now)
 def dispatch(path,payload,token):
  with api.LOCK:
   now=clock()
   if path=='/api/gta/sync'and token in api.PRESENCE:tick(now)
   result,cookie=original(path,payload,token)
   if path=='/api/gta/sync'and result.get('success'):
    p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
    if p and s:
     drivers={a['vehicle']:a['id']for a in agents.values()if a['route'].kind=='car'and a.get('point')}
     vehicles=[dict(v,driver=drivers[v['id']])if v['id']in drivers and not v.get('driver')and not world.SEATS.get((v['id'],-1))else v for v in result.get('vehicles',[])]
     if not car_traffic_enabled:
      vehicles=[dict(v,vx=0,vy=0,vz=0,speed=0)if v.get('ambient188')and not v.get('ambient188_taken')and not v.get('driver')else v for v in vehicles]
     result=dict(result,vehicles=vehicles,ambient188=dict(view(p,s,now),car_traffic_enabled=car_traffic_enabled))
   if path=='/api/vehicles/enter'and result.get('success'):
    p=api.PRESENCE.get(token,{});vid=result.get('vehicle_id')
    for key,a in list(agents.items()):
     if a.get('vehicle')==vid:
      row=world.vehicle(vid);fields=dict(world.VEHICLE_CACHE.get(vid,json.loads(row['state'])));fields.update(ambient188_taken=True,vx=0,vy=0,vz=0,speed=0);world.VEHICLE_CACHE[vid]=fields;world.persist_vehicle(vid);agents.pop(key)
   return result,cookie
 api.dispatch=dispatch;api.ambient188_installed=True;api.ambient188_agents=agents;api.ambient_car_traffic_enabled=car_traffic_enabled;return api
