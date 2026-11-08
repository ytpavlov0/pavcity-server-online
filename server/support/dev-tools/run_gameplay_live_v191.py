"""191 backend: 190 + no free revive by reloading the page.
- A dead character (health <= 100) that joins again (page reload, new tab, coming back later) was put at the hospital
  with full health (200) and charged nothing, while "Hastanede doğ" charges 10 % of the cash (at most $2,500), wakes
  the player with 25 % health and costs one water and one food. A death known to the server (live presence of that
  character, or the saved state) now gets exactly that recovery on join, audited as hospital-recovery-join191.
- /pn/server-capabilities-v191.json: counts."""
from pathlib import Path
import sys,time
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v190 as previous
host=previous.host;API=previous.API
STATS={'join_recoveries':0,'join_charged':0}
def dead_on_join(api,token,cid):
 """True if the server knows this character as dead: a live presence of it (any session) or its saved state."""
 for k,p in api.PRESENCE.items():
  if p.get('char_id')==cid and p.get('world')=='gta':
   return p.get('health',200)<=100
 try:
  with api.database()as db:ch=db.execute('SELECT * FROM characters WHERE id=?',(cid,)).fetchone()
  return bool(ch)and api.multiplayer.initial(dict(ch)).get('health',200)<=100
 except Exception:return False
def recover(api,token,result):
 """Same terms as /api/gta/respawn (gameplay_mobile170): 10 % of cash (max $2,500), health 125, -1 water/-1 food,
 hunger/thirst at least 30."""
 p=api.PRESENCE.get(token)
 if not p:return result
 uid=p['user_id'];world=api.world
 with api.database()as db:
  balance=world.wallet(uid);charge=min(2500,max(0,int(balance)//10))
  if charge:db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(charge,uid,charge))
  lost={k:min(1,max(0,int(p.get(k,0))))for k in('water','food')}
  for k,n in lost.items():p[k]=max(0,int(p.get(k,0))-n)
  p['health']=125;p['hunger']=max(30,p.get('hunger',100));p['thirst']=max(30,p.get('thirst',100))
  world.audit(db,uid,'hospital-recovery-join191',dict(char_id=p['char_id'],charge=charge,lost=lost))
 STATS['join_recoveries']+=1;STATS['join_charged']+=charge
 spawn=dict(result.get('spawn')or{},health=125)
 return dict(result,spawn=spawn,money=world.wallet(uid),recovery191=dict(charge=charge,lost=lost),
  notice=f"Baygın hâlde hastaneye kaldırıldın: %25 canla uyandın. Nakit kesintisi ${charge}; kayıp: {lost['water']} su, {lost['food']} yiyecek.")
def install():
 api=previous.install()
 if getattr(api,'v191_installed',False):return api
 wrap(api);API[0]=api;return api
def wrap(api):
 old=api.dispatch
 def dispatch(path,*a,**k):
  if path!='/api/gta/join':return old(path,*a,**k)
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  try:cid=int(payload.get('char_id',0))
  except(TypeError,ValueError):cid=0
  with api.LOCK:
   dead=bool(cid)and dead_on_join(api,token,cid)
   out=old(path,*a,**k)
   try:
    res=out[0]
    if dead and isinstance(res,dict)and res.get('success')and res.get('spawn'):out=(recover(api,token,res),)+tuple(out[1:])
   except Exception:pass
  return out
 api.dispatch=dispatch;api.v191_installed=True;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v191.json':
   return self.json51(200,dict(backend_release='v191',base_release='v190',v191=STATS,v190=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v191.db'):p.error('Disposable -v191.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes191.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous
 for _ in range(25):pp=pp.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
