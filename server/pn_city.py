"""Persistent V19 profile, property keys, job vehicles and vehicle recovery.

All identities/permissions/prices come from the authenticated server session.
Native positions remain client observations, not an authoritative simulation.
"""
import datetime,json,re,secrets,time
import pn_world as world
import pn_admin as staff
import pn_roleplay as rp
COUNTRIES={'other':'Diğer','tr':'Türkiye','us':'ABD','gb':'Birleşik Krallık','de':'Almanya','fr':'Fransa','ru':'Rusya','ua':'Ukrayna','az':'Azerbaycan','it':'İtalya','es':'İspanya','br':'Brezilya','jp':'Japonya','kr':'Güney Kore'}
VIP_NAMES=['Standart','VIP I','VIP II','VIP III','VIP IV','VIP V','VIP VI']
# Existing GTA V interior assets. SA/MTA dimension coordinates are not GTA V IPLs.
INTERIOR_TYPES={'apartment':dict(name='Daire',x=346.52,y=-1012.99,z=-99.20,heading=0,ipl=''), 'office':dict(name='Ofis',x=-141.2,y=-620.91,z=168.82,heading=90,ipl='ex_dt1_02_office_02b'), 'garage':dict(name='Garaj',x=228.7,y=-992.0,z=-99.0,heading=0,ipl='')}
JOB_PARKS={'courier':('blista',78.4,111.8,81.2,160),'recycling':('burrito3',1201,-1276,35.2,90),'contraband':('sultan',918.9,-1261.6,25.5,0),'harvest':('rebel',156,-2203,4.7,90)}
PROFILE_CACHE={}
FLEET_CHECK={}
FLEET_ABSENT={}
def schema(db):
 for sql in (
  "CREATE TABLE IF NOT EXISTS pn_profiles(user_id INTEGER PRIMARY KEY,email TEXT NOT NULL DEFAULT '',country TEXT NOT NULL DEFAULT 'other',vip INTEGER NOT NULL DEFAULT 0 CHECK(vip BETWEEN 0 AND 6),vip_until REAL NOT NULL DEFAULT 0)",
  'CREATE TABLE IF NOT EXISTS pn_vehicle_summons(char_id INTEGER NOT NULL,day TEXT NOT NULL,used INTEGER NOT NULL DEFAULT 0 CHECK(used BETWEEN 0 AND 3),PRIMARY KEY(char_id,day))',
  "CREATE TABLE IF NOT EXISTS pn_properties(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,kind TEXT NOT NULL,x REAL NOT NULL,y REAL NOT NULL,z REAL NOT NULL,heading REAL NOT NULL,price INTEGER NOT NULL CHECK(price>0),owner INTEGER NOT NULL DEFAULT 0,locked INTEGER NOT NULL DEFAULT 1,version INTEGER NOT NULL DEFAULT 1)",
  'CREATE TABLE IF NOT EXISTS pn_property_keys(property_id INTEGER NOT NULL,char_id INTEGER NOT NULL,PRIMARY KEY(property_id,char_id))',
  'CREATE TABLE IF NOT EXISTS pn_job_vehicles(job TEXT NOT NULL,slot INTEGER NOT NULL,vehicle_id INTEGER NOT NULL UNIQUE,borrower INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(job,slot))'):
  db.execute(sql)
 db.execute('CREATE INDEX IF NOT EXISTS pn_property_xy ON pn_properties(x,y)')
 if 'return_at' not in [r[1] for r in db.execute('PRAGMA table_info(pn_job_vehicles)')]:db.execute('ALTER TABLE pn_job_vehicles ADD COLUMN return_at REAL NOT NULL DEFAULT 0')

def parked(job,slot):
 model,x,y,z,heading=JOB_PARKS[job]
 return dict(x=x+8+slot*5,y=y+8,z=z,heading=heading,rx=0,ry=0,rz=heading,vx=0,vy=0,vz=0,body=1000,engine=False,windows=0,doors=0,fuel=100,km=0)
def ensure_fleet(db):
 for job,(model,*_) in JOB_PARKS.items():
  for slot in range(3):
   if db.execute('SELECT 1 FROM pn_job_vehicles WHERE job=? AND slot=?',(job,slot)).fetchone():continue
   fields=parked(job,slot);vid=db.execute('INSERT INTO pn_vehicles(owner,model,plate,locked,active,state,updated) VALUES(0,?,?,1,1,?,?)',(model,'JOB'+secrets.token_hex(2).upper(),json.dumps(fields),time.time())).lastrowid
   db.execute('INSERT INTO pn_job_vehicles(job,slot,vehicle_id) VALUES(?,?,?)',(job,slot,vid))
def borrow_job_car(db,key,cid):
 if key not in JOB_PARKS:return None
 ensure_fleet(db)
 row=db.execute('SELECT * FROM pn_job_vehicles WHERE job=? AND borrower=0 AND return_at=0 ORDER BY slot LIMIT 1',(key,)).fetchone()
 if not row:raise ValueError('Meslek araçları şu anda dolu; bir araç dönünce yeniden dene.')
 db.execute('UPDATE pn_job_vehicles SET borrower=? WHERE vehicle_id=?',(cid,row['vehicle_id']))
 db.execute('INSERT OR IGNORE INTO pn_vehicle_access VALUES(?,?)',(row['vehicle_id'],cid))
 db.execute('UPDATE pn_vehicles SET locked=0 WHERE id=?',(row['vehicle_id'],))
 return row['vehicle_id']
def return_job_car(db,cid):
 for row in db.execute('SELECT vehicle_id FROM pn_job_vehicles WHERE borrower=?',(cid,)).fetchall():
  if world.occupation(cid)[0]==row['vehicle_id']:
   world.release(cid)
   from session_api import PRESENCE
   for peer in PRESENCE.values():
    if peer['char_id']==cid:peer['seatbelt']=False
  db.execute('DELETE FROM pn_vehicle_access WHERE vehicle_id=?',(row['vehicle_id'],));db.execute('UPDATE pn_job_vehicles SET borrower=0,return_at=? WHERE vehicle_id=?',(time.time()+8,row['vehicle_id']))
def tick_fleet():
 import online_engine
 from session_api import PRESENCE
 now=time.time();key=online_engine.DB_PATH
 if now-FLEET_CHECK.get(key,0)<3:return
 FLEET_CHECK[key]=now
 with world.database() as db:
  for row in db.execute('SELECT j.*,v.state FROM pn_job_vehicles j JOIN pn_vehicles v ON v.id=j.vehicle_id').fetchall():
   vid=row['vehicle_id'];borrower=row['borrower']
   run=db.execute('SELECT started FROM pn_job_runs WHERE char_id=? AND completed IS NULL',(borrower,)).fetchone() if borrower else None
   absent_key=(key,vid)
   online=any(p['char_id']==borrower and now-p['last_seen']<120 for p in PRESENCE.values())
   if borrower and not online:FLEET_ABSENT.setdefault(absent_key,now)
   else:FLEET_ABSENT.pop(absent_key,None)
   expired=bool(run and now-run['started']>3600)
   abandoned=now-FLEET_ABSENT.get(absent_key,now)>120
   if borrower and (not run or expired or abandoned):
    db.execute('UPDATE pn_job_runs SET completed=? WHERE char_id=? AND completed IS NULL',(now,borrower))
    return_job_car(db,borrower);FLEET_ABSENT.pop(absent_key,None);continue
   if row['return_at'] and row['return_at']<=now and not any(v==vid for v,s in world.SEATS):
    old=json.loads(row['state']);fields=parked(row['job'],row['slot']);fields['pose_epoch']=old.get('pose_epoch',0)+1;fields['repair_epoch']=old.get('repair_epoch',0)+1
    db.execute('UPDATE pn_vehicles SET active=1,state=?,locked=1,updated=? WHERE id=?',(json.dumps(fields),now,vid));db.execute('UPDATE pn_job_vehicles SET return_at=0 WHERE vehicle_id=?',(vid,));world.VEHICLE_CACHE[vid]=fields;world.SAVED_AT[vid]=now
def profile(db,uid):
 db.execute('INSERT OR IGNORE INTO pn_profiles(user_id) VALUES(?)',(uid,));r=dict(db.execute('SELECT * FROM pn_profiles WHERE user_id=?',(uid,)).fetchone())
 if r['vip_until']<=time.time():r['vip']=0
 r['vip_name']=VIP_NAMES[r['vip']];return r
def public_profile(uid):
 import online_engine
 key=(online_engine.DB_PATH,uid);cached=PROFILE_CACHE.get(key)
 if cached and time.time()-cached[0]<2:return cached[1]
 with world.database() as db:r=profile(db,uid)
 public={k:r[k] for k in ('country','vip','vip_name','vip_until')};PROFILE_CACHE[key]=(time.time(),public)
 if len(PROFILE_CACHE)>1000:PROFILE_CACHE.pop(next(iter(PROFILE_CACHE)))
 return public
def view(uid,p,state):
 tick_fleet()
 with world.database() as db:
  bank=db.execute('SELECT balance FROM pn_bank WHERE user_id=?',(uid,)).fetchone()
  properties=[dict(r) for r in db.execute('SELECT * FROM pn_properties WHERE (x BETWEEN ? AND ? AND y BETWEEN ? AND ?) OR owner=? LIMIT 64',(state['x']-500,state['x']+500,state['y']-500,state['y']+500,p['char_id']))]
 with world.database() as db:
  loan=db.execute('SELECT j.vehicle_id,j.job,v.model,v.state FROM pn_job_vehicles j JOIN pn_vehicles v ON v.id=j.vehicle_id WHERE borrower=?',(p['char_id'],)).fetchone()
  car=dict(id=loan['vehicle_id'],job=loan['job'],model=loan['model'],**json.loads(loan['state'])) if loan else None
 import pn_commands
 info=public_profile(uid);info=dict(info,country=pn_commands.country(p['char_id']))
 return dict(bank=bank['balance'] if bank else 0,profile=info,properties=properties,dimension=p.get('dimension',0),activity=p.get('activity'),job_vehicle=car,environment=pn_commands.environment())
def pointer(value):
 if isinstance(value,str) and re.fullmatch(r'[0-9]{1,10}',value):value=int(value)
 return rp.integer(value)
def car_state(row):return dict(world.VEHICLE_CACHE.get(row['id'],json.loads(row['state'])))
def set_car(vid,fields):
 world.VEHICLE_CACHE[vid]=fields;world.persist_vehicle(vid)
def relocate(row,state):
 if any(vid==row['id'] for vid,seat in world.SEATS):raise ValueError('Araçta birisi var; taşıyamazsın.')
 f=car_state(row);f.update(world.spawn_location(state,row['model'],row['id']));f.update(rx=0,ry=0,rz=state['heading'],vx=0,vy=0,vz=0,engine=False,pose_epoch=f.get('pose_epoch',0)+1)
 with world.database() as db:db.execute('UPDATE pn_vehicles SET active=1,state=?,updated=? WHERE id=?',(json.dumps(f),time.time(),row['id']))
 world.VEHICLE_CACHE[row['id']]=f;world.SAVED_AT[row['id']]=time.time()
 return f
def admin_command(cmd,args,uid,p,state,presences):
 cid=p['char_id']
 if cmd in ('/getcar','/gotocar','/flipcar','/fixveh','/aracimigetir'):
  is_summon=cmd=='/aracimigetir'
  if not is_summon and staff.rank(uid)<2:raise ValueError('Yönetici yetkisi gerekli.')
  if len(args)>1 or not args and cmd in ('/getcar','/gotocar','/aracimigetir'):raise ValueError('Kullanım: '+cmd+' ARAÇ_ID')
  vid=pointer(args[0]) if args else world.occupation(cid)[0]
  if not vid:raise ValueError('Araç ID yaz veya araçta otur.')
  row=world.vehicle(vid);f=car_state(row)
  from pn_multiplayer import rate
  rate(str(uid),'vehicle-admin-'+cmd,1)
  if cmd=='/gotocar':
   result=teleport(p,state,dict(x=f['x']+3,y=f['y'],z=f['z']+.5,heading=f.get('heading',0)),0)
   p['respawn_spawn']['safe_ground']=True
   return dict(success=True,**result,notice='Araç #'+str(vid)+' yanına gidildi.')
  if cmd in ('/getcar','/aracimigetir'):
   if is_summon:
    if row['owner']!=cid:raise ValueError('Yalnız kendi aracını çağırabilirsin.')
    if state.get('vehicle_id') or p.get('dimension',0):raise ValueError('Dışarıda ve yaya olmalısın.')
    day=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    with world.database() as db:
     n=db.execute('SELECT used FROM pn_vehicle_summons WHERE char_id=? AND day=?',(cid,day)).fetchone()
     if n and n['used']>=3:raise ValueError('Günlük 3 araç çağırma hakkın doldu. UTC gece yarısında yenilenir.')
   relocate(row,state)
   if is_summon:
    with world.database() as db:db.execute('INSERT INTO pn_vehicle_summons VALUES(?,?,1) ON CONFLICT(char_id,day) DO UPDATE SET used=used+1',(cid,day))
   notice='Araç #'+str(vid)+' yakındaki boş alana getirildi.'
  else:
   f.update(rx=0,ry=0,rz=f.get('heading',0),vx=0,vy=0,vz=0,pose_epoch=f.get('pose_epoch',0)+1)
   if cmd=='/fixveh':f.update(body=1000,repair_epoch=f.get('repair_epoch',0)+1)
   set_car(vid,f);notice='Araç #'+str(vid)+(' tamir edildi.' if cmd=='/fixveh' else ' düzeltildi.')
  with world.database() as db:world.audit(db,uid,cmd,dict(vehicle=vid,char_id=cid))
  return dict(success=True,notice=notice)
 if cmd in ('/setvip','/vipver'):
  if staff.rank(uid)<4:raise ValueError('VIP ataması yalnız kurucuya açık.')
  if len(args)!=3:raise ValueError('Kullanım: '+cmd+' OYUNCU_ID SEVİYE(0–6) GÜN(1–365). Oyuncu ID için TAB listesini kullan.')
  target=world.resolve_player_id(args[0],presences);peer=next(v for v in presences.values() if v['char_id']==target);v=staff.number(args[1],0,6);days=staff.number(args[2],1,365)
  with world.database() as db:
   profile(db,peer['user_id']);db.execute('UPDATE pn_profiles SET vip=?,vip_until=? WHERE user_id=?',(v,time.time()+days*86400 if v else 0,peer['user_id']));world.audit(db,uid,'setvip',dict(target=target,level=v,days=days))
  PROFILE_CACHE.pop((__import__('online_engine').DB_PATH,peer['user_id']),None)
  return dict(success=True,notice=peer['name']+' · '+('VIP '+str(v)+' · '+str(days)+' gün kaydedildi.' if v else 'VIP kaldırıldı.'))
 if cmd in ('/setintid','/intlist'):
  if staff.rank(uid)<2:raise ValueError('Yönetici yetkisi gerekli.')
  templates=list(INTERIOR_TYPES)
  if cmd=='/intlist':return dict(success=True,info=dict(title='Interior şablonları',rows=[[i+1,INTERIOR_TYPES[k]['name']+' · '+k] for i,k in enumerate(templates)]))
  if len(args)!=2:raise ValueError('Kullanım: /setintid MÜLK_ID ŞABLON_ID · /intlist')
  id=staff.number(args[0],1,2147483647);kind=templates[staff.number(args[1],1,len(templates))-1]
  if any(x.get('dimension',0)==id for x in presences.values()):raise ValueError('İçeride oyuncu varken şablon değişmez.')
  with world.database() as db:
   if not db.execute('UPDATE pn_properties SET kind=?,version=version+1 WHERE id=?',(kind,id)).rowcount:raise ValueError('Mülk bulunamadı.')
   world.audit(db,uid,'setintid',dict(id=id,kind=kind))
  return dict(success=True,notice='Interior şablonu: '+INTERIOR_TYPES[kind]['name'])
 if cmd=='/addint':
  if staff.rank(uid)<2:raise ValueError('Yönetici yetkisi gerekli.')
  if len(args)<3:raise ValueError('Kullanım: /addint apartment|office|garage fiyat ad')
  kind=args[0];cost=staff.number(args[1],50000,100000000);name=rp.label(' '.join(args[2:]),3,48)
  if kind not in INTERIOR_TYPES:raise ValueError('Geçersiz interior türü.')
  if p.get('dimension',0) or state.get('vehicle_id'):raise ValueError('Dışarıda ve yaya olmalısın.')
  with world.database() as db:
   id=db.execute('INSERT INTO pn_properties(name,kind,x,y,z,heading,price) VALUES(?,?,?,?,?,?,?)',(name,kind,state['x'],state['y'],state['z'],state['heading'],cost)).lastrowid
   world.audit(db,uid,'addint',dict(property=id,kind=kind,price=cost))
  return dict(success=True,notice='Mülk #'+str(id)+' bulunduğun yerde oluşturuldu.')
 return None
def teleport(p,state,target,dimension):
 world.release(p['char_id']);p['dimension']=dimension;p['life_id']=p.get('life_id',0)+1;p['respawned_at']=time.time();p['respawn_spawn']=dict(**{k:target[k] for k in ('x','y','z','heading')},health=p['health'],armor=p.get('armor',0))
 p['admin_teleport']=p['respawn_spawn']
 state.update({k:p['respawn_spawn'][k] for k in ('x','y','z','heading')});state.update(vehicle_id=0,seat=-2,dimension=dimension)
 return dict(spawn=p['respawn_spawn'],life_id=p['life_id'],dimension=dimension,ipl=target.get('ipl',''))
def dispatch(path,uid,token,v,p,state,presences):
 action=path.rsplit('/',1)[-1]
 if path.startswith('/api/account/'):
  with world.database() as db:
   row=profile(db,uid)
   if action=='save':
    country=v.get('country',row['country']);email=str(v.get('email',row['email'])).strip()
    if country not in __import__('pn_commands').COUNTRIES:raise ValueError('Geçersiz ülke.')
    if email and (len(email)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email)):raise ValueError('Geçerli e-posta yaz.')
    db.execute('UPDATE pn_profiles SET country=?,email=? WHERE user_id=?',(country,email,uid));row=profile(db,uid)
    if p:__import__('pn_commands').country(p['char_id'],country)
   elif action=='users':
    if staff.rank(uid)<4:raise ValueError('Hesap listesi yalnız kurucuya açık.')
    return dict(success=True,users=[dict(r) for r in db.execute('SELECT u.id,u.username,u.created_at,p.email,p.country,p.vip,p.vip_until FROM users u LEFT JOIN pn_profiles p ON p.user_id=u.id ORDER BY u.id DESC LIMIT 100')])
   elif action!='profile':raise ValueError('Hesap işlemi bulunamadı.')
  import pn_commands
  if p:row['country']=pn_commands.country(p['char_id'])
  return dict(success=True,profile=row,countries=pn_commands.COUNTRIES,email_verified=False)
 world.live(p,state)
 if path.startswith('/api/properties/') and action in ('market','market-buy'):
  import pn_economy
  pn_economy.at('estate',p,state)
  with world.database() as db:
   if action=='market':return dict(success=True,properties=[dict(r) for r in db.execute('SELECT id,name,kind,price,x,y,z FROM pn_properties WHERE owner=0 ORDER BY price LIMIT 60')],types=INTERIOR_TYPES)
   id=rp.integer(v.get('id'),1);row=db.execute('SELECT * FROM pn_properties WHERE id=? AND owner=0',(id,)).fetchone()
   if not row:raise ValueError('Mülk satılık değil.')
   rp.debit(db,'pn_wallet','user_id',uid,row['price']);db.execute('UPDATE pn_properties SET owner=?,locked=1,version=version+1 WHERE id=? AND owner=0',(p['char_id'],id));world.audit(db,uid,'estate-buy',dict(id=id,price=row['price']))
  return dict(success=True,notice='Mülk satın alındı; anahtarın envanterinde.',money=world.wallet(uid))
 if path.startswith('/api/services/') and action=='open':
  kind=v.get('kind');s=next((s for s in world.SERVICES+rp.services() if s['kind']==kind and world.near(state,s,s['radius'])),None)
  if not s or state.get('vehicle_id') or p.get('dimension',0):raise ValueError('Menü için ilgili NPC yanına yaya olarak yaklaş ve E / ALT kullan.')
  return dict(success=True,service=s)
 if path.startswith('/api/properties/'):
  if action=='list':return dict(success=True,types=INTERIOR_TYPES,**view(uid,p,state))
  id=pointer(v.get('id'));cid=p['char_id']
  with world.database() as db:
   row=db.execute('SELECT * FROM pn_properties WHERE id=?',(id,)).fetchone()
   if not row:raise ValueError('Mülk bulunamadı.')
   row=dict(row);own=row['owner']==cid;key=own or bool(db.execute('SELECT 1 FROM pn_property_keys WHERE property_id=? AND char_id=?',(id,cid)).fetchone())
   at_door=world.near(state,row,3) and not p.get('dimension',0)
   inside=p.get('dimension',0)==id
   if not (at_door or inside) or state.get('vehicle_id'):raise ValueError('Mülkün kapısına yaya yaklaş.')
   if action=='buy':
    if row['owner']:raise ValueError('Mülkün sahibi var.')
    rp.debit(db,'pn_wallet','user_id',uid,row['price']);db.execute('UPDATE pn_properties SET owner=?,locked=1,version=version+1 WHERE id=?',(cid,id));world.audit(db,uid,'property-buy',dict(id=id,price=row['price']))
   elif action=='sell':
    if not own:raise ValueError('Yalnız mülk sahibi satabilir.')
    if any(peer.get('dimension',0)==id for peer in presences.values()):raise ValueError('Satmadan önce mülkün boşalmasını bekle.')
    db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(row['price']//2,uid));db.execute('UPDATE pn_properties SET owner=0,locked=1,version=version+1 WHERE id=?',(id,));db.execute('DELETE FROM pn_property_keys WHERE property_id=?',(id,));world.audit(db,uid,'property-sell',dict(id=id))
   elif action=='lock':
    if not key:raise ValueError('Mülk anahtarın yok.')
    db.execute('UPDATE pn_properties SET locked=1-locked,version=version+1 WHERE id=?',(id,))
   elif action in ('give-key','revoke-key'):
    if not own:raise ValueError('Anahtar yönetimi yalnız sahibine açık.')
    target=world.resolve_player_id(v.get('server_id'),presences)
    if action=='give-key':db.execute('INSERT OR IGNORE INTO pn_property_keys VALUES(?,?)',(id,target))
    else:db.execute('DELETE FROM pn_property_keys WHERE property_id=? AND char_id=?',(id,target))
   elif action=='edit':
    if staff.rank(uid)<2:raise ValueError('Mülk düzenleme yöneticiye açık.')
    kind=v.get('kind',row['kind']);price=rp.integer(v.get('price',row['price']),50000,100000000)
    if kind not in INTERIOR_TYPES:raise ValueError('Geçersiz tür.')
    if any(peer.get('dimension',0)==id for peer in presences.values()):raise ValueError('İçeride oyuncu varken tür değiştirilemez.')
    db.execute('UPDATE pn_properties SET name=?,kind=?,price=?,version=version+1 WHERE id=?',(rp.label(v.get('name',row['name']),3,48),kind,price,id))
   elif action=='enter':
    if not at_door:raise ValueError('Zaten içeridesin.')
    if row['locked'] and not key:raise ValueError('Kapı kilitli; anahtarın yok.')
    return dict(success=True,**teleport(p,state,INTERIOR_TYPES[row['kind']],id))
   elif action=='exit':
    if not inside:raise ValueError('Bu mülkte değilsin.')
    return dict(success=True,**teleport(p,state,row,0))
   else:raise ValueError('Mülk işlemi bulunamadı.')
  return dict(success=True,notice='Mülk işlemi kaydedildi.',money=world.wallet(uid))
 raise ValueError('Şehir işlemi bulunamadı.')
