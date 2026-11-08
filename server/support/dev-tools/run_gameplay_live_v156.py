"""156 backend: 155 with HTTP/1.1 keep-alive, built so it cannot exhaust the worker pool.

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
import run_gameplay_live_v155 as previous
host=previous.host
install=previous.install
IDLE=3;BUSY=300;WORKERS=512;QUEUE=1024
class Handler(previous.Handler):
 protocol_version='HTTP/1.1'
 timeout=IDLE
 def parse_request(self):
  self.connection.settimeout(BUSY)
  return super().parse_request()
 def handle_one_request(self):
  super().handle_one_request()
  if not self.close_connection:self.connection.settimeout(IDLE)
 def log_error(self,fmt,*args):
  if fmt.startswith('Request timed out'):return
  super().log_error(fmt,*args)
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v156.json':
   with previous.P.LOCK:prot=dict(previous.P.STATS)
   return self.json51(200,dict(backend_release='v156',base_release='v155',keep_alive=True,idle_timeout_s=IDLE,busy_timeout_s=BUSY,pool_workers=WORKERS,pool_queue=QUEUE,protection_requests=prot.get('requests',0),wasm_gzip=previous.P.WASM_GZ.is_file(),localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  return super().do_GET()
class Server(host.StableWorkerHTTPServer):
 request_queue_size=1024
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v156.db'):p.error('Disposable -v156.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes156.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();Server(('127.0.0.1',args.port),Handler,max_workers=WORKERS,pending_requests=QUEUE).serve_forever()
