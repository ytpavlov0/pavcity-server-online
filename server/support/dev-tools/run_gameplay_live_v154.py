"""154 backend: the v152 chain plus (a) the gzip engine and (b) origin-side abuse protection.

(a) /b/8b0b5899ed/game-pn-online-v117.wasm is 60.3 MB and the base server only gzips the v11-v16 engines, so every new
    visitor pulled 60 MB through the tunnel ("Motor başlatılıyor %2" for minutes). It is now served from the 18.9 MB
    game-pn-online-v117.wasm.gz when the browser accepts gzip, with X-Uncompressed-Length (the loader's progress bar
    reads it) and the same immutable cache / cross-origin headers as the raw file.
(b) The quick tunnels forward the visitor's real IP (Cf-Connecting-Ip) and country (Cf-Ipcountry). Per visitor IP:
    sliding-window limits (api 800/10 s, page assets 1500/10 s, login+register 12/60 s, game data 600/10 s), at most
    4 simultaneous game-data streams, and a 10-minute 403 after 400 rejections in a minute. Rejections are 429 with
    Retry-After (the io-worker97 client waits them out). Requests without the tunnel header (local) are not limited.
    Country allow-list: PAV154_COUNTRIES or the file backups/geo-allow154.txt (comma-separated codes, re-read every
    2 s, empty = off); other countries get a 403 page. Bans and geo blocks are appended to backups/protection154.log.
    Stats: /pn/server-capabilities-v154.json."""
from pathlib import Path
import sys,os,time,threading,collections,random
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v152 as previous
host=previous.host
install=previous.install
WASM=R/'mirror/playgta5.com/b/8b0b5899ed/game-pn-online-v117.wasm';WASM_GZ=WASM.with_suffix('.wasm.gz')
GEO_FILE=Path(os.environ.get('PAV154_GEO_FILE',str(R/'backups/geo-allow154.txt')))
PROT_LOG=Path(os.environ.get('PAV154_LOG',str(R/'backups/protection154.log')))
LIMITS={'api':(10,800),'auth':(60,12),'asset':(10,1500),'data':(10,600)}
RETRY={'api':2,'auth':30,'asset':2}
DATA_PER_IP=4;BAN_AFTER=400;BAN_SECONDS=600
LOCK=threading.Lock()
hits=collections.defaultdict(collections.deque);rejects=collections.defaultdict(collections.deque);banned={};active={};seen={};noted={}
STATS=collections.Counter();COUNTRIES=collections.Counter();PURGE={'at':0.0}
geo={'allow':frozenset(c.strip().upper()for c in os.environ.get('PAV154_COUNTRIES','').split(',')if c.strip()),'mtime':None,'checked':0.0}
GEO_PAGE=('<!doctype html><html lang="tr"><meta charset="utf-8"><title>PAVCITY</title><body style="margin:0;display:grid;place-items:center;min-height:100vh;background:#0e0916;color:#f6f1ff;font:600 16px/1.5 Segoe UI,system-ui,sans-serif;text-align:center"><div style="padding:24px"><h1 style="font-size:28px;margin:0 0 10px">PAVCITY</h1><p>Bu sunucu şu an bulunduğun ülkeden erişime kapalı.</p><p style="color:#a99bc0;font-weight:500">This server is not open from your country right now.</p></div></html>').encode()
def classify(p):
 if p.startswith(('/pn/model-data-v98/','/pn/story-data-v98/')):return'data'
 if p in('/api/auth/login','/api/auth/register'):return'auth'
 if p.startswith('/api/')or p in('/log','/mobile-diagnostics'):return'api'
 return'asset'
def geo_allow(now):
 if now-geo['checked']<2:return geo['allow']
 geo['checked']=now
 try:
  st=GEO_FILE.stat().st_mtime
  if st!=geo['mtime']:geo['mtime']=st;geo['allow']=frozenset(c.strip().upper()for c in GEO_FILE.read_text(encoding='utf8').replace('\n',',').replace(';',',').split(',')if c.strip())
 except FileNotFoundError:
  if geo['mtime']is not None:geo['mtime']=None;geo['allow']=frozenset()
 return geo['allow']
def note(kind,ip,country,now):
 """One line per ip and kind per minute, so a flood cannot grow the log."""
 k=(kind,ip)
 if now-noted.get(k,0)<60:return
 noted[k]=now
 try:
  with PROT_LOG.open('a',encoding='utf8')as f:f.write('%s %s %s %s\n'%(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(now)),kind,ip,country or'-'))
 except OSError:pass
def purge(now):
 if now-PURGE['at']<30:return
 PURGE['at']=now
 for ip,t in list(seen.items()):
  if t<now-180:seen.pop(ip,None)
 for key in list(hits):
  q=hits[key];w=LIMITS[key[1]][0]
  while q and q[0]<now-w:q.popleft()
  if not q:del hits[key]
 for ip in list(rejects):
  q=rejects[ip]
  while q and q[0]<now-60:q.popleft()
  if not q:del rejects[ip]
 for ip,t in list(banned.items()):
  if t<now:del banned[ip]
 for k,t in list(noted.items()):
  if t<now-120:del noted[k]
class Handler(previous.Handler):
 def _reject(self,code,retry=None,body=b'',ctype='text/plain; charset=utf-8'):
  self.close_connection=True;self.send_response(code)
  if retry:self.send_header('Retry-After',str(retry))
  self.send_header('Content-Type',ctype);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers()
  if body and self.command!='HEAD':self.wfile.write(body)
 def _guard(self,p):
  """(True, cleanup-or-None) when the request may proceed; (False, None) after a rejection was sent."""
  ip=self.headers.get('Cf-Connecting-Ip')or(self.headers.get('X-Forwarded-For')or'').split(',')[0].strip()
  if not ip:return True,None
  country=(self.headers.get('Cf-Ipcountry')or'').upper();now=time.time();kind=classify(p)
  with LOCK:
   purge(now);STATS['requests']+=1;seen[ip]=now
   if country:COUNTRIES[country]+=1
   until=banned.get(ip)
   if until and until>now:STATS['banned_requests']+=1;self._reject(403,body=b'Too many requests. Try again in a few minutes.');return False,None
   allow=geo_allow(now)
   if allow and country and country not in allow:
    STATS['geo_blocked']+=1;STATS['geo_'+country]+=1;note('geo',ip,country,now);self._reject(403,body=GEO_PAGE,ctype='text/html; charset=utf-8');return False,None
   window,limit=LIMITS[kind];q=hits[ip,kind]
   while q and q[0]<now-window:q.popleft()
   over=len(q)>=limit;reason=kind
   if not over and kind=='data'and active.get(ip,0)>=DATA_PER_IP:over=True;reason='data_streams'
   if over:
    rj=rejects[ip]
    while rj and rj[0]<now-60:rj.popleft()
    rj.append(now);STATS['limited_'+reason]+=1
    if len(rj)>=BAN_AFTER:banned[ip]=now+BAN_SECONDS;STATS['bans']+=1;rj.clear();note('ban',ip,country,now)
    self._reject(429,retry=RETRY.get(kind)or random.randint(1,3));return False,None
   q.append(now)
   if kind!='data':return True,None
   active[ip]=active.get(ip,0)+1
  def done():
   with LOCK:
    n=active.get(ip,1)-1
    if n<=0:active.pop(ip,None)
    else:active[ip]=n
  return True,done
 def _wasm_gz(self):
  if'gzip'not in(self.headers.get('Accept-Encoding')or'').lower()or not WASM_GZ.is_file():return False
  gz=WASM_GZ.stat();raw=WASM.stat()
  self.send_response(200)
  # The base handler's end_headers adds Cache-Control (immutable for /b/ files) and the Cross-Origin-* headers itself.
  for k,v in[('Content-Type','application/wasm'),('Content-Encoding','gzip'),('Vary','Accept-Encoding'),('Content-Length',str(gz.st_size)),('X-Uncompressed-Length',str(raw.st_size)),('Last-Modified',self.date_time_string(raw.st_mtime))]:self.send_header(k,v)
  self.end_headers()
  if self.command!='HEAD':
   with WASM_GZ.open('rb')as f:
    while True:
     b=f.read(1048576)
     if not b:break
     self.wfile.write(b)
  with LOCK:STATS['wasm_gzip']+=1
  return True
 def _dispatch(self,method):
  p=urlsplit(self.path).path
  ok,done=self._guard(p)
  if not ok:return
  try:
   if p==('/b/8b0b5899ed/'+WASM.name)and self._wasm_gz():return
   return method()
  finally:
   if done:done()
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v154.json':
   now=time.time()
   with LOCK:
    prot=dict(STATS);prot.update(unique_ips_3min=len(seen),active_data_ips=len(active),banned_now=sum(1 for t in banned.values()if t>now),countries=dict(COUNTRIES.most_common(15)),geo_allow=sorted(geo_allow(now)),limits={k:dict(window_s=w,max=m)for k,(w,m)in LIMITS.items()},data_streams_per_ip=DATA_PER_IP,ban_after=BAN_AFTER,ban_seconds=BAN_SECONDS)
   return self.json51(200,dict(backend_release='v154',base_release='v152',wasm_gzip=WASM_GZ.is_file(),protection=prot,pool_workers=192,data_slots=previous.SLOTS,data_stats=dict(previous.STATS),localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  return self._dispatch(super().do_GET)
 def do_HEAD(self):return self._dispatch(super().do_HEAD)
 def do_POST(self):return self._dispatch(super().do_POST)
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v154.db'):p.error('Disposable -v154.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes154.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();host.StableWorkerHTTPServer(('127.0.0.1',args.port),Handler,max_workers=192,pending_requests=512).serve_forever()
