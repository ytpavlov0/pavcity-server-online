"""133 over the live v132 chain: city events (2x job pay and friends).

/etkinlik 2x 60 [not]   staff (rank 3+) starts a job-pay event: 1.5x/2x/3x for 10–240 minutes
/etkinlik               anyone: shows the running event
/etkinlikbitir          staff ends it early
While an event runs every finished job run pays the bonus on top (pn_events133, audited as
job-event133), and every sync carries event133={mult,ends,note} so the HUD shows a countdown chip."""
import time,re
MULTS={'1.5x':1.5,'2x':2.0,'3x':3.0}
def install(api):
 if getattr(api,'features133_installed',False):return api
 import gameplay_v29.pn_admin as staff
 w=api.world;previous=api.dispatch;cache={'at':0,'row':None}
 with w.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_events133(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,mult REAL NOT NULL,starts REAL NOT NULL,ends REAL NOT NULL,by_user INTEGER NOT NULL,note TEXT NOT NULL DEFAULT "",ended REAL)')
 def current():
  now=time.time()
  if now-cache['at']>5:
   with w.database()as db:cache['row']=db.execute('SELECT * FROM pn_events133 WHERE ended IS NULL AND starts<=? AND ends>? ORDER BY id DESC LIMIT 1',(now,now)).fetchone()
   cache['at']=now
  r=cache['row'];return r if r and r['ends']>now else None
 def view(r):return dict(id=r['id'],kind=r['kind'],mult=r['mult'],ends=r['ends'],note=r['note'],now=time.time())if r else None
 def command(cmd,args,token):
  uid=api.authenticated61(token);p=api.PRESENCE.get(token)
  if not uid or not p:raise ValueError('Önce karakterinle şehre gir.')
  if cmd=='/etkinlik'and not args:
   r=current()
   if not r:return dict(success=True,notice='Şu an etkinlik yok.')
   left=int(r['ends']-time.time());return dict(success=True,event133=view(r),notice='Etkinlik: %s meslek kazancı · kalan %d:%02d%s'%(('%g'%r['mult'])+'x',left//60,left%60,(' · '+r['note'])if r['note']else''))
  if staff.rank(uid)<3:raise ValueError('Etkinlik yönetimi yetkili (3+) işidir.')
  if cmd=='/etkinlikbitir':
   r=current()
   if not r:raise ValueError('Çalışan etkinlik yok.')
   with w.database()as db:db.execute('UPDATE pn_events133 SET ended=? WHERE id=?',(time.time(),r['id']));w.audit(db,uid,'event-end133',dict(id=r['id']))
   cache['at']=0;return dict(success=True,notice='Etkinlik bitirildi.')
  if len(args)<2 or args[0].lower()not in MULTS or not args[1].isdigit()or not 10<=int(args[1])<=240:raise ValueError('Kullanım: /etkinlik 2x 60 [not] · çarpan 1.5x/2x/3x · süre 10–240 dk')
  if current():raise ValueError('Zaten bir etkinlik çalışıyor (/etkinlikbitir).')
  mult=MULTS[args[0].lower()];minutes=int(args[1]);note=re.sub(r'\s+',' ',' '.join(args[2:]))[:80];now=time.time()
  with w.database()as db:
   eid=db.execute('INSERT INTO pn_events133(kind,mult,starts,ends,by_user,note)VALUES(?,?,?,?,?,?)',('jobs',mult,now,now+minutes*60,uid,note)).lastrowid
   w.audit(db,uid,'event-start133',dict(id=eid,mult=mult,minutes=minutes))
  cache['at']=0;return dict(success=True,notice='Etkinlik başladı: %gx meslek kazancı · %d dakika.'%(mult,minutes))
 def dispatch(path,v,token):
  if path=='/api/chat/send'and isinstance(v,dict):
   parts=str(v.get('message','')).strip().split();cmd=parts[0].lower()if parts else''
   if cmd in('/etkinlik','/etkinlikbitir'):
    with api.LOCK:return command(cmd,parts[1:],token),None
  if '/jobs/'in path:
   with api.LOCK:
    p=api.PRESENCE.get(token);ev=current()if p else None
    if not ev:return previous(path,v,token)
    with w.database()as db:before=db.execute('SELECT COALESCE(MAX(id),0) FROM pn_job_runs WHERE char_id=? AND completed IS NOT NULL',(p['char_id'],)).fetchone()[0]
    result,cookie=previous(path,v,token)
    if result.get('success'):
     with w.database()as db:
      run=db.execute('SELECT id,job,paid FROM pn_job_runs WHERE char_id=? AND completed IS NOT NULL AND id>? AND paid>0 ORDER BY id DESC LIMIT 1',(p['char_id'],before)).fetchone()
      if run:
       bonus=int(round(run['paid']*(ev['mult']-1)))
       if bonus>0:
        db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(bonus,p['user_id']))
        w.audit(db,p['user_id'],'job-event133',dict(run=run['id'],job=run['job'],bonus=bonus,event=ev['id']))
        result=dict(result,money=w.wallet(p['user_id']),notice=str(result.get('notice',''))+' · Etkinlik bonusu +$%s (%gx)'%(f'{bonus:,}'.replace(',','.'),ev['mult']))
    return result,cookie
  result,cookie=previous(path,v,token)
  if path=='/api/gta/sync'and result.get('success'):
   ev=current()
   if ev:result=dict(result,event133=view(ev))
  return result,cookie
 api.dispatch=dispatch;api.features133_installed=True;return api
