"""167 backend: 164 (request accounting) + features167 (no rewrite of unchanged vehicle state; vehicle cell list kept
1 s). The 166 stack sampler is not carried over."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v164 as previous
host=previous.host;API=previous.API
def install():
 from features167 import install as features167
 API[0]=features167(previous.install());return API[0]
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v167.json':
   a=API[0];import features160
   with previous.ACC_LOCK:last=previous.table(previous.WIN['last'],previous.WIN['last_span'])
   return self.json51(200,dict(backend_release='v167',base_release='v164',rows_ttl=features160.ROWS_TTL,persist167=dict(getattr(a,'features167_stats',{}))if a else{},sync_cpu163=dict(getattr(a,'features163_stats',{}))if a else{},traffic_eviction=dict(getattr(a,'features162_stats',{}))if a else{},last_minute=last,boot_packs=True,keep_alive=True,gate=True,localhost_only=True,sync_one_connection=True))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v167.db'):p.error('Disposable -v167.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes167.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
