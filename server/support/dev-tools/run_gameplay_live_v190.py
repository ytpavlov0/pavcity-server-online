"""190 backend: 189 + job points reachable on slopes.
- Job steps asked for 5 m in 3D (pn_roleplay.near). Some gather points (Bağcılık · Üzüm toplama, 2nd point) sit inside
  the vine rows or off the walkable ground: the closest a player could stand was ~7 m, so "E basılı tut" never
  completed. For a point that is one of the jobs' own points / hubs / finishes, near() now also accepts a player
  within radius + 2 m horizontally and 8 m in height. Every other caller (banks, ATMs, duty points) keeps the strict
  3D check: the point must match a job coordinate exactly.
- /pn/server-capabilities-v190.json: counts of tolerant acceptances."""
from pathlib import Path
import sys,math
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v189 as previous
host=previous.host;API=previous.API
STATS={'job_point_tolerant':0}
def job_points(jobs):
 pts=set()
 for j in jobs.values():
  for q in [*(j.get('points')or[]),j.get('hub'),j.get('finish')]:
   if isinstance(q,dict)and all(k in q for k in('x','y','z')):pts.add((round(q['x'],2),round(q['y'],2),round(q['z'],2)))
 return pts
def tolerant(strict,points):
 def near(state,point,radius=5):
  if strict(state,point,radius):return True
  try:
   key=(round(point['x'],2),round(point['y'],2),round(point['z'],2))
   if key not in points or not state:return False
   ok=math.hypot(state['x']-point['x'],state['y']-point['y'])<=radius+2 and abs(state['z']-point['z'])<=8
  except(KeyError,TypeError):return False
  if ok:STATS['job_point_tolerant']+=1
  return ok
 near.strict190=strict
 return near
def install():
 api=previous.install()
 if getattr(api,'v190_installed',False):return api
 import pn_roleplay
 if not hasattr(pn_roleplay.near,'strict190'):pn_roleplay.near=tolerant(pn_roleplay.near,job_points(pn_roleplay.JOBS))
 api.v190_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v190.json':
   return self.json51(200,dict(backend_release='v190',base_release='v189',v190=STATS,v189=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v190.db'):p.error('Disposable -v190.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes190.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous
 for _ in range(25):pp=pp.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
