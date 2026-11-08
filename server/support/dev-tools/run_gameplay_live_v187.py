"""187 backend: 186 + scale for 60-100+ players.
- ambient187: the shared NPC tick tests only nearby obstacles (16 m grid) instead of every player and vehicle in the
  city; same results. It was ~60 ms per 80 ms tick at 60 players under the global lock.
- db187: identical SELECTs are answered from memory (up to 30 s); a write that changes a table drops its table's entries at once (see
  db187.py). The file backups/db187.off at start turns it off.
- sync answers carry the 20 nearest players (all the client draws), leave out the appearance of players the client
  says it already has (appearance_known189: ["char_id:version"]), and add sync_hint189 (longer HTTP sync interval
  in a busy city; older pages ignore it).
- /pn/server-capabilities-v187.json: tick timing (count, avg/max ms over the last minute), cache counters."""
from pathlib import Path
import sys,time,threading
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v186 as previous
import ambient187,db187
host=previous.host;API=previous.API
DB_OFF=R/'backups/db187.off'  # present at start: no SELECT cache
STATS={'post_root_redirects':0,'gate_wait_max_ms':0.0,'cached_paths':0,'peers_trimmed':0,'appearance_omitted':0,'wrap_errors':0,'ambient187':False,'tick_n':0,'tick_ms_sum':0.0,'tick_ms_max':0.0,'window_start':time.time(),'last':None}
SLOCK=threading.Lock()
def _timed(api):
 fn=ambient187.find()
 if fn is None:return
 i=fn.__code__.co_freevars.index('tick');inner=fn.__closure__[i].cell_contents
 if getattr(inner,'timed187',False):return
 def tick(now):
  t=time.perf_counter();inner(now);ms=(time.perf_counter()-t)*1000
  if ms<.05:return
  with SLOCK:
   if time.time()-STATS['window_start']>=60:
    STATS['last']=dict(n=STATS['tick_n'],avg_ms=round(STATS['tick_ms_sum']/max(1,STATS['tick_n']),2),max_ms=round(STATS['tick_ms_max'],2))
    STATS.update(tick_n=0,tick_ms_sum=0.0,tick_ms_max=0.0,window_start=time.time())
   STATS['tick_n']+=1;STATS['tick_ms_sum']+=ms;STATS['tick_ms_max']=max(STATS['tick_ms_max'],ms)
 tick.timed187=True;tick.ambient187=getattr(inner,'ambient187',False);fn.__closure__[i].cell_contents=tick
def install():
 api=previous.install()
 if getattr(api,'v187_installed',False):return api
 STATS['ambient187']=ambient187.install(api);_timed(api)
 if not DB_OFF.exists():db187.install(host.online_engine)
 # v172/v176 check backups/rt172.off and read backups/rt172.secret on every sync (4 stats + 1 read): 1 s cache
 for name in('run_gameplay_live_v172','run_gameplay_live_v176'):
  m=sys.modules.get(name)
  for attr in('SECRET','OFF'):
   p=getattr(m,attr,None)if m else None
   if isinstance(p,Path)and not isinstance(p,CPath):setattr(m,attr,CPath(str(p)));STATS['cached_paths']+=1
 old=api.dispatch;owned=getattr(api.LOCK,'_is_owned',lambda:False)
 def dispatch(path,*a,**k):
  # never wait for the gate while this thread already holds the game lock (nested dispatch): no lock-order inversion
  if GATE is None or path not in GATED or owned():out=old(path,*a,**k)
  else:
   t=time.perf_counter()
   with GATE:
    w=time.perf_counter()-t
    if w>STATS['gate_wait_max_ms']/1000:STATS['gate_wait_max_ms']=round(w*1000,1)
    out=old(path,*a,**k)
  if path!='/api/gta/sync':return out
  try:
   result=out[0];payload=a[0]if a else{}
   if not(isinstance(result,dict)and result.get('success')and isinstance(result.get('players'),list)):return out
   players=result['players'];n=int(result.get('player_count')or len(players))
   # the client draws the 20 nearest (players[0] is the caller, the rest sorted by distance)
   if len(players)>PEERS+1:players=players[:PEERS+1];STATS['peers_trimmed']+=1
   known=payload.get('appearance_known189')if isinstance(payload,dict)else None
   if isinstance(known,list)and len(known)<=64:
    known={x for x in known if isinstance(x,str)and len(x)<=24}
    slim=[]
    for i,p in enumerate(players):
     if i and isinstance(p,dict)and 'appearance'in p and '%s:%s'%(p.get('char_id'),p.get('appearance_version'))in known:
      p=dict(p);p.pop('appearance');STATS['appearance_omitted']+=1
     slim.append(p)
    players=slim
   out=(dict(result,players=players,sync_hint189=hint(n)),)+tuple(out[1:])
  except Exception:STATS['wrap_errors']+=1
  return out
 api.dispatch=dispatch
 api.v187_installed=True;API[0]=api;return api
PEERS=20
# One at a time through the frequent polling calls. They all take api.LOCK anyway, but 60-100 threads queueing on it
# and waking for every SQLite call doubled the CPU per sync (31 ms instead of ~16) and made the lock convoy: at 60
# players the gate cut the sync wait from ~1.7 s to ~0.1 s. Logins and everything else stay outside the gate.
# backups/gate187.off at start disables it.
GATED=frozenset(('/api/gta/sync','/api/gta/voice/poll','/api/gta/presence','/api/phone/status','/api/jobs/status','/api/status'))
GATE=None if(R/'backups/gate187.off').exists()else threading.RLock()
class CPath(type(Path())):
 """exists()/read_text() remembered for 1 s (kill switch and secret files; a change applies within a second)."""
 _memo={};_mlock=threading.Lock()
 def _get(self,key,fn):
  now=time.monotonic()
  with CPath._mlock:
   hit=CPath._memo.get(key)
   if hit and now-hit[0]<1.0:return hit[1]
  v=fn()
  with CPath._mlock:CPath._memo[key]=(now,v)
  return v
 def exists(self,*a,**k):return self._get(('e',str(self)),lambda:Path(str(self)).exists())
 def read_text(self,*a,**k):return self._get(('r',str(self),a,tuple(sorted(k.items()))),lambda:Path(str(self)).read_text(*a,**k))
def hint(n):
 """Busier city, fewer HTTP syncs: positions, voice and cars ride the realtime relay; the sync carries health, seats,
 chat and hits. idle: normal interval, hit: interval while hits wait for the server."""
 if n<40:return dict(idle_ms=1000,hit_ms=100)
 if n<70:return dict(idle_ms=1400,hit_ms=150)
 if n<100:return dict(idle_ms=1800,hit_ms=200)
 return dict(idle_ms=2200,hit_ms=250)
class Handler(previous.Handler):
 def do_POST(self):
  # Cloudflare's "security check" page re-sends the original request as a POST once solved; the page itself only
  # answers GET, so players saw "404 Nothing matches the given URI". Send them to the same address with a GET.
  if urlsplit(self.path).path in('/','/index.html'):
   try:n=min(int(self.headers.get('Content-Length')or 0),1<<20)
   except ValueError:n=0
   if n:self.rfile.read(n)
   STATS['post_root_redirects']+=1
   self.send_response(303);self.send_header('Location',self.path);self.send_header('Content-Length','0');self.send_header('Connection','close');self.end_headers();self.close_connection=True
   return
  return super().do_POST()
 def log_request(self,code='-',size='-'):
  # one stderr line per request grew backups/detached-server.log to 1.7 GB and cost ~3 % CPU: successful polling
  # calls are not logged any more; errors and everything else are
  try:
   if int(code)<400 and urlsplit(self.path).path in GATED:return
  except(TypeError,ValueError):pass
  return super().log_request(code,size)
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v187.json':
   with SLOCK:cur=dict(n=STATS['tick_n'],avg_ms=round(STATS['tick_ms_sum']/max(1,STATS['tick_n']),2),max_ms=round(STATS['tick_ms_max'],2));last=STATS['last']
   return self.json51(200,dict(backend_release='v187',base_release='v186',ambient187=STATS['ambient187'],tick_this_window=cur,tick_last_minute=last,db187=dict(db187.STATS,on=bool(getattr(host.online_engine,'db187',False)),entries=len(db187._CACHE)),v186=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v187.db'):p.error('Disposable -v187.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes187.jsonl'
 elif not args.live:p.error('Fixture DB required')
 # the same Server class v186 starts (v158's)
 pp=previous.previous
 for _ in range(25):pp=pp.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
