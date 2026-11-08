"""117 over the live v116 chain.

Sync errors: the host turned every exception in /api/gta/sync into a bare 500 without logging
(26% of syncs failed on 28–29 Oct, invisible). Failures are now written to the server log with
their traceback (rate-limited per message) and re-raised unchanged.
Jobs: interior enter/exit (pn_city.teleport) bumps life_id, which features108 read as a death and
cancelled the run. A life change between two syncs where the player was alive in both is a
teleport, so the active run's recorded life follows it; a real death (dead sync, then respawn)
still cancels.

Microphone: new players earn it with 15 minutes of play.

Play time is counted on the server from accepted /api/gta/sync calls (gaps over 10 s do not
count) and kept per account in pn_playtime117, so the client cannot shorten it. Until an account
has 900 s, /api/gta/voice is refused (text RP only) and every sync carries
voice117={locked,remaining,required} for the countdown. Staff are exempt. Accounts that existed
before 117 was installed start unlocked."""
import os,time,traceback
REQUIRED=int(os.environ.get('PAV117_MIC_SECONDS','900'));GAP=10.0;FLUSH=15.0  # fixture tests shorten REQUIRED
def install(api):
 if getattr(api,'features117_installed',False):return api
 import gameplay_v29.pn_admin as staff
 w=api.world;previous=api.dispatch;book={};errors={};lives={}
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_playtime117(user_id INTEGER PRIMARY KEY,seconds REAL NOT NULL DEFAULT 0,updated REAL NOT NULL DEFAULT 0)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_meta117(key TEXT PRIMARY KEY,value REAL NOT NULL)')
  db.execute("INSERT OR IGNORE INTO pn_meta117 VALUES('installed',?)",(time.time(),))
  installed=db.execute("SELECT value FROM pn_meta117 WHERE key='installed'").fetchone()[0]
 def entry(uid):
  e=book.get(uid)
  if e is None:
   with w.database()as db:
    row=db.execute('SELECT seconds FROM pn_playtime117 WHERE user_id=?',(uid,)).fetchone()
    if row is None:
     made=db.execute('SELECT created_at FROM users WHERE id=?',(uid,)).fetchone()
     seconds=float(REQUIRED)if made and made[0]<installed else 0.0
     db.execute('INSERT OR IGNORE INTO pn_playtime117 VALUES(?,?,?)',(uid,seconds,time.time()))
    else:seconds=float(row[0])
   e=book[uid]=dict(s=seconds,last=0.0,flushed=time.time(),staff=(0,0.0))
  return e
 def flush(uid,e,now):
  with w.database()as db:db.execute('UPDATE pn_playtime117 SET seconds=?,updated=? WHERE user_id=?',(e['s'],now,uid))
  e['flushed']=now
 def is_staff(uid,e,now):
  if now-e['staff'][1]>30:e['staff']=(staff.rank(uid),now)
  return e['staff'][0]>=1
 def status(uid,e,now):
  if e['s']>=REQUIRED or is_staff(uid,e,now):return dict(locked=False,remaining=0,required=REQUIRED)
  return dict(locked=True,remaining=int(REQUIRED-e['s']+.999),required=REQUIRED)
 def dispatch(path,v,token):
  if path=='/api/gta/voice':
   with api.LOCK:
    p=api.PRESENCE.get(token)
    if p:
     now=time.time();e=entry(p['user_id']);st=status(p['user_id'],e,now)
     if st['locked']:m,s=divmod(st['remaining'],60);raise ValueError(f'Mikrofon {m}:{s:02d} sonra açılır. Şimdilik yazılı RP (T).')
   return previous(path,v,token)
  if path!='/api/gta/sync':return previous(path,v,token)
  try:result,cookie=previous(path,v,token)
  except ValueError:raise
  except Exception as error:
   key=type(error).__name__+':'+str(error)[:160];now=time.time()
   if now-errors.get(key,0)>10:
    errors[key]=now
    print('[PAV117] sync failure',key,'\n'+traceback.format_exc(limit=12),flush=True)
   raise
  if result.get('success'):
   with api.LOCK:
    p=api.PRESENCE.get(token)
    if p:
     try:
      now=time.time();e=entry(p['user_id'])
      life,alive=p.get('life_id',0),p.get('health',200)>100;was=lives.get(p['char_id'])
      if was and was[0]!=life and was[1] and alive:
       with w.database()as db:db.execute('UPDATE pn_job_life108 SET life=? WHERE run IN(SELECT id FROM pn_job_runs WHERE char_id=? AND completed IS NULL)',(life,p['char_id']))
      lives[p['char_id']]=(life,alive)
      if e['last'] and 0<now-e['last']<=GAP and e['s']<REQUIRED:
       before=e['s'];e['s']=min(float(REQUIRED),e['s']+(now-e['last']))
       if e['s']>=REQUIRED>before or now-e['flushed']>=FLUSH:flush(p['user_id'],e,now)
      e['last']=now;result=dict(result,voice117=status(p['user_id'],e,now))
     except Exception as error:  # bookkeeping must never fail a movement sync
      key='post:'+type(error).__name__+':'+str(error)[:160]
      if time.time()-errors.get(key,0)>10:
       errors[key]=time.time();print('[PAV117] sync bookkeeping',key,'\n'+traceback.format_exc(limit=12),flush=True)
  return result,cookie
 api.dispatch=dispatch;api.features117_installed=True;api.features117_book=book;return api
