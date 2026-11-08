"""152 backend: as 151, with the engine .wasm no longer behind the download limiter (the loader fetches it once without a retry, so a 503 there stopped the engine: "Oyun motoru durdu: Isci hatasi") and a 192-thread / 512-queue pool so small files and the API are not refused under load.

151 backend: the v150 chain (v135 + features140 + features148) behind a game-data download limiter, listening on
127.0.0.1 only.

- Game data (/pn/model-data-v98/, /pn/story-data-v98/ GET/HEAD/POST, engine .wasm) shared the one Python process with
  the game API; ~100 viewers downloading at once saturated it, so syncs and joins timed out and players were thrown out.
  At most PAV151_DATA_SLOTS (default 8) data transfers run at once; the rest get 503 + Retry-After (1-3 s), which the
  io-worker97 client waits out instead of failing. API requests never wait for a data slot.
- The quick tunnels reach the server through 127.0.0.1, so the live server no longer listens on every interface: the
  machine's IP cannot reach the game server directly even where a firewall rule allows port 8000."""
from pathlib import Path
import sys,os,random,threading
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v150 as previous
host=previous.host
install=previous.install
SLOTS=max(1,int(os.environ.get('PAV151_DATA_SLOTS','8')))
GATE=threading.BoundedSemaphore(SLOTS)
STATS={'served':0,'busy':0,'active':0,'peak':0}
LOCK=threading.Lock()
def heavy(path):
 p=urlsplit(path).path
 return p.startswith(('/pn/model-data-v98/','/pn/story-data-v98/'))
class Handler(previous.Handler):
 def _limited(self,method):
  if not heavy(self.path):return method()
  if not GATE.acquire(timeout=.5):
   with LOCK:STATS['busy']+=1
   self.close_connection=True
   self.send_response(503);self.send_header('Retry-After',str(random.randint(1,3)));self.send_header('Cache-Control','no-store');self.send_header('Content-Length','0');self.end_headers();return
  with LOCK:STATS['active']+=1;STATS['peak']=max(STATS['peak'],STATS['active'])
  try:return method()
  finally:
   with LOCK:STATS['active']-=1;STATS['served']+=1
   GATE.release()
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v152.json':return self.json51(200,dict(backend_release='v152',base_release='v151',pool_workers=192,data_slots=SLOTS,data_stats=dict(STATS),localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  return self._limited(super().do_GET)
 def do_HEAD(self):return self._limited(super().do_HEAD)
 def do_POST(self):return self._limited(super().do_POST)
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v152.db'):p.error('Disposable -v152.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes152.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();host.StableWorkerHTTPServer(('127.0.0.1',args.port),Handler,max_workers=192,pending_requests=512).serve_forever()
