from pathlib import Path
import sys,json
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v98 as previous
from model_asset_host98 import ModelDataMixin
import crash98
import features85,features99
features85.install=features99.install
host=previous.host
def install():return previous.install()
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v99.json':return self.json51(200,dict(backend_release='v99',frontend_components=99,model_data=98,mobile=217,physical_acceptance=False,prelogin_crash_diagnostics=True))
  return super().do_GET()
 def do_POST(self):
  if urlsplit(self.path).path!='/api/engine99/crash':return super().do_POST()
  try:
   size=int(self.headers.get('Content-Length','0'));origin=self.headers.get('Origin')
   if origin and urlsplit(origin).netloc!=self.headers.get('Host')or self.headers.get('Sec-Fetch-Site')=='cross-site':self.close_connection=True;return self.json51(403,dict(success=False))
   if self.headers.get('Content-Type','').split(';')[0]!='application/json':self.close_connection=True;return self.json51(415,dict(success=False))
   if not 0<size<=5120:self.close_connection=True;return self.json51(413,dict(success=False))
   accepted=crash98.accept(json.loads(self.rfile.read(size)))
   return self.json51(200 if accepted else 429,dict(success=accepted))
  except(ValueError,TypeError,UnicodeDecodeError):return self.json51(400,dict(success=False))
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v99.db'):p.error('Disposable -v99.db under backups required')
  host.online_engine.DB_PATH=str(f)
  crash98.OUTPUT=f.parent/'fixture-crashes99.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else'127.0.0.1',args.port),Handler).serve_forever()
