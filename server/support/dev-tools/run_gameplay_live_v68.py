"""67 geometry and synchronization with property retail transaction68."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'support/dev-tools'))
import run_gameplay_live_v67 as previous
host = previous.host

def install():
    from retail68 import install as retail
    return retail(previous.install())

class Handler(previous.Handler):
    def do_GET(self):
        if urlsplit(self.path).path == '/pn/server-capabilities-v68.json':
            return self.json51(200, dict(backend_release='v68', seat_protocol=200, office_interior_available=True, market_interior_available=True, market_package='mobile-market210', property_retail=68, stock_factory_paint=66, full_mobile_parity=False, physical_acceptance=False))
        return super().do_GET()

if __name__ == '__main__':
    p = __import__('argparse').ArgumentParser()
    p.add_argument('--port', type=int, default=8018)
    p.add_argument('--fixture-db')
    p.add_argument('--live', action='store_true')
    args = p.parse_args()
    if args.port == 8000 and not args.live:
        p.error('Production requires --live')
    if args.fixture_db:
        fixture = Path(args.fixture_db).resolve()
        if R / 'backups' not in fixture.parents or not fixture.name.endswith('-v68.db'):
            p.error('Disposable -v68.db under backups required')
        host.online_engine.DB_PATH = str(fixture)
    elif not args.live:
        p.error('Fixture DB required')
    host.online_engine.init_db()
    install()
    print('Backend68: property retail, market210, office208, paint66', flush=True)
    host.StableWorkerHTTPServer(('0.0.0.0' if args.live and args.port == 8000 else '127.0.0.1', args.port), Handler).serve_forever()
