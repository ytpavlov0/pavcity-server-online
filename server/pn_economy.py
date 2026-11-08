"""Game-only shops, vehicle upgrades, keys and character cosmetics. Server prices."""
import json,time,hashlib,secrets
import pn_world as world,pn_roleplay as rp,pn_inventory as inv,pn_admin as staff
FUEL_STATIONS=[dict(id=2110,kind='fuel',name='LTD · Grove Benzinlik',sprite=361,color=5,radius=12,x=-70.3,y=-1761.2,z=29.5),dict(id=2111,kind='fuel',name='LTD · Little Seoul',sprite=361,color=5,radius=12,x=-724.6,y=-935.2,z=19.2),dict(id=2112,kind='fuel',name='RON · Sandy Shores',sprite=361,color=5,radius=12,x=2001.7,y=3774.9,z=32.4)]
FUEL_CAPACITY=60;FUEL_PRICE=45

def refuel(action,uid,token,payload,p,state):
 """Server-priced, atomic purchase; retry receipts cannot buy fuel twice."""
 import math
 world.live(p,state)
 if action=='refuel':
  litres=rp.integer(payload.get('litres'),1,FUEL_CAPACITY);request=payload.get('request_id')
  if not isinstance(request,str) or not 16<=len(request)<=80:raise ValueError('Geçersiz yakıt işlem kimliği.')
  digest=hashlib.sha256(json.dumps(['refuel',p['char_id'],litres]).encode()).hexdigest()
  with world.database() as db:old=db.execute('SELECT digest,result FROM pn_rp_receipts WHERE user_id=? AND key=?',(uid,request)).fetchone()
  if old:
   if old['digest']!=digest:raise ValueError('İşlem kimliği başka yakıt alımında kullanılmış.')
   return json.loads(old['result'])
 vid,seat=world.occupation(p['char_id'])
 if not vid or seat!=-1:raise ValueError('Yakıt almak için sürücü koltuğunda olmalısın.')
 row=world.vehicle(vid);car=world.public(row)
 station=next((s for s in FUEL_STATIONS if world.near(state,s,12) and world.near(car,s,16)),None)
 if p.get('dimension',0) or not row['active'] or not station:raise ValueError('Aracınla benzinlik pompalarına yaklaş.')
 missing=max(0,(100-car.get('fuel',100))/100*FUEL_CAPACITY)
 if action=='refuel-info':return dict(success=True,vehicle=car,station=station,capacity=FUEL_CAPACITY,price_per_litre=FUEL_PRICE,missing_litres=round(missing,3),money=world.wallet(uid))
 if car.get('engine'):raise ValueError('Yakıt almadan önce motoru durdur (M).')
 if max(math.hypot(*(car.get(k,0) for k in ('vx','vy','vz'))),state.get('speed',0))>.5:raise ValueError('Yakıt alırken araç tamamen durmalı.')
 if missing<.001:raise ValueError('Yakıt depon zaten dolu.')
 from pn_multiplayer import rate
 rate(token,'vehicle-refuel',.5)
 delivered=min(litres,missing);cost=math.ceil(delivered*FUEL_PRICE)
 fields=dict(world.VEHICLE_CACHE[vid]);fields.update(fuel=min(100,car.get('fuel',100)+delivered/FUEL_CAPACITY*100),fuel_at=time.time())
 result=dict(success=True,litres=round(delivered,3),cost=cost,vehicle={**car,**fields},notice=f'{delivered:.1f} litre yakıt alındı · ${cost:,}')
 with world.database() as db:
  if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(cost,uid,cost)).rowcount:raise ValueError('Yakıt için yeterli paran yok.')
  db.execute('UPDATE pn_vehicles SET state=?,updated=? WHERE id=?',(json.dumps(fields),time.time(),vid))
  result['money']=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()[0]
  db.execute('INSERT INTO pn_rp_receipts VALUES(?,?,?,?,?)',(uid,request,digest,json.dumps(result),time.time()))
  world.audit(db,uid,'refuel',dict(vehicle=vid,litres=delivered,cost=cost))
 world.VEHICLE_CACHE[vid]=fields;world.SAVED_AT[vid]=time.time()
 return result
PRODUCTS={
 'phone':dict(id=501,name='PAV Phone',kg=.25,price=8500,color='#ac80ed',icon='129',kind='electronics'),
 'coffee':dict(id=502,name='Kahve',kg=.2,price=220,color='#d5ad73',icon='38',kind='drink',value=20),
 'snack':dict(id=503,name='Hamburger',kg=.3,price=280,color='#c8ad78',icon='160',kind='food',value=25),
 'sandwich':dict(id=504,name='Etli sandviç',kg=.3,price=250,color='#c8ad78',icon='167',kind='food',value=20),
 'bandage':dict(id=505,name='Bandaj',kg=.2,price=650,color='#6ed3c1',icon='31',kind='heal',value=15),
 'grape':dict(id=506,name='Üzüm',kg=.3,price=0,color='#a78adc',icon='14',kind='material'),
 'herb':dict(id=507,name='İşlenmemiş kaçak ürün',kg=.3,price=0,color='#a5bb73',icon='228',kind='material')}
STORES=[dict(id=2101,kind='electronics',name='Digital Den · Telefon',sprite=459,color=2,radius=4,x=-660.8,y=-854.8,z=24.5),dict(id=2102,kind='locksmith',name='Anahtarcı',sprite=134,color=2,radius=4,x=170.2,y=-1799.6,z=29.3),dict(id=2103,kind='tuning',name='Los Santos Customs',sprite=72,color=2,radius=8,x=-337.0,y=-136.8,z=39.0),dict(id=2104,kind='clothes',name='Binco · Kıyafet',sprite=73,color=2,radius=4,x=-818.3,y=-1074.2,z=11.3),dict(id=2105,kind='clothes',name='Suburban · Kıyafet',sprite=73,color=2,radius=4,x=126.6,y=-224.4,z=54.6),dict(id=2106,kind='estate',name='PAV Emlak',sprite=375,color=2,radius=4,x=-716.8,y=270.3,z=84.7)]
TUNING={'primary':dict(name='Ana renk',price=4500,min=0,max=160),'secondary':dict(name='İkinci renk',price=3000,min=0,max=160),'wheels':dict(name='Jant tasarımı',price=8500,min=-1,max=20),'tint':dict(name='Cam filmi',price=5000,min=0,max=5),'engine':dict(name='Motor seviyesi',price=35000,min=-1,max=3),'brakes':dict(name='Fren seviyesi',price=20000,min=-1,max=2),'suspension':dict(name='Süspansiyon',price=18000,min=-1,max=3),'spoiler':dict(name='Spoiler',price=12000,min=-1,max=10),'turbo':dict(name='Turbo',price=75000,min=0,max=1)}
def schema(db):
 db.execute('CREATE TABLE IF NOT EXISTS pn_outfits(id INTEGER PRIMARY KEY,char_id INTEGER NOT NULL,name TEXT NOT NULL,appearance TEXT NOT NULL,created REAL NOT NULL)')
 db.execute('CREATE TABLE IF NOT EXISTS pn_vehicle_upgrades(vehicle_id INTEGER PRIMARY KEY,state TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1)')
 db.execute('CREATE TABLE IF NOT EXISTS pn_estate_seed(version INTEGER PRIMARY KEY)')
 if not db.execute('SELECT 1 FROM pn_estate_seed WHERE version=22').fetchone():
  for name,kind,price,x,y,z in [('Vespucci Dairesi','apartment',285000,-1149.5,-1521.9,4.4),('Alta Ofisi','office',690000,-269.5,-955.9,31.2),('Strawberry Garajı','garage',180000,77.1,-1744.1,29.6)]:
   db.execute('INSERT INTO pn_properties(name,kind,x,y,z,heading,price) VALUES(?,?,?,?,?,0,?)',(name,kind,x,y,z,price))
  db.execute('INSERT INTO pn_estate_seed VALUES(22)')

def at(kind,p,state):
 world.live(p,state)
 if p.get('dimension',0):raise ValueError('Dış dünyada olmalısın.')
 places=rp.MARKETS if kind=='market' else [s for s in STORES if s['kind']==kind]
 if not any(world.near(state,s,8 if kind=='tuning' else 5) for s in places):raise ValueError('İlgili NPC / işletme konumuna yaklaş.')
 if kind!='tuning' and world.occupation(p['char_id'])[0]:raise ValueError('NPC yanına yaya yaklaş.')
def stock_save(db,p,updated):
 version=p.get('loadout_version',1)+1;db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version',(p['char_id'],json.dumps(updated),version));return version
def dispatch(path,uid,token,v,p,state,presences):
 from pn_multiplayer import rate,emote
 world.live(p,state);inv.load(p);group=path.split('/')[2];action=path.rsplit('/',1)[-1];cid=p['char_id']
 if group=='shops':
  kind=v.get('kind','market')
  if kind not in ('market','electronics','weapons'):raise ValueError('Geçersiz mağaza.')
  if kind=='weapons':
   if not inv.at_shop(state,p):raise ValueError('Silahçıya yaya yaklaş.')
  else:at(kind,p,state)
  from pn_containers import catalog,personal,weight,augmented
  items=catalog();keys=['water','food','coffee','snack','sandwich','bandage'] if kind=='market' else ['phone'] if kind=='electronics' else list(inv.WEAPONS)+['armor']+['ammo_'+k for k,x in inv.WEAPONS.items() if x.get('category')!='NULL']
  def price(k):return 100 if k=='water' else 150 if k=='food' else 12000 if k=='armor' else inv.WEAPONS[k]['price'] if k in inv.WEAPONS else max(1500,inv.WEAPONS[k[5:]]['price']//30) if k.startswith('ammo_') else PRODUCTS[k]['price']
  if action=='list':return dict(success=True,kind=kind,items=[dict(items[k],price=price(k)) for k in keys],personal=augmented(personal(p),'self'),money=world.wallet(uid))
  if action!='buy':raise ValueError('Mağaza işlemi bulunamadı.')
  key=v.get('item');qty=rp.integer(v.get('qty',1),1,10)
  if key not in keys:raise ValueError('Ürün bu mağazada satılmıyor.')
  # Existing weapon/supply handlers keep their ownership and timing fences.
  if key in inv.WEAPONS or key=='armor' or key.startswith('ammo_'):
   if qty!=1:raise ValueError('Silah ve mühimmat paketini birer adet al.')
   return inv.dispatch('/api/inventory/'+('buy' if key in inv.WEAPONS else 'supply'),uid,token,{'weapon':key,'item':key},p,state)
  limit=1 if key=='phone' else 20;old=p.get(key,0) if key in ('water','food') else p['loadout'].get('stock',{}).get(key,0)
  if old+qty>limit:raise ValueError('Bu ürünün çanta sınırı dolu.')
  if weight(personal(p))+items[key]['kg']*qty>(1000 if world.admin(uid) else 30):raise ValueError('Çantanda yeterli yer yok.')
  rate(token,'shop-buy',.4);updated=json.loads(json.dumps(p['loadout']));cost=price(key)*qty
  with world.database() as db:
   rp.debit(db,'pn_wallet','user_id',uid,cost)
   if key in ('water','food'):
    from pn_multiplayer import save
    peer=dict(p);peer[key]=old+qty;save(peer,state,True,db);version=p['loadout_version']
   else:updated.setdefault('stock',{})[key]=old+qty;version=stock_save(db,p,updated)
   world.audit(db,uid,'shop-buy',dict(item=key,qty=qty,cost=cost))
  if key in ('water','food'):p.update({key:old+qty,'saved_at':peer['saved_at']})
  else:p['loadout']=updated;p['loadout_version']=version
  emote(p,state,items[key]['name']+' satın aldı.');return dict(success=True,loadout=inv.view(p),money=world.wallet(uid),notice=items[key]['name']+' çantana eklendi.')
 if group=='keys':
  at('locksmith',p,state)
  with world.database() as db:
   rows=[dict(r) for r in db.execute('SELECT id,model,plate FROM pn_vehicles WHERE owner=?',(cid,))]
   if action=='list':return dict(success=True,vehicles=rows,players=[dict(id=x['server_id'],name=x['name']) for x in presences.values() if x['char_id']!=cid and time.time()-x['last_seen']<10],price=2500)
   if action not in ('copy','revoke'):raise ValueError('Anahtar işlemi bulunamadı.')
   vid=rp.integer(v.get('id'),1);target=world.resolve_player_id(v.get('server_id'),presences)
   if not any(x['id']==vid for x in rows):raise ValueError('Anahtarı yalnız araç sahibi çoğaltabilir.')
   peer=next(x for x in presences.values() if x['char_id']==target)
   if action=='copy':
    if db.execute('SELECT 1 FROM pn_vehicle_access WHERE vehicle_id=? AND char_id=?',(vid,target)).fetchone():raise ValueError('Bu kişide zaten anahtar var.')
    from session_api import GTA_STATE
    sample=next((s for s in GTA_STATE.values() if s['char_id']==target),None)
    if not sample or time.time()-peer['last_seen']>=10 or peer.get('dimension',0)!=p.get('dimension',0) or not world.near(state,sample,5):raise ValueError('Anahtarın verileceği kişi yanına gelmeli.')
    rp.debit(db,'pn_wallet','user_id',uid,2500);db.execute('INSERT INTO pn_vehicle_access VALUES(?,?)',(vid,target))
   else:db.execute('DELETE FROM pn_vehicle_access WHERE vehicle_id=? AND char_id=?',(vid,target))
   world.audit(db,uid,'vehicle-key-'+action,dict(vehicle=vid,target=target))
  emote(p,state,'araç anahtarını '+('çoğalttı.' if action=='copy' else 'iptal etti.'));return dict(success=True,notice='Anahtar kaydı güncellendi.')
 if group=='tuning':
  at('tuning',p,state);vid,seat=world.occupation(cid)
  if not vid or seat!=-1:raise ValueError('Kendi aracınla sürücü koltuğunda atölyeye gir.')
  row=world.vehicle(vid)
  if row['owner']!=cid:raise ValueError('Modifiye için araç sahibi olmalısın.')
  with world.database() as db:
   record=db.execute('SELECT * FROM pn_vehicle_upgrades WHERE vehicle_id=?',(vid,)).fetchone();mods=json.loads(record['state']) if record else {}
   if action=='list':return dict(success=True,vehicle=world.public(row),options=TUNING,mods=mods,money=world.wallet(uid))
   if action!='buy' or v.get('part') not in TUNING:raise ValueError('Geçersiz modifiye.')
   part=v['part'];opt=TUNING[part];value=rp.integer(v.get('value'),opt['min'],opt['max'])
   if mods.get(part)==value:raise ValueError('Bu parça zaten takılı.')
   rate(token,'tuning-buy',1);rp.debit(db,'pn_wallet','user_id',uid,opt['price']);mods[part]=value
   db.execute('INSERT INTO pn_vehicle_upgrades VALUES(?,?,1) ON CONFLICT(vehicle_id) DO UPDATE SET state=excluded.state,version=version+1',(vid,json.dumps(mods)));world.audit(db,uid,'tuning-buy',dict(vehicle=vid,part=part,value=value,cost=opt['price']))
  world.VEHICLE_CACHE.setdefault(vid,json.loads(row['state']))['mods']=mods;world.persist_vehicle(vid)
  return dict(success=True,notice='Modifiye takıldı.',mods=mods,money=world.wallet(uid))
 if group=='clothes':
  at('clothes',p,state)
  with world.database() as db:
   if action=='list':return dict(success=True,outfits=[dict(r) for r in db.execute('SELECT id,name FROM pn_outfits WHERE char_id=? ORDER BY id DESC LIMIT 20',(cid,))],price=3500)
   if action=='buy':
    look=world.appearance(v.get('appearance',{}));name=rp.label(v.get('name','Kıyafetim'),2,32)
    if db.execute('SELECT COUNT(*) FROM pn_outfits WHERE char_id=?',(cid,)).fetchone()[0]>=20:raise ValueError('Gardırop sınırı 20.')
    rp.debit(db,'pn_wallet','user_id',uid,3500);db.execute('INSERT INTO pn_outfits(char_id,name,appearance,created) VALUES(?,?,?,?)',(cid,name,json.dumps(look),time.time()))
   elif action=='wear':
    saved=db.execute('SELECT appearance FROM pn_outfits WHERE id=? AND char_id=?',(rp.integer(v.get('id'),1),cid)).fetchone()
    if not saved:raise ValueError('Bu kıyafet senin değil.')
    look=json.loads(saved['appearance'])
   else:raise ValueError('Kıyafet işlemi bulunamadı.')
   # Only clothing may change here; face, gender and identity stay character-owned.
   saved=db.execute('SELECT appearance FROM pn_character WHERE char_id=?',(cid,)).fetchone();old=json.loads(saved['appearance']) if saved else world.appearance();old.update({k:look[k] for k in ('top','pants','shoes','torso','undershirt','texture') if k in look})
   db.execute('INSERT INTO pn_character VALUES(?,?,1) ON CONFLICT(char_id) DO UPDATE SET appearance=excluded.appearance,version=pn_character.version+1',(cid,json.dumps(old)));world.audit(db,uid,'clothes-'+action,dict(char_id=cid))
  return dict(success=True,notice='Kıyafet kaydedildi.',appearance=old,money=world.wallet(uid))
 raise ValueError('İşletme işlemi bulunamadı.')
