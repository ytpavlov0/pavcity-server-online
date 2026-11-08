"""Persistent marine custody; money, keys and placement stay authoritative."""
import json,math,re,secrets,time,unicodedata

CATALOG={'dinghy':dict(name='Nagasaki Dinghy',price=65000,seats=4),'jetmax':dict(name='Shitzu Jetmax',price=185000,seats=2),'marquis':dict(name='Dinka Marquis',price=350000,seats=4)}
MARINA=dict(id=8801,kind='marina',name='Puerto Del Sol · Marina',x=-794.3,y=-1509.6,z=1.6,sprite=356,color=3,radius=5)
BERTHS=[dict(x=-800.5,y=-1508.2,z=.2,heading=110),dict(x=-811.8,y=-1491.5,z=.2,heading=110),dict(x=-823.1,y=-1474.8,z=.2,heading=110)]

def boat_name(value):
 if not isinstance(value,str):raise ValueError('Tekne adını yaz.')
 value=' '.join(unicodedata.normalize('NFC',value).split())
 if not 2<=len(value)<=28 or any(not(c.isalnum()or c in " -'·")for c in value):raise ValueError('Tekne adı 2–28 harf/rakam olmalı.')
 return value

def install(api):
 if getattr(api,'marina88_installed',False):return api
 from restriction82 import free_actor
 w=api.world;previous=api.dispatch;public=w.public
 w.SPAWN_MODELS.update(CATALOG)
 if not any(s['id']==MARINA['id']for s in w.SERVICES):w.SERVICES.append(dict(MARINA))
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_boats88(vehicle_id INTEGER PRIMARY KEY,name TEXT NOT NULL,created REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_marina_receipts88(char_id INTEGER,request_id TEXT,signature TEXT,result TEXT,created REAL,PRIMARY KEY(char_id,request_id))')
 def state(row):return dict(w.VEHICLE_CACHE.get(row['id'],json.loads(row['state'])))
 def publish(row):
  result=public(row)
  if row['model']in CATALOG:
   with api.database()as db:b=db.execute('SELECT name FROM pn_boats88 WHERE vehicle_id=?',(row['id'],)).fetchone()
   result.update(marine=True,boat_name=b['name']if b else CATALOG[row['model']]['name'])
  return result
 def occupied(vid):return any(v==vid for v,seat in w.SEATS)
 def berth(db,vid):
  rows=db.execute('SELECT id,state FROM pn_vehicles WHERE active=1 AND id<>?',(vid,)).fetchall()
  for at in BERTHS:
   if all(not w.near(state(dict(r)),at,13)for r in rows):return dict(at)
  raise ValueError('Marina çıkışı dolu. Önce iskeledeki tekneleri uzaklaştır.')
 def actor(token,v):
  uid=api.authenticated61(token);api.require_client61(token,v);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
  if not uid or not p or p['user_id']!=uid:raise ValueError('Önce şehre gir.')
  w.live(p,s);free_actor(api,p,time.time())
  if p.get('dimension',0)or p.get('elevator176_ready'):raise ValueError('Marina işlemi için açık dünyaya çık.')
  return uid,p,s
 def response(p,s):
  with api.database()as db:rows=[dict(r)for r in db.execute('SELECT v.*,b.name AS boat_name FROM pn_vehicles v JOIN pn_boats88 b ON b.vehicle_id=v.id WHERE v.owner=? ORDER BY v.id',(p['char_id'],))]
  return dict(success=True,marina=MARINA,catalog=[dict(model=k,**v)for k,v in CATALOG.items()],money=w.wallet(p['user_id']),near=w.near(s,MARINA,30),boats=[dict(id=r['id'],model=r['model'],name=r['boat_name'],plate=r['plate'],active=bool(r['active']),occupied=occupied(r['id']),**{k:state(r).get(k,0)for k in('x','y','z','fuel','km')})for r in rows])
 def dispatch(path,v,token):
  if path.startswith('/api/marina88/'):
   with api.LOCK:
    uid,p,s=actor(token,v);action=path.rsplit('/',1)[-1];cid=p['char_id'];now=time.time()
    if action=='list':return response(p,s),None
    if action not in('buy','launch','store','rename'):raise ValueError('Geçersiz marina işlemi.')
    request=v.get('request_id')
    if not isinstance(request,str)or not re.fullmatch(r'[a-zA-Z0-9-]{16,64}',request):raise ValueError('İşlem kimliği eksik.')
    sig=json.dumps([action,v.get('id'),v.get('model'),v.get('name')],ensure_ascii=False)
    with api.database()as db:
     old=db.execute('SELECT * FROM pn_marina_receipts88 WHERE char_id=? AND request_id=?',(cid,request)).fetchone()
     if old:
      if old['signature']!=sig:raise ValueError('İşlem kimliği başka bir isteğe ait.')
      return dict(json.loads(old['result']),replayed=True),None
    if not w.near(s,MARINA,30):raise ValueError('Puerto Del Sol marina iskelesine yaklaş (30 m).')
    if w.occupation(cid)[0]or s.get('vehicle_id'):raise ValueError('Önce araçtan/tekneden in.')
    new=None;vid=0
    with api.database()as db:
     if not db.in_transaction:db.execute('BEGIN IMMEDIATE')
     if action=='buy':
      model=v.get('model')
      if model not in CATALOG:raise ValueError('Katalogdan bir tekne seç.')
      name=boat_name(v.get('name'));cost=CATALOG[model]['price']
      if db.execute('SELECT COUNT(*) FROM pn_vehicles WHERE owner=?',(cid,)).fetchone()[0]>=20:raise ValueError('Araç ve tekne toplam sınırı 20.')
      if db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(cost,uid,cost)).rowcount!=1:raise ValueError('Tekne için yeterli paran yok.')
      new=dict(BERTHS[0],rx=0,ry=0,rz=BERTHS[0]['heading'],vx=0,vy=0,vz=0,body=1000,engine=False,fuel=100,km=0,seats=CATALOG[model]['seats'],pose_epoch=1)
      vid=db.execute('INSERT INTO pn_vehicles(owner,model,plate,active,locked,state,updated) VALUES(?,?,?,0,1,?,?)',(cid,model,'SEA'+secrets.token_hex(2).upper(),json.dumps(new),now)).lastrowid
      db.execute('INSERT INTO pn_boats88 VALUES(?,?,?)',(vid,name,now));db.execute('INSERT INTO pn_vehicle_access VALUES(?,?)',(vid,cid))
      db.execute('INSERT INTO pn_vehicle_home61(vehicle_id,anchor,due,garage) VALUES(?,?,?,?)',(vid,json.dumps(BERTHS[0]),now+2100,MARINA['id']))
      notice=f'{name} satın alındı. İskeleye çıkarmak için Suya indir seç.'
     else:
      if type(v.get('id'))is not int:raise ValueError('Geçerli tekne ID seç.')
      vid=v['id'];row=db.execute('SELECT v.* FROM pn_vehicles v JOIN pn_boats88 b ON b.vehicle_id=v.id WHERE v.id=? AND v.owner=?',(vid,cid)).fetchone()
      if not row or row['model']not in CATALOG:raise ValueError('Bu teknenin sahibi değilsin.')
      row=dict(row);new=state(row)
      if action=='rename':
       name=boat_name(v.get('name'));db.execute('UPDATE pn_boats88 SET name=? WHERE vehicle_id=?',(name,vid));notice='Teknenin adı '+name+' olarak kaydedildi.'
      else:
       if occupied(vid):raise ValueError('Teknede oyuncu var; önce herkes insin.')
       if action=='launch':
        if row['active']:raise ValueError('Tekne zaten denizde. Konumunu GPS üzerinden bul.')
        at=berth(db,vid);new.update(at,rx=0,ry=0,rz=at['heading'],vx=0,vy=0,vz=0,engine=False,pose_epoch=int(new.get('pose_epoch',0))+1)
        db.execute('UPDATE pn_vehicle_home61 SET anchor=?,garage=0,due=? WHERE vehicle_id=?',(json.dumps(at),now+2100,vid));notice='Teknen iskelede. F ile bin, J ile motoru çalıştır; W/S ile sür.'
       else:
        if not row['active']:raise ValueError('Tekne zaten marina hangarında.')
        if not w.near(new,MARINA,75)or not w.near(s,new,15):raise ValueError('Tekneni marinaya getir ve yanına yaklaş.')
        speed=[new.get(k,0)for k in('vx','vy','vz')]
        if not all(isinstance(n,(int,float))and math.isfinite(n)for n in speed)or math.hypot(*speed)>1:raise ValueError('Tekne durmadan bağlanamaz.')
        new.update(engine=False,vx=0,vy=0,vz=0);db.execute('UPDATE pn_vehicle_home61 SET garage=? WHERE vehicle_id=?',(MARINA['id'],vid));notice='Teknen marina hangarına alındı.'
       db.execute('UPDATE pn_vehicles SET state=?,active=?,updated=? WHERE id=?',(json.dumps(new),int(action=='launch'),now,vid))
     w.audit(db,uid,'marina88-'+action,dict(vehicle_id=vid,name=v.get('name'),model=v.get('model')))
     result=dict(success=True,id=vid,notice=notice,money=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()[0])
     db.execute('INSERT INTO pn_marina_receipts88 VALUES(?,?,?,?,?)',(cid,request,sig,json.dumps(result),now))
     db.execute('DELETE FROM pn_marina_receipts88 WHERE char_id=? AND request_id NOT IN(SELECT request_id FROM pn_marina_receipts88 WHERE char_id=? ORDER BY created DESC LIMIT 64)',(cid,cid))
    if action in('store','buy'):w.VEHICLE_CACHE.pop(vid,None);w.SAVED_AT.pop(vid,None)
    elif action=='launch':w.VEHICLE_CACHE[vid]=new;w.SAVED_AT[vid]=now
    return result,None
  # All legacy creation/retrieval paths must respect water custody, including admin.
  if path.startswith(('/api/vehicles/','/api/garage61/')):
   with api.LOCK:
    action=path.rsplit('/',1)[-1];model=v.get('model')
    if type(v.get('id'))is int:
     with api.database()as db:row=db.execute('SELECT model FROM pn_vehicles WHERE id=?',(v['id'],)).fetchone()
     if row:model=row['model']
    if model in CATALOG and action=='enter':
     allowed=range(-1,CATALOG[model]['seats']-1);seat=v.get('seat')
     if seat is None:seat=next((n for n in allowed if(v.get('id'),n)not in w.SEATS),-2)
     if type(seat)is not int or seat not in allowed:raise ValueError('Teknede uygun boş koltuk yok.')
     v=dict(v,seat=seat)
    if model in CATALOG and action in('buy','spawn','retrieve','store','park','belt','window','door','indicator'):raise ValueError('Tekne işlemleri için /tekne marina panelini kullan.')
  return previous(path,v,token)
 w.public=publish;api.dispatch=dispatch;api.marina88_installed=True;return api
