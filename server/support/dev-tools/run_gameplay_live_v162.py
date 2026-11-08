"""162 backend: 161 + features162 (adopted traffic cars no longer stay stuck at the 256 cap: least recently used,
unoccupied, non-job cars away from players are removed before a registration; see features162.py)."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v161 as previous
host=previous.host
API=[None]
def install():
 from features162 import install as features162
 API[0]=features162(previous.install());return API[0]
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v162.json':
   a=API[0];st=dict(getattr(a,'features162_stats',{}))if a else{}
   return self.json51(200,dict(backend_release='v162',base_release='v161',traffic_eviction=st,boot_packs=dict(previous.STATS,available=(previous.PACKS/'packs/packs.json').is_file()),features160=dict(getattr(a,'features160_stats',{}))if a else{},keep_alive=True,safe_keepalive=True,gate=True,localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v162.db'):p.error('Disposable -v162.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes162.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
