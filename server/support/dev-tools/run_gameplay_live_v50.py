"""Release50 host: scoped seat generations, addon paint defaults, shadow NPCs."""
from pathlib import Path
import sys,argparse,json
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'support/dev-tools'),str(R/'backups/gameplay-v50-backend')]
import run_gameplay_live_v49 as previous
from v50_extensions.vehicle_seats50 import install as seats
from v50_extensions.population200 import install as population
from v50_extensions.factory_paint50 import install as paint
host=previous.host
def install():
 api=previous.install();data=R/'backups/gameplay-v50-backend';models=json.loads((data/'models.json').read_text());palettes=json.loads((data/'factory-palettes.json').read_text())
 seats(api);population(api,{int(k):v for k,v in models['peds'].items()},{int(k):v for k,v in models['vehicles'].items()});paint(api,palettes)
 return api
class Handler(previous.Handler):
 def do_GET(self):
  if self.path.split('?',1)[0]=='/pn/server-capabilities-v50.json':
   body=json.dumps(dict(backend_release='v50',backend_implementation=50,repair_epoch_ack=181,seat_protocol=200,native_sync=50,properties_transition=45,property_preflight=48,model_data_default=49,ambient_car_traffic=False,population200='shadow',population200_visual_enabled=False,addon_factory_paint=50,model_native_render_verified=False)).encode();self.send_response(200)
   for k,v in [('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(body))),('Cache-Control','no-store'),('Cross-Origin-Opener-Policy','same-origin'),('Cross-Origin-Embedder-Policy','require-corp'),('Cross-Origin-Resource-Policy','same-origin')]:self.send_header(k,v)
   self.end_headers();self.wfile.write(body);return
  return super().do_GET()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8010);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups'not in fixture.parents or not fixture.name.endswith('-v50.db'):p.error('Use a disposable -v50.db below backups')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('V50 seat200/addon factory paint/native shadow only; port'+str(args.port),flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else'127.0.0.1',args.port),Handler).serve_forever()
