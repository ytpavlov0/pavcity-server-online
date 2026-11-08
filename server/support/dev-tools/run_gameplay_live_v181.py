"""181 backend: 180 + spawns spread over the city. 40+ players spawning at one hospital (v179) made a crowd that stalled
everyone's frame rate. A join now goes to a random city spot when it is a first spawn, or when 6+ other players stand
within 40 m of where it would spawn; the spot with the fewest players within 60 m wins (random among equals) and a
small ring offset keeps two joins on one spot apart. Jail, interiors (dimension) and the dead/hospital rule are left
as they are; everyone else keeps their saved position."""
from pathlib import Path
import sys,math,random,itertools
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v180 as previous
host=previous.host;API=previous.API
STATS={'spread':0,'first':0,'crowd':0}
# sidewalks / doors of public places (service NPC spots, banks, job hub, depot, Legion Square)
SPOTS=[(215.7,-920.3,30.6,0),(-814.3,-183.8,37.6,120),(136.8,-1708.4,29.3,140),(-1282.4,-1116.8,7.0,90),(293.7,-601.5,43.2,70),
 (-56.5,-1096.3,26.4,250),(150.0,-1040.0,29.4,160),(-1212.9,-330.8,37.8,30),(314.2,-278.9,54.2,160),(78.4,111.8,81.2,160),(1201.0,-1276.0,35.2,0)]
RING=[(0,0),(1.8,0),(-1.8,0),(0,1.8),(0,-1.8),(1.8,1.8),(-1.8,1.8),(1.8,-1.8),(-1.8,-1.8)]
_n=itertools.count()
def install():
 api=previous.install()
 if getattr(api,'v181_installed',False):return api
 import importlib
 mp=importlib.import_module(api.__package__+'.pn_multiplayer')
 def others(token):
  out=[]
  for k,s in list(api.GTA_STATE.items()):
   if k==token:continue
   try:out.append((float(s['x']),float(s['y'])))
   except Exception:pass
  return out
 def near(pts,x,y,r):return sum(1 for a,b in pts if math.hypot(a-x,b-y)<r)
 old=api.dispatch
 def dispatch(path,*a,**k):
  if path!='/api/gta/join':return old(path,*a,**k)
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  first=False
  try:
   with mp.database()as db:first=db.execute('SELECT 1 FROM pn_saved WHERE char_id=?',(int(payload.get('char_id')),)).fetchone()is None
  except Exception:pass
  out=old(path,*a,**k)
  try:
   res=out[0];sp=res.get('spawn')if isinstance(res,dict)else None;p=api.PRESENCE.get(token)or{}
   if res.get('success')and isinstance(sp,dict)and not sp.get('jail')and not p.get('dimension')and not res.get('jail_until'):
    pts=others(token);crowd=near(pts,float(sp['x']),float(sp['y']),40)>=6
    if first or crowd:
     with api.LOCK:
      best=min(near(pts,x,y,60)for x,y,z,h in SPOTS);pick=random.choice([s for s in SPOTS if near(pts,s[0],s[1],60)==best])
      dx,dy=RING[next(_n)%len(RING)]
     sp.update(x=pick[0]+dx,y=pick[1]+dy,z=pick[2],heading=pick[3],safe_ground=True);STATS['spread']+=1;STATS['first' if first else 'crowd']+=1
  except Exception:pass
  return out
 api.dispatch=dispatch;api.v181_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v181.json':
   return self.json51(200,dict(backend_release='v181',base_release='v180',v181=STATS,v180=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v181.db'):p.error('Disposable -v181.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes181.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
