"""Shared two-stop lifts. Explicit install only; importing never opens a DB.

The renderer must prepare destination geometry/collision before committing a
ticket. This module grants no roles and never accepts client destination XYZ.
"""
import json,math,secrets,time

def install(api):
 if getattr(api,'elevators176_installed',False):return api
 original=api.dispatch;world=api.world
 with api.database() as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_elevators176(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,owner INTEGER NOT NULL,locked INTEGER NOT NULL DEFAULT 1 CHECK(locked IN(0,1)),a TEXT NOT NULL,b TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1,created REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_elevator_keys176(elevator_id INTEGER NOT NULL,char_id INTEGER NOT NULL,PRIMARY KEY(elevator_id,char_id))')
 def point(p,s):
  if p.get('health',200)<=100 or world.occupation(p['char_id'])[0]:raise ValueError('Asansör için hayatta ve yaya olmalısın.')
  if not all(type(s.get(k)) in (int,float) and math.isfinite(s[k]) and abs(s[k])<20000 for k in ('x','y','z','heading')):raise ValueError('Geçerli bir konum gerekli.')
  dimension=int(p.get('dimension',0));geometry={'kind':'outdoor','ipl':''}
  if dimension:
   with api.database() as db:prop=db.execute('SELECT kind FROM pn_properties WHERE id=?',(dimension,)).fetchone()
   if not prop:raise ValueError('Bu boyut için doğrulanmış iç mekân paketi yok.')
   from importlib import import_module
   city=import_module(api.__package__+'.pn_city');template=city.INTERIOR_TYPES.get(prop['kind'])
   if not template:raise ValueError('İç mekân türü hazırlanmadı.')
   geometry={'kind':'property','type':prop['kind'],'ipl':template.get('ipl','')}
  return {**{k:s[k] for k in ('x','y','z','heading')},'dimension':dimension,'geometry':geometry,'ipl':geometry['ipl']}
 def near(p,s,target,r=3):return p.get('dimension',0)==target['dimension'] and math.dist([s[k] for k in ('x','y','z')],[target[k] for k in ('x','y','z')])<=r
 def haskey(db,row,p):return row['owner']==p['char_id'] or bool(db.execute('SELECT 1 FROM pn_elevator_keys176 WHERE elevator_id=? AND char_id=?',(row['id'],p['char_id'])).fetchone())
 def at(db,row,p,s):
  here=point(p,s);a,b=json.loads(row['a']),json.loads(row['b']);choices=[(math.dist([s[k] for k in ('x','y','z')],[v[k] for k in ('x','y','z')]),side)for side,v in enumerate((a,b))if near(p,s,v)];side=min(choices)[1] if choices else None
  if side is None:raise ValueError('Asansör kapısına 3 metre içinde yaklaş.')
  return side,(b if side==0 else a)
 def snapshot(p,s,db=None):
  if db is None:
   with api.database() as current:return snapshot(p,s,current)
  found=[]
  for r in db.execute('SELECT * FROM pn_elevators176 ORDER BY id LIMIT 1000'):
   for side,k in enumerate(('a','b')):
    target=json.loads(r[k])
    if near(p,s,target,100):found.append(dict(id=r['id'],name=r['name'],locked=bool(r['locked']),has_key=haskey(db,r,p),owner=r['owner']==p['char_id'],side=side,**target))
  return found
 def dispatch(path,payload,token):
  with api.LOCK:
   raw=str(payload.get('message','')).strip();cmd=raw.split(None,1)[0].lower() if raw else ''
   ours=path.startswith('/api/elevators/') or path=='/api/chat/send' and cmd=='/addelevator'
   if not ours:
    result,cookie=original(path,payload,token)
    p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
    if result.get('success') and p and s:
     if path in ('/api/gta/sync','/api/elevators/list'):result=dict(result,elevators=snapshot(p,s))
     if path=='/api/storage/list':
      with api.database() as db:keys=[dict(id=r['id'],name=r['name'],item_id=900000+r['id'],type='elevator-key',image='/pn/assets-v19/items/keys.png') for r in db.execute('SELECT id,name FROM pn_elevators176 WHERE owner=? OR id IN(SELECT elevator_id FROM pn_elevator_keys176 WHERE char_id=?)',(p['char_id'],p['char_id']))]
      items=[]
      with api.database() as db:
       for item in result.get('items',[]):
        item=dict(item);context=item.get('context','')
        if context.startswith('drop:'):
         drop=db.execute('SELECT g.owner,g.created,c.name,c.surname FROM pn_ground g LEFT JOIN characters c ON c.id=g.owner WHERE g.id=?',(context[5:],)).fetchone()
         if drop:item.update(dropped_by=(' '.join(v for v in (drop['name'],drop['surname']) if v) or 'Bilinmeyen kişi'),dropped_by_char_id=drop['owner'],dropped_at=drop['created'])
        items.append(item)
      result=dict(result,keys=result.get('keys',[])+keys,items=items)
    return result,cookie
   checked,cookie=original('/api/auth/me',{},token)
   if not checked.get('success'):return checked,cookie
   p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
   if not p or not s:raise ValueError('Önce şehre bağlan.')
   uid=checked['user_id'];now=time.time()
   if path=='/api/elevators/rollback':
    pending=p.get('elevator176_ready');ticket=payload.get('ticket');cancelled=p.get('elevator176_cancelled')
    if isinstance(ticket,str) and (pending and secrets.compare_digest(ticket,pending['ticket']) or cancelled and secrets.compare_digest(ticket,cancelled['ticket'])):
     if pending and secrets.compare_digest(ticket,pending['ticket']):p.pop('elevator176_ready',None)
     p['elevator176_cancelled']={'ticket':ticket,'at':now}
     return dict(success=True,cancelled_before_use=True,spawn={**{k:s[k]for k in ('x','y','z','heading')},'health':p['health'],'armor':p.get('armor',0)},life_id=p.get('life_id',0),dimension=p.get('dimension',0),notice='Hazırlık iptal edildi; sunucu konumu korundu.'),None
    used=p.get('elevator176_used');ticket=payload.get('ticket')
    if not used or not isinstance(ticket,str) or not secrets.compare_digest(ticket,used['ticket']):raise ValueError('Geri dönüş kaydı bulunamadı.')
    if used.get('rolled_back'):return dict(success=True,already_rolled_back=True,notice='Güvenli geri dönüş zaten tamamlandı.'),None
    if now-used['at']>30 or p.get('life_id')!=used['life_id']:raise ValueError('Geri dönüş süresi veya oturumu sona erdi.')
    target=used['target']
    if p.get('dimension',0)!=target['dimension'] or math.hypot(s['x']-target['x'],s['y']-target['y'])>5 or world.occupation(p['char_id'])[0]:raise ValueError('Asansör varışından uzaklaşıldı; geri dönüş yapılamaz.')
    from importlib import import_module
    city=import_module(api.__package__+'.pn_city');source=used['source'];result=city.teleport(p,s,source,source['dimension']);used['rolled_back']=True
    with api.database() as db:world.audit(db,uid,'elevator-rollback176',{'id':used['id']})
    return dict(success=True,notice='Varış zemini hazır değildi; güvenli başlangıç noktasına dönüldü.',**result),None
   world.live(p,s);here=point(p,s)
   if cmd=='/addelevator' and path=='/api/chat/send':
    if api.staff.rank(uid)<2:raise ValueError('Asansör oluşturma yöneticiye açık.')
    name=raw.partition(' ')[2].strip()
    if name.lower() in ('iptal','cancel'):
     p.pop('elevator176_pending',None);return dict(success=True,notice='Asansör oluşturma iptal edildi.'),None
    pending=p.get('elevator176_pending')
    if not pending or now-pending['at']>300:
     name=name or 'Asansör'
     if not 3<=len(name)<=48 or any(ord(c)<32 for c in name):raise ValueError('Asansör adı 3–48 karakter olmalı.')
     p['elevator176_pending']={'point':here,'name':name,'at':now}
     return dict(success=True,notice='İlk kapı kaydedildi. İkinci konuma gidip /addelevator yaz. İptal: /addelevator iptal'),None
    if near(p,s,pending['point'],1):raise ValueError('İkinci kapı ilkinden en az 1 metre uzakta olmalı.')
    with api.database() as db:
     eid=db.execute('INSERT INTO pn_elevators176(name,owner,a,b,created) VALUES(?,?,?,?,?)',(pending['name'],p['char_id'],json.dumps(pending['point']),json.dumps(here),now)).lastrowid
     world.audit(db,uid,'elevator-create176',{'id':eid,'char_id':p['char_id']})
    p.pop('elevator176_pending',None)
    return dict(success=True,elevator_id=eid,notice=f'Asansör #{eid} oluşturuldu; anahtarı karakterinde, kapı kilitli.'),None
   action=path.rsplit('/',1)[-1]
   if action=='list':return dict(success=True,elevators=snapshot(p,s)),None
   if action=='use':
    ticket=payload.get('ticket');used=p.get('elevator176_used')
    if isinstance(ticket,str) and used and secrets.compare_digest(ticket,used['ticket']):return dict(success=True,already_used=True,notice='Asansör geçişi zaten tamamlandı.'),None
    ready=p.get('elevator176_ready')
    if not ready or not isinstance(ticket,str) or not secrets.compare_digest(ticket,ready['ticket']) or now>ready['until']:raise ValueError('Asansör hazırlığı sona erdi; yeniden dene.')
    if ready['life_id']!=p.get('life_id',0) or ready['dimension']!=p.get('dimension',0):raise ValueError('Asansör hazırlığı farklı bir oturuma ait.')
    if payload.get('ready') is not True:raise ValueError('İç mekân ve zemin hazır olmadan geçiş yapılamaz.')
    eid=ready['id']
   else:
    eid=payload.get('id')
    if type(eid) is not int or eid<=0:raise ValueError('Geçerli asansör seç.')
   with api.database() as db:
    row=db.execute('SELECT * FROM pn_elevators176 WHERE id=?',(eid,)).fetchone()
    if not row:raise ValueError('Asansör bulunamadı.')
    side,target=at(db,row,p,s);key=haskey(db,row,p)
    if action in ('lock','give-key','revoke-key'):
     if not key:raise ValueError('Asansör anahtarın yok.')
     if action=='lock':db.execute('UPDATE pn_elevators176 SET locked=1-locked,version=version+1 WHERE id=?',(eid,))
     else:
      if row['owner']!=p['char_id']:raise ValueError('Anahtar dağıtımı yalnız sahibine açık.')
      target_id=world.resolve_player_id(payload.get('server_id'),api.PRESENCE)
      if action=='give-key':
       peer=next((q for q in api.PRESENCE.values() if q['char_id']==target_id),None);state=next((q for q in api.GTA_STATE.values() if q['char_id']==target_id),None)
       if not peer or not state or not near(peer,state,here):raise ValueError('Anahtarı alacak oyuncu yanına gelmeli.')
       db.execute('INSERT OR IGNORE INTO pn_elevator_keys176 VALUES(?,?)',(eid,target_id))
      else:db.execute('DELETE FROM pn_elevator_keys176 WHERE elevator_id=? AND char_id=?',(eid,target_id))
     world.audit(db,uid,'elevator-'+action,{'id':eid});return dict(success=True,elevators=snapshot(p,s,db),notice='Asansör anahtar/kilit işlemi kaydedildi.'),None
    if row['locked'] and not key:raise ValueError('Asansör kilitli; anahtar gerekli.')
    if action=='prepare':
     ticket=secrets.token_hex(16);p['elevator176_ready']={'ticket':ticket,'id':eid,'side':side,'version':row['version'],'until':now+20,'life_id':p.get('life_id',0),'dimension':p.get('dimension',0)}
     return dict(success=True,ticket=ticket,target=target,expires_in=20),None
    if action!='use':raise ValueError('Asansör işlemi bulunamadı.')
    if ready['side']!=side or ready['version']!=row['version']:raise ValueError('Asansör kilidi veya konumu değişti; tekrar hazırla.')
    from importlib import import_module
    city=import_module(api.__package__+'.pn_city');result=city.teleport(p,s,target,target['dimension'])
    p['elevator176_used']={'ticket':ticket,'at':now,'life_id':p['life_id'],'source':here,'target':target,'id':eid};p.pop('elevator176_ready',None);world.audit(db,uid,'elevator-use176',{'id':eid,'side':side})
    return dict(success=True,notice='Asansör geçişi tamamlandı.',**result),None
 api.dispatch=dispatch;api.elevators176_installed=True;return api
