"""Vehicle lifecycle and city services61; engine/camera60 remain separate."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v53 as previous
host=previous.host

def install():
    sys.path.insert(0,str(R/'backups/gameplay-v61-backend'))
    from v61_extensions.city61 import install as city
    from v61_extensions.vehicles61 import install as vehicles
    from v61_extensions.property61 import install as properties
    from v61_extensions.radio61 import install as radio
    return radio(properties(vehicles(city(previous.install()))))

class Handler(previous.Handler):
    def do_GET(self):
        if urlsplit(self.path).path=='/pn/server-capabilities-v61.json':
            return self.json51(200,dict(backend_release='v61',native_sync=52,seat_protocol=200,account_single_presence=True,paid_parking=250,empty_return_minutes=35,garages=3,payroll_bank=True,phone_text=True,faction_radio=True,full_mobile_parity=False,office_interior_available=False))
        return super().do_GET()

if __name__=='__main__':
    p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
    if args.port==8000 and not args.live:p.error('Production requires --live')
    if args.fixture_db:
        fixture=Path(args.fixture_db).resolve()
        if R/'backups' not in fixture.parents or not fixture.name.endswith('-v61.db'):p.error('Disposable -v61.db under backups required')
        host.online_engine.DB_PATH=str(fixture)
    elif not args.live:p.error('Fixture DB required')
    host.online_engine.init_db();install()
    print('Backend61: guarded vehicles, account lease, bank payroll, phone text, property metadata',flush=True)
    host.StableWorkerHTTPServer(('0.0.0.0' if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
