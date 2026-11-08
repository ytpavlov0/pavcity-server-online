"""158 backend: 157 with a larger pool: 1024 workers, 2048 queue. Each of the four quick tunnels keeps up to 100 idle connections to the origin; with keep-alive every open connection holds a worker, and a burst from ~6 players already produced one raw 503 from the 512 pool. Blocked threads cost no CPU.

156 backend: 155 with HTTP/1.1 keep-alive, built so it cannot exhaust the worker pool.

Why: the server answered every request on its own TCP connection. With 6 players the host already had ~15,000 sockets in
TIME_WAIT on 127.0.0.1:8000 against Windows' 16,384-port range, and 100 players (10-15 requests/s each) need more
connections per minute than any port range allows, so the tunnels could not reach the origin (502). Reusing connections
is the only way to carry that many players. The 153 attempt failed because idle connections were kept for 20 s on a
192-thread pool: ~800 open tunnel connections held every worker and all requests were refused.
How: a connection is kept open only while the client keeps requesting: 3 s idle read timeout between requests, but a
300 s timeout while a response is being written (a slow remote download must not be cut); 512 workers, a 1024-deep job
queue and a 1024 listen backlog; the pool's raw 503 remains the last resort. Idle closes are not logged."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v157 as previous
host=previous.host
install=previous.install
IDLE=3;BUSY=300;WORKERS=1024;QUEUE=2048
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v158.json':
   with previous.P.LOCK:prot=dict(previous.P.STATS)
   return self.json51(200,dict(backend_release='v158',base_release='v157',keep_alive=True,idle_timeout_s=IDLE,busy_timeout_s=BUSY,pool_workers=WORKERS,pool_queue=QUEUE,gate=True,protection_requests=prot.get('requests',0),wasm_gzip=previous.P.WASM_GZ.is_file(),localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  return super().do_GET()
class Server(host.StableWorkerHTTPServer):
 request_queue_size=2048
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v158.db'):p.error('Disposable -v158.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes158.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();Server(('127.0.0.1',args.port),Handler,max_workers=WORKERS,pending_requests=QUEUE).serve_forever()
