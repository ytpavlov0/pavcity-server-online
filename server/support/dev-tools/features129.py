"""129 over the live v128 chain: keys, lockpicks, hotwiring and theft reports.

Lockpick item: 'lockpick' (Maymuncuk, $450, 24/7 market, at most 5 in the bag). Opening a locked car
needs one; a wrong move breaks it with 50 % chance, a success wears it out with 20 % chance.
Engine: without a key (owner, shared key, job key or a key earned by lockpicking/hotwiring) the
engine no longer starts, street cars included; an engine that is already running can be switched off.
Hotwire (/api/hotwire129/start|step|finish|cancel): from the driver seat, five wires in order
(red/blue/yellow/green) within 2.4 s each; success grants the key for this vehicle and starts the
engine, a wrong wire ends the attempt.
Reports: starting a lockpick (35 %) or a hotwire (45 %) sends a theft report with model, plate and
place to on-duty police (and staff on duty) through the chat (scope police129, merged into their
sync like the staff chat). Everything is audited."""
import time,math,random,secrets,json,os
from collections import deque
LOCKPICK=dict(id=508,name='Maymuncuk',kg=.1,price=450,color='#c9b8ff',icon='lockpick',kind='tool')
BAG_MAX=5;WIRES=('red','blue','yellow','green');STEPS=5;WINDOW=2.4;REPORT_WINDOW=300
# chances (env overrides exist for deterministic fixture tests only)
P_REPORT_LOCK=float(os.environ.get('PAV129_P_REPORT_LOCK','.35'));P_REPORT_WIRE=float(os.environ.get('PAV129_P_REPORT_WIRE','.45'));P_BREAK_FAIL=float(os.environ.get('PAV129_P_BREAK_FAIL','.5'));P_BREAK_WEAR=float(os.environ.get('PAV129_P_BREAK_WEAR','.2'))
def install(api):
 if getattr(api,'features129_installed',False):return api
 import gameplay_v29.pn_economy as eco,gameplay_v29.pn_containers as box,gameplay_v29.pn_traffic as traffic,gameplay_v29.pn_roleplay as rp,gameplay_v29.pn_admin as staff,gameplay_v29.pn_inventory as inv
 w=api.world;previous=api.dispatch;attempts={};cops={};reports=deque(maxlen=60);rng=random.SystemRandom()
 eco.PRODUCTS['lockpick']=LOCKPICK
 base_catalog=box.catalog
 def catalog():
  r=base_catalog()
  if 'lockpick' in r:r['lockpick']['image']='/pn/fixes129/lockpick.svg'
  return r
 box.catalog=catalog
 with w.database()as db:
  for r in db.execute("SELECT * FROM pn_chat WHERE scope='police129' AND created>? ORDER BY id",(time.time()-REPORT_WINDOW,)):reports.append(dict(r))
 def me(token):
  uid=api.authenticated61(token);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
  if not uid or not p or not s:raise ValueError('Önce karakterinle şehre gir.')
  return uid,p,s
 def police(db,p):
  if staff.rank(p['user_id'])>=1 and p.get('admin_duty'):return True
  return bool(p.get('faction_duty'))and bool(db.execute("SELECT 1 FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id WHERE m.char_id=? AND f.kind='police'",(p['char_id'],)).fetchone())
 def bag(p):return int(inv.load(p).get('stock',{}).get('lockpick',0))
 def take(db,p,why):
  load=json.loads(json.dumps(inv.load(p)));stock=load.setdefault('stock',{})
  if stock.get('lockpick',0)<=0:return False
  stock['lockpick']-=1
  if stock['lockpick']<=0:stock.pop('lockpick',None)
  p['loadout_version']=eco.stock_save(db,p,load);p['loadout']=load;w.audit(db,p['user_id'],'lockpick-used129',dict(char_id=p['char_id'],why=why));return True
 def report(p,s,row,kind):
  data=w.public(row)
  street=data.get('street_name')or data.get('zone')or''
  body='İHBAR · Araç %s · %s %s%s'%('kilidi zorlanıyor'if kind=='lockpick'else'düz kontakla çalıştırılmaya çalışılıyor',str(row['model']).upper(),row['plate'],(' · '+street)if isinstance(street,str)and street else' · konum GPS’te')
  now=time.time();row2=dict(char_id=0,name='LSPD Merkez',body=body[:240],scope='police129',x=round(s['x'],1),y=round(s['y'],1),z=round(s['z'],1),created=now,admin=0,dimension=0)
  with w.database()as db:
   row2['id']=db.execute('INSERT INTO pn_chat(char_id,name,body,scope,x,y,z,created,admin,dimension)VALUES(?,?,?,?,?,?,?,?,?,?)',tuple(row2[k]for k in('char_id','name','body','scope','x','y','z','created','admin','dimension'))).lastrowid
   w.audit(db,p['user_id'],'theft-report129',dict(vehicle=row['id'],kind=kind,x=row2['x'],y=row2['y']))
  reports.append(row2)
 def has_key(db,p,row):
  cid=p['char_id']
  if row['owner']==cid or rp.vehicle_access(row['id'],cid)or traffic.has_key(row['id'],cid):return True
  job=db.execute('SELECT borrower FROM pn_job_vehicles WHERE vehicle_id=?',(row['id'],)).fetchone()
  return bool(job and job['borrower']==cid)
 def view(a):
  now=time.time();done=a['step']==len(a['wires'])
  return dict(success=True,id=a['id'],challenge=a['challenge'],step=a['step'],total=len(a['wires']),completed=done,wire=None if done else a['wires'][a['step']],ready_in_ms=max(0,math.ceil((a['ready_at']-now)*1000)),timeout_ms=max(0,math.ceil((a['deadline']-now)*1000)))
 def hotwire(action,token,v):
  uid,p,s=me(token);vid=v.get('id')
  if type(vid)is not int:raise ValueError('Araç seçilmedi.')
  if action=='cancel':
   a=attempts.get(token)
   if a and a['id']==vid and secrets.compare_digest(a['challenge'],str(v.get('challenge',''))):attempts.pop(token,None)
   return dict(success=True)
  row=w.vehicle(vid)
  if not row:raise ValueError('Araç bulunamadı.')
  if w.occupation(p['char_id'])!=(vid,-1):raise ValueError('Düz kontak için sürücü koltuğunda ol.')
  now=time.time()
  if action=='start':
   with w.database()as db:
    if has_key(db,p,row):raise ValueError('Bu aracın anahtarı sende; motoru M ile çalıştır.')
    if db.execute('SELECT 1 FROM pn_job_vehicles WHERE vehicle_id=?',(vid,)).fetchone():raise ValueError('Meslek araçlarında düz kontak yapılmaz.')
   if p.get('hotwire129_at',0)>now-4:raise ValueError('Kabloları yeniden ayırmak için birkaç saniye bekle.')
   p['hotwire129_at']=now
   for k,a in list(attempts.items()):
    if now-a['start']>40:attempts.pop(k,None)
   a=dict(id=vid,char_id=p['char_id'],life=p.get('life_id',0),challenge=secrets.token_urlsafe(24),wires=[rng.choice(WIRES)for _ in range(STEPS)],step=0,start=now,ready_at=now+.35,deadline=now+.35+WINDOW)
   attempts[token]=a
   if rng.random()<P_REPORT_WIRE:report(p,s,row,'hotwire')
   with w.database()as db:w.audit(db,uid,'hotwire-start129',dict(vehicle=vid))
   return view(a)
  a=attempts.get(token)
  if not a or a['id']!=vid or a['char_id']!=p['char_id']or a['life']!=p.get('life_id',0)or not secrets.compare_digest(a['challenge'],str(v.get('challenge','')))or now-a['start']>35:
   attempts.pop(token,None);raise ValueError('Düz kontak denemesi sona erdi.')
  if action=='step':
   if a['step']>=len(a['wires'])or type(v.get('step'))is not int or v['step']!=a['step']or v.get('wire')!=a['wires'][a['step']]or not a['ready_at']<=now<=a['deadline']:
    attempts.pop(token,None);raise ValueError('Yanlış kablo ya da geç kaldın. Kıvılcım çıktı, motor çalışmadı.')
   a['step']+=1;a.update(ready_at=now+.3,deadline=now+.3+WINDOW);return view(a)
  if action=='finish':
   attempts.pop(token,None)
   if a['step']!=len(a['wires']):raise ValueError('Önce tüm kabloları bağla.')
   fields=dict(w.VEHICLE_CACHE.get(vid,json.loads(row['state'])))
   if fields.get('fuel',100)<=0:raise ValueError('Kablolar bağlandı ama yakıt yok.')
   with w.database()as db:
    traffic.grant_key(db,vid,p['char_id']);w.audit(db,uid,'hotwire129',dict(vehicle=vid))
   fields['engine']=True;fields['fuel_at']=time.time();w.VEHICLE_CACHE[vid]=fields;w.persist_vehicle(vid)
   return dict(success=True,vehicle=w.public(w.vehicle(vid)),notice='Düz kontak tuttu, motor çalıştı.')
  raise ValueError('Düz kontak işlemi bulunamadı.')
 def dispatch(path,v,token):
  if path.startswith('/api/hotwire129/'):
   with api.LOCK:return hotwire(path.rsplit('/',1)[-1],token,v if isinstance(v,dict)else{}),None
  if path=='/api/vehicles/engine'and isinstance(v,dict)and type(v.get('id'))is int:
   with api.LOCK:
    p=api.PRESENCE.get(token);row=w.vehicle(v['id'])if p else None
    if p and row and not(staff.rank(p['user_id'])>=2 and p.get('admin_duty')):
     fields=w.VEHICLE_CACHE.get(row['id'])or json.loads(row['state'])
     if not fields.get('engine')and w.occupation(p['char_id'])==(row['id'],-1):
      with w.database()as db:
       if not has_key(db,p,row)and not db.execute('SELECT 1 FROM pn_job_vehicles WHERE vehicle_id=?',(row['id'],)).fetchone():
        raise ValueError('Anahtarın yok — düz kontak gerekiyor.')
   return previous(path,v,token)
  if path=='/api/vehicles/enter'and isinstance(v,dict)and type(v.get('id'))is int:
   # The stock driver-seat entry handed every parked street car's key to whoever sat in it. A key in
   # the ignition only exists when the engine is already running (a driver was pulled out).
   with api.LOCK:
    p=api.PRESENCE.get(token);row=w.vehicle(v['id'])if p else None
    before=None
    if p and row and row['owner']==0:
     with w.database()as db:before=has_key(db,p,row)
    result,cookie=previous(path,v,token)
    if before is False and result.get('success')and result.get('seat')==-1:
     fields=w.VEHICLE_CACHE.get(row['id'])or json.loads(row['state'])
     if not fields.get('engine'):
      with w.database()as db:db.execute('DELETE FROM pn_vehicle_access WHERE vehicle_id=? AND char_id=?',(row['id'],p['char_id']))
      result=dict(result,notice='Kontakta anahtar yok. Motoru çalıştırmak için düz kontak gerekir (M).')
    return result,cookie
  if path=='/api/vehicles/break-start'and isinstance(v,dict):
   with api.LOCK:
    uid,p,s=me(token)
    if bag(p)<=0:raise ValueError('Maymuncuğun yok. 24/7 marketten alabilirsin ($450).')
    result,cookie=previous(path,v,token)
    if result.get('success'):
     row=w.vehicle(v.get('id'))
     if row and rng.random()<P_REPORT_LOCK:report(p,s,row,'lockpick')
    return result,cookie
  if path in('/api/vehicles/break-step','/api/vehicles/break-finish')and isinstance(v,dict):
   with api.LOCK:
    p=api.PRESENCE.get(token)
    try:result,cookie=previous(path,v,token)
    except ValueError as e:
     if p and path.endswith('break-step')and rng.random()<P_BREAK_FAIL:
      with w.database()as db:broke=take(db,p,'broke')
      if broke:raise ValueError(str(e)+' Maymuncuk kırıldı.')
     raise
    if p and path.endswith('break-finish')and result.get('success')and rng.random()<P_BREAK_WEAR:
     with w.database()as db:
      if take(db,p,'worn'):result=dict(result,notice=str(result.get('notice',''))+' Maymuncuk aşındı ve kırıldı.')
    return result,cookie
  if path=='/api/shops/buy'and isinstance(v,dict)and v.get('item')=='lockpick':
   with api.LOCK:
    uid,p,s=me(token)
    if v.get('kind','market')!='market':raise ValueError('Ürün bu mağazada satılmıyor.')
    eco.at('market',p,s)
    qty=v.get('qty',1)
    if type(qty)is not int or not 1<=qty<=BAG_MAX:raise ValueError('Adet 1–5 olmalı.')
    if bag(p)+qty>BAG_MAX:raise ValueError('Çantada en fazla %d maymuncuk taşıyabilirsin.'%BAG_MAX)
    cost=LOCKPICK['price']*qty;load=json.loads(json.dumps(inv.load(p)));load.setdefault('stock',{})['lockpick']=bag(p)+qty
    with w.database()as db:
     if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(cost,uid,cost)).rowcount:raise ValueError('Yeterli paran yok.')
     p['loadout_version']=eco.stock_save(db,p,load);p['loadout']=load;w.audit(db,uid,'shop-buy',dict(item='lockpick',qty=qty,cost=cost))
    return dict(success=True,money=w.wallet(uid),loadout=inv.view(p),notice='%d maymuncuk çantaya eklendi.'%qty),None
  result,cookie=previous(path,v,token)
  if path=='/api/shops/list'and isinstance(v,dict)and v.get('kind','market')=='market'and result.get('success')and isinstance(result.get('items'),list):
   item=dict(catalog()['lockpick'],price=LOCKPICK['price'])
   result=dict(result,items=result['items']+[item])
  if path=='/api/gta/sync'and reports and reports[-1]['created']>time.time()-REPORT_WINDOW and isinstance(result.get('messages'),list):
   p=api.PRESENCE.get(token)
   if p:
    hit=cops.get(p['char_id'])
    if not hit or time.time()-hit[1]>10:
     with w.database()as db:hit=cops[p['char_id']]=(police(db,p),time.time())
     if len(cops)>1024:cops.clear()
    if hit[0]:
     cutoff=time.time()-REPORT_WINDOW;cursor=v.get('chat_cursor')if isinstance(v,dict)else None
     extra=[dict(r)for r in reports if r['created']>cutoff and(type(cursor)is not int or r['id']>cursor)]
     if extra:result=dict(result,messages=sorted(result['messages']+extra,key=lambda m:m['id'])[-120:])
  return result,cookie
 api.dispatch=dispatch;api.features129_installed=True;return api
