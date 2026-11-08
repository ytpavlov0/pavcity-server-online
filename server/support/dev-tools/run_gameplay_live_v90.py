from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v89 as previous
host=previous.host
def install():
 from duty90 import install as duty
 return duty(previous.install())
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v90.json':return self.json51(200,dict(backend_release='v90',frontend_components=90,model_data=89,mobile=217,physical_acceptance=False,magazines=True))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups' not in f.parents or not f.name.endswith('-v90.db'):p.error('Disposable -v90.db under backups required')
  host.online_engine.DB_PATH=str(f)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();host.StableWorkerHTTPServer(('0.0.0.0' if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
