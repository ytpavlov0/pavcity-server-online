"""Nearby faction consent, production jobs and safe fleet lifecycle."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v68 as previous
host=previous.host

def install():
    from factions69 import install as factions
    from jobs69 import install as jobs
    from fleet69 import install as fleet
    return fleet(jobs(factions(previous.install())))

class Handler(previous.Handler):
    def do_GET(self):
        if urlsplit(self.path).path=='/pn/server-capabilities-v69.json':
            return self.json51(200,dict(backend_release='v69',faction_consent=69,production_jobs=69,seat_protocol=200,property_retail=68,full_mobile_parity=False,physical_acceptance=False))
        return super().do_GET()

if __name__=='__main__':
    p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018)
    p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
    if args.port==8000 and not args.live:p.error('Production requires --live')
    if args.fixture_db:
        fixture=Path(args.fixture_db).resolve()
        if R/'backups' not in fixture.parents or not fixture.name.endswith('-v69.db'):p.error('Disposable -v69.db under backups required')
        host.online_engine.DB_PATH=str(fixture)
    elif not args.live:p.error('Fixture DB required')
    host.online_engine.init_db();install()
    print('Backend69: faction consent, production, fleet lifecycle',flush=True)
    host.StableWorkerHTTPServer(('0.0.0.0' if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
