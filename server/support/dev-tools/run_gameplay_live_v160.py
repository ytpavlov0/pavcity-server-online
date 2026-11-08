"""160 backend: 159 + features160 (vehicle row cache per cell, memoized vehicle-state JSON, schema() once per 30 s,
WAL + synchronous=NORMAL). Sync CPU under api.LOCK ~48 ms -> ~15 ms at 8 clustered players; join 897 SQL -> ~60."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v159 as previous
host=previous.host
API=[None]
def install():
 from features160 import install as features160
 API[0]=features160(previous.install());return API[0]
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v160.json':
   st=dict(getattr(API[0],'features160_stats',{}))if API[0]else{}
   return self.json51(200,dict(backend_release='v160',base_release='v159',features160=st,keep_alive=True,safe_keepalive=True,pool_workers=previous.WORKERS,pool_queue=previous.QUEUE,gate=True,wasm_gzip=previous.P.WASM_GZ.is_file(),localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v160.db'):p.error('Disposable -v160.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes160.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();previous.Server(('127.0.0.1',args.port),Handler,max_workers=previous.WORKERS,pending_requests=previous.QUEUE).serve_forever()
