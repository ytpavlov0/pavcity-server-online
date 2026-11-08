"""134 over the live v133 chain: AFK zone.

Vespucci Beach AFK zone (radius 24 m). Standing in it on foot, alive and outside interiors earns
$150 per full minute and 1 PAV Point per 10 minutes, at most 240 minutes per character per UTC day
(pn_afk134). Inside the zone nobody can be hurt: client-reported health/armor drops are ignored, PvP hits
on a player in the zone are discarded and the sync turns on godmode for the engine. Every sync carries
afk134 (in zone, minutes today, earned today, next payment) for the HUD counter; /afk sets the GPS."""
import time,datetime,math
ZONE=dict(name='Vespucci AFK Bölgesi',x=-1270.0,y=-1520.0,z=4.4,r=24.0)
PAY=150;PP_EVERY=600;CAP=240*60;GAP=10.0
def install(api):
 if getattr(api,'features134_installed',False):return api
 w=api.world;previous=api.dispatch;seen={}
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_afk134(char_id INTEGER NOT NULL,day TEXT NOT NULL,seconds REAL NOT NULL DEFAULT 0,paid INTEGER NOT NULL DEFAULT 0,pp INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(char_id,day))')
  db.execute('CREATE TABLE IF NOT EXISTS pn_pp115(user_id INTEGER PRIMARY KEY,balance INTEGER NOT NULL DEFAULT 0 CHECK(balance>=0))')
  db.execute('CREATE TABLE IF NOT EXISTS pn_pp_ledger115(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,delta INTEGER NOT NULL,kind TEXT NOT NULL,other_user INTEGER NOT NULL DEFAULT 0,actor INTEGER NOT NULL,created REAL NOT NULL)')
 def inside(p,s):
  return bool(p and s and not p.get('dimension',0)and math.hypot(s['x']-ZONE['x'],s['y']-ZONE['y'])<=ZONE['r']and abs(s['z']-ZONE['z'])<8)
 def day():return datetime.datetime.now(datetime.timezone.utc).date().isoformat()
 def accrue(p,s):
  now=time.time();cid=p['char_id'];prev=seen.get(cid);seen[cid]=now
  if len(seen)>4096:
   for k in [k for k,t in seen.items() if now-t>120]:seen.pop(k,None)
  alive=p.get('health',200)>100 and 'dead_at'not in p;foot=not w.occupation(cid)[0]
  d=day()
  with w.database()as db:
   db.execute('INSERT OR IGNORE INTO pn_afk134(char_id,day) VALUES(?,?)',(cid,d))
   row=db.execute('SELECT * FROM pn_afk134 WHERE char_id=? AND day=?',(cid,d)).fetchone()
   secs=row['seconds'];paid=row['paid'];pp=row['pp']
   if prev and alive and foot and secs<CAP:
    secs=min(CAP,secs+min(GAP,max(0,now-prev)))
    owed=int(secs//60)-paid//PAY;owed_pp=int(secs//PP_EVERY)-pp
    if owed>0:
     db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(owed*PAY,p['user_id']));paid+=owed*PAY
     w.audit(db,p['user_id'],'afk-pay134',dict(char_id=cid,amount=owed*PAY))
    if owed_pp>0:
     db.execute('INSERT INTO pn_pp115(user_id,balance) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET balance=balance+excluded.balance',(p['user_id'],owed_pp))
     db.execute('INSERT INTO pn_pp_ledger115(user_id,delta,kind,actor,created) VALUES(?,?,?,?,?)',(p['user_id'],owed_pp,'afk134',0,now));pp+=owed_pp
    db.execute('UPDATE pn_afk134 SET seconds=?,paid=?,pp=? WHERE char_id=? AND day=?',(secs,paid,pp,cid,d))
  return dict(active=True,zone=ZONE['name'],seconds=int(secs),cap=CAP,earned=paid,pp=pp,next_pay=int(60-secs%60)if secs<CAP else None,capped=secs>=CAP,alive=alive,on_foot=foot)
 def dispatch(path,v,token):
  if path=='/api/chat/send'and isinstance(v,dict)and str(v.get('message','')).strip().lower()=='/afk':
   return dict(success=True,waypoint=dict(x=ZONE['x'],y=ZONE['y']),afk134=dict(active=False,zone=ZONE['name']),notice='%s GPS’e işlendi. Bölgede dakikada $%d ve 10 dakikada 1 PP kazanırsın (günde en fazla 4 saat); bölgede hasar almazsın.'%(ZONE['name'],PAY)),None
  if path!='/api/gta/sync'or not isinstance(v,dict):return previous(path,v,token)
  with api.LOCK:
   p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
   coords={k:v.get(k)for k in('x','y','z')}
   zone_now=p is not None and all(isinstance(coords[k],(int,float))for k in coords)and inside(p,coords)
   if zone_now:
    v=dict(v,health=max(v.get('health',200)if isinstance(v.get('health'),(int,float))else 200,p.get('health',200)),armor=max(v.get('armor',0)if isinstance(v.get('armor'),(int,float))else 0,p.get('armor',0)))
   hits=v.get('hits')
   if isinstance(hits,list)and hits:
    safe={q['char_id']for k,q in api.PRESENCE.items()if inside(q,api.GTA_STATE.get(k))}
    if safe:v=dict(v,hits=[h for h in hits if not(isinstance(h,dict)and h.get('target')in safe)])
   result,cookie=previous(path,v,token)
   if not result.get('success'):return result,cookie
   p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
   if p and inside(p,s):
    try:info=accrue(p,s)
    except Exception as e:print('[PAV134] afk',repr(e),flush=True);info=dict(active=True,zone=ZONE['name'])
    result=dict(result,afk134=info,godmode=True)
   elif p:seen.pop(p['char_id'],None)
   return result,cookie
 api.dispatch=dispatch;api.features134_installed=True;return api
