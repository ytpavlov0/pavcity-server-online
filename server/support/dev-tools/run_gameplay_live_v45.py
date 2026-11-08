"""Explicit V33 host, retaining V32 elevators and the shared mobile/MDC API."""
from pathlib import Path
import sys,argparse,json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_gameplay_live_v44 as previous
host=previous.host
def install():
 api=previous.install();sys.path.insert(0,str(R/'backups/gameplay-v45-backend'))
 from v45_extensions.property_transition45 import install as properties
 properties(api,R/'backups/gameplay-v45-backend/v45_data/properties45.json');host.serve_local.session_api=api;return api
from donate_asset_host_v41 import ModelDataMixin
class Handler(previous.Handler):
 def send_head(self):
  from urllib.parse import urlsplit,unquote
  decoded=unquote(urlsplit(self.path).path)
  if chr(92)in decoded or chr(0)in decoded:self.send_error(404);return None
  return super().send_head()
 def do_GET(self):
  if self.path.split('?',1)[0]=='/pn/server-capabilities-v45.json':
   body=json.dumps(dict(backend_release='v45',api_namespace='gameplay_v29',repair_epoch_ack=181,invalid_legacy_models_filtered=True,baseline='v44',backend_implementation=45,properties_transition=45,property_package='mobile-interiors196',property_geometry={k:{name:v[name]for name in ('scene_sha256','ground_sha256','floor_z')}for k,v in host.serve_local.session_api.property_transition45_catalog['packages'].items()},property_kinds=['apartment','garage'],property_prepare_seconds=20,property_confirm_seconds=15,city_branding=37,new_vehicle_models=True,additional_models=['pavtofas', 'pavbus', 'g65', 'audquattros'],model_activation=41,model_native_render_verified=False,native_sync=44,vehicle_paint=43,stability=42,ambient_car_traffic=False,appearance=182,environment=183,clock_rate=30,weather_step_seconds=600,ambient=188,services=180,community=179,casino=34,rp_currency_only=True)).encode();self.send_response(200)
   for k,v in [('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(body))),('Cache-Control','no-store'),('Cross-Origin-Opener-Policy','same-origin'),('Cross-Origin-Embedder-Policy','require-corp'),('Cross-Origin-Resource-Policy','same-origin')]:self.send_header(k,v)
   self.end_headers();self.wfile.write(body);return
  return super().do_GET()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8010);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups' not in fixture.parents or not fixture.name.endswith('-v45.db'):p.error('Use a disposable -v45.db below backups')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('V45 bounded mobile property transitions and preserved donate activation; port'+str(args.port),flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
