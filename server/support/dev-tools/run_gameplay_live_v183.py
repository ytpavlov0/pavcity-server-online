"""183 backend: 182 + microphone rule.
- New accounts earn the microphone with 2 hours of play (features117.REQUIRED 900 -> 7200 s). Accounts that had
  already earned it (>= 900 s recorded) are moved to 7200 once, so nobody who could talk loses it.
- The lock now also covers realtime voice: while a sync answer says voice117.locked, its voice176 route is removed
  (pavrt relays nothing without a route) and the speaking flag is cleared. Since 176 a locked newcomer could talk over
  the realtime socket because only /api/gta/voice was refused.
- Only accounts made before the opening (31 Oct 21:30 TR) keep an already earned microphone (900 s -> 7200 s once);
  accounts made after it (opening-night trolls) need the full 2 hours.
- Chat filter (profanity183): text chat, OOC and /me /do /b /ooc /pm /p /r /f with a swear/insult is refused; the 3rd
  refusal within 10 minutes mutes the chat for 15 minutes (pn_mutes180, actor 0). Other commands are not checked.
- Character names: /api/character/create refuses swear words and keyboard mash ("dwadwa dwadwadw")."""
from pathlib import Path
import sys,time,datetime,collections
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v182 as previous
from profanity183 import bad,nonsense_name
host=previous.host;API=previous.API
STATS={'route_withheld':0,'grandfathered':0,'chat_blocked':0,'auto_muted':0,'names_refused':0}
MIC_SECONDS=7200
OPENING=datetime.datetime(2026,10,31,18,30,tzinfo=datetime.timezone.utc).timestamp()
CHAT_CMDS=('/me','/do','/b','/ooc','/pm','/p','/r','/f')
STRIKES=collections.defaultdict(collections.deque);AUTO={}
def install():
 import features117
 features117.REQUIRED=MIC_SECONDS
 api=previous.install()
 if getattr(api,'v183_installed',False):return api
 w=api.world
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_meta117(key TEXT PRIMARY KEY,value REAL NOT NULL)')
  if not db.execute("SELECT 1 FROM pn_meta117 WHERE key='v183_grandfathered'").fetchone():
   try:STATS['grandfathered']=db.execute('UPDATE pn_playtime117 SET seconds=? WHERE seconds>=900 AND seconds<? AND user_id IN (SELECT id FROM users WHERE created_at<?)',(float(MIC_SECONDS),float(MIC_SECONDS),OPENING)).rowcount
   except Exception:pass
   db.execute("INSERT OR REPLACE INTO pn_meta117 VALUES('v183_grandfathered',?)",(time.time(),))
 old=api.dispatch
 def strike(p):
  now=time.time();q=STRIKES[p['user_id']]
  while q and now-q[0]>600:q.popleft()
  q.append(now)
  if len(q)>=3:
   q.clear()
   with w.database()as db:
    db.execute('CREATE TABLE IF NOT EXISTS pn_mutes180(user_id INTEGER NOT NULL,kind TEXT NOT NULL,until REAL NOT NULL,reason TEXT,actor INTEGER,PRIMARY KEY(user_id,kind))')
    db.execute('INSERT INTO pn_mutes180 VALUES(?,?,?,?,?) ON CONFLICT(user_id,kind) DO UPDATE SET until=excluded.until,reason=excluded.reason,actor=excluded.actor',(p['user_id'],'chat',now+900,'otomatik: küfür',0))
    w.audit(db,0,'automute183',dict(char_id=p.get('char_id')))
   AUTO[p['user_id']]=now+900;STATS['auto_muted']+=1;return True
  return False
 def dispatch(path,*a,**k):
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  if path=='/api/chat/send'and isinstance(payload,dict)and isinstance(payload.get('message'),str):
   msg=payload['message'].strip();head=msg.split()[0].lower()if msg else''
   if not msg.startswith('/')or head in CHAT_CMDS:
    p=api.PRESENCE.get(token);until=AUTO.get(p['user_id'],0)if p else 0
    if until>time.time():raise ValueError('Sohbetten susturuldun (%d dk kaldı).'%(int((until-time.time())//60)+1))
   if(not msg.startswith('/')or head in CHAT_CMDS)and bad(msg):
    p=api.PRESENCE.get(token);STATS['chat_blocked']+=1
    if p and strike(p):raise ValueError('Küfür ettiğin için 15 dakika sohbetten susturuldun.')
    raise ValueError('Küfür ve hakaret içeren mesaj gönderilemez. Tekrarında sohbetten susturulursun.')
  elif path=='/api/character/create'and isinstance(payload,dict):
   for part in(payload.get('name'),payload.get('surname')):
    if isinstance(part,str)and(bad(part)or nonsense_name(part)):
     STATS['names_refused']+=1;raise ValueError('Bu ad kullanılamaz. Gerçekçi bir ad ve soyad yaz (küfür veya anlamsız harf dizisi olamaz).')
  out=old(path,*a,**k)
  if path=='/api/gta/sync':
   try:
    res=out[0]
    if isinstance(res,dict)and(res.get('voice117')or{}).get('locked')and'voice176'in res:
     res.pop('voice176',None);STATS['route_withheld']+=1
     token=a[1]if len(a)>1 else k.get('token','');s=api.GTA_STATE.get(token)
     if s is not None:s['speaking_until']=0
   except Exception:pass
  return out
 api.dispatch=dispatch;api.v183_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v183.json':
   import features117
   return self.json51(200,dict(backend_release='v183',base_release='v182',v183=STATS,mic_seconds=features117.REQUIRED,v182=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v183.db'):p.error('Disposable -v183.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes183.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
