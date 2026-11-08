"""Release53 opt-in mobile finite ammunition; native52 retained."""
from pathlib import Path
import sys, json
from urllib.parse import urlsplit
R = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(R/'support/dev-tools'),str(R/'backups/gameplay-v53-backend')]
import run_gameplay_live_v51 as previous
from v53_extensions.combat53 import install as combat
from v53_extensions.cover53 import Cover53
host = previous.host


def install(cover=None, clock=None):
    api = previous.install()
    if getattr(api, 'combat53_installed', False): return api
    if cover is None: cover = Cover53(R/'backups/gameplay-v53-backend/collision')
    kwargs = dict(cover=cover)
    if clock is not None: kwargs['clock'] = clock
    return combat(api, **kwargs)


class Handler(previous.Handler):
    def do_GET(self):
        if urlsplit(self.path).path == '/pn/server-capabilities-v53.json':
            return self.json51(200, dict(backend_release='v53', backend_implementation=53,
                         native_sync=52, model_data_default=49, seat_protocol=200,
                         repair_epoch_ack=181, combat53=True, combat53_mobile_only=True,
                         combat53_fire='/api/combat53/fire', combat53_state='/api/combat53/state',
                         combat53_damage_requires_verified_cover=True, combat53_cover='static-ybn-blockers-only',
                         combat53_positive_damage_enabled=False,
                         ambient_car_traffic=False, native_runtime_or_variation_parity_verified=False))
        return super().do_GET()


if __name__ == '__main__':
    p = __import__('argparse').ArgumentParser()
    p.add_argument('--port', type=int, default=8010); p.add_argument('--fixture-db'); p.add_argument('--live', action='store_true')
    args = p.parse_args()
    if args.port == 8000 and not args.live: p.error('Production requires --live')
    if args.fixture_db:
        fixture = Path(args.fixture_db).resolve()
        if R/'backups' not in fixture.parents or not fixture.name.endswith('-v53.db'): p.error('Disposable -v53.db under backups required')
        host.online_engine.DB_PATH = str(fixture)
    elif not args.live: p.error('Fixture DB required')
    host.online_engine.init_db(); install()
    print('V53 opt-in finite ammunition, exact receipts; partial static blockers; native52 retained', flush=True)
    host.StableWorkerHTTPServer(('0.0.0.0' if args.live and args.port==8000 else '127.0.0.1',args.port), Handler).serve_forever()
