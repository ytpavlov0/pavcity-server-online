"""Explicit V33 host, retaining V32 elevators and the shared mobile/MDC API."""
from pathlib import Path
import sys,argparse,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_gameplay_live_v45 as previous
host=previous.host
def install():
 api=previous.install();sys.path.insert(0,str(R/'backups/gameplay-v48-backend'))
 from v48_extensions.property_preflight48 import install as preflight
 preflight(api);host.serve_local.session_api=api;return api
from candidate_asset_host47 import ModelDataMixin
class Handler(ModelDataMixin,previous.Handler):
 def do_GET(self):
  if self.path.split('?',1)[0]=='/pn/server-capabilities-v48.json':
   api=host.serve_local.session_api
   body=json.dumps(dict(backend_release='v48',repair_epoch_ack=181,compatible_property_api=45,native_sync=48,properties_transition=45,property_preflight=48,property_preflight_read_only=True,property_package='mobile-interiors196',property_geometry={k:{n:v[n]for n in('scene_sha256','ground_sha256','floor_z')}for k,v in api.property_transition45_catalog['packages'].items()},model_data_default=41,model_data_candidate=47,model_candidate_opt_in_only=True,model_native_render_verified=False,ambient_car_traffic=False)).encode();self.send_response(200)
   for k,v in [('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(body))),('Cache-Control','no-store'),('Cross-Origin-Opener-Policy','same-origin'),('Cross-Origin-Embedder-Policy','require-corp'),('Cross-Origin-Resource-Policy','same-origin')]:self.send_header(k,v)
   self.end_headers();self.wfile.write(body);return
  return super().do_GET()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8010);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups' not in fixture.parents or not fixture.name.endswith('-v48.db'):p.error('Use a disposable -v48.db below backups')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('V48 PC property preflight/focus and opt-in Tofas candidate; port'+str(args.port),flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
