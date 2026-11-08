"""Orientation-safe garage64, retaining frozen61/63 account/property policies."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v63 as previous
host=previous.host
def install():
 sys.path[:0]=[str(R/'backups/gameplay-v64-backend'),str(R/'backups/gameplay-v63-backend'),str(R/'backups/gameplay-v61-backend')]
 from v61_extensions.city61 import install as city
 from v64_extensions.vehicles64 import install as vehicles
 from v61_extensions.property61 import install as property61
 from v61_extensions.radio61 import install as radio
 from v63_extensions.vehicles63 import install as fleet
 from v63_extensions.property63 import install as factions
 import run_gameplay_live_v53 as base
 api=factions(fleet(radio(property61(vehicles(city(base.install()))))));host.serve_local.session_api=api;return api
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v64.json':
   return self.json51(200,dict(backend_release='v64',seat_protocol=200,canonical_garage_retrieval=True,permanent_fleet_deletion=True,faction_property_ownership=True,orientation_safe_parking=True,office_interior_available=False,full_mobile_parity=False))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups' not in fixture.parents or not fixture.name.endswith('-v64.db'):p.error('Disposable -v64.db under backups required')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('Backend64: orientation-safe garage, existing63 policies retained',flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
