"""A daily account reward. The server selects and durably records every spin."""
import json,re,secrets,time
PRIZES=[500,750,1000,1500,2000,3000,5000,10000]
WEIGHTS=[250,200,180,150,100,70,40,10]

def install(api):
 if getattr(api,'casino82_installed',False):return api
 from v40_extensions.casino34 import VENUE
 w,previous=api.world,api.dispatch
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_dailywheel82(user_id INTEGER PRIMARY KEY,last_spin REAL NOT NULL,result TEXT NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_wheel_receipts82(user_id INTEGER NOT NULL,request_id TEXT NOT NULL,result TEXT NOT NULL,PRIMARY KEY(user_id,request_id))')
 def dispatch(path,payload,token):
  with api.LOCK:
   if not path.startswith('/api/casino82/'):return previous(path,payload,token)
   uid=api.authenticated61(token)
   if not uid:raise ValueError('Önce hesabına giriş yap.')
   api.require_client61(token,payload);now=time.time()
   if path.endswith('/list'):
    with api.database()as db:row=db.execute('SELECT last_spin,result FROM pn_dailywheel82 WHERE user_id=?',(uid,)).fetchone()
    return dict(success=True,money=w.wallet(uid),prizes=PRIZES,next_spin=row['last_spin']+86400 if row else 0,last=json.loads(row['result'])if row else None,server_now=now),None
   if not path.endswith('/spin'):raise ValueError('Çark işlemi bulunamadı.')
   rid=payload.get('request_id')
   if not isinstance(rid,str)or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}',rid):raise ValueError('Geçerli işlem kimliği gerekli.')
   p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
   if not p or not s:raise ValueError('Önce karakterinle şehre gir.')
   w.live(p,s)
   from restriction82 import free_actor
   free_actor(api,p,now)
   if p.get('dimension',0)or s.get('vehicle_id')or w.occupation(p['char_id'])[0]or p.get('cuffed')or p.get('restrained')or not w.near(s,VENUE,5):raise ValueError('Şans çarkı için oyun salonuna hayatta, serbest ve yaya yaklaş (5 m).')
   with api.database()as db:
    db.execute('BEGIN IMMEDIATE')
    prior=db.execute('SELECT result FROM pn_wheel_receipts82 WHERE user_id=? AND request_id=?',(uid,rid)).fetchone()
    if prior:return dict(json.loads(prior['result']),replayed=True),None
    row=db.execute('SELECT last_spin FROM pn_dailywheel82 WHERE user_id=?',(uid,)).fetchone()
    if row and now<row['last_spin']+86400:raise ValueError('Bu hesabın günlük çarkı kullanıldı. 24 saat dolunca yeniden çevirebilirsin.')
    draw=secrets.randbelow(sum(WEIGHTS));index=0
    for i,weight in enumerate(WEIGHTS):
     if draw<weight:index=i;break
     draw-=weight
    reward=PRIZES[index];db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(reward,uid));money=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()[0]
    result=dict(success=True,reward=reward,index=index,money=money,next_spin=now+86400,server_now=now,notice='Günlük çark · $'+format(reward,',')+' oyun parası kazandın.')
    db.execute('INSERT INTO pn_dailywheel82 VALUES(?,?,?) ON CONFLICT(user_id)DO UPDATE SET last_spin=excluded.last_spin,result=excluded.result',(uid,now,json.dumps(result)))
    db.execute('INSERT INTO pn_wheel_receipts82 VALUES(?,?,?)',(uid,rid,json.dumps(result)));w.audit(db,uid,'dailywheel82',dict(char_id=p['char_id'],reward=reward))
   return result,None
 api.dispatch=dispatch;api.casino82_installed=True
 return api
