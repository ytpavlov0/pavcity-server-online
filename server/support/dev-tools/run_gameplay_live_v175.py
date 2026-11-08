"""175 backend: 174 + strict maintenance entry. While maintenance is on, the page itself (/ and /index.html) through
Cloudflare always shows the countdown, even for a browser that holds the owner cookie; only a URL that carries
?bakim=<bypass> opens the game (and refreshes the cookie that lets the game's own requests through). Everything else
is unchanged from 171 (assets/API with the cookie pass, game data always served, local requests never blocked)."""
from pathlib import Path
import sys,json
from urllib.parse import urlsplit,parse_qs
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v174 as previous
host=previous.host;API=previous.API;install=previous.install
def v171():
 m=previous
 while not hasattr(m,'maintenance_page171'):
  if hasattr(m,'PAGE')and hasattr(m,'conf')and m.__name__.endswith('v171'):return m
  m=m.previous
 return m
M171=v171()
class Handler(previous.Handler):
 def maint171(self):
  c=M171.conf()
  if c and self.headers.get('Cf-Connecting-Ip'):
   u=urlsplit(self.path);bypass=str(c.get('bypass')or'')
   if u.path in('/','/index.html')and self.command in('GET','HEAD')and not(bypass and len(bypass)>=16 and parse_qs(u.query).get('bakim',[''])[0]==bypass):
    body=M171.PAGE.read_text(encoding='utf8').replace('__UNTIL__',str(c.get('until','2026-10-31T22:00:00+03:00'))).encode()
    M171.STATS['pages']+=1;self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.close_connection=True;self.end_headers()
    if self.command!='HEAD':self.wfile.write(body)
    return True
   if u.path in('/','/index.html')and self.command=='GET'and bypass and parse_qs(u.query).get('bakim',[''])[0]==bypass:
    self._bakim175=bypass   # serve the real page and refresh the cookie
    return False
  return super().maint171()
 def send_response(self,code,message=None):
  r=super().send_response(code,message)
  b=getattr(self,'_bakim175',None)
  if b:self._bakim175=None;self.send_header('Set-Cookie','pav_bakim='+b+'; Path=/; Max-Age=86400; HttpOnly; Secure; SameSite=Lax')
  return r
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v175.json':
   c=M171.conf()
   return self.json51(200,dict(backend_release='v175',base_release='v174',maintenance=bool(c),strict_entry=True))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v175.db'):p.error('Disposable -v175.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes175.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
