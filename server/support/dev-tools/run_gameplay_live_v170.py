"""170 backend: 169 + shorter GIL switch interval, tunable at runtime.

The 169 sampler (31 Oct, 13 players) showed api.LOCK held ~51 % of the time, the holder spread over ~30 small SQLite
queries per sync that each take <0.5 ms alone. sqlite3 releases the GIL around every statement; getting it back waits
until the current GIL holder (JSON encode/parse of other requests, file serving, the 60 dispatch layers outside the lock)
reaches the switch interval (CPython default 5 ms). So every query of the lock holder could cost up to ~5 ms of waiting,
~100+ ms per sync, while every other request queued for api.LOCK (a GIL convoy). sys.setswitchinterval is now
DEFAULT (1 ms); the file backups/switch170.txt (seconds, 0.0002-0.01) overrides it, re-read once per second, so the
value can be tuned or reverted without a restart. No request or response changes."""
from pathlib import Path
import sys,threading,time
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v169 as previous
host=previous.host;API=previous.API;install=previous.install
DEFAULT=0.001;FILE=R/'backups/switch170.txt';STATE={'value':DEFAULT,'source':'default','changes':0}
def apply():
 v=DEFAULT;src='default'
 try:
  if FILE.exists():
   x=float(FILE.read_text(encoding='utf8').strip())
   if 0.0002<=x<=0.01:v=x;src='file'
 except Exception:pass
 if abs(sys.getswitchinterval()-v)>1e-9:sys.setswitchinterval(v);STATE['changes']+=1
 STATE.update(value=sys.getswitchinterval(),source=src)
def watcher():
 while True:
  try:apply()
  except Exception:pass
  time.sleep(1)
apply();threading.Thread(target=watcher,name='pav-switch170',daemon=True).start()
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v170.json':
   with previous.previous.previous.previous.ACC_LOCK:
    W=previous.previous.previous.previous.WIN;last=previous.previous.previous.previous.table(W['last'],W['last_span'])
   return self.json51(200,dict(backend_release='v170',base_release='v169',switch_interval=dict(STATE),last_minute=last))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v170.db'):p.error('Disposable -v170.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes170.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
