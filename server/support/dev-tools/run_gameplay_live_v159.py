"""159 backend: 158 with keep-alive made safe (a reset socket can no longer spin a worker) and a fairer stream cap.

Why: the 156 keep-alive runs the stdlib loop `while not close_connection: handle_one_request()`. The base server
(serve_local.Handler.handle_one_request) swallows ConnectionResetError/ConnectionAbortedError/BrokenPipeError and every
other exception WITHOUT setting close_connection. Under HTTP/1.0 that was harmless (the connection closed anyway), but
under HTTP/1.1 a connection that cloudflared resets mid-response ("Incoming request ended abruptly") is read again at
once, raises again, is swallowed again: the worker spins at 100% forever and never returns to the pool. 156 wedged this
way on 2026-10-30 (every worker spinning, raw 503 to everything, 132% CPU, nothing logged); 158 showed a full core busy
with 0 players within minutes of starting.
How: handle_one_request here calls the stdlib implementation directly; any exception closes the connection (counted as
keepalive_stats.closed_on_error in the capabilities) and the idle timeout is re-armed only on a healthy connection.
Also: the per-IP data stream cap (4) now needs at least two IPs with active streams. 155 meant "only under contention",
but it measured contention as the sum of active streams, which a single player's 32 prefetch lanes exceed by themselves:
28% of responses were 429 in a quiet window on 2026-10-30, each costing that player 0.75-3.75 s of waiting."""
from pathlib import Path
import sys,time,random,threading,collections,http.server
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v158 as previous
host=previous.host
install=previous.install
IDLE=previous.IDLE;WORKERS=previous.WORKERS;QUEUE=previous.QUEUE
L155=previous.previous.previous.previous;P=L155.P;SLOTS=L155.SLOTS
LOCK=threading.Lock();STATS=collections.Counter()
class Handler(previous.Handler):
 def handle_one_request(self):
  try:http.server.BaseHTTPRequestHandler.handle_one_request(self)
  except Exception as e:
   # the socket is gone or the handler failed: this connection must never be read again
   self.close_connection=True
   with LOCK:STATS['closed_on_error']+=1;STATS['closed_'+type(e).__name__]+=1
   return
  if not self.close_connection:self.connection.settimeout(IDLE)
 def _guard(self,p):
  ip=self.headers.get('Cf-Connecting-Ip')or(self.headers.get('X-Forwarded-For')or'').split(',')[0].strip()
  if not ip:return True,None
  country=(self.headers.get('Cf-Ipcountry')or'').upper();now=time.time();kind=P.classify(p)
  with P.LOCK:
   P.purge(now);P.STATS['requests']+=1;P.seen[ip]=now
   if country:P.COUNTRIES[country]+=1
   until=P.banned.get(ip)
   if until and until>now:P.STATS['banned_requests']+=1;self._reject(403,body=b'Too many requests. Try again in a few minutes.');return False,None
   allow=P.geo_allow(now)
   if allow and country and country not in allow:
    P.STATS['geo_blocked']+=1;P.STATS['geo_'+country]+=1;P.note('geo',ip,country,now);self._reject(403,body=P.GEO_PAGE,ctype='text/html; charset=utf-8');return False,None
   window,limit=P.LIMITS[kind];q=P.hits[ip,kind]
   while q and q[0]<now-window:q.popleft()
   over=len(q)>=limit;reason=kind
   # the per-IP stream cap only shares the slots between players: it needs another player with active streams
   if not over and kind=='data'and P.active.get(ip,0)>=P.DATA_PER_IP and len(P.active)>=2 and sum(P.active.values())>=max(1,SLOTS-2):over=True;reason='data_streams'
   if over:
    P.STATS['limited_'+reason]+=1
    if reason!='data_streams':
     rj=P.rejects[ip]
     while rj and rj[0]<now-60:rj.popleft()
     rj.append(now)
     if len(rj)>=L155.BAN_AFTER:P.banned[ip]=now+P.BAN_SECONDS;P.STATS['bans']+=1;rj.clear();P.note('ban',ip,country,now)
    self._reject(429,retry=P.RETRY.get(kind)or random.randint(1,3));return False,None
   q.append(now)
   if kind!='data':return True,None
   P.active[ip]=P.active.get(ip,0)+1
  def done():
   with P.LOCK:
    n=P.active.get(ip,1)-1
    if n<=0:P.active.pop(ip,None)
    else:P.active[ip]=n
  return True,done
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v159.json':
   with LOCK:st=dict(STATS)
   with P.LOCK:prot=dict(P.STATS)
   return self.json51(200,dict(backend_release='v159',base_release='v158',keep_alive=True,safe_keepalive=True,idle_timeout_s=IDLE,pool_workers=WORKERS,pool_queue=QUEUE,gate=True,keepalive_stats=st,protection_requests=prot.get('requests',0),limited_data_streams=prot.get('limited_data_streams',0),stream_cap_needs_ips=2,wasm_gzip=P.WASM_GZ.is_file(),localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  return super().do_GET()
class Server(host.StableWorkerHTTPServer):
 request_queue_size=QUEUE
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v159.db'):p.error('Disposable -v159.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes159.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();Server(('127.0.0.1',args.port),Handler,max_workers=WORKERS,pending_requests=QUEUE).serve_forever()
