"""130 over the live v129 chain: vehicle body integrity, life log, character history, rentals.

Body: a driver's vehicle sample may lower the body value but never raise it, except within 10 s of a
repair (repair_epoch change), so a modified client cannot repair its car for free.
Life log (pn_life130): every death (with the killer and weapon when a player's hit caused it) and
every player kill, written by the sync that caused it.
/api/character130/profile: the character page — playtime, money, faction and rank, properties,
vehicles, job runs, jail state, last deaths/kills and the latest account activity.
Rentals (pn_rental130): at four rental points a scooter, motorbike or small car can be rented for 30
or 60 minutes (/api/rental130/list|rent|status|return). The car is a street car (it cannot be sold)
with the renter's key; when the time is up it is removed as soon as nobody sits in it."""
import time,json,secrets,math,os
POINTS=[dict(id=1,name='Legion Kiralama',x=231.4,y=-874.6,z=30.5),dict(id=2,name='Havalimanı Kiralama',x=-1037.2,y=-2730.8,z=20.2),dict(id=3,name='Vespucci Kiralama',x=-1222.6,y=-1494.1,z=4.4),dict(id=4,name='Sandy Shores Kiralama',x=1968.5,y=3792.4,z=32.2)]
MODELS={'faggio':('Faggio scooter',250),'bati':('Bati 801',600),'sanchez':('Sanchez',450),'blista':('Blista',400),'asea':('Asea',500)}
def install(api):
 if getattr(api,'features130_installed',False):return api
 import gameplay_v29.pn_traffic as traffic,gameplay_v29.pn_roleplay as rp
 w=api.world;previous=api.dispatch;repairs={};tick={'at':0}
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_life130(id INTEGER PRIMARY KEY AUTOINCREMENT,char_id INTEGER NOT NULL,kind TEXT NOT NULL,other_char INTEGER,other_name TEXT,weapon INTEGER,x REAL,y REAL,created REAL NOT NULL)')
  db.execute('CREATE INDEX IF NOT EXISTS pn_life130_char ON pn_life130(char_id,created)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_rental130(vehicle_id INTEGER PRIMARY KEY,char_id INTEGER NOT NULL,model TEXT NOT NULL,point INTEGER NOT NULL,price INTEGER NOT NULL,started REAL NOT NULL,until REAL NOT NULL,ended REAL)')
 def me(token):
  uid=api.authenticated61(token);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
  if not uid or not p or not s:raise ValueError('Önce karakterinle şehre gir.')
  return uid,p,s
 def life(db,cid,kind,other=None,weapon=None,pos=None):
  db.execute('INSERT INTO pn_life130(char_id,kind,other_char,other_name,weapon,x,y,created)VALUES(?,?,?,?,?,?,?,?)',(cid,kind,other and other.get('char_id'),other and other.get('name'),weapon,pos and round(pos.get('x',0),1),pos and round(pos.get('y',0),1),time.time()))
 # ---- rentals ----
 def active_rental(db,cid):return db.execute('SELECT * FROM pn_rental130 WHERE char_id=? AND ended IS NULL',(cid,)).fetchone()
 def end_rental(db,r):
  vid=r['vehicle_id']
  db.execute('DELETE FROM pn_vehicles WHERE id=?',(vid,));db.execute('DELETE FROM pn_vehicle_access WHERE vehicle_id=?',(vid,))
  db.execute('UPDATE pn_rental130 SET ended=? WHERE vehicle_id=?',(time.time(),vid))
  w.VEHICLE_CACHE.pop(vid,None);getattr(w,'SAVED_AT',{}).pop(vid,None)
 def housekeeping():
  now=time.time()
  if now-tick['at']<float(os.environ.get('PAV130_TICK','20')):return
  tick['at']=now;occupied={vid for vid,seat in w.SEATS}
  with w.database()as db:
   for r in db.execute('SELECT * FROM pn_rental130 WHERE ended IS NULL').fetchall():
    if r['until']<=now and r['vehicle_id']not in occupied:end_rental(db,r);w.audit(db,0,'rental-end130',dict(vehicle=r['vehicle_id'],char_id=r['char_id']))
    elif r['until']>now:db.execute('UPDATE pn_vehicles SET updated=? WHERE id=?',(now,r['vehicle_id']))
 def rental(action,token,v):
  uid,p,s=me(token);cid=p['char_id']
  if action=='list':
   with w.database()as db:r=active_rental(db,cid)
   return dict(success=True,points=POINTS,models=[dict(model=k,name=n,price30=c)for k,(n,c)in MODELS.items()],active=dict(r)if r else None,now=time.time())
  if action=='status':
   with w.database()as db:r=active_rental(db,cid)
   return dict(success=True,active=dict(r)if r else None,now=time.time())
  if action=='return':
   with w.database()as db:
    r=active_rental(db,cid)
    if not r:raise ValueError('Kiralık aracın yok.')
    if any(vid==r['vehicle_id']for vid,seat in w.SEATS):raise ValueError('Önce araçtan herkes insin.')
    end_rental(db,r);w.audit(db,uid,'rental-return130',dict(vehicle=r['vehicle_id']))
   return dict(success=True,removed=r['vehicle_id'],notice='Kiralık araç teslim edildi.')
  if action!='rent':raise ValueError('Kiralama işlemi bulunamadı.')
  model=v.get('model');minutes=v.get('minutes',30)
  if model not in MODELS:raise ValueError('Bu araç kiralanamıyor.')
  if minutes not in(30,60):raise ValueError('Süre 30 ya da 60 dakika olmalı.')
  if p.get('dimension',0)or w.occupation(cid)[0]:raise ValueError('Kiralama için dışarıda ve yaya ol.')
  point=next((q for q in POINTS if math.dist([s['x'],s['y']],[q['x'],q['y']])<8 and abs(s['z']-q['z'])<6),None)
  if not point:raise ValueError('Bir kiralama noktasına yaklaş (/kirala ile en yakını GPS’e işlenir).')
  price=MODELS[model][1]*(minutes//30)
  with w.database()as db:
   if active_rental(db,cid):raise ValueError('Zaten kiralık bir aracın var. /kiraiade ile teslim et.')
  position=dict(**w.spawn_location(s,model),heading=s['heading'],rx=0,ry=0,rz=s['heading'],vx=0,vy=0,vz=0,body=1000,engine=False,fuel=100,km=0,seats=2)
  now=time.time()
  with w.database()as db:
   if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(price,uid,price)).rowcount:raise ValueError('Yeterli paran yok ($%s).'%f'{price:,}'.replace(',','.'))
   plate='KIRA'+secrets.token_hex(2).upper()
   vid=db.execute('INSERT INTO pn_vehicles(owner,model,plate,locked,state,updated) VALUES(0,?,?,0,?,?)',(model,plate,json.dumps(position),now)).lastrowid
   traffic.grant_key(db,vid,cid)
   db.execute('INSERT INTO pn_rental130(vehicle_id,char_id,model,point,price,started,until)VALUES(?,?,?,?,?,?,?)',(vid,cid,model,point['id'],price,now,now+minutes*60))
   w.audit(db,uid,'rental130',dict(vehicle=vid,model=model,minutes=minutes,price=price,point=point['id']))
  return dict(success=True,vehicle=w.public(w.vehicle(vid)),money=w.wallet(uid),until=now+minutes*60,now=now,notice='%s %d dakikalığına kiralandı · %s · $%s'%(MODELS[model][0],minutes,plate,f'{price:,}'.replace(',','.')))
 # ---- character page ----
 def profile(token):
  uid,p,s=me(token);cid=p['char_id']
  with w.database()as db:
   q=lambda sql,*a:db.execute(sql,a).fetchall()
   one=lambda sql,*a:db.execute(sql,a).fetchone()
   ch=one('SELECT * FROM characters WHERE id=?',cid)
   play=one('SELECT seconds FROM pn_playtime117 WHERE user_id=?',uid)if one("SELECT 1 FROM sqlite_master WHERE name='pn_playtime117'")else None
   faction=one("SELECT f.name,f.kind,m.* FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id WHERE m.char_id=?",cid)
   rank=None
   if faction:
    rank=one('SELECT title AS name FROM pn_faction_ranks WHERE faction_id=? AND rank=?',faction['faction_id'],faction['rank'])
   props=[dict(r)for r in q('SELECT id,name,kind,price FROM pn_properties WHERE owner=?',cid)]
   cars=[dict(id=r['id'],model=r['model'],plate=r['plate'])for r in q('SELECT id,model,plate FROM pn_vehicles WHERE owner=? ORDER BY id',cid)]
   jobs=[dict(r)for r in q('SELECT job,completed,paid,started FROM pn_job_runs WHERE char_id=? ORDER BY id DESC LIMIT 12',cid)]
   done=one('SELECT COUNT(*) n,COALESCE(SUM(paid),0) s FROM pn_job_runs WHERE char_id=? AND completed IS NOT NULL AND completed>0',cid)
   jail=one('SELECT until,reason FROM pn_jail WHERE char_id=?',cid)
   events=[dict(r)for r in q('SELECT kind,other_name,weapon,created FROM pn_life130 WHERE char_id=? ORDER BY id DESC LIMIT 20',cid)]
   tally={k:one('SELECT COUNT(*) n FROM pn_life130 WHERE char_id=? AND kind=?',cid,k)['n']for k in('death','kill')}
   activity=[dict(action=r['action'],created=r['created'])for r in q("SELECT action,created FROM pn_audit WHERE user_id=? AND action NOT LIKE '/%' ORDER BY id DESC LIMIT 15",uid)]
   bank=one('SELECT balance FROM pn_bank WHERE user_id=?',uid)
  return dict(success=True,name=p['name'],char_id=cid,created=(ch['created_at']if ch else None),playtime=(play['seconds']if play else 0),cash=w.wallet(uid),bank=(bank['balance']if bank else 0),
   faction=(dict(name=faction['name'],kind=faction['kind'],rank=(rank['name']if rank else faction['rank']))if faction else None),properties=props,vehicles=cars,jobs=jobs,jobs_done=done['n'],jobs_paid=done['s'],
   jail=(dict(until=jail['until'],reason=jail['reason'])if jail and jail['until']>time.time()else None),life=events,deaths=tally['death'],kills=tally['kill'],activity=activity,health=p.get('health',200),armor=p.get('armor',0),hunger=p.get('hunger',100),thirst=p.get('thirst',100))
 def dispatch(path,v,token):
  v=v if isinstance(v,dict)else{}
  if path.startswith('/api/rental130/'):
   with api.LOCK:return rental(path.rsplit('/',1)[-1],token,v),None
  if path=='/api/character130/profile':
   with api.LOCK:return profile(token),None
  if path=='/api/chat/send':
   parts=str(v.get('message','')).strip().split();cmd=parts[0].lower()if parts else''
   if cmd in('/kirala','/kiraiade','/kiradurum'):
    with api.LOCK:
     uid,p,s=me(token)
     if cmd=='/kiraiade':return rental('return',token,{}),None
     if cmd=='/kiradurum':
      r=rental('status',token,{})['active']
      if not r:return dict(success=True,notice='Kiralık aracın yok.'),None
      left=max(0,int(r['until']-time.time()));return dict(success=True,notice='%s · kalan %d:%02d'%(MODELS[r['model']][0],left//60,left%60)),None
     near=min(POINTS,key=lambda q:math.dist([s['x'],s['y']],[q['x'],q['y']]))
     return dict(success=True,waypoint=dict(x=near['x'],y=near['y']),rental130=True,notice='En yakın kiralama: %s · GPS işlendi. Yanına gidince menü açılır.'%near['name']),None
  if path!='/api/gta/sync':return previous(path,v,token)
  with api.LOCK:
   try:housekeeping()
   except Exception as e:print('[PAV130] rental housekeeping',repr(e),flush=True)
   p=api.PRESENCE.get(token)
   sample=v.get('vehicle_sample')
   if p and isinstance(sample,dict)and type(sample.get('id'))is int and isinstance(sample.get('body'),(int,float)):
    vid=sample['id'];cur=w.VEHICLE_CACHE.get(vid)
    if cur is None:
     row=w.vehicle(vid);cur=json.loads(row['state'])if row else None
    if cur is not None:
     ep=cur.get('repair_epoch',0);seen=repairs.get(vid)
     if not seen or seen[0]!=ep:repairs[vid]=seen=(ep,time.time()if seen else 0)
     if len(repairs)>4096:repairs.clear()
     if sample['body']>cur.get('body',1000)+1 and time.time()-seen[1]>10:
      v=dict(v,vehicle_sample=dict(sample,body=cur.get('body',1000)))
   hits=v.get('hits')if isinstance(v.get('hits'),list)else[]
   wanted={h.get('target')for h in hits if isinstance(h,dict)}
   before={k:(q,'dead_at'in q)for k,q in api.PRESENCE.items()if q.get('char_id')in wanted and k!=token}
   alive=bool(p and 'dead_at'not in p)
   result,cookie=previous(path,v,token)
   if not result.get('success'):return result,cookie
   try:
    p=api.PRESENCE.get(token);killed=[]
    for k,(q,was) in before.items():
     if not was and 'dead_at'in q:killed.append(q)
    if killed or(p and alive and 'dead_at'in p):
     with w.database()as db:
      for q in killed:
       life(db,p['char_id'],'kill',q,v.get('weapon'),api.GTA_STATE.get(token));life(db,q['char_id'],'death',p,v.get('weapon'),None);q['life130_logged']=time.time()
      if p and alive and 'dead_at'in p and time.time()-p.get('life130_logged',0)>5:life(db,p['char_id'],'death',None,None,api.GTA_STATE.get(token))
   except Exception as e:print('[PAV130] life log',repr(e),flush=True)
   return result,cookie
 api.dispatch=dispatch;api.features130_installed=True;return api
