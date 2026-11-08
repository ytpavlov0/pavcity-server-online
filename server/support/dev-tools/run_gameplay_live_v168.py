"""168 backend: 167 + edge-cacheable scripts and styles. The base server sent `no-cache, no-store` for every .js/.css, so
Cloudflare passed each one through (cf-cache-status BYPASS): every player join fetched the engine glue
(game-pn-online-v15-gameplay-v117.js, 126 KB) and crash-worker.js once per engine thread, plus ~120 UI files = ~33
requests/s and ~20 % of the server's Python time on 31 Oct. Successful GET/HEAD answers for .js/.css under /pn/ and /b/
now carry `public, max-age=300` (5 min; releases use new file names or ?build= hashes, an in-place edit reaches players
within 5 min). The page itself (/ and /index.html), JSON and API answers are unchanged (no-store)."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v167 as previous
host=previous.host;API=previous.API;install=previous.install
EDGE='public, max-age=300';STATS={'edge_cacheable':0}
def cacheable(path):
 p=urlsplit(path or '').path
 return p.startswith(('/pn/','/b/'))and p.endswith(('.js','.css'))
class Handler(previous.Handler):
 def send_response(self,code,message=None):
  self._code168=code;return super().send_response(code,message)
 def send_header(self,keyword,value):
  if keyword in('Cache-Control','Pragma','Expires')and getattr(self,'_code168',0)in(200,304)and self.command in('GET','HEAD')and cacheable(self.path):
   if keyword!='Cache-Control':return
   if str(value).startswith('no-cache, no-store'):STATS['edge_cacheable']+=1;value=EDGE
  return super().send_header(keyword,value)
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v168.json':
   a=API[0];import features160
   with previous.previous.ACC_LOCK:last=previous.previous.table(previous.previous.WIN['last'],previous.previous.WIN['last_span'])
   return self.json51(200,dict(backend_release='v168',base_release='v167',edge_cache=dict(STATS,cache_control=EDGE),rows_ttl=features160.ROWS_TTL,persist167=dict(getattr(a,'features167_stats',{}))if a else{},sync_cpu163=dict(getattr(a,'features163_stats',{}))if a else{},traffic_eviction=dict(getattr(a,'features162_stats',{}))if a else{},last_minute=last,boot_packs=True,keep_alive=True,gate=True,localhost_only=True,sync_one_connection=True))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v168.db'):p.error('Disposable -v168.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes168.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
