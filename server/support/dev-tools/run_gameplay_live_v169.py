"""169 backend: 168 + switchable inclusive stack sampler for /api/gta/sync (diagnosis without restarts). While the file
backups/sampler169.on exists, a daemon thread samples sys._current_frames() at 10 Hz and, for every thread whose stack
contains session_api.dispatch, counts each project function on the stack once (inclusive time share) plus the innermost
project function (self share). /pn/server-capabilities-v169.json shows the last full window and the running one.
Without the flag file the thread only checks for it once a second. No request or response changes."""
from pathlib import Path
import sys,threading,time,collections
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v168 as previous
host=previous.host;API=previous.API;install=previous.install
FLAG=R/'backups/sampler169.on';INTERVAL=0.1;WLOCK=threading.Lock();W={'start':time.time(),'cur':None,'last':None}
def fresh():return{'ticks':0,'threads':0,'incl':collections.Counter(),'self':collections.Counter()}
W['cur']=fresh()
def name(c):return c.co_filename.replace('\\','/').split('/')[-1]+':'+c.co_name
def sampler():
 me=threading.get_ident()
 while True:
  if not FLAG.exists():time.sleep(1);continue
  time.sleep(INTERVAL)
  try:
   frames=sys._current_frames();now=time.time();rows=[]
   for tid,f in frames.items():
    if tid==me:continue
    codes=[];hit=False;depth=0
    while f is not None and depth<120:
     c=f.f_code;codes.append(c);depth+=1
     if c.co_name=='dispatch'and c.co_filename.endswith('session_api.py'):hit=True
     f=f.f_back
    if not hit:continue
    proj=[name(c)for c in codes if 'gta5' in c.co_filename.replace('\\','/')]
    rows.append((set(proj),name(codes[0])))
   with WLOCK:
    if now-W['start']>=60:W['last']=W['cur'];W['cur']=fresh();W['start']=now
    w=W['cur'];w['ticks']+=1
    for incl,leaf in rows:
     w['threads']+=1;w['self'][leaf]+=1
     for n in incl:w['incl'][n]+=1
  except Exception:pass
threading.Thread(target=sampler,name='pav-sampler169',daemon=True).start()
def view(w):
 if not w or not w['ticks']:return None
 t=w['ticks']
 return{'ticks':t,'avg_threads_in_dispatch':round(w['threads']/t,2),'inclusive_pct':[[k,round(v/t*100,1)]for k,v in w['incl'].most_common(60)],'self_pct':[[k,round(v/t*100,1)]for k,v in w['self'].most_common(30)]}
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v169.json':
   with WLOCK:last=view(W['last']);cur=view(W['cur'])
   return self.json51(200,dict(backend_release='v169',base_release='v168',sampler_on=FLAG.exists(),interval_s=INTERVAL,last_window=last,this_window=cur))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v169.db'):p.error('Disposable -v169.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes169.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
