"""171 backend: 170 + maintenance mode.

While backups/maintenance171.json exists with "enabled": true, every request that arrives through Cloudflare (it carries
Cf-Connecting-Ip) gets the maintenance page (HTML, countdown to "until") or, for /api/* and POSTs, a 503 JSON
"bakımda" answer. Still served for everyone: /pn/maintenance-status171.json (the page polls it and reloads when the
server reopens) and the immutable game data under /pn/model-data-v98/ and /pn/story-data-v98/ (cache pre-warming).
Direct local requests (no Cf-Connecting-Ip) are never blocked. A browser that once opened /?bakim=<bypass> gets the
cookie pav_bakim=<bypass> and plays normally (owner testing). The file is re-read at most every 2 s."""
from pathlib import Path
import sys,json,time,threading
from urllib.parse import urlsplit,parse_qs
from http.cookies import SimpleCookie
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v170 as previous
host=previous.host;API=previous.API;install=previous.install
CONF=R/'backups/maintenance171.json';PAGE=R/'support/dev-tools/maintenance171.html'
STATE={'at':0.0,'mtime':None,'conf':None};LOCK=threading.Lock();STATS={'pages':0,'api':0,'bypass':0}
def conf():
 now=time.time()
 with LOCK:
  if now-STATE['at']<2:return STATE['conf']
  STATE['at']=now
  try:
   m=CONF.stat().st_mtime
   if m!=STATE['mtime']:
    c=json.loads(CONF.read_text(encoding='utf-8-sig'));STATE['mtime']=m;STATE['conf']=c if c.get('enabled')else None
  except FileNotFoundError:STATE['mtime']=None;STATE['conf']=None
  except Exception:pass
  return STATE['conf']
OPEN=('/pn/model-data-v98/','/pn/story-data-v98/')
class Handler(previous.Handler):
 def maint171(self):
  c=conf()
  p=urlsplit(self.path).path
  if p=='/pn/maintenance-status171.json':
   body=json.dumps({'maintenance':bool(c),'until':(c or{}).get('until')}).encode()
   self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers()
   if self.command!='HEAD':self.wfile.write(body)
   return True
  if not c or not self.headers.get('Cf-Connecting-Ip')or p.startswith(OPEN):return False
  bypass=str(c.get('bypass')or'')
  q=parse_qs(urlsplit(self.path).query).get('bakim',[''])[0]
  ck=SimpleCookie(self.headers.get('Cookie','')).get('pav_bakim')
  if bypass and len(bypass)>=16 and ck is not None and ck.value==bypass:STATS['bypass']+=1;return False
  if bypass and len(bypass)>=16 and q==bypass:
   self.send_response(302);self.send_header('Set-Cookie','pav_bakim='+bypass+'; Path=/; Max-Age=86400; HttpOnly; Secure; SameSite=Lax');self.send_header('Location','/');self.send_header('Cache-Control','no-store');self.send_header('Content-Length','0');self.end_headers();return True
  if p.startswith('/api/')or self.command=='POST':
   STATS['api']+=1;body=json.dumps({'success':False,'maintenance':True,'error':'Sunucu kısa bir bakımda. Tahmini açılış 22:00 (TR).'},ensure_ascii=False).encode()
   self.send_response(503);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Retry-After','60')
  else:
   STATS['pages']+=1;body=PAGE.read_text(encoding='utf8').replace('__UNTIL__',str(c.get('until','2026-10-31T22:00:00+03:00'))).encode()
   self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8')
  self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.close_connection=True;self.end_headers()
  if self.command!='HEAD':self.wfile.write(body)
  return True
 def do_POST(self):
  if self.maint171():return
  return super().do_POST()
 def do_HEAD(self):
  if self.maint171():return
  return super().do_HEAD()
 def get164(self):
  if self.maint171():return
  if urlsplit(self.path).path=='/pn/server-capabilities-v171.json':
   c=conf()
   return self.json51(200,dict(backend_release='v171',base_release='v170',maintenance=bool(c),until=(c or{}).get('until'),maintenance_stats=dict(STATS)))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v171.db'):p.error('Disposable -v171.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes171.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
