"""173 backend: 172 + player ping in the TAB list. client158 sends ping_ms (smoothed round trip of its /api/gta/sync) in
every sync; it is kept per character for 15 s and /api/gta/roster answers carry "ping" (ms, or null when unknown)
for every listed player. Values outside 0..60000 are ignored."""
from pathlib import Path
import sys,time,threading
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v172 as previous
host=previous.host;API=previous.API
PING={};LOCK=threading.Lock();STATS={'reports':0,'rosters':0}
def install():
 api=previous.install()
 if getattr(api,'ping173_installed',False):return api
 old=api.dispatch
 def dispatch(path,*a,**k):
  if path=='/api/gta/sync':
   try:
    payload=a[0]if a else k.get('payload')or{};token=a[1]if len(a)>1 else k.get('token','')
    v=payload.get('ping_ms')if isinstance(payload,dict)else None
    if isinstance(v,(int,float))and not isinstance(v,bool)and 0<=v<=60000:
     p=api.PRESENCE.get(token)
     if p and p.get('char_id'):
      with LOCK:PING[int(p['char_id'])]=(int(round(v)),time.time());STATS['reports']+=1
   except Exception:pass
  out=old(path,*a,**k)
  if path=='/api/gta/roster':
   try:
    result=out[0];now=time.time()
    if isinstance(result,dict)and isinstance(result.get('players'),list):
     STATS['rosters']+=1
     with LOCK:
      for pl in result['players']:
       hit=PING.get(int(pl.get('char_id')or 0))
       pl['ping']=hit[0]if hit and now-hit[1]<15 else None
      if len(PING)>5000:
       for c in[c for c,(_,t)in PING.items()if now-t>60]:PING.pop(c,None)
   except Exception:pass
  return out
 api.dispatch=dispatch;api.ping173_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v173.json':
   return self.json51(200,dict(backend_release='v173',base_release='v172',ping173=dict(STATS),rt172=dict(previous.STATS,enabled=previous.SECRET.exists()and not previous.OFF.exists()),realtime=previous.rt_status(),maintenance=bool(previous.previous.conf()),auto_open=bool((previous._conf171()or{}).get('auto_open'))))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v173.db'):p.error('Disposable -v173.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes173.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
