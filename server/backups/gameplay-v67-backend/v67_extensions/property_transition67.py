"""Explicit mobile property readiness tickets; normal PC/mobile guards remain.

The client retains source geometry until confirm. Readiness is a renderer ACK,
not a claim that the server can remotely prove a GPU frame or floor collision.
"""
import copy,hashlib,importlib,json,math,re,secrets,time
clock=time.time
PREFIX='/api/properties/transition/'
KINDS=('apartment','garage','office','market')
PREPARE_SECONDS=20
CONFIRM_SECONDS=15
POSE=('x','y','z','heading')

def digest(token):return hashlib.sha256(token.encode()).hexdigest()
def finite(value):return type(value)in(int,float)and math.isfinite(value)
def pose(value):
 if not isinstance(value,dict)or not all(finite(value.get(k))for k in POSE):raise ValueError('Geçerli mülk konumu bulunamadı.')
 if any(abs(value[k])>16000 for k in ('x','y'))or not -1700<value['z']<2700:raise ValueError('Mülk konumu sınırların dışında.')
 return {k:value[k]for k in POSE}

def install(api,catalog_path):
 if getattr(api,'property_transition45_installed',False):return api
 packages=json.loads(__import__('pathlib').Path(catalog_path).read_text())
 office=json.loads((__import__('pathlib').Path(__file__).parent/'office208.json').read_text())
 packages['packages']['office']=office
 packages['packages']['market']=json.loads((__import__('pathlib').Path(__file__).parent/'market210.json').read_text())
 if packages.get('protocol')!=45 or set(packages.get('packages',{}))!=set(KINDS):raise ValueError('Mülk paket kataloğu doğrulanmadı.')
 world=api.world;city=importlib.import_module(api.__package__+'.pn_city');mp=importlib.import_module(api.__package__+'.pn_multiplayer');inv=importlib.import_module(api.__package__+'.pn_inventory')
 for kind in KINDS:
  item=packages['packages'][kind]
  if not finite(item.get('floor_z'))or not all(isinstance(item.get(k),str)and re.fullmatch('[0-9a-f]{64}',item[k])for k in ('scene_sha256','ground_sha256')):raise ValueError('Mülk dosya veya zemin kaydı geçersiz.')
  if abs(item['floor_z']+1-city.INTERIOR_TYPES[kind]['z'])>.05:raise ValueError('Mülk zemin yüksekliği şablonla eşleşmiyor.')
 with api.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_property_recovery45(char_id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,property_id INTEGER NOT NULL,exterior TEXT NOT NULL,updated REAL NOT NULL)')
 original=api.dispatch;initial=mp.initial

 def geometry(kind):
  if kind=='outdoor':return dict(kind='outdoor')
  item=packages['packages'][kind]
  return dict(kind='property',type=kind,package='mobile-market210'if kind=='market'else'mobile-office208'if kind=='office'else'mobile-interiors196',scene_sha256=item['scene_sha256'],ground_sha256=item['ground_sha256'])
 def point(values,dimension=0,kind='outdoor'):return dict(**pose(values),dimension=dimension,geometry=geometry(kind))
 def key(db,row,p):return row['owner']==p['char_id']or bool(db.execute('SELECT 1 FROM pn_property_keys WHERE property_id=?AND char_id=?',(row['id'],p['char_id'])).fetchone())
 def free(p,s):
  world.live(p,s)
  if p.get('client_platform')!='mobile':raise ValueError('Bu hazırlık akışı mobil istemci içindir.')
  if world.occupation(p['char_id'])[0]or s.get('vehicle_id'):raise ValueError('Mülkün kapısına yaya yaklaş.')
  with api.database()as db:
   r=db.execute('SELECT *FROM pn_restrictions178 WHERE char_id=?',(p['char_id'],)).fetchone()
   if r and r['life']==p.get('life_id',0)and r['dimension']==p.get('dimension',0)and r['until']>time.time()and(r['cuffed']or r['prone']):raise ValueError('Kısıtlıyken mülk geçişi yapılamaz.')
   if db.execute('SELECT 1 FROM pn_custody178 WHERE char_id=?',(p['char_id'],)).fetchone():raise ValueError('Önce nezarethane işlemini tamamla.')
  lift=p.get('elevator176_ready');live_lift=lift and lift.get('until',0)>=time.time()and lift.get('life_id')==p.get('life_id',0)and lift.get('dimension',0)==p.get('dimension',0)
  if p.get('inventory_action')or live_lift:raise ValueError('Devam eden işlemi bitir.')
 def authorize(db,row,p,s,direction):
  if row['kind']not in KINDS:raise ValueError('Bu iç mekânın mobil geometri paketi hazır değil.')
  if direction=='enter':
   if p.get('dimension',0)or not world.near(s,row,3):raise ValueError('Mülkün dış kapısına 3 metre içinde yaklaş.')
   if row['locked']and not key(db,row,p):raise ValueError('Kapı kilitli; anahtarın yok.')
  elif direction=='exit':
   if p.get('dimension',0)!=row['id']or not world.near(s,city.INTERIOR_TYPES[row['kind']],3):raise ValueError('İç mekânın çıkış kapısına yaklaş.')
  else:raise ValueError('Geçiş yönü geçersiz.')
 def bound(record,p,token):
  return record and record['uid']==p['user_id']and record['cid']==p['char_id']and secrets.compare_digest(record['session'],digest(token))
 def find(p,token,ticket):
  if not isinstance(ticket,str)or len(ticket)>96:raise ValueError('Geçiş bileti bulunamadı.')
  for name in ('property45_ready','property45_used'):
   item=p.get(name)
   if bound(item,p,token)and secrets.compare_digest(item['ticket'],ticket):return item
  raise ValueError('Geçiş bileti farklı bir oturuma ait veya sona erdi.')
 def active(p):
  item=p.get('property45_used')
  return item if item and item['phase']=='pending'and p.get('life_id',0)==item['commit_life']and p.get('dimension',0)==item['target']['dimension']and p.get('health',200)>100 else None
 def view(p):
  item=p.get('property45_used')or p.get('property45_ready')
  if not item:return dict(protocol=45,phase='idle',pending_confirm=False)
  return dict(protocol=45,phase=item['phase'],pending_confirm=bool(active(p)),ticket=item['ticket'],property_id=item['id'],source=item['source'],target=item['target'],life_id=p.get('life_id',0),remaining=max(0,item.get('until',0)-clock()))
 def save(p,s,db):
  s.update(health=p['health'],armor=p.get('armor',0));mp.save(p,s,True,connection=db)
 def reply(p,s,**more):
  result=dict(success=True,life_id=p.get('life_id',0),dimension=p.get('dimension',0),spawn=dict(**pose(s),health=p['health'],armor=p.get('armor',0)),observation_only=True)
  result.update(more);return result
 def ready_ack(data,target):
  if data.get('ready')is not True or data.get('geometry')!=target['geometry']or not finite(data.get('floor_z')):raise ValueError('Doğru geometri ve zemin yüklenmeden geçiş yapılamaz.')
  expected=packages['packages'][target['geometry']['type']]['floor_z']if target['geometry']['kind']=='property'else target['z']-1
  tolerance=.25 if target['geometry']['kind']=='property'else 1.25
  if abs(data['floor_z']-expected)>tolerance:raise ValueError('Yüklenen zemin hedef katla eşleşmiyor.')
 def journal(db,p,item,inside):
  if inside:
   exterior=item['source']if item['direction']=='enter'else item['target']
   db.execute('INSERT INTO pn_property_recovery45 VALUES(?,?,?,?,?) ON CONFLICT(char_id)DO UPDATE SET user_id=excluded.user_id,property_id=excluded.property_id,exterior=excluded.exterior,updated=excluded.updated',(p['char_id'],p['user_id'],item['id'],json.dumps(exterior),clock()))
  else:db.execute('DELETE FROM pn_property_recovery45 WHERE char_id=?AND user_id=?',(p['char_id'],p['user_id']))
 def rollback(p,s,item,reason='client'):
  if item['phase']!='pending':return reply(p,s,already_rolled_back=item['phase']in('rolled_back','cancelled'),phase=item['phase'])
  if not active(p):item['phase']='interrupted';raise ValueError('Karakterin yaşamı veya konumu değişti; eski geri dönüş uygulanmadı.')
  before_p,before_s=dict(p),dict(s)
  try:
   with api.database()as db:
    result=city.teleport(p,s,item['source'],item['source']['dimension']);save(p,s,db)
    journal(db,p,item,inside=bool(item['source']['dimension']));world.audit(db,p['user_id'],'property-rollback45',dict(id=item['id'],reason=reason))
  except Exception:p.clear();p.update(before_p);s.clear();s.update(before_s);raise
  item.update(phase='rolled_back',rollback_life=p['life_id'],until=clock()+30)
  return dict(success=True,phase='rolled_back',pending_confirm=False,**result)
 def refresh(token,p,s):
  item=p.get('property45_used')
  if not item or item['phase']!='pending':return
  if not active(p):item['phase']='interrupted';return
  if clock()>item['until']:rollback(p,s,item,'confirmation-timeout')
 def recovered_initial(character):
  result=initial(character)
  with api.database()as db:
   record=db.execute('SELECT *FROM pn_property_recovery45 WHERE char_id=?AND user_id=?',(character['id'],character['user_id'])).fetchone()
   saved=db.execute('SELECT state FROM pn_saved WHERE char_id=?',(character['id'],)).fetchone();values=json.loads(saved[0])if saved else {}
   if record:
    target=json.loads(record['exterior']);pose(target);result.update(pose(target));values.update(pose(target),dimension=0)
   elif values.get('dimension')and not db.execute('SELECT 1 FROM pn_properties WHERE id=?',(values['dimension'],)).fetchone():
    result.update({k:world.HOSPITAL_SPAWN[k]for k in POSE});values.update(pose(result),dimension=0)
   else:return result
   db.execute('INSERT INTO pn_saved VALUES(?,?,?)ON CONFLICT(char_id)DO UPDATE SET state=excluded.state,updated=excluded.updated',(character['id'],json.dumps(values),time.time()))
   db.execute('UPDATE characters SET pos_x=?,pos_y=?,pos_z=?WHERE id=?',(*(result[k]for k in ('x','y','z')),character['id']))
   db.execute('DELETE FROM pn_property_recovery45 WHERE char_id=?AND user_id=?',(character['id'],character['user_id']))
  return result

 def dispatch(path,payload,token):
  with api.LOCK:
   # Every actor's sync passes here, so protected loading targets cannot receive
   # combat damage or queue an old hit to land immediately after confirmation.
   if path=='/api/gta/sync':
    for other,actor in list(api.PRESENCE.items()):
     state=api.GTA_STATE.get(other)
     if state:refresh(other,actor,state)
   p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
   if p and s:refresh(token,p,s)
   if p and p.get('client_platform')=='mobile'and path in ('/api/properties/enter','/api/properties/exit'):
    raise ValueError('Mobilde geometri ve zemin hazırlığı gerekli. Güvenli mülk geçişini kullan; mülk kaydın korunuyor.')
   blocked_sequences=[]
   if path=='/api/gta/sync'and isinstance(payload.get('hits'),list):
    protected={q['char_id']for q in api.PRESENCE.values()if active(q)};hits=[]
    for hit in payload['hits']:
     if isinstance(hit,dict)and type(hit.get('target'))is int and hit['target']in protected and type(hit.get('seq'))is int and hit['seq']>0:blocked_sequences.append(hit['seq'])
     else:hits.append(hit)
    if blocked_sequences:payload=dict(payload,hits=hits)
   held=active(p)if p and s else None
   if held:
    if path in ('/api/gta/sync','/api/gta/checkpoint'):
     info=inv.view(p);hits=payload.get('hits',[])
     blocked_sequences.extend(h['seq']for h in hits if isinstance(h,dict)and type(h.get('seq'))is int and h['seq']>0)
     payload=dict(payload,**pose(held['target']),health=p['health'],armor=p.get('armor',0),vx=0,vy=0,vz=0,speed=0,flags=0,hits=[],ammo=info['ammo'],clip=info['clip'])
    elif not path.startswith(PREFIX)and(path.startswith(('/api/inventory/','/api/storage/','/api/containers/','/api/vehicles/','/api/elevators/','/api/properties/','/api/shops/','/api/keys/','/api/tuning/','/api/clothes/','/api/jobs/','/api/activity/','/api/services178/transition/'))or path in ('/api/character/appearance','/api/factions/duty')or path=='/api/chat/send'and str(payload.get('message','')).lstrip().startswith('/')):raise ValueError('İç mekânın yükleme onayını bekle veya geçişi iptal et.')
   if path in ('/api/services178/cuff','/api/services178/prone','/api/services178/jail-offer'):
    if any(q.get('server_id')==payload.get('server_id')and active(q)for q in api.PRESENCE.values()):raise ValueError('Oyuncunun iç mekân yükleme geçişini tamamlamasını bekle.')
   if not path.startswith(PREFIX):
    result,cookie=original(path,payload,token);p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
    if result.get('success')and p and s and path=='/api/gta/sync':
     if blocked_sequences:p['hit_sequence']=max(p.get('hit_sequence',0),max(blocked_sequences));result=dict(result,hit_ack=p['hit_sequence'])
     result=dict(result,property_transition45=view(p))
     protected={q['char_id']for q in api.PRESENCE.values()if active(q)}
     result['players']=[dict(q,transition_pending45=q.get('char_id')in protected)for q in result.get('players',[])]
    return result,cookie
   auth,cookie=original('/api/auth/me',{},token)
   if not auth.get('success'):return auth,cookie
   p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
   if not p or not s or p.get('world')!='gta'or p.get('user_id')!=auth['user_id']:raise ValueError('Önce karakterinle şehre bağlan.')
   action=path[len(PREFIX):]
   if action=='status':return reply(p,s,transition=view(p)),None
   if action=='prepare':
    free(p,s)
    if active(p):raise ValueError('Önce devam eden yüklemeyi onayla veya iptal et.')
    pid,direction=payload.get('id'),payload.get('direction')
    if type(pid)is not int or pid<=0:raise ValueError('Geçerli mülk seç.')
    with api.database()as db:
     row=db.execute('SELECT *FROM pn_properties WHERE id=?',(pid,)).fetchone()
     if not row:raise ValueError('Mülk bulunamadı.')
     authorize(db,row,p,s,direction)
     source=point(s,p.get('dimension',0),row['kind']if direction=='exit'else'outdoor')
     target=point(city.INTERIOR_TYPES[row['kind']],pid,row['kind'])if direction=='enter'else point(dict(row))
     old=p.get('property45_ready')
     if bound(old,p,token)and old['until']>=clock()and old['life']==p.get('life_id',0)and old['id']==pid and old['direction']==direction and old['version']==row['version']:item=old
     else:item=dict(ticket=secrets.token_urlsafe(24),phase='prepared',uid=auth['user_id'],cid=p['char_id'],session=digest(token),id=pid,direction=direction,version=row['version'],life=p.get('life_id',0),source=source,target=target,until=clock()+PREPARE_SECONDS)
    p['property45_ready']=item;p.pop('property45_used',None)
    return reply(p,s,protocol=45,ticket=item['ticket'],source=item['source'],target=item['target'],expires_in=max(0,item['until']-clock()),confirm_timeout=CONFIRM_SECONDS),None
   if action not in ('use','confirm','rollback'):raise ValueError('Mülk geçiş işlemi bulunamadı.')
   item=find(p,token,payload.get('ticket'))
   if action=='rollback':
    if item['phase']=='prepared':
     item.update(phase='cancelled',until=clock()+30);p.pop('property45_ready',None);p['property45_used']=item
     return reply(p,s,cancelled_before_use=True,phase='cancelled'),None
    return rollback(p,s,item),None
   if action=='use':
    if type(payload.get('life_id'))is not int or payload['life_id']!=item['life']:raise ValueError('Hazırlık yaşam sürümü eşleşmedi.')
    if item['phase']in ('pending','confirmed'):
     if p.get('life_id',0)!=item['commit_life']:raise ValueError('Eski yaşam bileti yeniden kullanılamaz.')
     return reply(p,s,already_used=True,phase=item['phase'],pending_confirm=bool(active(p))),None
    if item['phase']!='prepared'or clock()>item['until']:raise ValueError('Mülk hazırlığı sona erdi; tekrar dene.')
    if type(payload.get('life_id'))is not int or payload['life_id']!=item['life']or p.get('life_id',0)!=item['life']:raise ValueError('Mülk hazırlığı farklı bir yaşama ait.')
    free(p,s);ready_ack(payload,item['target'])
    before_p,before_s=dict(p),dict(s)
    try:
     with api.database()as db:
      row=db.execute('SELECT *FROM pn_properties WHERE id=?',(item['id'],)).fetchone()
      if not row or row['version']!=item['version']:raise ValueError('Mülkün kilidi veya türü değişti; yeniden hazırla.')
      authorize(db,row,p,s,item['direction'])
      result=city.teleport(p,s,item['target'],item['target']['dimension']);journal(db,p,item,inside=True);save(p,s,db);world.audit(db,p['user_id'],'property-use45',dict(id=item['id'],direction=item['direction']))
    except Exception:p.clear();p.update(before_p);s.clear();s.update(before_s);raise
    item.update(phase='pending',commit_life=p['life_id'],until=clock()+CONFIRM_SECONDS);p.pop('property45_ready',None);p['property45_used']=item
    return dict(success=True,phase='pending',pending_confirm=True,confirm_timeout=CONFIRM_SECONDS,**result),None
   if item['phase']=='confirmed':
    if p.get('life_id',0)!=item['commit_life']or type(payload.get('life_id'))is not int or payload['life_id']!=item['commit_life']:raise ValueError('Eski yaşam onayı uygulanmadı.')
    return reply(p,s,already_confirmed=True,phase='confirmed'),None
   if not active(p):raise ValueError('Geçiş iptal edildi veya yaşam değişti; varış onaylanmadı.')
   if type(payload.get('life_id'))is not int or payload['life_id']!=item['commit_life']:raise ValueError('Varış yaşam sürümü eşleşmedi.')
   ready_ack(payload,item['target']);arrival=payload.get('arrival')
   if not isinstance(arrival,dict)or type(arrival.get('dimension'))is not int or arrival['dimension']!=item['target']['dimension']or not all(finite(arrival.get(k))for k in ('x','y','z'))or not world.near(arrival,item['target'],1.25):raise ValueError('Varış konumu doğrulanmadı.')
   if p.get('dimension',0)!=item['target']['dimension']or not world.near(s,item['target'],1.25):raise ValueError('Karakter varış noktasında değil.')
   with api.database()as db:
    if item['direction']=='exit':journal(db,p,item,inside=False)
    save(p,s,db);world.audit(db,p['user_id'],'property-confirm45',dict(id=item['id']))
   item.update(phase='confirmed',until=clock()+30)
   return reply(p,s,phase='confirmed',pending_confirm=False),None
 api.dispatch=dispatch;mp.initial=recovered_initial;api.property_transition45_installed=True;api.property_transition45_catalog=copy.deepcopy(packages)
 return api
