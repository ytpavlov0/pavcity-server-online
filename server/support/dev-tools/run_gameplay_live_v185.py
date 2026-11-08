"""185 backend: 184 + device bans and ban-evasion hints (device185.js sends the pav_dev cookie: device id, fingerprint,
time zone, language).
- Every register / login / join records the device (id, fingerprint, time zone, language, Cloudflare country) per
  account in pn_devices185.
- /cihazban ID dakika sebep (rank >= 2): /ipban (account + IP + kick) and every device id the account used is banned
  (pn_devbans185, fingerprints kept with it); any API request from a banned device id gets 403 - VPN or a new account
  do not help. /uncihazban kullaniciadi lifts the device bans of that account.
- Hints for staff (pn_flags185, /supheliler, rank >= 1): VPN suspicion (browser time zone Turkey or Turkish language
  while the IP country is not TR, or Tor), a new login whose fingerprint matches a banned device, and a device id
  shared with another account. /hesapbilgi also lists the account's devices and the other accounts on the same
  device or fingerprint. Fingerprints only flag (shared or identical PCs exist); device ids ban."""
from pathlib import Path
import sys,time,re,json,base64,threading
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v184 as previous
host=previous.host;API=previous.API;CUR=previous.CUR
STATS={'devices':0,'devbans':0,'blocked':0,'flags':0}
DEVBANS={'at':0.0,'set':set()}
HEX=re.compile(r'^[0-9a-f]{32}$')
def parse_dev(cookie):
 for part in(cookie or'').split(';'):
  k,_,v=part.strip().partition('=')
  if k=='pav_dev'and v:
   try:
    d=json.loads(base64.urlsafe_b64decode(v+'='*(-len(v)%4)).decode())
    did=str(d.get('d',''));fp=str(d.get('f',''))
    return(did if HEX.match(did)else'',fp if HEX.match(fp)else'',str(d.get('z',''))[:40],str(d.get('l',''))[:12])
   except Exception:return('','','','')
 return('','','','')
def vpn_suspect(country,tz,lang):
 if country=='T1':return 'Tor ağı'
 if country and country not in('TR','XX')and(tz=='Europe/Istanbul'or lang.lower().startswith('tr')):return 'tarayıcı Türkiye (%s/%s) ama IP %s'%(tz or'?',lang or'?',country)
 return''
def install():
 api=previous.install()
 if getattr(api,'v185_installed',False):return api
 import importlib
 adm=importlib.import_module(api.__package__+'.pn_admin');w=api.world
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_devices185(user_id INTEGER NOT NULL,did TEXT NOT NULL,fp TEXT,tz TEXT,lang TEXT,country TEXT,first REAL,last REAL,count INTEGER,PRIMARY KEY(user_id,did))')
  db.execute('CREATE TABLE IF NOT EXISTS pn_devbans185(did TEXT PRIMARY KEY,fp TEXT,user_id INTEGER,until REAL NOT NULL,reason TEXT,actor INTEGER,created REAL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_flags185(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,kind TEXT,detail TEXT,at REAL)')
 def banned_dids():
  now=time.time()
  if now-DEVBANS['at']>=5:
   with w.database()as db:DEVBANS['set']={r['did']for r in db.execute('SELECT did FROM pn_devbans185 WHERE until=-1 OR until>?',(now,))};DEVBANS['at']=now
  return DEVBANS['set']
 api.devbanned185=lambda did:bool(did)and did in banned_dids()
 def flag(db,uid,kind,detail):
  if db.execute('SELECT 1 FROM pn_flags185 WHERE user_id=? AND kind=? AND at>?',(uid,kind,time.time()-21600)).fetchone():return
  db.execute('INSERT INTO pn_flags185(user_id,kind,detail,at) VALUES(?,?,?,?)',(uid,kind,detail[:300],time.time()));STATS['flags']+=1
 def seen(uid):
  did=getattr(CUR,'did','');fp=getattr(CUR,'fp','');tz=getattr(CUR,'tz','');lang=getattr(CUR,'lang','');country=getattr(CUR,'country','')
  if not uid or not did:return
  now=time.time()
  with w.database()as db:
   db.execute('INSERT INTO pn_devices185 VALUES(?,?,?,?,?,?,?,?,1) ON CONFLICT(user_id,did) DO UPDATE SET fp=excluded.fp,tz=excluded.tz,lang=excluded.lang,country=excluded.country,last=excluded.last,count=count+1',(uid,did,fp,tz,lang,country,now,now))
   STATS['devices']+=1
   v=vpn_suspect(country,tz,lang)
   if v:flag(db,uid,'vpn',v)
   if fp:
    hit=db.execute('SELECT b.user_id,u.username FROM pn_devbans185 b LEFT JOIN users u ON u.id=b.user_id WHERE b.fp=? AND (b.until=-1 OR b.until>?) AND b.user_id<>? LIMIT 1',(fp,now,uid)).fetchone()
    if hit:flag(db,uid,'fp_match','yasaklı %s ile aynı cihaz parmak izi'%(hit['username']or hit['user_id']))
   other=db.execute('SELECT u.username FROM pn_devices185 d JOIN users u ON u.id=d.user_id WHERE d.did=? AND d.user_id<>? LIMIT 3',(did,uid)).fetchall()
   if other:flag(db,uid,'did_shared','aynı cihaz: '+', '.join(r['username']for r in other))
 def who(cid):
  key,peer=next(((k,v)for k,v in api.PRESENCE.items()if v.get('char_id')==cid),(None,None));return key,peer
 old=api.dispatch
 def dispatch(path,*a,**k):
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  if path in('/api/auth/register','/api/auth/login'):
   out=old(path,*a,**k)
   try:
    if isinstance(out[0],dict)and out[0].get('success'):seen(out[0].get('user_id'))
   except Exception:pass
   return out
  if path=='/api/gta/join':
   out=old(path,*a,**k)
   try:
    p=api.PRESENCE.get(token)
    if p and out[0].get('success'):seen(p['user_id'])
   except Exception:pass
   return out
  if path=='/api/chat/send'and isinstance(payload,dict)and isinstance(payload.get('message'),str):
   parts=payload['message'].strip().split();head=parts[0].lower()if parts else''
   if head in('/cihazban','/uncihazban','/supheliler','/şüpheliler'):
    with api.LOCK:
     p=api.PRESENCE.get(token)
     if not p:raise ValueError('Oturum bulunamadı.')
     level=adm.rank(p['user_id'])
     if head in('/supheliler','/şüpheliler'):
      if level<1:raise ValueError('Bu komut için yetkin yok.')
      with w.database()as db:rows=db.execute('SELECT f.kind,f.detail,f.at,u.username FROM pn_flags185 f LEFT JOIN users u ON u.id=f.user_id ORDER BY f.id DESC LIMIT 15').fetchall()
      if not rows:return dict(success=True,notice='Şüpheli kayıt yok.'),None
      names={'vpn':'VPN şüphesi','fp_match':'Yasaklı cihaz parmak izi','did_shared':'Ortak cihaz'}
      return dict(success=True,notice='%d şüpheli kayıt (en yenisi: %s).'%(len(rows),rows[0]['username']),info=dict(title='Şüpheli bağlantılar',rows=[[str(r['username']),names.get(r['kind'],r['kind'])+' · '+str(r['detail'])+' · '+time.strftime('%d.%m %H:%M',time.gmtime(r['at']+10800))]for r in rows])),None
     if level<2:raise ValueError('Bu komut için yönetici yetkisi gerekli.')
     if head=='/uncihazban':
      if len(parts)<2:raise ValueError('Kullanım: /uncihazban kullanıcıadı')
      with w.database()as db:
       u=db.execute('SELECT id FROM users WHERE username=? COLLATE NOCASE',(parts[1],)).fetchone()
       if not u:raise ValueError('Hesap bulunamadı.')
       n=db.execute('DELETE FROM pn_devbans185 WHERE user_id=?',(u['id'],)).rowcount;w.audit(db,p['user_id'],'uncihazban',dict(user_id=u['id']))
      DEVBANS['at']=0;return dict(success=True,notice='%d cihaz yasağı kaldırıldı (IP: /unipban, hesap: /unban).'%n),None
     if len(parts)<4 or not parts[2].isdigit():raise ValueError('Kullanım: /cihazban ID dakika sebep (0 = süresiz)')
     cid=w.resolve_player_id(parts[1],api.PRESENCE);key,peer=who(cid)
     if not peer:raise ValueError('Oyuncu bağlı değil.')
     uid=peer['user_id'];minutes=int(parts[2]);reason=' '.join(parts[3:])[:200];until=-1 if minutes==0 else time.time()+minutes*60
     with w.database()as db:devs=db.execute('SELECT did,fp FROM pn_devices185 WHERE user_id=?',(uid,)).fetchall()
     live_did=None
     res,cookie=old(path,dict(payload,message='/ipban %s %s %s'%(parts[1],parts[2],reason)),*a[1:],**k)
     if not res.get('success'):return res,cookie
     with w.database()as db:
      for d in devs:db.execute('INSERT OR REPLACE INTO pn_devbans185 VALUES(?,?,?,?,?,?,?)',(d['did'],d['fp'],uid,until,reason,p['user_id'],time.time()))
      w.audit(db,p['user_id'],'cihazban',dict(user_id=uid,devices=len(devs),minutes=minutes))
     DEVBANS['at']=0;STATS['devbans']+=1
     return dict(res,notice=res.get('notice','')+' · %d cihaz yasaklandı.'%len(devs)),cookie
   if head=='/hesapbilgi':
    out=old(path,*a,**k)
    try:
     res=out[0]
     if res.get('success')and isinstance(res.get('info'),dict):
      cid=w.resolve_player_id(parts[1],api.PRESENCE)
      with w.database()as db:
       uid=db.execute('SELECT user_id FROM characters WHERE id=?',(cid,)).fetchone()['user_id']
       devs=db.execute('SELECT did,fp,tz,lang,country,last FROM pn_devices185 WHERE user_id=? ORDER BY last DESC',(uid,)).fetchall()
       same=db.execute('SELECT DISTINCT u.username FROM pn_devices185 d JOIN users u ON u.id=d.user_id WHERE d.user_id<>? AND (d.did IN (SELECT did FROM pn_devices185 WHERE user_id=?) OR (d.fp<>\'\' AND d.fp IN (SELECT fp FROM pn_devices185 WHERE user_id=? AND fp<>\'\'))) LIMIT 10',(uid,uid,uid)).fetchall()
       flags=db.execute('SELECT kind,detail FROM pn_flags185 WHERE user_id=? ORDER BY id DESC LIMIT 3',(uid,)).fetchall()
       dban=db.execute('SELECT COUNT(*) n FROM pn_devbans185 WHERE user_id=? AND (until=-1 OR until>?)',(uid,time.time())).fetchone()['n']
      rows=list(res['info'].get('rows')or[])
      rows.append(['Cihaz sayısı',str(len(devs))+(' · %d cihaz yasaklı'%dban if dban else'')])
      for d in devs[:2]:rows.append(['Cihaz',d['did'][:8]+'… · '+(d['tz']or'?')+' · '+(d['lang']or'?')+' · IP ülkesi '+(d['country']or'?')])
      rows.append(['Aynı cihazdaki hesaplar',', '.join(r['username']for r in same)or'yok'])
      for f in flags:rows.append(['Uyarı',f['kind']+' · '+f['detail']])
      res['info']=dict(res['info'],rows=rows)
    except Exception:pass
    return out
   if head in('/adminkomutlari','/adminkomutları','/admincommands'):
    out=old(path,*a,**k)
    try:
     res=out[0]
     if res.get('success')and isinstance(res.get('info'),dict):res['info']=dict(res['info'],rows=list(res['info'].get('rows')or[])+[['/cihazban ID dakika sebep','Hesap + IP + cihaz yasağı (VPN ile de giremez) · Yönetici+'],['/uncihazban kullanıcıadı','Cihaz yasağını kaldır · Yönetici+'],['/supheliler','VPN / yasaklı cihaz / ortak cihaz uyarıları · Moderatör+']])
    except Exception:pass
    return out
  return old(path,*a,**k)
 api.dispatch=dispatch;api.v185_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def do_POST(self):
  CUR.did,CUR.fp,CUR.tz,CUR.lang=parse_dev(self.headers.get('Cookie'))
  try:
   api=API[0]
   if CUR.did and urlsplit(self.path).path.startswith('/api/')and getattr(api,'devbanned185',None)and api.devbanned185(CUR.did):
    STATS['blocked']+=1;self.close_connection=True;self.json51(403,dict(success=False,error='Bu cihaz sunucudan yasaklandı.'));return
   return super().do_POST()
  finally:CUR.did=CUR.fp=CUR.tz=CUR.lang=''
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v185.json':
   return self.json51(200,dict(backend_release='v185',base_release='v184',v185=STATS,v184=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v185.db'):p.error('Disposable -v185.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes185.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
