"""182 backend: 181 + IP tools for staff (chat commands).
- Every API request through Cloudflare records its gta_session token -> (IP, country, time) in memory (bounded).
- /ipgor ID (rank >= 3): the player's connecting IP and Cloudflare country (Cf-Ipcountry) as a notice for that admin
  only, plus a line in backups/ipgor182.jsonl (who looked, when); audited.
- /ipban ID dakika sebep (rank >= 2, 0 = permanent): account ban (pn_bans) + IP ban (HMAC of the IP in pn_ipbans182)
  + kick (sessions and presence). Any later API request from that IP gets 403 until it ends - new accounts included.
- /unipban kullaniciadi|charID (rank >= 2): lifts that account's IP bans (account ban: /unban as before).
- /ipbanlar (rank >= 2): the active IP bans (no addresses shown)."""
from pathlib import Path
import sys,time,json,hmac,hashlib,base64,threading
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v181 as previous
host=previous.host;API=previous.API
STATS={'ipgor':0,'ipban':0,'blocked':0}
IPS={};IPLOCK=threading.Lock();BANS={'at':0.0,'set':set()};LOG=R/'backups/ipgor182.jsonl'
def iphash(ip):
 key=base64.b64decode((R/'backups/rt172.secret').read_text().strip())
 return hmac.new(key,('ip182:'+ip).encode(),hashlib.sha256).hexdigest()
def install():
 api=previous.install()
 if getattr(api,'v182_installed',False):return api
 import importlib
 adm=importlib.import_module(api.__package__+'.pn_admin');w=api.world;mp=importlib.import_module(api.__package__+'.pn_multiplayer')
 with w.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_ipbans182(hash TEXT NOT NULL,user_id INTEGER,name TEXT,until REAL NOT NULL,reason TEXT,actor INTEGER,created REAL,PRIMARY KEY(hash,user_id))')
 def refresh():
  now=time.time()
  if now-BANS['at']<5:return BANS['set']
  with w.database()as db:rows=db.execute('SELECT hash FROM pn_ipbans182 WHERE until=-1 OR until>?',(now,)).fetchall()
  BANS['set']={r['hash']for r in rows};BANS['at']=now;return BANS['set']
 api.ipbanned182=lambda ip:bool(ip)and iphash(ip)in refresh()
 def peer_of(args,level,uid):
  if not args:raise ValueError('Oyuncu ID gerekli.')
  cid=w.resolve_player_id(args[0],api.PRESENCE)
  key,peer=next(((k,v)for k,v in api.PRESENCE.items()if v.get('char_id')==cid),(None,None))
  if not peer:raise ValueError('Oyuncu bağlı değil.')
  if peer['user_id']==uid or adm.rank(peer['user_id'])>=level:raise ValueError('Kendine veya eşit/üst yetkiliye bu işlemi uygulayamazsın.')
  return key,peer
 def run(cmd,args,token):
  p=api.PRESENCE.get(token)
  if not p:raise ValueError('Oturum bulunamadı.')
  uid=p['user_id'];level=adm.rank(uid)
  if cmd=='/ipgor':
   if level<3:raise ValueError('Bu komut için baş yönetici yetkisi gerekli.')
   key,peer=peer_of(args,level,uid)
   with IPLOCK:rec=IPS.get(key)
   if not rec:raise ValueError('Bu oyuncunun bağlantı bilgisi henüz yok (birkaç saniye sonra tekrar dene).')
   ip,country,at=rec
   with w.database()as db:w.audit(db,uid,'ipgor',dict(char_id=peer['char_id']))
   with LOG.open('a',encoding='utf8')as f:f.write(json.dumps(dict(t=time.time(),by=uid,char_id=peer['char_id'],name=peer.get('name'),ip=ip,country=country),ensure_ascii=False)+'\n')
   STATS['ipgor']+=1
   return dict(success=True,notice='%s [%s] · IP %s · Ülke %s · son istek %d sn önce'%(peer.get('name'),peer.get('server_id'),ip,country or'?',int(time.time()-at)),
    info=dict(title='Bağlantı bilgisi',rows=[['Oyuncu',peer.get('name')],['ID',peer.get('server_id')],['IP',ip],['Ülke (Cloudflare)',country or'?']]))
  if level<2:raise ValueError('Bu komut için yönetici yetkisi gerekli.')
  if cmd=='/ipbanlar':
   with w.database()as db:rows=db.execute('SELECT name,until,reason FROM pn_ipbans182 WHERE until=-1 OR until>? ORDER BY created DESC LIMIT 20',(time.time(),)).fetchall()
   if not rows:return dict(success=True,notice='Aktif IP yasağı yok.')
   return dict(success=True,notice='Aktif IP yasakları: '+' · '.join('%s (%s, %s)'%(r['name'],'süresiz'if r['until']==-1 else str(int((r['until']-time.time())//60)+1)+' dk',r['reason'])for r in rows))
  if cmd=='/unipban':
   if not args:raise ValueError('Kullanım: /unipban kullanıcıadı veya karakter ID')
   with w.database()as db:
    if args[0].isdigit():u=db.execute('SELECT user_id FROM characters WHERE id=?',(int(args[0]),)).fetchone()
    else:u=db.execute('SELECT id AS user_id FROM users WHERE username=? COLLATE NOCASE',(args[0],)).fetchone()
    if not u:raise ValueError('Hesap bulunamadı.')
    n=db.execute('DELETE FROM pn_ipbans182 WHERE user_id=?',(u['user_id'],)).rowcount;w.audit(db,uid,'unipban',dict(user_id=u['user_id']))
   BANS['at']=0;return dict(success=True,notice='%d IP yasağı kaldırıldı (hesap yasağı için /unban).'%n)
  # /ipban
  key,peer=peer_of(args,level,uid)
  if len(args)<3 or not args[1].isdigit():raise ValueError('Kullanım: /ipban ID dakika sebep (0 = süresiz)')
  minutes=int(args[1]);reason=' '.join(args[2:])[:200];until=-1 if minutes==0 else time.time()+minutes*60
  with IPLOCK:rec=IPS.get(key)
  ips=[rec[0]]if rec else[]
  with IPLOCK:ips+=[v[0]for k,v in IPS.items()if k!=key and api.SESSIONS.get(k,{}).get('user_id')==peer['user_id']]
  with w.database()as db:
   for ip in set(ips):db.execute('INSERT OR REPLACE INTO pn_ipbans182 VALUES(?,?,?,?,?,?,?)',(iphash(ip),peer['user_id'],peer.get('name'),until,reason,uid,time.time()))
   db.execute('INSERT INTO pn_bans VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET until=excluded.until,reason=excluded.reason,actor=excluded.actor',(peer['user_id'],0 if minutes==0 else until,reason,uid))
   db.execute('DELETE FROM pn_sessions WHERE user_id=?',(peer['user_id'],));w.audit(db,uid,'ipban',dict(char_id=peer['char_id'],minutes=minutes,reason=reason,ips=len(set(ips))))
  for t,sess in list(api.SESSIONS.items()):
   if isinstance(sess,dict)and sess.get('user_id')==peer['user_id']:api.SESSIONS.pop(t,None)
  try:
   if key in api.GTA_STATE:mp.save(peer,api.GTA_STATE[key],True)
  except Exception:pass
  w.release(peer['char_id']);api.PRESENCE.pop(key,None);api.GTA_STATE.pop(key,None);BANS['at']=0;STATS['ipban']+=1
  return dict(success=True,notice='%s [%s] hesap + IP yasaklandı (%s · %s)%s.'%(peer.get('name'),peer.get('server_id'),'süresiz'if minutes==0 else str(minutes)+' dk',reason,'' if ips else ' · IP henüz bilinmiyordu, yalnız hesap'))
 old=api.dispatch
 def dispatch(path,*a,**k):
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  if path=='/api/chat/send'and isinstance(payload,dict)and isinstance(payload.get('message'),str):
   parts=payload['message'].strip().split()
   if parts and parts[0].lower()in('/ipgor','/ipban','/unipban','/ipbanlar'):
    with api.LOCK:return run(parts[0].lower(),parts[1:],token),None
  return old(path,*a,**k)
 api.dispatch=dispatch;api.v182_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def _ip182(self):
  ip=self.headers.get('Cf-Connecting-Ip')or''
  if not ip:return True
  path=urlsplit(self.path).path
  if not path.startswith('/api/'):return True
  token=''
  for part in(self.headers.get('Cookie')or'').split(';'):
   k,_,v=part.strip().partition('=')
   if k=='gta_session':token=v
  if token:
   with IPLOCK:
    IPS[token]=(ip,self.headers.get('Cf-Ipcountry')or'',time.time())
    if len(IPS)>5000:
     for t in sorted(IPS,key=lambda t:IPS[t][2])[:1000]:IPS.pop(t,None)
  api=API[0]
  if getattr(api,'ipbanned182',None)and api.ipbanned182(ip):
   STATS['blocked']+=1;self.close_connection=True;self.json51(403,dict(success=False,error='Bu bağlantı sunucudan yasaklandı.'));return False
  return True
 def do_POST(self):
  if not self._ip182():return
  return super().do_POST()
 def get164(self):
  if not self._ip182():return
  if urlsplit(self.path).path=='/pn/server-capabilities-v182.json':
   return self.json51(200,dict(backend_release='v182',base_release='v181',v182=STATS,v181=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v182.db'):p.error('Disposable -v182.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes182.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
