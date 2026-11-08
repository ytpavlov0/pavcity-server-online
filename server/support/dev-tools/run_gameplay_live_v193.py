"""193 backend: 192 + rescue193 (a reload while dead brings the player back down where he fell, the medic window
continues; see rescue193.py). /pn/server-capabilities-v193.json."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v192 as previous
import run_gameplay_live_v191 as v191
import rescue193
host=previous.host;API=previous.API
def install():
 api=previous.install()
 if getattr(api,'v193_installed',False):return api
 rescue193.install(api,v191);api.v193_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v193.json':
   api=API[0];st=dict(getattr(api,'rescue193',{}).get('stats',{}))if api else{}
   return self.json51(200,dict(backend_release='v193',base_release='v192',v193=st,v192=dict(getattr(api,'crime192',{}).get('stats',{}))if api else{}))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v193.db'):p.error('Disposable -v193.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes193.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous
 for _ in range(25):pp=pp.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
