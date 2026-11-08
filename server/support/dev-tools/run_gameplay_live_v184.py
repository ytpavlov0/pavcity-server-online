"""184 backend: 183 + accounts and staff tools.
- Registration needs an e-mail at a known mail provider (gmail, hotmail/outlook/live, yahoo, icloud, yandex, mail.ru,
  proton, gmx, aol ...); keyboard-mash local parts and an address already used by another account are refused.
  Stored in pn_emails184 (one account per address). Existing accounts are not affected.
- Every successful register / login / join records the connection (IP, Cloudflare country, browser, device) per
  account in pn_logins184; a banned account that tries to log in gets the IP it came from IP-banned (ban evasion).
- /hesapbilgi ID (rank >= 3): username, e-mail, account date, play time and the last 3 connections.
- /api/gta/roster for staff (rank >= 1): every row also carries "username" (the TAB list shows Ad Soyad (kullanıcı)).
- /adminkomutları, /adminkomutlari: the staff command list (/admincommands) plus the commands added since 180."""
from pathlib import Path
import sys,time,re,threading,datetime
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v183 as previous
from profanity183 import nonsense_name
host=previous.host;API=previous.API
STATS={'emails':0,'email_refused':0,'logins':0,'evasion_ipbans':0,'hesapbilgi':0}
CUR=threading.local()
PROVIDERS={'gmail.com','googlemail.com','hotmail.com','hotmail.com.tr','outlook.com','outlook.com.tr','live.com','msn.com','windowslive.com',
 'yahoo.com','yahoo.com.tr','ymail.com','icloud.com','me.com','mac.com','yandex.com','yandex.com.tr','yandex.ru','ya.ru','mail.ru','bk.ru','inbox.ru',
 'proton.me','protonmail.com','pm.me','gmx.com','gmx.de','gmx.net','aol.com','web.de','zoho.com','tutanota.com','tuta.io','hotmail.de','hotmail.fr',
 'hotmail.co.uk','outlook.de','yahoo.de','yahoo.fr','yahoo.co.uk','mynet.com','superonline.com','ttmail.com','windowslive.com'}
EMAIL=re.compile(r'^[a-z0-9](?:[a-z0-9._+-]{0,62}[a-z0-9])?@([a-z0-9-]+(?:\.[a-z0-9-]+)+)$')
def check_email(raw):
 e=str(raw or'').strip().lower()
 m=EMAIL.match(e)
 if not m or '..'in e:raise ValueError('Geçerli bir e-posta adresi yaz (ör. adin@gmail.com).')
 if m.group(1)not in PROVIDERS:raise ValueError('Bu e-posta sağlayıcısı kabul edilmiyor. Gmail, Hotmail/Outlook, Yahoo, iCloud veya Yandex gibi gerçek bir adres kullan.')
 local=e.split('@')[0];letters=re.sub(r'[^a-z]','',local)
 if len(local)<3 or(len(letters)>=5 and not re.search(r'\d',local)and nonsense_name(letters)):raise ValueError('Bu e-posta adresi gerçek görünmüyor. Kendi e-posta adresini yaz.')
 return e
def ua_label(ua):
 ua=ua or'';b=('Edge'if'Edg/'in ua else'Opera'if'OPR/'in ua else'Chrome'if'Chrome/'in ua else'Firefox'if'Firefox/'in ua else'Safari'if'Safari/'in ua else'?')
 o=('Android'if'Android'in ua else'iPhone/iPad'if('iPhone'in ua or'iPad'in ua)else'Windows'if'Windows'in ua else'macOS'if'Mac OS'in ua else'Linux'if'Linux'in ua else'?')
 return b+' / '+o
def install():
 api=previous.install()
 if getattr(api,'v184_installed',False):return api
 import importlib
 adm=importlib.import_module(api.__package__+'.pn_admin');w=api.world
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_emails184(user_id INTEGER PRIMARY KEY,email TEXT NOT NULL UNIQUE,created REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_logins184(user_id INTEGER NOT NULL,ip TEXT NOT NULL,country TEXT,device TEXT,first REAL,last REAL,count INTEGER,PRIMARY KEY(user_id,ip))')
 def seen(uid):
  ip=getattr(CUR,'ip','')
  if not uid or not ip:return
  now=time.time()
  with w.database()as db:db.execute('INSERT INTO pn_logins184 VALUES(?,?,?,?,?,?,1) ON CONFLICT(user_id,ip) DO UPDATE SET last=excluded.last,count=count+1,country=excluded.country,device=excluded.device',(uid,ip,getattr(CUR,'country',''),ua_label(getattr(CUR,'ua','')),now,now))
  STATS['logins']+=1
 NAMES={}
 def username(uid):
  hit=NAMES.get(uid)
  if hit and time.time()-hit[1]<300:return hit[0]
  with w.database()as db:r=db.execute('SELECT username FROM users WHERE id=?',(uid,)).fetchone()
  NAMES[uid]=(r['username']if r else'',time.time());return NAMES[uid][0]
 EXTRA=[['— Moderasyon (yeni) —',''],['/kick ID sebep','Oyuncuyu sunucudan atar (tekrar giriş gerekir) · Moderatör+'],['/mute ID dakika sebep','Yazılı sohbet susturma (0 = süresiz) · Moderatör+'],['/unmute ID','Sohbet susturmasını kaldır · Moderatör+'],
  ['/sesmute ID dakika sebep','Sesli sohbet susturma (0 = süresiz) · Moderatör+'],['/unsesmute ID','Ses susturmasını kaldır · Moderatör+'],['/ipban ID dakika sebep','Hesap + IP yasağı ve atma · Yönetici+'],['/unipban kullanıcıadı','IP yasağını kaldır · Yönetici+'],
  ['/ipbanlar','Aktif IP yasakları (adres gösterilmez) · Yönetici+'],['/ipgor ID','Bağlantı IP ve ülke · Baş yönetici+'],['/hesapbilgi ID','Kullanıcı adı, e-posta, kayıt, son bağlantılar · Baş yönetici+'],['/aparadagit miktar','Çevrimiçi herkese para · Yönetici+']]
 old=api.dispatch
 def dispatch(path,*a,**k):
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  if path=='/api/auth/register'and isinstance(payload,dict):
   try:email=check_email(payload.get('email'))
   except ValueError:STATS['email_refused']+=1;raise
   with w.database()as db:
    if db.execute('SELECT 1 FROM pn_emails184 WHERE email=?',(email,)).fetchone():STATS['email_refused']+=1;raise ValueError('Bu e-posta ile zaten bir hesap var.')
   out=old(path,*a,**k)
   if isinstance(out[0],dict)and out[0].get('success'):
    uid=out[0].get('user_id')
    with w.database()as db:db.execute('INSERT OR REPLACE INTO pn_emails184 VALUES(?,?,?)',(uid,email,time.time()))
    STATS['emails']+=1;seen(uid)
   return out
  if path=='/api/auth/login'and isinstance(payload,dict):
   def evasion():
    try:
     with w.database()as db:
      u=db.execute('SELECT id FROM users WHERE username=? COLLATE NOCASE',(str(payload.get('username','')),)).fetchone()
      b=u and db.execute('SELECT until FROM pn_bans WHERE user_id=? AND (until=0 OR until>?)',(u['id'],time.time())).fetchone()
      ip=getattr(CUR,'ip','')
      if b and ip:
       until=-1 if b['until']==0 else b['until']
       db.execute('INSERT OR REPLACE INTO pn_ipbans182 VALUES(?,?,?,?,?,?,?)',(previous.previous.iphash(ip),u['id'],str(payload.get('username')),until,'yasak kaçırma (otomatik)',0,time.time()))
       db.execute('INSERT INTO pn_logins184 VALUES(?,?,?,?,?,?,1) ON CONFLICT(user_id,ip) DO UPDATE SET last=excluded.last,count=count+1',(u['id'],ip,getattr(CUR,'country',''),ua_label(getattr(CUR,'ua','')),time.time(),time.time()))
       previous.previous.BANS['at']=0;STATS['evasion_ipbans']+=1
    except Exception:pass
   try:out=old(path,*a,**k)
   except ValueError:evasion();raise
   if isinstance(out[0],dict)and out[0].get('success'):seen(out[0].get('user_id'))
   else:evasion()
   return out
  if path=='/api/gta/join':
   out=old(path,*a,**k)
   try:
    p=api.PRESENCE.get(token)
    if p and out[0].get('success'):seen(p['user_id'])
   except Exception:pass
   return out
  if path=='/api/gta/roster':
   out=old(path,*a,**k)
   try:
    p=api.PRESENCE.get(token)
    if p and adm.rank(p['user_id'])>=1 and isinstance(out[0],dict):
     by_sid={v.get('server_id'):v.get('user_id')for v in list(api.PRESENCE.values())}
     for row in out[0].get('players')or[]:
      uid=by_sid.get(row.get('server_id'))
      if uid:row['username']=username(uid)
   except Exception:pass
   return out
  if path=='/api/chat/send'and isinstance(payload,dict)and isinstance(payload.get('message'),str):
   parts=payload['message'].strip().split();head=parts[0].lower()if parts else''
   if head in('/adminkomutlari','/adminkomutları','/admincommands'):
    out=old(path,dict(payload,message='/admincommands'),*a[1:],**k)
    try:
     res=out[0]
     if res.get('success')and isinstance(res.get('info'),dict):res['info']=dict(res['info'],rows=list(res['info'].get('rows')or[])+EXTRA)
    except Exception:pass
    return out
   if head=='/hesapbilgi':
    with api.LOCK:
     p=api.PRESENCE.get(token)
     if not p:raise ValueError('Oturum bulunamadı.')
     level=adm.rank(p['user_id'])
     if level<3:raise ValueError('Bu komut için baş yönetici yetkisi gerekli.')
     if len(parts)<2:raise ValueError('Kullanım: /hesapbilgi ID')
     cid=w.resolve_player_id(parts[1],api.PRESENCE)
     peer=next((v for v in api.PRESENCE.values()if v.get('char_id')==cid),None)
     with w.database()as db:
      ch=db.execute('SELECT c.name,c.surname,c.user_id,u.username,u.created_at FROM characters c JOIN users u ON u.id=c.user_id WHERE c.id=?',(cid,)).fetchone()
      if not ch:raise ValueError('Karakter bulunamadı.')
      em=db.execute('SELECT email FROM pn_emails184 WHERE user_id=?',(ch['user_id'],)).fetchone()
      pt=db.execute('SELECT seconds FROM pn_playtime117 WHERE user_id=?',(ch['user_id'],)).fetchone()
      ban=db.execute('SELECT until,reason FROM pn_bans WHERE user_id=?',(ch['user_id'],)).fetchone()
      logs=db.execute('SELECT ip,country,device,first,last,count FROM pn_logins184 WHERE user_id=? ORDER BY last DESC LIMIT 3',(ch['user_id'],)).fetchall()
      firstc=db.execute('SELECT ip,country,device,first FROM pn_logins184 WHERE user_id=? ORDER BY first ASC LIMIT 1',(ch['user_id'],)).fetchone()
      w.audit(db,p['user_id'],'hesapbilgi',dict(char_id=cid))
     with previous.previous.IPLOCK:live=previous.previous.IPS.get(next((k for k,v in api.PRESENCE.items()if v.get('char_id')==cid),''),None)
     when=lambda t:datetime.datetime.fromtimestamp(t,datetime.timezone(datetime.timedelta(hours=3))).strftime('%d.%m.%Y %H:%M')if t else'?'
     rows=[['Karakter',ch['name']+' '+ch['surname']+(' [%s]'%peer.get('server_id')if peer else'')],['Kullanıcı adı',ch['username']],['E-posta',em['email']if em else'(eski hesap, e-posta yok)'],
      ['Hesap açılışı',when(ch['created_at'])],['Oyun süresi',str(int((pt['seconds']if pt else 0)//60))+' dk (mikrofon sayacı)'],['Yasak','yok'if not ban else('süresiz'if ban['until']==0 else when(ban['until']))+' · '+str(ban['reason'])]]
     if live:rows.append(['Şu anki bağlantı',live[0]+' · '+(live[1]or'?')])
     if firstc:rows.append(['İlk bağlantı',firstc['ip']+' · '+(firstc['country']or'?')+' · '+(firstc['device']or'?')+' · '+when(firstc['first'])])
     for r in logs:rows.append(['Son bağlantı',r['ip']+' · '+(r['country']or'?')+' · '+(r['device']or'?')+' · '+when(r['last'])+' ('+str(r['count'])+' kez)'])
     STATS['hesapbilgi']+=1
     return dict(success=True,notice='%s · %s · %s'%(ch['name']+' '+ch['surname'],ch['username'],em['email']if em else'e-posta yok'),info=dict(title='Hesap bilgisi',rows=rows)),None
  return old(path,*a,**k)
 api.dispatch=dispatch;api.v184_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def do_POST(self):
  CUR.ip=self.headers.get('Cf-Connecting-Ip')or'';CUR.country=self.headers.get('Cf-Ipcountry')or'';CUR.ua=self.headers.get('User-Agent')or''
  try:return super().do_POST()
  finally:CUR.ip=CUR.country=CUR.ua=''
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v184.json':
   return self.json51(200,dict(backend_release='v184',base_release='v183',v184=STATS,v183=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v184.db'):p.error('Disposable -v184.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes184.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
