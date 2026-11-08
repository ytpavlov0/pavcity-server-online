"""177 backend: 176 + (a) ATMs open the server bank: a sync carrying "atm163": [x, y, z] (bridge v163 reports the ATM
prop within 1.6 m) is accepted when the player really stands within 3 m of it (p['atm177'], 20 s); /api/bank/* then
counts that ATM as a bank point for that request only. (b) Vehicle exterior controls: /api/vehicles/door (doors, hood,
trunk), /window and /lock are refused to a player outside the car while anyone else sits in it (an outsider with a key
could open a moving car's doors / trunk)."""
from pathlib import Path
import sys,time,math,threading
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v176 as previous
host=previous.host;API=previous.API
STATS={'atm_seen':0,'atm_bank':0,'outside_refused':0}
EXTERIOR=('/api/vehicles/door','/api/vehicles/window','/api/vehicles/lock')
def install():
 api=previous.install()
 if getattr(api,'v177_installed',False):return api
 import importlib
 rp=importlib.import_module(api.__package__+'.pn_roleplay');w=api.world
 def near(state,pt,r):
  try:return math.dist([float(state[k])for k in'xyz'],pt[:3])<=r
  except Exception:return False
 old=api.dispatch
 def dispatch(path,*a,**k):
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  if path=='/api/gta/sync'and isinstance(payload,dict)and isinstance(payload.get('atm163'),list):
   try:
    pt=[float(x)for x in payload['atm163'][:3]];p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
    if p and len(pt)==3 and all(map(math.isfinite,pt))and near(s,pt,3)and not(s or{}).get('vehicle_id'):p['atm177']=(*pt,time.time());STATS['atm_seen']+=1
   except Exception:pass
  elif path.startswith('/api/bank/'):
   p=api.PRESENCE.get(token);atm=p.get('atm177')if p else None
   if atm and time.time()-atm[3]<20 and near(api.GTA_STATE.get(token),atm,3):
    with api.LOCK:
     point=dict(x=atm[0],y=atm[1],z=atm[2]);rp.BANKS.append(point)
     try:out=old(path,*a,**k)
     finally:
      try:rp.BANKS.remove(point)
      except ValueError:pass
    STATS['atm_bank']+=1;return out
  elif path in EXTERIOR and isinstance(payload,dict):
   p=api.PRESENCE.get(token)
   try:vid=int(payload.get('id'))
   except Exception:vid=0
   if p and vid:
    with api.LOCK:
     cid=p['char_id'];mine=w.occupation(cid)
     if mine[0]!=vid and any(key[0]==vid and (seat or{}).get('char_id')not in(None,cid)for key,seat in list(w.SEATS.items())):
      STATS['outside_refused']+=1;raise ValueError('Araçta biri varken dışarıdan kapı, bagaj, cam veya kilit kullanamazsın.')
  return old(path,*a,**k)
 api.dispatch=dispatch;api.v177_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v177.json':
   return self.json51(200,dict(backend_release='v177',base_release='v176',v177=STATS,voice176=dict(previous.STATS)))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v177.db'):p.error('Disposable -v177.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes177.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
