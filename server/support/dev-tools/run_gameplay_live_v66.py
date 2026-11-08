"""Canonical stock paint and write throttling; office65/native64 retained."""
from pathlib import Path
import sys,json,importlib
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v65 as previous
host=previous.host
def configure():
 sys.path.insert(0,str(R/'backups/gameplay-v66-backend'))
 module=importlib.import_module('v66_extensions.vehicle_paint66');key='v43_extensions.vehicle_paint43'
 if key in sys.modules and sys.modules[key]is not module:raise RuntimeError('Paint module already installed from old release')
 sys.modules[key]=module
def install():
 configure();api=previous.install()
 from v66_extensions.factory_paint66 import install as paint
 paint(api,json.loads((R/'backups/gameplay-v66-backend/palettes.json').read_text()))
 host.serve_local.session_api=api
 return api
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v66.json':return self.json51(200,dict(backend_release='v66',seat_protocol=200,office_interior_available=True,office_package='mobile-office208',stock_factory_paint=66,paint_write_throttle=66,full_mobile_parity=False,physical_acceptance=False))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups'not in fixture.parents or not fixture.name.endswith('-v66.db'):p.error('Disposable -v66.db under backups required')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('Backend66: stock factory paint and bounded paint writes',flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
