"""164 backend: 163 + request accounting (diagnosis of the remaining lock waits, 31 Oct). Every handled request adds its
wall time and its own thread CPU time (time.thread_time) to a per-category bucket (API path, or model-data / story-data /
other static); /pn/server-capabilities-v164.json shows the buckets of the last full minute and the running minute, and
the Python switch interval. No request or response changes."""
from pathlib import Path
import sys,time,threading,re
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v163 as previous
host=previous.host
API=previous.API
install=previous.install
ACC_LOCK=threading.Lock();WIN={'start':time.time(),'cur':{},'last':{},'last_span':0}
def category(path):
 p=urlsplit(path or '').path
 if p.startswith('/pn/model-data-v98/'):return 'model-data'
 if p.startswith('/pn/story-data'):return 'story-data'
 if p.startswith('/api/'):return re.sub(r'\d+','N',p)
 return 'static'
def note(cat,wall,cpu):
 now=time.time()
 with ACC_LOCK:
  if now-WIN['start']>=60:WIN['last']=WIN['cur'];WIN['last_span']=now-WIN['start'];WIN['cur']={};WIN['start']=now
  b=WIN['cur'].setdefault(cat,[0,0.,0.,0.]);b[0]+=1;b[1]+=wall;b[2]+=cpu;b[3]=max(b[3],wall)
def table(d,span):
 return sorted(({'cat':k,'n':v[0],'per_s':round(v[0]/max(span,1),1),'wall_ms_avg':round(v[1]/v[0]*1000,1),'cpu_ms_avg':round(v[2]/v[0]*1000,2),'cpu_ms_per_s':round(v[2]*1000/max(span,1),1),'wall_ms_max':round(v[3]*1000)}for k,v in d.items()),key=lambda r:-r['cpu_ms_per_s'])
class Handler(previous.Handler):
 def timed(self,fn):
  t0=time.perf_counter();c0=time.thread_time()
  try:return fn()
  finally:
   try:note(category(self.path),time.perf_counter()-t0,time.thread_time()-c0)
   except Exception:pass
 def do_POST(self):return self.timed(super().do_POST)
 def do_HEAD(self):return self.timed(super().do_HEAD)
 def do_GET(self):return self.timed(self.get164)
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v164.json':
   a=API[0]
   with ACC_LOCK:last=table(WIN['last'],WIN['last_span']);cur=table(WIN['cur'],time.time()-WIN['start'])
   return self.json51(200,dict(backend_release='v164',base_release='v163',switch_interval=sys.getswitchinterval(),threads=threading.active_count(),last_minute=last,this_minute=cur,sync_cpu163=dict(getattr(a,'features163_stats',{}))if a else{},traffic_eviction=dict(getattr(a,'features162_stats',{}))if a else{},boot_packs=True,keep_alive=True,safe_keepalive=True,gate=True,localhost_only=True,sync_one_connection=True))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v164.db'):p.error('Disposable -v164.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes164.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
