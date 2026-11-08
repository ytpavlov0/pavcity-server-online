"""Explicit faction closure and revocable rank-aware police credentials."""
import time,secrets
def install(api):
 if getattr(api,'factions85_installed',False):return api
 import gameplay_v29.pn_roleplay as rp
 old,view,previous=rp.faction_action,rp.faction_view,api.dispatch
 cache={};cache_at=0
 with api.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_badges85(char_id INTEGER PRIMARY KEY,faction_id INTEGER NOT NULL,serial TEXT NOT NULL UNIQUE,issuer INTEGER NOT NULL,created REAL NOT NULL)')
 def badge(db,cid):
  r=db.execute('''SELECT b.serial,b.char_id,b.faction_id,f.name AS faction,c.name||' '||c.surname AS name,m.rank,r.title
   FROM pn_badges85 b JOIN pn_faction_members m ON m.char_id=b.char_id AND m.faction_id=b.faction_id
   JOIN pn_factions f ON f.id=m.faction_id JOIN characters c ON c.id=m.char_id
   JOIN pn_faction_ranks r ON r.faction_id=m.faction_id AND r.rank=m.rank
   WHERE b.char_id=? AND f.kind='police' ''',(cid,)).fetchone()
  return dict(r)if r else None
 def faction_view(db,cid):
  r=view(db,cid)
  for m in r.get('members',[]):m['badge85']=badge(db,m['char_id'])
  return r
 def action(db,act,uid,cid,v,p,s,peers,releases):
  if act not in('disband','leave-transfer','badge-issue','badge-revoke'):return old(db,act,uid,cid,v,p,s,peers,releases)
  m=rp.lead(db,cid);fid=m['faction_id']
  if act.startswith('badge-'):
   if m['kind']!='police':raise ValueError('Rozet yalnız polis birliğinde düzenlenebilir.')
   target=rp.integer(v.get('char_id'));member=rp.membership(db,target)
   if not member or member['faction_id']!=fid:raise ValueError('Oyuncu birliğinin üyesi değil.')
   if act=='badge-issue':
    prior=badge(db,target)
    if not prior:db.execute('INSERT OR REPLACE INTO pn_badges85 VALUES(?,?,?,?,?)',(target,fid,m['tag']+'-'+secrets.token_hex(3).upper(),cid,time.time()))
   else:db.execute('DELETE FROM pn_badges85 WHERE char_id=? AND faction_id=?',(target,fid))
  elif act=='leave-transfer':
   target=rp.integer(v.get('char_id'));member=rp.membership(db,target)
   if target==cid or not member or member['faction_id']!=fid:raise ValueError('Birliğinden başka bir üyeyi yeni lider seç.')
   db.execute('UPDATE pn_faction_members SET leader=CASE WHEN char_id=? THEN 1 ELSE 0 END WHERE faction_id=?',(target,fid))
   old(db,'leave',uid,cid,v,p,s,peers,releases)
  else:
   if str(v.get('confirm','')).strip()!=m['tag']:raise ValueError('Kapatmayı onaylamak için birlik etiketini aynen yaz.')
   if m['kind']in('police','medical'):raise ValueError('Resmî kurum kapatılamaz. Liderliği devrederek ayrılabilirsin.')
   # Preserve member-owned cars and transfer treasury/fleet/property assets to the closing leader.
   fleet=[r[0]for r in db.execute('SELECT vehicle_id FROM pn_faction_fleet69 WHERE faction_id=?',(fid,))]
   for vid in fleet:
    if api.world.occupation(cid)[0]==vid or any(k[0]==vid for k in api.world.SEATS):raise ValueError('Önce birlik filo araçlarını boşaltıp parka bırakın.')
    db.execute('UPDATE pn_vehicles SET owner=?,active=0,updated=? WHERE id=?',(cid,time.time(),vid));db.execute('DELETE FROM pn_vehicle_access WHERE vehicle_id=?',(vid,));db.execute('INSERT INTO pn_vehicle_access VALUES(?,?)',(vid,cid))
   props=[r[0]for r in db.execute('SELECT property_id FROM pn_property_factions63 WHERE faction_id=?',(fid,))]
   for pid in props:
    if any(q.get('dimension')==pid for q in peers.values()):raise ValueError('Birlik mülkündeki oyuncular önce dışarı çıkmalı.')
   for q in peers.values():
    member=rp.membership(db,q['char_id'])
    if member and member['faction_id']==fid:rp.release_shared_seat(db,q['char_id'],fid,releases)
   db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(m['bank'],uid))
   db.execute('DELETE FROM pn_faction_members WHERE faction_id=?',(fid,))
   for pid in props:
    db.execute('DELETE FROM pn_property_keys WHERE property_id=?',(pid,));db.execute('UPDATE pn_properties SET owner=?,version=version+1 WHERE id=?',(cid,pid));db.execute('DELETE FROM pn_property_factions63 WHERE property_id=?',(pid,))
   for table in('pn_badges85','pn_faction_vehicles','pn_faction_fleet69','pn_faction_duty','pn_faction_ranks','pn_faction_invites'):
    db.execute('DELETE FROM '+table+' WHERE faction_id=?',(fid,))
   # Depot schema uses faction_id, same as the fleet service.
   db.execute('DELETE FROM pn_faction_depot69 WHERE faction_id=?',(fid,));db.execute('DELETE FROM pn_factions WHERE id=?',(fid,))
  api.world.audit(db,uid,'faction85-'+act,dict(char_id=cid,faction_id=fid,target=v.get('char_id')))
  return dict(faction=faction_view(db,cid),on_duty=bool(p.get('faction_duty')),notice='Birlik işlemi tamamlandı.')
 def dispatch(path,v,token):
  nonlocal cache_at,cache
  r,c=previous(path,v,token)
  if r.get('success')and path.startswith('/api/factions/')and not path.endswith('/list'):
   cache_at=0
   with api.database()as db:
    db.execute('DELETE FROM pn_badges85 WHERE NOT EXISTS(SELECT 1 FROM pn_faction_members m WHERE m.char_id=pn_badges85.char_id AND m.faction_id=pn_badges85.faction_id)')
    for q in api.PRESENCE.values():
     m=rp.membership(db,q['char_id'])
     if not m:
      q.pop('faction_duty',None);q.pop('duty_started',None)
  if r.get('success')and path in('/api/gta/sync','/api/gta/roster','/api/storage/list'):
   if time.monotonic()-cache_at>1:
    with api.database()as db:
     ids=[row[0]for row in db.execute('SELECT char_id FROM pn_badges85')];cache={cid:b for cid in ids if (b:=badge(db,cid))}
    cache_at=time.monotonic()
   live={q['char_id']:q for q in api.PRESENCE.values()}
   for peer in r.get('players',[]):
    cid=peer.get('char_id',peer.get('id'));q=live.get(cid);peer['police_badge']=cache.get(cid)if q and q.get('faction_duty')else None
   q=api.PRESENCE.get(token);r['badge85']=cache.get(q['char_id'])if q and q.get('faction_duty')else None
  return r,c
 rp.faction_action=action;rp.faction_view=faction_view;api.dispatch=dispatch;api.factions85_installed=True;return api
