"""176 backend: 175 + voice over the realtime server. Successful /api/gta/sync answers carry "voice176": {"t": route}
where route = base64url("c=<char>&r=<radio faction or 0>&k=<phone partner or 0>&d=<dimension>&e=<unix exp, 30 s>") +
"." + base64url(HMAC-SHA256(backups/rt172.secret, payload)); pavrt verifies it and relays audio with the same rules
as audio()/radio61 (phone partner, else nearby 30 m same dimension, else own faction radio when nobody is in a call).
radio = the faction only while the player's radio is on (radio61). A sync with "speaking176": true marks the player
as speaking (speaking_until, the microphone icon) and active, as /api/gta/voice did. backups/rt172.off disables it."""
from pathlib import Path
import sys,time,hmac,hashlib,base64,threading,importlib
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v175 as previous
host=previous.host;API=previous.API
SECRET=R/'backups/rt172.secret';OFF=R/'backups/rt172.off';STATS={'routes':0,'speaking':0};FAC={};LOCK=threading.Lock()
def b64(b):return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
def sign(s):return b64(s.encode())+'.'+b64(hmac.new(base64.b64decode(SECRET.read_text().strip()),s.encode(),hashlib.sha256).digest())
def install():
 api=previous.install()
 if getattr(api,'voice176_installed',False):return api
 phone=importlib.import_module(api.__package__+'.pn_phone')
 def faction(cid):
  now=time.time()
  with LOCK:
   hit=FAC.get(cid)
   if hit and now-hit[1]<5:return hit[0]
  with api.database()as db:r=db.execute('SELECT faction_id FROM pn_faction_members WHERE char_id=?',(cid,)).fetchone()
  fid=int(r[0])if r else 0
  with LOCK:FAC[cid]=(fid,now)
  return fid
 old=api.dispatch
 def dispatch(path,*a,**k):
  out=old(path,*a,**k)
  if path=='/api/gta/sync':
   try:
    result=out[0];payload=a[0]if a else{};token=a[1]if len(a)>1 else k.get('token','')
    p=api.PRESENCE.get(token)
    if isinstance(result,dict)and result.get('success')and p and p.get('char_id'):
     now=time.time();cid=int(p['char_id'])
     if isinstance(payload,dict)and payload.get('speaking176')is True:
      s=api.GTA_STATE.get(token)
      if s is not None:s['speaking_until']=now+0.7
      p['activity_at']=now;STATS['speaking']+=1
     if SECRET.exists()and not OFF.exists():
      radio=faction(cid)if p.get('radio61')else 0
      try:call=int(phone.call_peer(cid)or 0)
      except Exception:call=0
      result['voice176']={'t':sign('c=%d&r=%d&k=%d&d=%d&e=%d'%(cid,radio,call,int(p.get('dimension',0)or 0),int(now)+30))};STATS['routes']+=1
   except Exception:pass
  return out
 api.dispatch=dispatch;api.voice176_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v176.json':
   return self.json51(200,dict(backend_release='v176',base_release='v175',voice176=dict(STATS,enabled=SECRET.exists()and not OFF.exists())))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v176.db'):p.error('Disposable -v176.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes176.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
