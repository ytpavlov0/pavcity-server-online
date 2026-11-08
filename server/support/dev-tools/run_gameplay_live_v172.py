"""172 backend: 171 (maintenance) + realtime tickets for pavrt172 (support/rt172/pavrt.exe, WebSocket /rt).

Successful /api/gta/join and /api/gta/sync answers carry "rt172": {"path":"/rt","t":<ticket>} where ticket =
base64url("c=<char_id>&s=<server_id>&e=<unix exp>") + "." + base64url(HMAC-SHA256(secret, payload)), secret =
backups/rt172.secret (shared with pavrt.exe). Tickets live 2 h and are re-issued after 30 min. The file
backups/rt172.off switches tickets off (clients then stay on plain HTTP sync). /pn/server-capabilities-v172.json also
reports the realtime server's /rt/status."""
from pathlib import Path
import sys,json,time,hmac,hashlib,base64,threading,urllib.request
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v171 as previous
host=previous.host;API=previous.API
SECRET=R/'backups/rt172.secret';OFF=R/'backups/rt172.off';TTL=7200;RENEW=1800
# maintenance with "auto_open": true ends by itself at "until" (the countdown's 22:00), no restart needed
import datetime
_conf171=previous.conf
def conf_auto():
 c=_conf171()
 if c and c.get('auto_open'):
  try:
   if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(str(c.get('until'))):return None
  except Exception:pass
 return c
previous.conf=conf_auto
CACHE={};LOCK=threading.Lock();STATS={'issued':0,'attached':0,'off':0}
def b64(b):return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
def ticket(cid,sid):
 now=int(time.time());key=(cid,sid)
 with LOCK:
  hit=CACHE.get(key)
  if hit and now<hit[0]:return hit[1]
 payload=('c=%d&s=%d&e=%d'%(cid,sid,now+TTL)).encode()
 t=b64(payload)+'.'+b64(hmac.new(base64.b64decode(SECRET.read_text().strip()),payload,hashlib.sha256).digest())
 with LOCK:
  CACHE[key]=(now+RENEW,t);STATS['issued']+=1
  if len(CACHE)>5000:CACHE.clear()
 return t
def install():
 api=previous.install()
 if getattr(api,'rt172_installed',False):return api
 old=api.dispatch
 def dispatch(path,*a,**k):
  out=old(path,*a,**k)
  if path in('/api/gta/sync','/api/gta/join'):
   try:
    result=out[0]
    if isinstance(result,dict)and result.get('success')and SECRET.exists():
     if OFF.exists():STATS['off']+=1
     else:
      token=a[1]if len(a)>1 else k.get('token','')
      p=api.PRESENCE.get(token)
      if p and p.get('char_id'):result['rt172']={'path':'/rt','t':ticket(int(p['char_id']),int(p.get('server_id')or 0))};STATS['attached']+=1
   except Exception:pass
  return out
 api.dispatch=dispatch;api.rt172_installed=True;API[0]=api;return api
def rt_status():
 try:
  with urllib.request.urlopen('http://127.0.0.1:8090/rt/status',timeout=2)as r:return json.load(r)
 except Exception as e:return{'error':str(e)[:80]}
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v172.json':
   return self.json51(200,dict(backend_release='v172',base_release='v171',rt172=dict(STATS,enabled=SECRET.exists()and not OFF.exists()),realtime=rt_status(),maintenance=bool(previous.conf()),auto_open=bool((_conf171()or{}).get('auto_open'))))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v172.db'):p.error('Disposable -v172.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes172.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
