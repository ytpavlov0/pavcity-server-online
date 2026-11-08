"""Nearby faction consent, production jobs and safe fleet lifecycle."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v71 as previous
host=previous.host

def install():
    from city72 import install as vehicles
    from customs72 import install as customs
    from economy72 import install as economy
    from moderation72 import install as moderation
    return moderation(economy(customs(vehicles(previous.install()))))

from model_asset_host72 import ModelDataMixin
class Handler(ModelDataMixin,previous.Handler):
    def do_GET(self):
        if urlsplit(self.path).path=='/pn/server-capabilities-v72.json':
            return self.json51(200,dict(backend_release='v72',faction_consent=69,production_jobs=69,seat_protocol=200,property_retail=68,property_exit_marker=72,workshop_camera=72,air_controls=72,staff_tools=72,country_changes=72,office_income=72,missing_casino_models=72,full_mobile_parity=False,physical_acceptance=False))
        return super().do_GET()

if __name__=='__main__':
    p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018)
    p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
    if args.port==8000 and not args.live:p.error('Production requires --live')
    if args.fixture_db:
        fixture=Path(args.fixture_db).resolve()
        if R/'backups' not in fixture.parents or not fixture.name.endswith('-v72.db'):p.error('Disposable -v72.db under backups required')
        host.online_engine.DB_PATH=str(fixture)
    elif not args.live:p.error('Fixture DB required')
    host.online_engine.init_db();install()
    print('Backend70: places, paint, mechanic, UI and native fixes',flush=True)
    host.StableWorkerHTTPServer(('0.0.0.0' if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
