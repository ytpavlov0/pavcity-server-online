"""Police duty zones are dimension-aware; credentials can be revoked immediately."""
import time
HQ=dict(id=17801,kind='police',name='Mission Row · Polis görev merkezi',x=441.2,y=-981.9,z=30.69,radius=3,sprite=60,color=3)

def install(api):
 if getattr(api,'duty90_installed',False):return api
 from gameplay_v29 import pn_roleplay as rp
 from restriction82 import free_actor
 old,view,previous=rp.faction_action,rp.faction_view,api.dispatch
 def seed(db,fid):
  if not db.execute('SELECT 1 FROM pn_faction_duty WHERE faction_id=?',(fid,)).fetchone():
   db.execute('INSERT INTO pn_faction_duty(faction_id,name,x,y,z,min_rank,armor) VALUES(?,?,?,?,?,20,100)',(fid,'Mission Row · Polis görevi',HQ['x'],HQ['y'],HQ['z']))
 with api.database()as db:
  for r in db.execute("SELECT id FROM pn_factions WHERE kind='police'").fetchall():seed(db,r['id'])
 def faction_view(db,cid):
  r=view(db,cid);m=r.get('member')
  if m:
   q=next((p for p in api.PRESENCE.values()if p['char_id']==cid),None)
   s=next((s for s in api.GTA_STATE.values()if s.get('char_id')==cid),None)
   has_badge=bool(db.execute('SELECT 1 FROM pn_badges85 WHERE char_id=? AND faction_id=?',(cid,m['faction_id'])).fetchone())
   r['duty90']=dict(badge_required=m['kind']=='police',has_badge=has_badge,current_dimension=q.get('dimension',0)if q else 0)
   for point in r.get('duty',[]):
    point['dimension']=0;point['near90']=bool(q and s and not q.get('dimension',0)and api.world.near(s,point,3))
  return r
 def action(db,act,uid,cid,v,p,s,peers,releases):
  m=rp.membership(db,cid)
  if act=='duty-hq':
   m=rp.lead(db,cid)
   if m['kind']!='police':raise ValueError('Merkez görev bölgesi yalnız polis birliği içindir.')
   seed(db,m['faction_id']);return dict(faction=rp.faction_view(db,cid),on_duty=bool(p.get('faction_duty')),notice='Polis görev bölgesi hazır. Görev sekmesinden GPS açabilirsin.')
  if act in('duty','duty-create'):
   api.world.live(p,s);free_actor(api,p,time.time())
   if p.get('elevator176_ready'):raise ValueError('Önce iç mekân geçişini tamamla.')
   if act=='duty'and not p.get('faction_duty'):
    point=db.execute('SELECT * FROM pn_faction_duty WHERE id=?',(rp.integer(v.get('point')),)).fetchone()
    if not m or not point or point['faction_id']!=m['faction_id']or p.get('dimension',0)!=0:raise ValueError('Birliğinin görev bölgesinde ve aynı iç mekânda olmalısın.')
    if m['kind']=='police'and not db.execute('SELECT 1 FROM pn_badges85 WHERE char_id=? AND faction_id=?',(cid,m['faction_id'])).fetchone():raise ValueError('Önce birlik lideri Üyeler sekmesinden adına rozet düzenlemeli.')
   if act=='duty-create'and(p.get('dimension',0)or s.get('vehicle_id')or api.world.occupation(cid)[0]):raise ValueError('Görev bölgesini dış dünyada, yaya oluştur.')
  result=old(db,act,uid,cid,v,p,s,peers,releases)
  if act=='create':
   m=rp.membership(db,cid)
   if m and m['kind']=='police':seed(db,m['faction_id']);result['faction']=rp.faction_view(db,cid)
  return result
 def dispatch(path,v,token):
  command=str(v.get('message','')).strip().lower()
  if path=='/api/chat/send'and command in('/duty','/pduty','/mduty'):
   with api.LOCK:
    uid=api.authenticated61(token);api.require_client61(token,v);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
    if not uid or not p or p['user_id']!=uid:raise ValueError('Önce şehre gir.')
    api.world.live(p,s)
    with api.database()as db:
     m=rp.membership(db,p['char_id'])
     if not m or command=='/pduty'and m['kind']!='police'or command=='/mduty'and m['kind']!='medical':raise ValueError('Uygun birlik üyeliğin bulunmuyor.')
     points=rp.faction_view(db,p['char_id']).get('duty',[])
     point=next((r for r in points if r['near90']),None)
     if not p.get('faction_duty')and not point:raise ValueError('Birliğinin görev noktasına yaya, 3 metre içinde yaklaş.')
    return dispatch('/api/factions/duty',dict(v,point=point['id']if point else p['faction_duty']),token)
  if not path.startswith('/api/factions/')or path.endswith('/list'):return previous(path,v,token)
  with api.LOCK:
   before={q['char_id']:(q.get('faction_duty'),q.get('duty_original_armor',0))for q in api.PRESENCE.values()if q.get('faction_duty')}
   result,cookie=previous(path,v,token)
   if result.get('success'):
    with api.database()as db:
     states={s.get('char_id'):s for s in api.GTA_STATE.values()}
     for q in api.PRESENCE.values():
      if not q.get('faction_duty')and q['char_id']not in before:continue
      m=rp.membership(db,q['char_id']);point=db.execute('SELECT * FROM pn_faction_duty WHERE id=?',(q.get('faction_duty',0),)).fetchone()
      valid=bool(m and point and m['faction_id']==point['faction_id']and m['rank']<=point['min_rank'])
      if valid and m['kind']=='police':valid=bool(db.execute('SELECT 1 FROM pn_badges85 WHERE char_id=? AND faction_id=?',(q['char_id'],m['faction_id'])).fetchone())
      if not valid:
       original=q.pop('duty_original_armor',before.get(q['char_id'],(0,0))[1]);q.pop('faction_duty',None);q.pop('duty_started',None);q['armor']=min(q.get('armor',0),original);q['armor_ready_at']=time.time()+1
       if q['char_id']in states:
        s=states[q['char_id']];s['armor']=q['armor']
        from gameplay_v29.pn_multiplayer import save
        save(q,s,True,db)
    if 'on_duty'in result:result['on_duty']=bool(api.PRESENCE.get(token,{}).get('faction_duty'))
   return result,cookie
 rp.faction_view=faction_view;rp.faction_action=action;api.dispatch=dispatch;api.duty90_installed=True;return api
