"""157 backend: 156 + an origin-side "under attack" gate (a one-second browser check), automatic.

The quick tunnels carry anything to the origin and offer no edge rules, so the origin filters floods itself: while the
gate is active, a visitor without a valid pav_gate cookie gets a tiny page that sets the cookie with JavaScript and
reloads; every other request without the cookie (API, assets, data) is refused with a tiny 403. Real browsers pass in
about a second and never see it again for 24 h; flood tools that do not run JavaScript never reach anything heavy.
The cookie is an HMAC of the visitor's IP (Cf-Connecting-Ip) and the day, keyed with a secret kept in
backups/gate157-secret.txt (so a restart does not re-challenge everyone). Requests without the tunnel header (local)
are never gated. Mode file backups/gate157.txt: "on", "off" or "auto" (default, re-read every 2 s). In auto mode the
gate switches on when the origin sees more than PAV157_AUTO_RPS (300) requests/s over 10 s and stays on for 10 min
after the rate last exceeded it. Stats: /pn/server-capabilities-v157.json."""
from pathlib import Path
import sys,os,time,hmac,hashlib,secrets,threading,collections
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v156 as previous
host=previous.host
install=previous.install
P=previous.previous.P
SECRET_FILE=Path(os.environ.get('PAV157_SECRET_FILE',str(R/'backups/gate157-secret.txt')))
MODE_FILE=Path(os.environ.get('PAV157_GATE_FILE',str(R/'backups/gate157.txt')))
AUTO_RPS=max(1,int(os.environ.get('PAV157_AUTO_RPS','300')));HOLD=int(os.environ.get('PAV157_HOLD','600'));WINDOW=10
def load_secret():
 try:s=SECRET_FILE.read_text(encoding='utf8').strip()
 except FileNotFoundError:s=''
 if len(s)<32:
  s=secrets.token_hex(32);SECRET_FILE.parent.mkdir(parents=True,exist_ok=True);SECRET_FILE.write_text(s,encoding='utf8')
 return s.encode()
SECRET=load_secret()
LOCK=threading.Lock();ticks=collections.deque();gate={'mode':'auto','mtime':None,'checked':0.0,'until':0.0,'rps':0.0}
STATS=collections.Counter()
def mode(now):
 if now-gate['checked']<2:return gate['mode']
 gate['checked']=now
 try:
  st=MODE_FILE.stat().st_mtime
  if st!=gate['mtime']:gate['mtime']=st;m=MODE_FILE.read_text(encoding='utf8').strip().lower();gate['mode']=m if m in('on','off','auto')else'auto'
 except FileNotFoundError:
  if gate['mtime']is not None or gate['mode']not in('on','off','auto'):gate['mtime']=None;gate['mode']='auto'
 return gate['mode']
def token(ip,day):return'%d.%s'%(day,hmac.new(SECRET,('%s|%d'%(ip,day)).encode(),hashlib.sha256).hexdigest()[:24])
def valid(cookie,ip,now):
 if not cookie:return False
 for part in cookie.split(';'):
  k,_,v=part.strip().partition('=')
  if k!='pav_gate':continue
  day,_,sig=v.partition('.')
  if not day.isdigit():return False
  d=int(day);today=int(now//86400)
  return d in(today,today-1)and hmac.compare_digest(token(ip,d),v)
 return False
def active(now):
 m=mode(now)
 if m=='on':return True
 if m=='off':return False
 return now<gate['until']
PAGE=('<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PAVCITY</title>'
 '<style>body{margin:0;display:grid;place-items:center;min-height:100vh;background:#0e0916;color:#f6f1ff;font:600 16px/1.5 Segoe UI,system-ui,sans-serif;text-align:center}div{padding:24px}h1{font-size:26px;margin:0 0 8px}p{margin:4px 0;color:#c9bfe0}i{display:inline-block;width:18px;height:18px;border:3px solid #ff5fa8;border-right-color:transparent;border-radius:50%;animation:s .8s linear infinite;vertical-align:middle;margin-right:8px}@keyframes s{to{transform:rotate(360deg)}}</style></head>'
 '<body><div><h1>PAVCITY</h1><p><i></i>Bağlantı doğrulanıyor…</p><p id="n" hidden>Çerezler kapalı görünüyor. Tarayıcında çerezlere izin verip sayfayı yenile.</p><noscript><p>Oyun için JavaScript gerekli. Tarayıcında JavaScript\'i aç ve sayfayı yenile.</p></noscript></div>'
 '<script>(function(){try{var k="pav_gate157",n=+(sessionStorage.getItem(k)||0);if(n>=3){document.getElementById("n").hidden=false;return}sessionStorage.setItem(k,n+1)}catch(e){}'
 'document.cookie="pav_gate=%TOKEN%; Path=/; Max-Age=86400; SameSite=Lax%SECURE%";setTimeout(function(){location.replace(location.href)},150)})()</script></body></html>')
class Handler(previous.Handler):
 def _gate(self,p):
  """True when the request may continue; False after the challenge or a 403 was sent."""
  ip=self.headers.get('Cf-Connecting-Ip')or(self.headers.get('X-Forwarded-For')or'').split(',')[0].strip()
  if not ip:return True
  now=time.time()
  with LOCK:
   ticks.append(now)
   while ticks and ticks[0]<now-WINDOW:ticks.popleft()
   rps=len(ticks)/WINDOW;gate['rps']=rps
   if rps>AUTO_RPS:
    if now>=gate['until']:STATS['auto_activations']+=1
    gate['until']=now+HOLD
   on=active(now)
  if not on:return True
  if valid(self.headers.get('Cookie'),ip,now):return True
  accept=self.headers.get('Accept')or''
  if p=='/'or p.endswith('.html')or('text/html'in accept and not p.startswith('/api/')):
   secure='; Secure'if(self.headers.get('X-Forwarded-Proto')or'').lower()=='https'or(self.headers.get('Cf-Visitor')or'').find('https')>=0 else''
   body=PAGE.replace('%TOKEN%',token(ip,int(now//86400))).replace('%SECURE%',secure).encode('utf8')
   with LOCK:STATS['challenges']+=1
   self.close_connection=True;self.send_response(200)
   # the base end_headers adds its own no-store Cache-Control for the page
   for k,v in[('Content-Type','text/html; charset=utf-8'),('Content-Length',str(len(body)))]:self.send_header(k,v)
   self.end_headers()
   if self.command!='HEAD':self.wfile.write(body)
   return False
  with LOCK:STATS['blocked']+=1
  self._reject(403,body=b'gate')
  return False
 def _dispatch(self,method):
  if not self._gate(urlsplit(self.path).path):return
  return super()._dispatch(method)
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v157.json':
   now=time.time()
   with LOCK:g=dict(mode=mode(now),active=active(now),rps=round(gate['rps'],1),auto_rps=AUTO_RPS,hold_s=HOLD,until_in_s=max(0,int(gate['until']-now)),**STATS)
   return self.json51(200,dict(backend_release='v157',base_release='v156',gate=g,keep_alive=True,wasm_gzip=P.WASM_GZ.is_file(),localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v157.db'):p.error('Disposable -v157.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes157.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();previous.Server(('127.0.0.1',args.port),Handler,max_workers=previous.WORKERS,pending_requests=previous.QUEUE).serve_forever()
