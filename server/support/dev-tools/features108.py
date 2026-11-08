"""108: job integrity, LSPD duty repairs and a log-only movement anticheat over the live v99 chain.

Jobs (wraps whatever rp.job_action is installed, including jobs69 production jobs):
 * A run remembers the life it started in. If the character died and respawned, the next
   job request cancels the run (vehicle/key returned through the stock cancel path) and
   nothing is paid.
 * When a job vehicle is on loan, a stop can only be completed with that vehicle within
   30 m, so a faster personal car cannot replace it.
Anticheat (log only — client elevators/transitions also move the player, so nothing is
snapped back yet): after every accepted /api/gta/sync the server compares the new position
with the previous one. Impossible on-foot or vehicle speed is recorded in pn_anticheat108
(rate-limited per character) and visible to staff through /api/anticheat108/recent."""
import json,math,time,secrets
BLIPS={'police':(60,3),'medical':(61,1)}
FOOT_MPS=11.0;CAR_MPS=115.0;SLACK=6.0;RECORD_EVERY=10.0
def install(api):
 if getattr(api,'features108_installed',False):return api
 import gameplay_v29.pn_roleplay as rp
 w=api.world;previous_dispatch=api.dispatch;old_action=rp.job_action;last_record={}
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_job_life108(run TEXT PRIMARY KEY,life INTEGER NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_anticheat108(id INTEGER PRIMARY KEY AUTOINCREMENT,char_id INTEGER NOT NULL,user_id INTEGER NOT NULL,at REAL NOT NULL,kind TEXT NOT NULL,detail TEXT NOT NULL)')
 def active_run(db,cid):return db.execute('SELECT * FROM pn_job_runs WHERE char_id=? AND completed IS NULL',(cid,)).fetchone()
 def loan_position(db,cid):
  loan=db.execute('SELECT vehicle_id FROM pn_job_vehicles WHERE borrower=?',(cid,)).fetchone()
  if not loan:return None
  pos=w.VEHICLE_CACHE.get(loan['vehicle_id'])
  if pos is None:
   row=db.execute('SELECT state FROM pn_vehicles WHERE id=?',(loan['vehicle_id'],)).fetchone()
   pos=json.loads(row['state'])if row else None
  return pos
 def action(db,verb,uid,cid,v,state,p):
  row=active_run(db,cid)
  if row and verb not in('start','contract-optin','cancel'):
   started=db.execute('SELECT life FROM pn_job_life108 WHERE run=?',(row['id'],)).fetchone()
   if started and started['life']!=p.get('life_id',0):
    result=old_action(db,'cancel',uid,cid,v,state,p)
    db.execute('DELETE FROM pn_job_life108 WHERE run=?',(row['id'],))
    return dict(result,notice='Görev sırasında öldüğün için iş iptal edildi; ödeme yapılmadı.',job_cancelled108=True)
   if verb=='complete-step':
    car=loan_position(db,cid)
    if car is not None and math.dist([car[k]for k in('x','y','z')],[state[k]for k in('x','y','z')])>30:raise ValueError('Görev aracını teslimat noktasına getir (30 m içinde olmalı).')
  result=old_action(db,verb,uid,cid,v,state,p)
  if verb=='start':
   new=active_run(db,cid)
   if new:db.execute('INSERT OR REPLACE INTO pn_job_life108 VALUES(?,?)',(new['id'],int(p.get('life_id',0))))
  elif verb=='cancel'and row:db.execute('DELETE FROM pn_job_life108 WHERE run=?',(row['id'],))
  return result
 rp.job_action=action
 # LSPD duty: a police leader may always carry their own badge. pn_badges85 was empty in
 # production, so every duty attempt (leader included) failed on the badge requirement.
 old_faction=rp.faction_action
 def faction_action(db,act,uid,cid,v,p,s,peers,releases):
  if act=='duty'and not p.get('faction_duty'):
   m=db.execute("SELECT m.faction_id,m.leader,f.tag FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id WHERE m.char_id=? AND f.kind='police'",(cid,)).fetchone()
   if m and m['leader']and not db.execute('SELECT 1 FROM pn_badges85 WHERE char_id=? AND faction_id=?',(cid,m['faction_id'])).fetchone():
    db.execute('INSERT INTO pn_badges85 VALUES(?,?,?,?,?)',(cid,m['faction_id'],(m['tag']or'PD')+'-'+secrets.token_hex(3).upper(),cid,time.time()))
  return old_faction(db,act,uid,cid,v,p,s,peers,releases)
 rp.faction_action=faction_action
 def judge(p,before,after,elapsed):
  if p.get('fly')or p.get('admin_duty')or p.get('godmode')or elapsed<=0:return None
  horizontal=math.dist([before['x'],before['y']],[after['x'],after['y']]);rise=after['z']-before['z']
  driving=bool(after.get('vehicle_id')or before.get('vehicle_id'))
  limit=(CAR_MPS if driving else FOOT_MPS)*min(elapsed,3.0)+SLACK
  if horizontal>limit:return dict(kind='teleport'if horizontal>150 else'speed',meters=round(horizontal,1),seconds=round(elapsed,2),limit=round(limit,1),vehicle=driving,origin=[round(before[k],1)for k in('x','y','z')],target=[round(after[k],1)for k in('x','y','z')])
  if not driving and rise>limit:return dict(kind='climb',meters=round(rise,1),seconds=round(elapsed,2),limit=round(limit,1))
  return None
 def dispatch(path,v,token):
  if path=='/api/anticheat108/recent':
   with api.LOCK:
    uid=api.authenticated61(token)
    import pn_admin
    if not uid or pn_admin.rank(uid)<1:raise ValueError('Bu kayıtlar yalnızca yetkililere açık.')
    with w.database()as db:rows=[dict(r)for r in db.execute('SELECT id,char_id,at,kind,detail FROM pn_anticheat108 ORDER BY id DESC LIMIT 100')]
   for r in rows:r['detail']=json.loads(r['detail'])
   return dict(success=True,events=rows),None
  # /duty, /pduty, /mduty (and the LSPD panel, which sends /pduty) were forwarded by duty90
  # to /api/factions/duty without the request_id pn_roleplay requires, so they always failed.
  if path=='/api/chat/send'and str(v.get('message','')).strip().lower()in('/duty','/pduty','/mduty')and not v.get('request_id'):
   return previous_dispatch(path,dict(v,request_id=secrets.token_hex(16)),token)
  if path!='/api/gta/sync':return previous_dispatch(path,v,token)
  p=api.PRESENCE.get(token);old=api.GTA_STATE.get(token)
  before=dict(old)if old else None;life=p.get('life_id',0)if p else None;dim=p.get('dimension',0)if p else None
  result,cookie=previous_dispatch(path,v,token)
  # PD/EMS desks were sent without sprite/colour (blip sprite 0) — give them station blips.
  for service in result.get('services')or[]:
   if isinstance(service,dict)and not service.get('sprite')and service.get('kind')in BLIPS:service['sprite'],service['color']=BLIPS[service['kind']]
  try:
   new=api.GTA_STATE.get(token);p=api.PRESENCE.get(token)
   if result.get('success')and before and new and p and p.get('life_id',0)==life and p.get('dimension',0)==dim and not result.get('teleport'):
    finding=judge(p,before,new,new.get('last_seen',0)-before.get('last_seen',0))
    now=time.time()
    if finding and now-last_record.get(p['char_id'],0)>=RECORD_EVERY:
     last_record[p['char_id']]=now
     with w.database()as db:db.execute('INSERT INTO pn_anticheat108(char_id,user_id,at,kind,detail)VALUES(?,?,?,?,?)',(p['char_id'],p['user_id'],now,finding['kind'],json.dumps(finding)))
  except Exception:pass  # observation must never break movement sync
  return result,cookie
 api.dispatch=dispatch;api.features108_installed=True;return api
