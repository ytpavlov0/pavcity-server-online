"""Nearby vehicle sale offers. Money, keys, ownership and audit commit together."""
import copy,json,secrets,time,math
def install(api):
 if getattr(api,'vehicle_trade84_installed',False):return api
 import gameplay_v29.pn_commands as commands
 import gameplay_v29.pn_admin as staff
 import gameplay_v29.pn_roleplay as rp
 from restriction82 import free_actor
 w=api.world;previous=api.dispatch;old=commands.command;public=w.public
 with api.database()as db:
  db.execute('''CREATE TABLE IF NOT EXISTS pn_vehicle_sale84(id TEXT PRIMARY KEY,vehicle_id INTEGER NOT NULL,seller INTEGER NOT NULL,buyer INTEGER NOT NULL,price INTEGER NOT NULL,expires REAL NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created REAL NOT NULL)''')
  db.execute('CREATE INDEX IF NOT EXISTS pn_sale84_buyer ON pn_vehicle_sale84(buyer,status)')
 def actors(cid):
  for t,p in api.PRESENCE.items():
   if p['char_id']==cid and time.time()-p.get('last_seen',0)<10 and t in api.GTA_STATE:return p,api.GTA_STATE[t]
  raise ValueError('Oyuncu çevrimiçi değil veya konumu güncel değil.')
 def together(p,s,q,qs):
  w.live(p,s);w.live(q,qs)
  free_actor(api,p,time.time());free_actor(api,q,time.time())
  if p.get('dimension',0)!=q.get('dimension',0)or p.get('dimension',0)or not w.near(s,qs,5):raise ValueError('Alıcı 5 metre içinde ve aynı dış dünyada olmalı.')
 def personal(db,vid):
  if db.execute('SELECT 1 FROM pn_faction_vehicles WHERE vehicle_id=?',(vid,)).fetchone()or db.execute('SELECT 1 FROM pn_faction_fleet69 WHERE vehicle_id=?',(vid,)).fetchone():raise ValueError('Birlik araçları satılamaz. Önce birlik paylaşımını kaldır.')
 def card(row):
  car=w.vehicle(row['vehicle_id']);seller=w.character(row['seller']);return dict(id=row['id'],vehicle_id=row['vehicle_id'],model=car['model'],plate=car['plate'],seller=(seller['name']+' '+seller['surname']).strip(),price=row['price'],currency='USD',expires=row['expires'])
 def command(cmd,args,uid,p,s,peers):
  if cmd not in('/aracimisat','/arackabul','/aracreddet'):return old(cmd,args,uid,p,s,peers)
  w.live(p,s);free_actor(api,p,time.time())
  if cmd=='/aracimisat':
   if len(args)!=2:raise ValueError('Kullanım: /aracimisat OYUNCU_ID FİYAT · Para birimi USD ($).')
   cid=w.resolve_player_id(args[0],peers);price=staff.number(args[1],1,1000000000)
   if cid==p['char_id']:raise ValueError('Aracı kendine satamazsın.')
   q,qs=actors(cid);together(p,s,q,qs);vid,seat=w.occupation(p['char_id'])
   if not vid or seat!=-1:raise ValueError('Satacağın kendi aracının sürücü koltuğunda olmalısın.')
   row=w.vehicle(vid);car=w.public(row)
   if row['owner']!=p['char_id']or not row['active']:raise ValueError('Yalnızca kendi kişisel aracını satabilirsin.')
   if car.get('job')or car.get('faction_id'):raise ValueError('Meslek ve birlik araçları satılamaz.')
   if math.hypot(*[car.get(k,0)for k in('vx','vy','vz')])>.5:raise ValueError('Önce aracı durdur.')
   now=time.time();id=secrets.token_hex(8)
   with api.database()as db:
    db.execute('BEGIN IMMEDIATE');personal(db,vid);db.execute("UPDATE pn_vehicle_sale84 SET status='cancelled'WHERE vehicle_id=? AND status='pending'",(vid,));db.execute('INSERT INTO pn_vehicle_sale84 VALUES(?,?,?,?,?,?,?,?)',(id,vid,p['char_id'],cid,price,now+90,'pending',now));w.audit(db,uid,'vehicle-sale84-offer',dict(id=id,vehicle=vid,buyer=cid,price=price))
   return dict(success=True,notice=q['name']+' kişisine '+car['model'].upper()+' · '+car['plate']+' için $'+format(price,',')+' satış teklifi gönderildi. Süre: 90 sn.')
  if len(args)!=1 or not __import__('re').fullmatch('[a-f0-9]{16}',args[0]):raise ValueError('Kullanım: '+cmd+' TEKLİF_ID')
  id=args[0];changed=None
  with api.database()as db:
   db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM pn_vehicle_sale84 WHERE id=?',(id,)).fetchone()
   if not row or row['buyer']!=p['char_id']:raise ValueError('Bu teklif sana ait değil.')
   if row['status']=='accepted':return dict(success=True,notice='Bu araç devri zaten tamamlandı.')
   if row['status']!='pending'or row['expires']<time.time():raise ValueError('Teklifin süresi dolmuş veya iptal edilmiş.')
   if cmd=='/aracreddet':db.execute("UPDATE pn_vehicle_sale84 SET status='rejected'WHERE id=?",(id,));return dict(success=True,notice='Araç teklifi reddedildi.')
   seller,ss=actors(row['seller']);together(p,s,seller,ss);carrow=db.execute('SELECT * FROM pn_vehicles WHERE id=?',(row['vehicle_id'],)).fetchone()
   if not carrow or carrow['owner']!=seller['char_id']or not carrow['active']:raise ValueError('Araç sahibi veya araç durumu değişmiş.')
   personal(db,row['vehicle_id'])
   if w.occupation(seller['char_id'])!=(row['vehicle_id'],-1):raise ValueError('Satıcı aracın sürücü koltuğunda olmalı.')
   car=copy.deepcopy(w.VEHICLE_CACHE.get(row['vehicle_id'],json.loads(carrow['state'])))
   if math.hypot(*[car.get(k,0)for k in('vx','vy','vz')])>.5 or not w.near(s,car,8):raise ValueError('Araç durmalı ve yanında olmalısın.')
   rp.debit(db,'pn_wallet','user_id',uid,row['price'])
   if db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(row['price'],seller['user_id'])).rowcount!=1:raise ValueError('Satıcının cüzdanı bulunamadı.')
   if db.execute('UPDATE pn_vehicles SET owner=?,updated=? WHERE id=? AND owner=?',(p['char_id'],time.time(),row['vehicle_id'],seller['char_id'])).rowcount!=1:raise ValueError('Araç sahibi değişmiş.')
   db.execute('DELETE FROM pn_vehicle_access WHERE vehicle_id=?',(row['vehicle_id'],))
   db.execute('INSERT OR IGNORE INTO pn_vehicle_access(vehicle_id,char_id) VALUES(?,?)',(row['vehicle_id'],p['char_id']))
   db.execute("UPDATE pn_vehicle_sale84 SET status='accepted'WHERE id=?",(id,));db.execute("UPDATE pn_vehicle_sale84 SET status='cancelled'WHERE vehicle_id=? AND id<>? AND status='pending'",(row['vehicle_id'],id))
   w.audit(db,uid,'vehicle-sale84-accept',dict(id=id,vehicle=row['vehicle_id'],seller=seller['char_id'],buyer=p['char_id'],price=row['price']));changed=row['vehicle_id']
  return dict(success=True,notice='Araç ve anahtarları adına devredildi. Ödenen: $'+format(row['price'],','),vehicle_id=changed)
 names={}
 def view(row):
  result=public(row);owner=result.get('owner',0)
  if owner>0:
   live=next((p['name']for p in api.PRESENCE.values()if p['char_id']==owner),None)
   if live:result['owner_label']=live
   else:
    if owner not in names or time.monotonic()-names[owner][1]>30:
     
     with api.database()as db:c=db.execute('SELECT name,surname FROM characters WHERE id=?',(owner,)).fetchone()
     names[owner]=((' '.join(str(c[k])for k in('name','surname')if c[k]).strip()if c else 'Bilinmeyen sahip'),time.monotonic())
     if len(names)>128:names.pop(next(iter(names)))
    result['owner_label']=names[owner][0]
  return result
 def dispatch(path,v,token):
  result,cookie=previous(path,v,token)
  if path=='/api/gta/sync'and result.get('success'):
   p=api.PRESENCE.get(token)
   if p:
    with api.database()as db:rows=list(db.execute("SELECT * FROM pn_vehicle_sale84 WHERE buyer=? AND status='pending'AND expires>? ORDER BY created DESC LIMIT 4",(p['char_id'],time.time())))
    result['vehicle_sales84']=[card(row)for row in rows]
  return result,cookie
 commands.command=command;w.public=view;api.dispatch=dispatch;api.vehicle_trade84_installed=True;return api
