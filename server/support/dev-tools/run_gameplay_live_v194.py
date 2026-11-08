"""194 backend: 193 + the NPC ambulance. A player who has been down for 5 s calls it (/api/gta/ems194); the call is
shared in every sync with players within 400 m (result['ems194'] = nearest 3 calls: id, x, y, z, age_ms, me), so each
of them plays the same scene in the engine (bridge v215: ambulance with sirens from a road ~140 m away, the paramedic
gets out and tends to the victim). The NPC revive (/api/gta/npcrevive192, 20 % health, $300) is allowed once the
call is 18 s old instead of after the 60 s medic minute; without a call the 192 rule stands. A call ends with the
revive, a respawn, a new death, leaving, or after 120 s. The hospital still waits 60 s; /canlandir works any time.
/pn/server-capabilities-v194.json."""
from pathlib import Path
import math,sys,time
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v193 as previous
host=previous.host;API=previous.API
CALL_AFTER=5;ARRIVE=18;TTL=120;NEAR=400;SHOW=3
STATE={'calls':{},'seq':0}
STATS={'calls':0,'revives':0,'early':0}
def wrap(api,now=time.time):
 calls=STATE['calls']
 def alive(c):
  p=api.PRESENCE.get(c['token'])
  return bool(p and p.get('char_id')==c['cid']and p.get('health',200)<=100 and p.get('dead_at')==c['dead_at']and now()-c['t']<TTL)
 def sweep():
  for cid in[k for k,c in calls.items()if not alive(c)]:calls.pop(cid,None)
 def call(token):
  p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
  if not p or not s:raise ValueError('Önce oyuna gir.')
  if p.get('health',200)>100 or 'dead_at'not in p:raise ValueError('Karakterin hayatta.')
  waited=now()-p['dead_at']
  if waited<CALL_AFTER:raise ValueError('Ambulans %d sn sonra çağrılabilir.'%max(1,math.ceil(CALL_AFTER-waited)))
  sweep();c=calls.get(p['char_id'])
  if not c:
   STATE['seq']+=1;STATS['calls']+=1
   c=calls[p['char_id']]=dict(id=STATE['seq'],cid=p['char_id'],token=token,dead_at=p['dead_at'],t=now(),x=float(s.get('x',0)),y=float(s.get('y',0)),z=float(s.get('z',0)))
  return dict(success=True,ems194=dict(id=c['id'],age_ms=int((now()-c['t'])*1000),arrive=ARRIVE),notice='Ambulans yola çıktı, sirenlerle geliyor (~20 sn).')
 old=api.dispatch
 def dispatch(path,*a,**k):
  token=a[1]if len(a)>1 else k.get('token','')
  if path=='/api/gta/ems194':
   try:
    with api.LOCK:return call(token),None
   except ValueError as e:return dict(success=False,error=str(e)),None
  if path=='/api/gta/npcrevive192':
   with api.LOCK:
    p=api.PRESENCE.get(token);sweep();c=calls.get(p['char_id'])if p else None
    if c and c['token']==token:
     age=now()-c['t']
     if age<ARRIVE:return dict(success=False,error='Ambulans yolda: %d sn.'%max(1,math.ceil(ARRIVE-age))),None
     if now()-p['dead_at']<61:p['dead_at']=now()-61;STATS['early']+=1   # the 192 check only knows the medic minute
     out=old(path,*a,**k)
     if out[0].get('success'):calls.pop(c['cid'],None);STATS['revives']+=1
     elif p.get('health',200)<=100:p['dead_at']=c['dead_at']
     return out
  out=old(path,*a,**k)
  if path=='/api/gta/sync':
   try:
    res=out[0]
    if isinstance(res,dict)and res.get('success'):
     with api.LOCK:
      s=api.GTA_STATE.get(token);p=api.PRESENCE.get(token)
      if calls and s and p:
       sweep();t=now();x,y=float(s.get('x',0)),float(s.get('y',0))
       near=sorted((math.hypot(c['x']-x,c['y']-y),c)for c in calls.values())
       rows=[dict(id=c['id'],x=round(c['x'],2),y=round(c['y'],2),z=round(c['z'],2),age_ms=int((t-c['t'])*1000),me=c['cid']==p['char_id'])for d,c in near if d<NEAR][:SHOW]
       if rows:out=(dict(res,ems194=rows),)+tuple(out[1:])
   except Exception:pass
  return out
 api.dispatch=dispatch;api.v194_installed=True;api.ems194=STATE;return api
def install():
 api=previous.install()
 if getattr(api,'v194_installed',False):return api
 wrap(api);API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v194.json':
   return self.json51(200,dict(backend_release='v194',base_release='v193',ems194=dict(STATS,open=len(STATE['calls']),arrive=ARRIVE)))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v194.db'):p.error('Disposable -v194.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes194.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous
 for _ in range(25):pp=pp.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
