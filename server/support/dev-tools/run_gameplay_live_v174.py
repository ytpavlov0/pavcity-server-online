"""174 backend: 173 + features174 (no car drops out of the vehicle list because of the per-cell row cache; a traffic car
adopted with G is listed at once). See features174.py."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v173 as previous
host=previous.host;API=previous.API
def install():
 from features174 import install as features174
 api=features174(previous.install());API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v174.json':
   a=API[0];v172=previous.previous
   return self.json51(200,dict(backend_release='v174',base_release='v173',rows174=dict(getattr(a,'features174_stats',{}))if a else{},ping173=dict(previous.STATS),rt172=dict(v172.STATS,enabled=v172.SECRET.exists()and not v172.OFF.exists()),realtime=v172.rt_status(),maintenance=bool(v172.previous.conf()),auto_open=bool((v172._conf171()or{}).get('auto_open'))))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v174.db'):p.error('Disposable -v174.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes174.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
