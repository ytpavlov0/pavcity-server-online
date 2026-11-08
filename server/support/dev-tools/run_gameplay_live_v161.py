"""161 backend: 160 + static boot packs and batch copies (build_packs161.py output under backups/models98).

GET /pn/model-data-v98/packs.json, /pn/model-data-v98/packs/<name>.bin and /pn/model-data-v98/batchc/<sha1>.bin are served
from backups/models98/{packs,batchc} as whole files: application/octet-stream, Content-Length, strong ETag, and
Cache-Control public/immutable for the content-named .bin files (packs.json 300 s). batchc files are raw gzip that the
io-worker inflates itself, so NO Content-Encoding header. They count as data streams for the 151 limiter like every
other model-data request. An unknown name is a 404 (the client then falls back to ranges / the POST batch)."""
from pathlib import Path
import sys,re,os
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v160 as previous
host=previous.host
install=previous.install
PACKS=Path(os.environ.get('PAV161_PACKS',str(R/'backups/models98')))
PREFIX='/pn/model-data-v98/'
NAME=re.compile(r'^(packs/p\d{3}-[0-9a-f]{12}\.bin|batchc/[0-9a-f]{40}\.bin|packs\.json)$')
STATS={'packs':0,'batchc':0,'index':0,'missing':0}
class Handler(previous.Handler):
 def static161(self,p,head=False):
  rel=p[len(PREFIX):]
  if not NAME.match(rel):return False
  f=PACKS/('packs/packs.json'if rel=='packs.json'else rel)
  if not f.is_file():
   STATS['missing']+=1;self.close_connection=True;self.send_response(404);self.send_header('Content-Length','0');self.send_header('Cache-Control','no-store');self.end_headers();return True
  st=f.stat();kind='index'if rel=='packs.json'else rel.split('/')[0];STATS[kind]+=1
  self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8'if kind=='index'else'application/octet-stream');self.send_header('Content-Length',str(st.st_size))
  self.send_header('ETag','"%x-%x"'%(int(st.st_mtime),st.st_size))
  # the base end_headers adds Cache-Control only for known game extensions; these names carry their content hash
  self.send_header('Cache-Control','public, max-age=300'if kind=='index'else'public, max-age=31536000, immutable')
  self.end_headers()
  if not head:
   with f.open('rb')as fh:
    while True:
     chunk=fh.read(1048576)
     if not chunk:break
     self.wfile.write(chunk)
  return True
 def do_GET(self):
  p=urlsplit(self.path).path
  if p=='/pn/server-capabilities-v161.json':
   st=dict(getattr(previous.API[0],'features160_stats',{}))if previous.API[0]else{}
   return self.json51(200,dict(backend_release='v161',base_release='v160',boot_packs=dict(STATS,available=(PACKS/'packs/packs.json').is_file()),features160=st,keep_alive=True,safe_keepalive=True,gate=True,wasm_gzip=previous.previous.P.WASM_GZ.is_file(),localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  if p.startswith(PREFIX)and self._limited(lambda:self.static161(p)):return
  return super().do_GET()
 def do_HEAD(self):
  p=urlsplit(self.path).path
  if p.startswith(PREFIX)and self.static161(p,True):return
  return super().do_HEAD()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v161.db'):p.error('Disposable -v161.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes161.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();previous.previous.Server(('127.0.0.1',args.port),Handler,max_workers=previous.previous.WORKERS,pending_requests=previous.previous.QUEUE).serve_forever()
