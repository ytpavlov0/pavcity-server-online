"""178 backend: 177 + /fixveh repairs a moving car without stopping it. The stock command zeroed the velocity, reset the
rotation and bumped pose_epoch (every client re-placed and froze the car on the ground). The pose, velocity, rotation
and pose_epoch from before the command are put back; only body=1000 and repair_epoch+1 stay, so clients just repair."""
from pathlib import Path
import sys,re
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v177 as previous
host=previous.host;API=previous.API
STATS={'fixveh_kept_moving':0}
KEEP=('x','y','z','heading','rx','ry','rz','vx','vy','vz','pose_epoch')
def install():
 api=previous.install()
 if getattr(api,'v178_installed',False):return api
 import importlib
 city=importlib.import_module(api.__package__+'.pn_city');w=api.world
 old=api.dispatch
 def dispatch(path,*a,**k):
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  msg=payload.get('message')if path=='/api/chat/send'and isinstance(payload,dict)else None
  if isinstance(msg,str)and re.match(r'\s*/fixveh(\s|$)',msg,re.I):
   with api.LOCK:
    before=vid=None
    try:
     p=api.PRESENCE.get(token);parts=msg.split()
     vid=city.pointer(parts[1])if len(parts)>1 else(w.occupation(p['char_id'])[0]if p else 0)
     if vid:before=dict(city.car_state(w.vehicle(vid)))
    except Exception:before=None
    out=old(path,*a,**k)
    try:
     if before and isinstance(out[0],dict)and out[0].get('success'):
      f=dict(city.car_state(w.vehicle(vid)))
      for key in KEEP:
       if key in before:f[key]=before[key]
      city.set_car(vid,f);STATS['fixveh_kept_moving']+=1
    except Exception:pass
    return out
  return old(path,*a,**k)
 api.dispatch=dispatch;api.v178_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v178.json':
   return self.json51(200,dict(backend_release='v178',base_release='v177',v178=STATS,v177=previous.STATS,voice176=dict(previous.previous.STATS)))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v178.db'):p.error('Disposable -v178.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes178.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
