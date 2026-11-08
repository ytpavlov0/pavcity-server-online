"""Explicit V33 host, retaining V32 elevators and the shared mobile/MDC API."""
from pathlib import Path
import sys,argparse,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_gameplay_live_v32 as previous
host=previous.host
def install():
 api=previous.install();sys.path.insert(0,str(R/'backups/gameplay-v33-backend'))
 from v33_extensions.gameplay33 import install as extend
 extend(api);host.serve_local.session_api=api;return api
class Handler(previous.Handler):
 def do_GET(self):
  if self.path.split('?',1)[0]=='/pn/server-capabilities-v33.json':
   body=json.dumps(dict(backend_release='v33',api_namespace='gameplay_v29',elevators=176,bound_rollback=True,finite_walking_reload=True,package_guard=True,client_platform=True)).encode();self.send_response(200)
   for k,v in [('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(body))),('Cache-Control','no-store'),('Cross-Origin-Opener-Policy','same-origin'),('Cross-Origin-Embedder-Policy','require-corp'),('Cross-Origin-Resource-Policy','same-origin')]:self.send_header(k,v)
   self.end_headers();self.wfile.write(body);return
  return super().do_GET()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8010);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups' not in fixture.parents or not fixture.name.endswith('-v33.db'):p.error('Use a disposable -v33.db below backups')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('V33 pinned API; port'+str(args.port),flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
