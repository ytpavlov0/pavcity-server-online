"""V32 extension host. Importing does not install schemas or start a server."""
from pathlib import Path
import sys,argparse,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_gameplay_live_v30 as previous
host=previous.host
def install():
 api=previous.install();sys.path.insert(0,str(ROOT/'backups/gameplay-v32-backend'))
 from v32_extensions.elevators176 import install as extend_lifts
 extend_lifts(api);host.serve_local.session_api=api;return api
class Handler(previous.Handler):
 def do_GET(self):
  if self.path.split('?',1)[0]=='/pn/server-capabilities-v32.json':
   body=json.dumps(dict(backend_release='v32',api_namespace='gameplay_v29',elevators=176,server_target_tickets=True,bound_rollback=True)).encode()
   self.send_response(200)
   for k,v in [('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(body))),('Cache-Control','no-store'),('Cross-Origin-Opener-Policy','same-origin'),('Cross-Origin-Embedder-Policy','require-corp'),('Cross-Origin-Resource-Policy','same-origin')]:self.send_header(k,v)
   self.end_headers();self.wfile.write(body);return
  return super().do_GET()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8009);parser.add_argument('--fixture-db');parser.add_argument('--live',action='store_true');args=parser.parse_args()
 if args.port==8000 and not args.live:parser.error('Production requires explicit --live.')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if ROOT/'backups' not in fixture.parents or not fixture.name.endswith('-v32.db'):parser.error('Fixture DB must be a named -v32.db below workspace backups.')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:parser.error('Use a disposable --fixture-db unless running an authorized live release.')
 host.online_engine.init_db();install();print('V32 pinned gameplay_v29 + mobile170 + elevators176; port'+str(args.port),flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else'127.0.0.1',args.port),Handler).serve_forever()
