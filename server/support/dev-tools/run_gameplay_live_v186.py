"""186 backend: 185 + disconnects and a cheaper database.
- A player whose last sync is more than 2.5 s old (net drop, PC or browser closed) takes no hits: hits aimed at them
  are dropped from the attacker's sync. They still disappear for everyone 10 s after their last sync (as before).
- New SQLite connections use synchronous=NORMAL (WAL keeps it crash-safe; fewer disk flushes per sync)."""
from pathlib import Path
import sys,time
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v185 as previous
host=previous.host;API=previous.API
STATS={'hits_dropped':0,'seats_released':0,'normal_conns':0}
GRACE=2.5;SEAT_AFTER=15.0;STATE={'swept':0.0}
def _normal():
 eng=host.online_engine
 if getattr(eng,'normal186',False):return
 orig=eng.get_db
 def get_db(*a,**k):
  c=orig(*a,**k)
  try:c.execute('PRAGMA synchronous=NORMAL');STATS['normal_conns']+=1
  except Exception:pass
  return c
 eng.get_db=get_db;eng.normal186=True
def install():
 _normal()
 api=previous.install()
 if getattr(api,'v186_installed',False):return api
 w=api.world
 def last_seen_of(cid):
  best=None
  for s in list(api.GTA_STATE.values()):
   if s.get('char_id')==cid:best=max(best or 0.0,float(s.get('last_seen',0)or 0))
  return best
 def sweep(now):
  if now-STATE['swept']<2:return
  STATE['swept']=now
  for(vid,seat),info in list(w.SEATS.items()):
   cid=(info or{}).get('char_id')
   if cid and now-last_seen_of(cid)>SEAT_AFTER and now-float((info or{}).get('time',0)or 0)>SEAT_AFTER:
    try:w.release(cid);STATS['seats_released']+=1
    except Exception:pass
 old=api.dispatch
 def dispatch(path,*a,**k):
  if path=='/api/gta/sync'and a and isinstance(a[0],dict):
   payload=a[0];now=time.time()
   hits=payload.get('hits')
   if isinstance(hits,list)and hits:
    keep=[]
    for h in hits:
     try:t=int(h.get('target',0))
     except Exception:t=0
     ls=last_seen_of(t)if t else None
     if ls is not None and now-ls>GRACE:STATS['hits_dropped']+=1;continue
     keep.append(h)
    if len(keep)!=len(hits):a=(dict(payload,hits=keep),)+tuple(a[1:])
  return old(path,*a,**k)
 api.dispatch=dispatch;api.v186_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v186.json':
   return self.json51(200,dict(backend_release='v186',base_release='v185',v186=STATS,v185=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v186.db'):p.error('Disposable -v186.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes186.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
