"""Original 24/7 property geometry with existing account/vehicle policies."""
from pathlib import Path
import sys,json
from urllib.parse import urlsplit,unquote
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v66 as previous
host=previous.host
def install():
 previous.configure()
 from market67 import configure
 pins=configure()
 import run_gameplay_live_v64 as base
 api=base.install()
 from v66_extensions.factory_paint66 import install as paint
 paint(api,json.loads((R/'backups/gameplay-v66-backend/palettes.json').read_text()))
 api.office208=pins;api.market210=json.loads((R/'backups/gameplay-v67-backend/v67_extensions/market210.json').read_text());host.serve_local.session_api=api
 return api
class Handler(previous.Handler):
 def translate_path(self,path):
  decoded=unquote(urlsplit(path).path)
  if decoded.startswith('/mlo210/'):
   root=(R/'backups/mobile-market210/public').resolve();name=decoded[len('/mlo210/'):]
   if not name or '\\'in name or '\x00'in name or ':'in name or any(p in('','..','.')for p in name.split('/')):return str(root/'__unavailable__')
   file=(root/name).resolve()
   if file.is_relative_to(root)and(name=='index.json'or name in('market/scene.json','market/ground.bin')or name.startswith('models/')and file.suffix=='.glb'):return str(file)
   return str(root/'__unavailable__')
  return super().translate_path(path)
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v67.json':return self.json51(200,dict(backend_release='v67',seat_protocol=200,office_interior_available=True,market_interior_available=True,market_package='mobile-market210',stock_factory_paint=66,full_mobile_parity=False,physical_acceptance=False))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups'not in fixture.parents or not fixture.name.endswith('-v67.db'):p.error('Disposable -v67.db under backups required')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('Backend67: original market210, office208 and paint66',flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
