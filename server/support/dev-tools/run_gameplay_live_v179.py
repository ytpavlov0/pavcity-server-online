"""179 backend: 178 + first-time characters (no saved state yet) spawn at the hospital (Pillbox, the respawn point) instead
of the Legion Square default, spread over 12 spots ~2 m apart; a spot with another player within 1.5 m is skipped, so
new players do not spawn inside each other. Later joins keep their saved position as before."""
from pathlib import Path
import sys,math,itertools
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v178 as previous
host=previous.host;API=previous.API
STATS={'first_spawns':0}
# around HOSPITAL_SPAWN (293.7,-601.5,43.2, heading 70) on the Pillbox upper plaza
OFFSETS=[(0,0),(1.8,1.2),(-1.8,1.2),(1.8,-1.2),(-1.8,-1.2),(0,2.4),(0,-2.4),(3.6,0),(-3.6,0),(3.6,2.4),(-3.6,2.4),(3.6,-2.4)]
_turn=itertools.count()
def install():
 api=previous.install()
 if getattr(api,'v179_installed',False):return api
 import importlib
 mp=importlib.import_module(api.__package__+'.pn_multiplayer');w=api.world
 base=dict(w.HOSPITAL_SPAWN)
 def spots_taken():
  out=[]
  for s in list(api.GTA_STATE.values()):
   try:out.append((float(s['x']),float(s['y'])))
   except Exception:pass
  return out
 def pick():
  taken=spots_taken();start=next(_turn)%len(OFFSETS)
  for k in range(len(OFFSETS)):
   dx,dy=OFFSETS[(start+k)%len(OFFSETS)];x,y=base['x']+dx,base['y']+dy
   if all(math.hypot(x-tx,y-ty)>1.5 for tx,ty in taken):return x,y
  dx,dy=OFFSETS[start];return base['x']+dx,base['y']+dy
 old=api.dispatch
 def dispatch(path,*a,**k):
  if path!='/api/gta/join':return old(path,*a,**k)
  payload=a[0]if a else k.get('payload',{})
  first=False
  try:
   cid=int(payload.get('char_id'))
   with mp.database()as db:first=db.execute('SELECT 1 FROM pn_saved WHERE char_id=?',(cid,)).fetchone()is None
  except Exception:first=False
  out=old(path,*a,**k)
  try:
   res=out[0]
   if first and isinstance(res,dict)and res.get('success')and isinstance(res.get('spawn'),dict)and not res['spawn'].get('jail'):
    with api.LOCK:x,y=pick()
    res['spawn'].update(x=x,y=y,z=base['z'],heading=base.get('heading',70),safe_ground=True);STATS['first_spawns']+=1
  except Exception:pass
  return out
 api.dispatch=dispatch;api.v179_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v179.json':
   return self.json51(200,dict(backend_release='v179',base_release='v178',v179=STATS,v178=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v179.db'):p.error('Disposable -v179.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes179.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
