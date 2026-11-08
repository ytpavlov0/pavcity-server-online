"""City63 policies on the immutable61 backend; native/frontend62 unchanged."""
from pathlib import Path
import sys,json
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v61 as previous
host=previous.host
def install():
 sys.path.insert(0,str(R/'backups/gameplay-v63-backend'))
 from v63_extensions.vehicles63 import install as vehicles
 from v63_extensions.property63 import install as properties
 api=properties(vehicles(previous.install()));host.serve_local.session_api=api;return api
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v63.json':
   return self.json51(200,dict(backend_release='v63',seat_protocol=200,canonical_garage_retrieval=True,permanent_fleet_deletion=True,faction_property_ownership=True,faction_property_pc_mobile_keys=True,office_interior_available=False,full_mobile_parity=False))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups' not in fixture.parents or not fixture.name.endswith('-v63.db'):p.error('Disposable -v63.db under backups required')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('Backend63: shared garage and membership-bound property keys',flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
