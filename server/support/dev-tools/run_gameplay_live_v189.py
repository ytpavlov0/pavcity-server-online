"""189 backend: 188 + shared broken street props (pairs with bridge v197 / client197).
- A sync may carry props197: up to 4 props the player's car just broke ({m: model hash, x, y, z} of the prop's original
  place). Accepted outside interiors, within 40 m of the player, at most 30 per player per minute; kept 15 minutes.
- Every sync answer carries props197: the broken props within 400 m (at most 80). The page hides them in the engine
  and restores a prop when it drops out of the list (expired or out of range).
- /pn/server-capabilities-v189.json: counts."""
from pathlib import Path
import sys,time,math,threading,contextlib
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v188 as previous
host=previous.host;API=previous.API
TTL=15*60;NEAR=40.0;VIEW=400.0;PER_MIN=30;MAXLIST=80
BROKEN={}  # (model, x*2, y*2, z*2) rounded -> dict(m,x,y,z,at)
RATE={}    # token -> [times]
BLOCK=threading.Lock()
STATS={'props_reported':0,'props_refused':0,'props_live':0}
def fin(*v):return all(type(x)in(int,float)and math.isfinite(x)for x in v)
def report(p,s,items,now=None):
 now=now or time.time()
 if not(isinstance(items,list)and p and s)or p.get('dimension',0):return 0
 if not fin(s.get('x'),s.get('y'),s.get('z')):return 0
 times=[t for t in RATE.get(id(p),[])if now-t<60];added=0
 for q in items[:4]:
  if not isinstance(q,dict):STATS['props_refused']+=1;continue
  m,x,y,z=q.get('m'),q.get('x'),q.get('y'),q.get('z')
  if type(m)is not int or not -2**31<=m<2**31 or m==0 or not fin(x,y,z)or abs(x)>16000 or abs(y)>16000 or not-200<z<2000:STATS['props_refused']+=1;continue
  if math.dist((x,y,z),(s['x'],s['y'],s['z']))>NEAR or len(times)>=PER_MIN:STATS['props_refused']+=1;continue
  key=(m,round(x*2),round(y*2),round(z*2))
  with BLOCK:
   if key not in BROKEN:BROKEN[key]=dict(m=m,x=round(x,2),y=round(y,2),z=round(z,2),at=now);times.append(now);added+=1
 RATE[id(p)]=times;STATS['props_reported']+=added
 return added
def near(s,now=None):
 now=now or time.time()
 if not s or not fin(s.get('x'),s.get('y')):return[]
 out=[]
 with BLOCK:
  for k,v in list(BROKEN.items()):
   if now-v['at']>TTL:del BROKEN[k];continue
   d=math.hypot(v['x']-s['x'],v['y']-s['y'])
   if d<=VIEW:out.append((d,v))
  STATS['props_live']=len(BROKEN)
 out.sort(key=lambda t:t[0])
 return[{k:v[k]for k in('m','x','y','z')}for _,v in out[:MAXLIST]]
def install():
 api=previous.install()
 if getattr(api,'v189_installed',False):return api
 old=api.dispatch
 def dispatch(path,*a,**k):
  if path!='/api/gta/sync':return old(path,*a,**k)
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  items=payload.get('props197')if isinstance(payload,dict)else None
  if isinstance(items,list)and items:
   try:
    with api.LOCK:report(api.PRESENCE.get(token),api.GTA_STATE.get(token),items)
   except Exception:pass
  out=old(path,*a,**k)
  try:
   res=out[0]
   if isinstance(res,dict)and res.get('success'):
    p=api.PRESENCE.get(token)
    lst=[]if p is None or p.get('dimension',0)else near(api.GTA_STATE.get(token))
    out=(dict(res,props197=lst),)+tuple(out[1:])
  except Exception:pass
  return out
 api.dispatch=dispatch;api.v189_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v189.json':
   return self.json51(200,dict(backend_release='v189',base_release='v188',v189=STATS,v188=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v189.db'):p.error('Disposable -v189.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes189.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous
 for _ in range(25):pp=pp.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
