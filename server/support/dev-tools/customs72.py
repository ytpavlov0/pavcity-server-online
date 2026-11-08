"""Idempotent workshop purchases and versioned per-vehicle air settings."""
import copy,hashlib,json,re,time,math

def install(api):
 if getattr(api,'customs72_installed',False):return api
 import gameplay_v29.pn_economy as economy
 import gameplay_v29.pn_roleplay as rp
 import gameplay_v29.pn_traffic as traffic
 w=api.world;previous=api.dispatch;public=w.public;air={}
 with api.database() as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_air72(vehicle_id INTEGER PRIMARY KEY,front REAL NOT NULL DEFAULT 0,rear REAL NOT NULL DEFAULT 0,version INTEGER NOT NULL DEFAULT 1)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_customs_receipts72(user_id INTEGER NOT NULL,request_id TEXT NOT NULL,digest TEXT NOT NULL,result TEXT NOT NULL,PRIMARY KEY(user_id,request_id))')
  for row in db.execute('SELECT * FROM pn_air72'):air[row['vehicle_id']]=dict(row)
 def view(row):
  r=public(row)
  if row['id'] in air:r['air72']=air[row['id']]
  return r
 def actor(token,v):
  uid=api.authenticated61(token);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
  if not uid or not p or p['user_id']!=uid:raise ValueError('Önce şehre gir.')
  api.require_client61(token,v);w.live(p,s)
  if p.get('dimension',0):raise ValueError('Aracı dışarıdaki atölyeye getir.')
  if (p.get('property45_used') or {}).get('phase')=='pending' or p.get('inventory_action'):raise ValueError('Önce devam eden işlemi bitir.')
  return uid,p,s
 def target(p,s,v,shop=False):
  vid=v.get('vehicle_id',w.occupation(p['char_id'])[0])
  if type(vid)is not int or vid<=0:raise ValueError('Araç seç.')
  row=w.vehicle(vid);car=copy.deepcopy(w.VEHICLE_CACHE.get(vid,json.loads(row['state'])))
  if not row['active'] or not w.near(s,car,8):raise ValueError('Araca 8 metre içinde yaklaş.')
  seat=w.occupation(p['char_id'])
  if seat[0] and seat!=(vid,-1):raise ValueError('Air kumandasını yaya veya sürücü koltuğunda kullan.')
  if row['owner']!=p['char_id'] and not traffic.has_key(vid,p['char_id']):raise ValueError('Araç anahtarın sende değil.')
  if any(id==vid and held['char_id']!=p['char_id'] and st==-1 for (id,st),held in w.SEATS.items()):raise ValueError('Başka oyuncunun kullandığı aracı kontrol edemezsin.')
  vals=[car.get(k,0) for k in ('vx','vy','vz')]
  if any(type(x)not in(int,float) or not math.isfinite(x) for x in vals) or math.hypot(*vals)>.5:raise ValueError('Önce aracı tamamen durdur.')
  if shop:
   economy.at('tuning',p,s)
   if seat!=(vid,-1) or row['owner']!=p['char_id']:raise ValueError('Kendi aracınla sürücü koltuğunda atölyeye gir.')
   if car.get('engine'):raise ValueError('Atölyede motoru kapat.')
  return row,car
 def transaction(uid,v,details,callback):
  rid=v.get('request_id')
  if not isinstance(rid,str) or not re.fullmatch('[a-zA-Z0-9_-]{12,80}',rid):raise ValueError('Satın alma işlem kimliği gerekli; paneli yeniden aç.')
  digest=hashlib.sha256(json.dumps(details,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  with api.database() as db:
   db.execute('BEGIN IMMEDIATE');r=db.execute('SELECT * FROM pn_customs_receipts72 WHERE user_id=? AND request_id=?',(uid,rid)).fetchone()
   if r:
    if r['digest']!=digest:raise ValueError('İşlem kimliği farklı bir alışverişte kullanıldı.')
    return json.loads(r['result']),False
   result=callback(db)
   db.execute('INSERT INTO pn_customs_receipts72 VALUES(?,?,?,?)',(uid,rid,digest,json.dumps(result)))
  return result,True
 def dispatch(path,v,token):
  if not path.startswith('/api/customs72/') and path!='/api/tuning/buy':return previous(path,v,token)
  with api.LOCK:
   uid,p,s=actor(token,v);action=path.rsplit('/',1)[-1]
   if path=='/api/tuning/buy' or action=='buy':
    part=v.get('part');vid=v.get('vehicle_id',w.occupation(p['char_id'])[0]);value=v.get('value')
    if part not in economy.TUNING:raise ValueError('Geçerli parça seç.')
    opt=economy.TUNING[part];value=rp.integer(value,opt['min'],opt['max'])
    fields={}
    def purchase(db):
     row,car=target(p,s,{**v,'vehicle_id':vid},True)
     if row['model']=='pavtofas' and part=='wheels':raise ValueError('Doğan özel jant geometrisi kullanır; stok jant takılamaz. Ücret kesilmedi.')
     record=db.execute('SELECT state FROM pn_vehicle_upgrades WHERE vehicle_id=?',(vid,)).fetchone()
     mods={**car.get('mods',{}),**(json.loads(record[0]) if record else {})}
     if mods.get(part)==value:raise ValueError('Bu parça zaten takılı.')
     rp.debit(db,'pn_wallet','user_id',uid,opt['price']);mods[part]=value;mods.pop(part+'_rgb',None);car['mods']=mods
     db.execute('INSERT INTO pn_vehicle_upgrades VALUES(?,?,1) ON CONFLICT(vehicle_id) DO UPDATE SET state=excluded.state,version=version+1',(vid,json.dumps(mods)))
     db.execute('UPDATE pn_vehicles SET state=?,updated=? WHERE id=?',(json.dumps(car),time.time(),vid));fields.update(car)
     w.audit(db,uid,'customs72-buy',dict(vehicle=vid,part=part,value=value,price=opt['price']))
     return dict(success=True,mods=mods,notice=opt['name']+' takıldı.',vehicle_id=vid,money=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()[0])
    result,changed=transaction(uid,v,dict(action='buy',vehicle=vid,part=part,value=value),purchase)
    if changed:w.VEHICLE_CACHE[vid]=fields;w.SAVED_AT[vid]=time.time()
    return result,None
   if action=='list':
    row,car=target(p,s,v,True)
    return dict(success=True,vehicle=w.public(row),options=economy.TUNING,air_price=18000,air=air.get(row['id']),money=w.wallet(uid)),None
   if action=='air-status':
    row,car=target(p,s,v)
    return dict(success=True,vehicle=w.public(row),air=air.get(row['id'])),None
   if action=='air-buy':
    vid=v.get('vehicle_id')
    def purchase(db):
     row,car=target(p,s,v,True)
     if v.get('native_verified') is not True:raise ValueError('Bu araçta air desteği motor tarafından doğrulanmadı. Ücret kesilmedi.')
     if db.execute('SELECT 1 FROM pn_air72 WHERE vehicle_id=?',(vid,)).fetchone():raise ValueError('Air kiti zaten takılı.')
     rp.debit(db,'pn_wallet','user_id',uid,18000)
     db.execute('INSERT INTO pn_air72(vehicle_id) VALUES(?)',(vid,));w.audit(db,uid,'air72-buy',dict(vehicle=vid,price=18000))
     return dict(success=True,air=dict(vehicle_id=vid,front=0,rear=0,version=1),notice='Air kiti ve araca bağlı kumanda takıldı.',money=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()[0])
    result,changed=transaction(uid,v,dict(action='air-buy',vehicle=vid),purchase)
    if changed:air[vid]=result['air']
    return result,None
   if action=='air-set':
    row,car=target(p,s,v);vid=row['id'];values=[]
    for k in ('front','rear'):
     x=v.get(k)
     if type(x)not in(int,float) or not math.isfinite(x) or not 0<=x<=1:raise ValueError('Air yüksekliği 0–1 aralığında olmalı.')
     values.append(round(x,2))
    version=v.get('version')
    if type(version)is not int:raise ValueError('Kumandayı yeniden aç.')
    with api.database() as db:
     db.execute('BEGIN IMMEDIATE')
     if db.execute('UPDATE pn_air72 SET front=?,rear=?,version=version+1 WHERE vehicle_id=? AND version=?',(*values,vid,version)).rowcount!=1:raise ValueError('Air durumu değişti veya kit takılı değil. Kumandayı yeniden aç.')
    air[vid]=dict(vehicle_id=vid,front=values[0],rear=values[1],version=version+1)
    return dict(success=True,air=air[vid]),None
   raise ValueError('Atölye işlemi bulunamadı.')
 w.public=view;api.dispatch=dispatch;api.customs72_installed=True;api.air72=air
 return api
