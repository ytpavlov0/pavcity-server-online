"""192: crime and rescue systems over the live chain (gameplay_v29 session API).

Chop shop (/api/chop192/start|strip|sell|crush|cancel)
  A car that is not the player's own (street car or another player's stolen car) parked within 20 m of the chop
  spot is stripped part by part: the player kneels at a door or wheel (6 s animation on the client), carries the
  part to the counter (the chop spot) and sells it ($350 door, $250 wheel). With at least 4 parts sold the hull is
  pressed for $900 (street car) or $1,200 (a player's car). A street car is deleted; a player's car goes to the city
  impound (garage 4) marked stolen and the thieves' keys are removed. One chop job per player per 8 minutes.
  Starting a chop alerts on-duty police (pn_dispatch178 "Hurdacı") and gives the player wanted level 2 (NPC police).
Wanted / arrest (/api/police192/npc-arrest)
  The server keeps who committed a crime in the last 10 minutes (chop, hotwiring or lockpicking another player's car:
  wanted level 1). The page sets that level in the engine once (NPC police chase; hiding and waiting it out works as
  in GTA). When NPC police arrest the player the page reports it: within the crime window $1,500 fine (at most the
  cash) and 2 minutes in jail, otherwise $500 and 1 minute. Any running chop job ends.
Impound release (/api/garage61/retrieve on a car in garage 4)
  $750, plus $1,500 for a car that was stolen and pressed at the chop shop.
Rescue
  /api/gta/respawn waits 60 s after death (time for medics; sync respawn_delay shows it). /canlandir ID (on-duty
  medical faction, within 4 m) revives a dead player on the spot with 50 % health; the patient pays the medic $500 if
  he has it. /api/gta/npcrevive192 after 60 s: an NPC paramedic revives on the spot with 20 % health for $300.
Weapon attachments (att_mag, att_supp, att_flash, att_scope, att_grip)
  Sold in the weapon shop; "use" from the inventory fits it to the weapon in hand if that weapon takes it (2 s), the
  item is consumed. Stored per weapon in loadout['components192']; the sync carries the hashes for the weapon in
  hand and the page fits them in the engine.
Sync: result['crime192'] = {wanted:{seq,level}|null, chop:{spot,session}, comp:{weapon,hashes}}.
Also fixes v190: the job point tolerance now patches gameplay_v29.pn_roleplay (the live module)."""
import time,math,json,secrets
CHOP_DEFAULT=dict(x=-458.1,y=-1713.6,z=18.7)
PARTS=['door0','door1','door2','door3','wheel0','wheel1','wheel2','wheel3']
PRICE=dict(door=350,wheel=250);CRUSH_STREET=900;CRUSH_OWNED=1200;MIN_PARTS=4;STRIP_SECONDS=6;CHOP_COOLDOWN=480
WANTED_WINDOW=600;IMPOUND_FEE=750;STOLEN_FEE=1500;MEDIC_WAIT=60;NPC_REVIVE_FEE=300;MEDIC_FEE=500
ATT={'att_mag':dict(id=520,name='Uzatılmış şarjör',kg=.4,price=2500,color='#ffb36b',icon='magazine',kind='attachment'),
 'att_supp':dict(id=521,name='Susturucu',kg=.5,price=4000,color='#9fb4c8',icon='suppressor',kind='attachment'),
 'att_flash':dict(id=522,name='Silah feneri',kg=.2,price=1200,color='#ffe38a',icon='flashlight',kind='attachment'),
 'att_scope':dict(id=523,name='Dürbün',kg=.4,price=3000,color='#8ad7ff',icon='scope',kind='attachment'),
 'att_grip':dict(id=524,name='Tutamak',kg=.3,price=1500,color='#c9b8ff',icon='grip',kind='attachment')}
P,SP,SP2,AF,AF2,MAC,MAC2,SMALL,SMALL2,MED,MAX='COMPONENT_AT_PI_FLSH','COMPONENT_AT_PI_SUPP','COMPONENT_AT_PI_SUPP_02','COMPONENT_AT_AR_FLSH','COMPONENT_AT_AR_AFGRIP','COMPONENT_AT_SCOPE_MACRO','COMPONENT_AT_SCOPE_MACRO_02','COMPONENT_AT_SCOPE_SMALL','COMPONENT_AT_SCOPE_SMALL_02','COMPONENT_AT_SCOPE_MEDIUM','COMPONENT_AT_SCOPE_MAX'
ARS,ARS2='COMPONENT_AT_AR_SUPP','COMPONENT_AT_AR_SUPP_02'
FIT={'pistol':dict(att_mag='COMPONENT_PISTOL_CLIP_02',att_supp=SP2,att_flash=P),
 'combatpistol':dict(att_mag='COMPONENT_COMBATPISTOL_CLIP_02',att_supp=SP,att_flash=P),
 'appistol':dict(att_mag='COMPONENT_APPISTOL_CLIP_02',att_supp=SP,att_flash=P),
 'pistol50':dict(att_mag='COMPONENT_PISTOL50_CLIP_02',att_supp=ARS2,att_flash=P),
 'microsmg':dict(att_mag='COMPONENT_MICROSMG_CLIP_02',att_supp=ARS2,att_flash=P,att_scope=MAC),
 'smg':dict(att_mag='COMPONENT_SMG_CLIP_02',att_supp=SP,att_flash=AF,att_scope=MAC2),
 'assaultsmg':dict(att_mag='COMPONENT_ASSAULTSMG_CLIP_02',att_supp=ARS2,att_flash=AF,att_scope=MAC),
 'assaultrifle':dict(att_mag='COMPONENT_ASSAULTRIFLE_CLIP_02',att_supp=ARS2,att_flash=AF,att_scope=MAC,att_grip=AF2),
 'carbinerifle':dict(att_mag='COMPONENT_CARBINERIFLE_CLIP_02',att_supp=ARS,att_flash=AF,att_scope=MED,att_grip=AF2),
 'advancedrifle':dict(att_mag='COMPONENT_ADVANCEDRIFLE_CLIP_02',att_supp=ARS,att_flash=AF,att_scope=SMALL),
 'mg':dict(att_mag='COMPONENT_MG_CLIP_02',att_scope=SMALL2),
 'combatmg':dict(att_mag='COMPONENT_COMBATMG_CLIP_02',att_scope=MED,att_grip=AF2),
 'pumpshotgun':dict(att_supp='COMPONENT_AT_SR_SUPP',att_flash=AF),
 'assaultshotgun':dict(att_mag='COMPONENT_ASSAULTSHOTGUN_CLIP_02',att_supp=ARS,att_flash=AF,att_grip=AF2),
 'bullpupshotgun':dict(att_supp=ARS2,att_flash=AF,att_grip=AF2),
 'sniperrifle':dict(att_supp=ARS2,att_scope=MAX),
 'heavysniper':dict(att_scope=MAX)}
def joaat(s):
 h=0
 for c in s.lower().encode():
  h=(h+c)&0xffffffff;h=(h+(h<<10))&0xffffffff;h^=h>>6
 h=(h+(h<<3))&0xffffffff;h^=h>>11;h=(h+(h<<15))&0xffffffff
 return h
def dist(a,b,keys=('x','y','z')):return math.dist([a[k]for k in keys],[b[k]for k in keys])
def flat(a,b):return math.hypot(a['x']-b['x'],a['y']-b['y'])
def install(api,now=time.time):
 if getattr(api,'crime192_installed',False):return api
 import gameplay_v29.pn_economy as eco,gameplay_v29.pn_inventory as inv,gameplay_v29.pn_admin as staff
 w=api.world;old=api.dispatch
 STATE=dict(chops={},cool={},wanted={},seq=0,arrest_at={},att={},stats=dict(chop_started=0,parts_sold=0,crushed=0,arrests=0,fines=0,impound_fees=0,medic_revives=0,npc_revives=0,attached=0))
 for k,v in ATT.items():eco.PRODUCTS.setdefault(k,v)
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_stolen192(vehicle_id INTEGER PRIMARY KEY,owner INTEGER NOT NULL,thief INTEGER NOT NULL,at REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_dispatch178(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,x REAL NOT NULL,y REAL NOT NULL,z REAL NOT NULL,dimension INTEGER NOT NULL,created REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_vehicle_home61(vehicle_id INTEGER PRIMARY KEY,anchor TEXT NOT NULL,paid INTEGER NOT NULL DEFAULT 0,due REAL NOT NULL,garage INTEGER NOT NULL DEFAULT 0)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_chop192_spot(id INTEGER PRIMARY KEY CHECK(id=1),x REAL,y REAL,z REAL)')
 def spot():
  with w.database()as db:r=db.execute('SELECT x,y,z FROM pn_chop192_spot WHERE id=1').fetchone()
  return dict(x=r['x'],y=r['y'],z=r['z'])if r else dict(CHOP_DEFAULT)
 def me(token):
  p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
  uid=api.authenticated61(token)if hasattr(api,'authenticated61')else(p or{}).get('user_id')
  if not uid or not p or not s:raise ValueError('Önce karakterinle şehre gir.')
  return uid,p,s
 def credit(db,uid,n):
  if n>0:db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(int(n),uid))
 def debit(db,uid,n):
  return n<=0 or db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(int(n),uid,int(n))).rowcount==1
 def protected(db,vid):
  for q in("SELECT 1 FROM pn_job_vehicles WHERE vehicle_id=?","SELECT 1 FROM pn_faction_vehicles WHERE vehicle_id=?","SELECT 1 FROM pn_ambient188 WHERE vehicle_id=?",
           "SELECT 1 FROM pn_donate_vehicles WHERE vehicle_id=?","SELECT 1 FROM pn_faction_fleet69 WHERE vehicle_id=?","SELECT 1 FROM pn_vehicle_sale84 WHERE vehicle_id=? AND status='pending'"):
   try:
    if db.execute(q,(vid,)).fetchone():return True
   except Exception:pass
  return False
 def vstate(row):
  s=w.VEHICLE_CACHE.get(row['id'])if hasattr(w,'VEHICLE_CACHE')else None
  return s or json.loads(row['state'])
 def dispatch_alert(kind,s,p):
  with w.database()as db:db.execute('INSERT INTO pn_dispatch178(kind,x,y,z,dimension,created) VALUES(?,?,?,?,?,?)',(kind,s['x'],s['y'],s['z'],p.get('dimension',0),now()))
 def want(cid,level,why):
  STATE['seq']+=1;cur=STATE['wanted'].get(cid)
  STATE['wanted'][cid]=dict(seq=STATE['seq'],level=max(level,cur['level']if cur and now()<cur['until']else 0),until=now()+WANTED_WINDOW,why=why)
 # ---------------- chop shop
 def chop(path,payload,token):
  uid,p,s=me(token);cid=p['char_id'];verb=path.rsplit('/',1)[-1];sp=spot();sess=STATE['chops'].get(cid)
  if p.get('health',200)<=100 or p.get('dimension',0):raise ValueError('Hurdacıda çalışmak için hayatta ve dışarıda olmalısın.')
  if verb=='cancel':
   STATE['chops'].pop(cid,None);return dict(success=True,notice='Hurdacı işi bırakıldı.')
  if verb=='start':
   if sess:raise ValueError('Zaten bir aracı söküyorsun.')
   if now()-STATE['cool'].get(cid,0)<CHOP_COOLDOWN:raise ValueError('Hurdacı yeni iş için %d sn sonra hazır.'%(CHOP_COOLDOWN-(now()-STATE['cool'].get(cid,0))))
   if s.get('vehicle_id'):raise ValueError('Araçtan in; sökülecek aracın yanında dur.')
   if flat(s,sp)>25:raise ValueError('Hurdacının alanına gel (GPS: /hurdaci).')
   best=None
   for row in w.rows(s):
    if not row['active']or row['owner']==cid:continue
    vs=vstate(row)
    if not all(k in vs for k in('x','y','z')):continue
    if flat(vs,sp)>20 or dist(vs,s)>8:continue
    d=dist(vs,s)
    if best is None or d<best[0]:best=(d,row)
   if not best:raise ValueError('Hurdacının alanında, yanında (8 m) sana ait olmayan bir araç yok.')
   row=best[1]
   with w.database()as db:
    if protected(db,row['id']):raise ValueError('Bu araç meslek, birlik veya bağış aracı; hurdaya verilemez.')
   if any(c.get('vehicle')==row['id']for c in STATE['chops'].values()):raise ValueError('Bu aracı başka biri söküyor.')
   STATE['chops'][cid]=dict(vehicle=row['id'],owner=row['owner'],model=row['model'],done=[],carrying=None,last=now()-STRIP_SECONDS,started=now());STATE['cool'][cid]=now()
   want(cid,2,'chop');dispatch_alert('Hurdacı · %s parçalanıyor'%str(row['model']).upper(),s,p)
   STATE['stats']['chop_started']+=1
   with w.database()as db:w.audit(db,uid,'chop-start192',dict(char_id=cid,vehicle=row['id'],owner=row['owner']))
   return dict(success=True,session=view(cid),notice='Araç hurdacıya alındı. Kapıları ve tekerlekleri tek tek sök, tezgâha götürüp sat. Polis haberdar oldu!')
  if not sess:raise ValueError('Önce bir aracı sökmeye başla.')
  vrow=w.vehicle(sess['vehicle'])if hasattr(w,'vehicle')else None
  if not vrow:STATE['chops'].pop(cid,None);raise ValueError('Araç artık yok.')
  vs=vstate(vrow)
  if verb=='strip':
   part=payload.get('part')
   if part not in PARTS or part in sess['done']:raise ValueError('Bu parça sökülemez.')
   if sess['carrying']:raise ValueError('Elindeki parçayı önce tezgâha götürüp sat.')
   if dist(vs,s)>4.5:raise ValueError('Aracın yanına yaklaş (4 m).')
   if now()-sess['last']<STRIP_SECONDS-.5:raise ValueError('Söküm sürüyor.')
   sess['carrying']=part;sess['last']=now()
   return dict(success=True,session=view(cid),notice=('Kapı söküldü.'if part.startswith('door')else'Tekerlek söküldü.')+' Tezgâha götür ve sat.')
  if verb=='sell':
   part=sess['carrying']
   if not part:raise ValueError('Elinde satılacak parça yok.')
   if dist(s,sp)>3.5:raise ValueError('Tezgâha yaklaş (3 m).')
   pay=PRICE['door'if part.startswith('door')else'wheel']
   with w.database()as db:credit(db,uid,pay);w.audit(db,uid,'chop-sell192',dict(char_id=cid,vehicle=sess['vehicle'],part=part,pay=pay))
   sess['done'].append(part);sess['carrying']=None;STATE['stats']['parts_sold']+=1
   return dict(success=True,session=view(cid),money=w.wallet(uid),notice='Parça $%d karşılığında satıldı.'%pay)
  if verb=='crush':
   if sess['carrying']:raise ValueError('Elindeki parçayı önce sat.')
   if len(sess['done'])<MIN_PARTS:raise ValueError('Preslemeden önce en az %d parça sök ve sat.'%MIN_PARTS)
   if flat(vs,sp)>20:raise ValueError('Araç hurdacının alanında olmalı.')
   vid=sess['vehicle']
   with w.database()as db:
    row=db.execute('SELECT * FROM pn_vehicles WHERE id=?',(vid,)).fetchone()
    if not row:STATE['chops'].pop(cid,None);raise ValueError('Araç artık yok.')
    if row['owner']:
     pay=CRUSH_OWNED
     db.execute('UPDATE pn_vehicles SET active=0,locked=1 WHERE id=?',(vid,))
     vs0=json.loads(row['state']);db.execute('INSERT INTO pn_vehicle_home61(vehicle_id,anchor,due,garage) VALUES(?,?,?,4) ON CONFLICT(vehicle_id) DO UPDATE SET garage=4',(vid,json.dumps({k:vs0.get(k,0)for k in('x','y','z','heading')}),now()+10**9))
     db.execute('DELETE FROM pn_vehicle_access WHERE vehicle_id=?',(vid,))
     db.execute('INSERT INTO pn_stolen192 VALUES(?,?,?,?) ON CONFLICT(vehicle_id) DO UPDATE SET thief=excluded.thief,at=excluded.at',(vid,row['owner'],cid,now()))
    else:
     pay=CRUSH_STREET
     for t in('pn_vehicle_access','pn_vehicle_home61'):
      try:db.execute('DELETE FROM '+t+' WHERE vehicle_id=?',(vid,))
      except Exception:pass
     db.execute('DELETE FROM pn_vehicles WHERE id=?',(vid,))
    credit(db,uid,pay);w.audit(db,uid,'chop-crush192',dict(char_id=cid,vehicle=vid,owner=row['owner'],pay=pay,parts=sess['done']))
   for c in('VEHICLE_CACHE','SAVED_AT'):
    try:getattr(w,c).pop(vid,None)
    except Exception:pass
   STATE['chops'].pop(cid,None);STATE['stats']['crushed']+=1
   return dict(success=True,money=w.wallet(uid),session=None,notice='Araç preslendi: $%d.'%pay+(' Sahibi aracını otoparktan ücretle geri alabilir.'if row['owner']else''))
  raise ValueError('Hurdacı işlemi bulunamadı.')
 def view(cid):
  sess=STATE['chops'].get(cid)
  if not sess:return None
  return dict(vehicle=sess['vehicle'],model=sess['model'],done=list(sess['done']),carrying=sess['carrying'],min_parts=MIN_PARTS,prices=PRICE)
 # ---------------- arrest
 def npc_arrest(token):
  uid,p,s=me(token);cid=p['char_id']
  if now()-STATE['arrest_at'].get(cid,0)<30:return dict(success=True,notice='')
  STATE['arrest_at'][cid]=now();wt=STATE['wanted'].get(cid);crime=bool(wt and now()<wt['until'])
  fine,minutes=(1500,2)if crime else(500,1)
  with w.database()as db:
   fine=min(fine,max(0,int(w.wallet(uid))));
   if fine:debit(db,uid,fine)
   old=db.execute('SELECT return_state FROM pn_jail WHERE char_id=?',(cid,)).fetchone()
   back=old['return_state']if old else json.dumps({k:s[k]for k in('x','y','z','heading')})
   db.execute('INSERT INTO pn_jail VALUES(?,?,?,?) ON CONFLICT(char_id) DO UPDATE SET until=excluded.until,reason=excluded.reason',(cid,now()+minutes*60,'NPC polis tutuklaması'+(' · hurdacı/araç hırsızlığı'if crime else''),back))
   w.audit(db,uid,'npc-arrest192',dict(char_id=cid,fine=fine,minutes=minutes,crime=crime))
  STATE['wanted'].pop(cid,None);STATE['chops'].pop(cid,None);STATE['stats']['arrests']+=1;STATE['stats']['fines']+=fine
  return dict(success=True,money=w.wallet(uid),notice='Polis seni yakaladı: $%d ceza ve %d dakika hapis.'%(fine,minutes))
 # ---------------- rescue
 def npc_revive(token):
  uid,p,s=me(token)
  if p.get('health',200)>100:raise ValueError('Karakterin hayatta.')
  wait=MEDIC_WAIT-(now()-p.get('dead_at',now()))
  if wait>0:raise ValueError('Sağlık ekibi bekleniyor: %d sn.'%math.ceil(wait))
  if staff.jail(p['char_id']):raise ValueError('Hapisteyken hastanede doğarsın.')
  with w.database()as db:
   fee=min(NPC_REVIVE_FEE,max(0,int(w.wallet(uid))));debit(db,uid,fee);w.audit(db,uid,'npc-revive192',dict(char_id=p['char_id'],fee=fee))
  revive(p,s,120);STATE['stats']['npc_revives']+=1
  return dict(success=True,life_id=p['life_id'],spawn=dict(p['respawn_spawn']),money=w.wallet(uid),notice='NPC sağlıkçı seni ayılttı (%%20 can). Ücret $%d.'%fee)
 def revive(p,s,health):
  p['health']=health;p['respawned_at']=now();p.pop('dead_at',None);p['life_id']=p.get('life_id',0)+1
  p['respawn_spawn']=dict({k:s[k]for k in('x','y','z','heading')},health=health,armor=p.get('armor',0))
  s['health']=health;s.update(vehicle_id=0,seat=-2,carried_by=0,speed=0,vx=0,vy=0,vz=0)
 def medic_revive(token,arg):
  uid,p,s=me(token)
  with w.database()as db:
   medic=bool(p.get('faction_duty'))and bool(db.execute("SELECT 1 FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id WHERE m.char_id=? AND f.kind='medical'",(p['char_id'],)).fetchone())
  if not medic and not(staff.rank(uid)>=2 and p.get('admin_duty')):raise ValueError('/canlandir için sağlık ekibinde görevde ol (/mduty).')
  cid=w.resolve_player_id(arg,api.PRESENCE)
  pair=next(((k,v)for k,v in api.PRESENCE.items()if v.get('char_id')==cid and k in api.GTA_STATE),None)
  if not pair:raise ValueError('Oyuncu bulunamadı.')
  tk,tp=pair;ts=api.GTA_STATE[tk]
  if tp.get('health',200)>100:raise ValueError('Bu oyuncu baygın değil.')
  if dist(ts,s)>4:raise ValueError('Hastanın yanına yaklaş (4 m).')
  with w.database()as db:
   fee=min(MEDIC_FEE,max(0,int(w.wallet(tp['user_id']))))
   if fee and debit(db,tp['user_id'],fee):credit(db,uid,fee)
   else:fee=0
   w.audit(db,uid,'medic-revive192',dict(medic=p['char_id'],patient=cid,fee=fee))
  revive(tp,ts,150);STATE['stats']['medic_revives']+=1
  return dict(success=True,notice='%s canlandırıldı (%%50 can).%s'%(tp.get('name','Hasta'),' Hizmet ücreti $%d hesabına geçti.'%fee if fee else''))
 # ---------------- attachments
 def selected_weapon(p):
  load=inv.load(p);slot=load.get('selected')
  for k,v in inv.WEAPONS.items():
   if v.get('slot')==slot and k in load.get('owned',{}):return k,v
  return None,None
 def components(p):
  k,v=selected_weapon(p)
  if not k:return None
  kinds=(inv.load(p).get('components192')or{}).get(k)or[]
  fit=FIT.get(k,{})
  return dict(weapon=int(v['hash'])&0xffffffff if isinstance(v.get('hash'),int)else joaat('weapon_'+k),hashes=[joaat(fit[a])for a in kinds if a in fit])
 def attach_start(token,item):
  uid,p,s=me(token);load=inv.load(p)
  if int(load.get('stock',{}).get(item,0))<=0:raise ValueError('Çantanda bu eklenti yok.')
  k,_=selected_weapon(p)
  if not k:raise ValueError('Eklentiyi takmak için silahı eline al.')
  if item not in FIT.get(k,{}):raise ValueError('%s bu silaha takılmaz.'%ATT[item]['name'])
  if item in((load.get('components192')or{}).get(k)or[]):raise ValueError('Bu silahta zaten takılı.')
  aid=secrets.token_hex(8);STATE['att'][p['char_id']]=dict(id=aid,item=item,weapon=k,until=now()+1.8)
  return dict(success=True,action_id=aid,duration=2000,kind='reload',label=ATT[item]['name']+' takılıyor')
 def attach_finish(token,aid):
  uid,p,s=me(token);job=STATE['att'].pop(p['char_id'],None)
  if not job or job['id']!=aid:return None
  if now()<job['until']:raise ValueError('Takma işlemi sürüyor.')
  load=json.loads(json.dumps(inv.load(p)));stock=load.setdefault('stock',{})
  if int(stock.get(job['item'],0))<=0:raise ValueError('Çantanda bu eklenti yok.')
  stock[job['item']]-=1
  if stock[job['item']]<=0:stock.pop(job['item'],None)
  comp=load.setdefault('components192',{}).setdefault(job['weapon'],[])
  if job['item']not in comp:comp.append(job['item'])
  with w.database()as db:p['loadout_version']=eco.stock_save(db,p,load);p['loadout']=load;w.audit(db,uid,'attach192',dict(char_id=p['char_id'],weapon=job['weapon'],item=job['item']))
  STATE['stats']['attached']+=1
  return dict(success=True,loadout=inv.view(p)if hasattr(inv,'view')else None,notice=ATT[job['item']]['name']+' takıldı.')
 def shop_buy(token,item):
  uid,p,s=me(token)
  if not inv.at_shop(s,p):raise ValueError('Silah dükkânında ol.')
  load=json.loads(json.dumps(inv.load(p)));stock=load.setdefault('stock',{})
  if int(stock.get(item,0))>=5:raise ValueError('Çantada en fazla 5 adet taşıyabilirsin.')
  with w.database()as db:
   if not debit(db,uid,ATT[item]['price']):raise ValueError('Bunun için $%d gerekli.'%ATT[item]['price'])
   stock[item]=int(stock.get(item,0))+1;p['loadout_version']=eco.stock_save(db,p,load);p['loadout']=load
   w.audit(db,uid,'attach-buy192',dict(char_id=p['char_id'],item=item,price=ATT[item]['price']))
  return dict(success=True,money=w.wallet(uid),notice=ATT[item]['name']+' alındı. Envanterden “Kullan” ile elindeki silaha tak.')
 # ---------------- dispatch
 def dispatch(path,payload,token):
  payload=payload if isinstance(payload,dict)else{}
  try:
   if path.startswith('/api/chop192/'):
    with api.LOCK:return chop(path,payload,token),None
   if path=='/api/police192/npc-arrest':
    with api.LOCK:return npc_arrest(token),None
   if path=='/api/gta/npcrevive192':
    with api.LOCK:return npc_revive(token),None
   if path=='/api/gta/respawn':
    with api.LOCK:
     p=api.PRESENCE.get(token)
     if p and p.get('health',200)<=100:
      wait=MEDIC_WAIT-(now()-p.get('dead_at',now()))
      if wait>0:raise ValueError('Sağlık ekibi bekleniyor: %d sn. Sonra hastanede doğabilir ya da NPC sağlıkçı çağırabilirsin.'%math.ceil(wait))
   if path=='/api/inventory/use-start'and payload.get('item')in ATT:
    with api.LOCK:return attach_start(token,payload['item']),None
   if path=='/api/inventory/use-finish':
    with api.LOCK:
     r=attach_finish(token,payload.get('action_id'))
     if r:return r,None
   if path=='/api/shops/buy'and payload.get('item')in ATT:
    with api.LOCK:return shop_buy(token,payload['item']),None
   if path=='/api/chat/send':
    msg=str(payload.get('message','')).strip();parts=msg.split()
    if parts and parts[0].lower()in('/canlandir','/canlandır'):
     if len(parts)!=2:raise ValueError('Kullanım: /canlandir OYUNCU_ID')
     with api.LOCK:return medic_revive(token,parts[1]),None
    if parts and parts[0].lower()in('/hurdaci','/hurdacı'):
     sp=spot();return dict(success=True,waypoint192=sp,notice='Hurdacı GPS’e işlendi. Sana ait olmayan bir aracı oraya getir.'),None
    if parts and parts[0].lower()=='/hurdaciyer':
     with api.LOCK:
      uid,p,s=me(token)
      if staff.rank(uid)<3 or not p.get('admin_duty'):raise ValueError('/hurdaciyer için yönetici görevinde ol (rütbe 3+).')
      with w.database()as db:db.execute('INSERT INTO pn_chop192_spot VALUES(1,?,?,?) ON CONFLICT(id) DO UPDATE SET x=excluded.x,y=excluded.y,z=excluded.z',(s['x'],s['y'],s['z']));w.audit(db,uid,'chop-spot192',{k:s[k]for k in('x','y','z')})
      return dict(success=True,notice='Hurdacı noktası buraya taşındı.'),None
   if path=='/api/garage61/retrieve':
    return impound(payload,token)
  except ValueError as e:return dict(success=False,error=str(e)),None
  if path in('/api/hotwire129/finish','/api/vehicles/break-finish'):
   out=old(path,payload,token)
   try:
    if out[0].get('success'):
     with api.LOCK:
      p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token);vid=int(payload.get('id')or payload.get('vehicle_id')or(s or{}).get('vehicle_id')or 0)
      row=w.vehicle(vid)if vid else None
      if p and s and row and row['owner']and row['owner']!=p['char_id']:want(p['char_id'],1,'theft');dispatch_alert('Araç hırsızlığı · %s %s'%(str(row['model']).upper(),row['plate']),s,p)
   except Exception:pass
   return out
  out=old(path,payload,token)
  if path=='/api/gta/sync':
   try:
    res=out[0]
    if isinstance(res,dict)and res.get('success'):
     with api.LOCK:
      p=api.PRESENCE.get(token)
      if p:
       cid=p['char_id'];wt=STATE['wanted'].get(cid)
       if wt and now()>=wt['until']:STATE['wanted'].pop(cid,None);wt=None
       extra=dict(wanted=dict(seq=wt['seq'],level=wt['level'])if wt else None,chop=dict(spot=spot(),session=view(cid)),comp=components(p))
       if p.get('health',200)<=100 and 'dead_at'in p:extra['medic_wait']=max(0,math.ceil(MEDIC_WAIT-(now()-p['dead_at'])))
       res=dict(res,crime192=extra)
       if 'respawn_delay'in res and p.get('health',200)<=100 and 'dead_at'in p:res['respawn_delay']=max(res.get('respawn_delay')or 0,MEDIC_WAIT-(now()-p['dead_at']))
       out=(res,)+tuple(out[1:])
   except Exception:pass
  if path=='/api/shops/list'and payload.get('kind')=='weapons':
   try:
    res=out[0]
    if isinstance(res,dict)and isinstance(res.get('items'),list):
     res=dict(res,items=res['items']+[dict(key=k,id=v['id'],name=v['name'],kg=v['kg'],price=v['price'],image='/pn/fixes210/att/'+k+'.svg',weapon=False)for k,v in ATT.items()]);out=(res,)+tuple(out[1:])
   except Exception:pass
  if path=='/api/garage61/list':
   try:
    res=out[0]
    if isinstance(res,dict)and isinstance(res.get('vehicles'),list):
     with w.database()as db:stolen={r[0]for r in db.execute('SELECT vehicle_id FROM pn_stolen192')}
     res=dict(res,vehicles=[dict(v,impound_fee=(IMPOUND_FEE+(STOLEN_FEE if v.get('id')in stolen else 0))if v.get('garage')==4 else 0,stolen192=v.get('id')in stolen)for v in res['vehicles']]);out=(res,)+tuple(out[1:])
   except Exception:pass
  return out
 def impound(payload,token):
  try:vid=int(payload.get('id',0))
  except(TypeError,ValueError):vid=0
  fee=0;uid=None
  if vid:
   with api.LOCK:
    p=api.PRESENCE.get(token)
    with w.database()as db:
     h=db.execute('SELECT garage FROM pn_vehicle_home61 WHERE vehicle_id=?',(vid,)).fetchone()
     row=db.execute('SELECT owner,active FROM pn_vehicles WHERE id=?',(vid,)).fetchone()
     if p and h and h['garage']==4 and row and row['owner']==p['char_id']and not row['active']:
      stolen=db.execute('SELECT 1 FROM pn_stolen192 WHERE vehicle_id=?',(vid,)).fetchone()
      fee=IMPOUND_FEE+(STOLEN_FEE if stolen else 0);uid=p['user_id']
      if not debit(db,uid,fee):return dict(success=False,error='Otoparktan çıkarmak için $%d gerekli%s.'%(fee,' (çalınıp hurdaya verilmiş araç)'if stolen else'')),None
  out=old('/api/garage61/retrieve',payload,token)
  if fee:
   with api.LOCK,w.database()as db:
    if out[0].get('success'):
     db.execute('DELETE FROM pn_stolen192 WHERE vehicle_id=?',(vid,));w.audit(db,uid,'impound-release192',dict(vehicle=vid,fee=fee));STATE['stats']['impound_fees']+=fee
     out=(dict(out[0],money=w.wallet(uid),notice=(out[0].get('notice')or'')+' Otopark ücreti $%d.'%fee),)+tuple(out[1:])
    else:credit(db,uid,fee)
  return out
 api.dispatch=dispatch;api.crime192_installed=True;api.crime192=STATE
 return api
