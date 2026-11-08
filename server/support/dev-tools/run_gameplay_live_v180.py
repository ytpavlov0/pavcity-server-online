"""180 backend: 179 + moderation commands (chat): /kick ID sebep, /mute ID dakika sebep, /unmute ID, /sesmute ID dakika
sebep, /unsesmute ID (rank >= 1 moderator; never on yourself or an equal/higher rank; audited).
- /kick: the player's session is ended (saved, seat released, presence and login removed); they can log in again.
- /mute: chat (local/OOC text, /me /do /b /ooc /pm /p /r /f) refused until it ends; other commands still work.
- /sesmute: no voice route in the sync answer (the realtime voice route lapses within 30 s), /api/gta/voice audio
  refused, and the speaking flag ignored. Mutes are stored in pn_mutes180 (user, kind, until) and survive reconnects."""
from pathlib import Path
import sys,time,re
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v179 as previous
host=previous.host;API=previous.API
STATS={'kick':0,'mute':0,'sesmute':0,'refused_chat':0,'refused_voice':0}
CHAT_CMDS=('/me','/do','/b','/ooc','/pm','/p','/r','/f')
MOD=('/kick','/mute','/unmute','/sesmute','/unsesmute')
def install():
 api=previous.install()
 if getattr(api,'v180_installed',False):return api
 import importlib
 adm=importlib.import_module(api.__package__+'.pn_admin');w=api.world
 with w.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_mutes180(user_id INTEGER NOT NULL,kind TEXT NOT NULL,until REAL NOT NULL,reason TEXT,actor INTEGER,PRIMARY KEY(user_id,kind))')
 CACHE={}
 def muted(uid,kind):
  now=time.time();hit=CACHE.get((uid,kind))
  if hit and now-hit[1]<5:until=hit[0]
  else:
   with w.database()as db:r=db.execute('SELECT until FROM pn_mutes180 WHERE user_id=? AND kind=?',(uid,kind)).fetchone()
   until=float(r['until'])if r else 0.0;CACHE[(uid,kind)]=(until,now)
  return until if until==-1 or until>now else 0
 def left(until):return 'süresiz' if until==-1 else str(max(1,int((until-time.time()+59)//60)))+' dk'
 def target(args,level,uid):
  if not args:raise ValueError('Oyuncu ID gerekli.')
  cid=w.resolve_player_id(args[0],api.PRESENCE)
  key,peer=next(((k,v)for k,v in api.PRESENCE.items()if v.get('char_id')==cid),(None,None))
  if not peer:raise ValueError('Oyuncu bağlı değil.')
  if peer['user_id']==uid or adm.rank(peer['user_id'])>=level:raise ValueError('Kendine veya eşit/üst yetkiliye bu işlemi uygulayamazsın.')
  return key,peer
 def moderate(cmd,args,token):
  p=api.PRESENCE.get(token)
  if not p:raise ValueError('Oturum bulunamadı.')
  uid=p['user_id'];level=adm.rank(uid)
  if level<1:raise ValueError('Bu komut için yetkin yok.')
  key,peer=target(args,level,uid);name='%s [%s]'%(peer.get('name'),peer.get('server_id'))
  if cmd=='/kick':
   reason=' '.join(args[1:])[:200]or'sebep belirtilmedi'
   with w.database()as db:
    db.execute('DELETE FROM pn_sessions WHERE user_id=?',(peer['user_id'],));w.audit(db,uid,'kick',dict(char_id=peer['char_id'],reason=reason))
   try:
    from importlib import import_module
    mp=import_module(api.__package__+'.pn_multiplayer')
    if key in api.GTA_STATE:mp.save(peer,api.GTA_STATE[key],True)
   except Exception:pass
   for t,sess in list(getattr(api,'SESSIONS',{}).items()):
    if isinstance(sess,dict)and sess.get('user_id')==peer['user_id']:api.SESSIONS.pop(t,None)
   w.release(peer['char_id']);api.PRESENCE.pop(key,None);api.GTA_STATE.pop(key,None);STATS['kick']+=1
   return dict(success=True,notice='%s sunucudan atıldı (%s).'%(name,reason))
  kind='chat'if cmd in('/mute','/unmute')else'voice'
  if cmd in('/unmute','/unsesmute'):
   with w.database()as db:db.execute('DELETE FROM pn_mutes180 WHERE user_id=? AND kind=?',(peer['user_id'],kind));w.audit(db,uid,cmd[1:],dict(char_id=peer['char_id']))
   CACHE.pop((peer['user_id'],kind),None)
   return dict(success=True,notice='%s için %s susturması kaldırıldı.'%(name,'sohbet'if kind=='chat'else'sesli sohbet'))
  if len(args)<2 or not re.fullmatch(r'\d{1,6}',args[1]):raise ValueError('Kullanım: %s ID dakika sebep (0 = süresiz)'%cmd)
  minutes=int(args[1]);reason=' '.join(args[2:])[:200]or'sebep belirtilmedi';until=-1 if minutes==0 else time.time()+minutes*60
  with w.database()as db:
   db.execute('INSERT INTO pn_mutes180 VALUES(?,?,?,?,?) ON CONFLICT(user_id,kind) DO UPDATE SET until=excluded.until,reason=excluded.reason,actor=excluded.actor',(peer['user_id'],kind,until,reason,uid))
   w.audit(db,uid,cmd[1:],dict(char_id=peer['char_id'],minutes=minutes,reason=reason))
  CACHE.pop((peer['user_id'],kind),None);STATS['mute'if kind=='chat'else'sesmute']+=1
  if kind=='voice':
   s=api.GTA_STATE.get(key)
   if s is not None:s['speaking_until']=0
  return dict(success=True,notice='%s %s susturuldu (%s · %s).'%(name,'sohbetten'if kind=='chat'else'sesli sohbetten','süresiz'if minutes==0 else str(minutes)+' dk',reason))
 old=api.dispatch
 def dispatch(path,*a,**k):
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  if path=='/api/chat/send'and isinstance(payload,dict)and isinstance(payload.get('message'),str):
   msg=payload['message'].strip();cmd=msg.split()[0].lower()if msg else''
   if cmd in MOD:
    with api.LOCK:return moderate(cmd,msg.split()[1:],token),None
   p=api.PRESENCE.get(token)
   if p and(not msg.startswith('/')or cmd in CHAT_CMDS):
    u=muted(p['user_id'],'chat')
    if u:STATS['refused_chat']+=1;raise ValueError('Sohbetten susturuldun (%s kaldı).'%left(u))
  elif path=='/api/gta/voice'and isinstance(payload,dict)and payload.get('audio'):
   p=api.PRESENCE.get(token)
   if p and muted(p['user_id'],'voice'):STATS['refused_voice']+=1;raise ValueError('Sesli sohbetten susturuldun.')
  elif path=='/api/gta/sync'and isinstance(payload,dict):
   p=api.PRESENCE.get(token)
   if p and payload.get('speaking176')and muted(p['user_id'],'voice'):payload=dict(payload,speaking176=False);a=(payload,)+tuple(a[1:])
   out=old(path,*a,**k)
   try:
    if p and isinstance(out[0],dict)and'voice176'in out[0]and muted(p['user_id'],'voice'):out[0].pop('voice176',None)
   except Exception:pass
   return out
  return old(path,*a,**k)
 api.dispatch=dispatch;api.v180_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v180.json':
   return self.json51(200,dict(backend_release='v180',base_release='v179',v180=STATS,v179=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v180.db'):p.error('Disposable -v180.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes180.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
