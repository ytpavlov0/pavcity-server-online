"""Faction-owned properties using the existing persistent key/transition policy.

Negative owner IDs name factions, positive IDs retain character ownership.
Membership keys are durable and revoked by DB triggers, never temporarily forged.
"""
import importlib,time

def install(api):
 if getattr(api,'property63_installed',False):return api
 city=importlib.import_module(api.__package__+'.pn_city');w=api.world
 previous=api.dispatch;old_city=city.dispatch
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_property_factions63(property_id INTEGER PRIMARY KEY,faction_id INTEGER NOT NULL,created REAL NOT NULL)')
  db.execute('CREATE INDEX IF NOT EXISTS pn_property_factions63_fac ON pn_property_factions63(faction_id)')
  db.executescript('''
CREATE TRIGGER IF NOT EXISTS pn_prop63_member_add AFTER INSERT ON pn_faction_members BEGIN
 DELETE FROM pn_property_keys WHERE char_id=NEW.char_id AND property_id IN(SELECT property_id FROM pn_property_factions63);
 INSERT OR IGNORE INTO pn_property_keys SELECT property_id,NEW.char_id FROM pn_property_factions63 WHERE faction_id=NEW.faction_id;
 UPDATE pn_properties SET version=version+1 WHERE id IN(SELECT property_id FROM pn_property_factions63 WHERE faction_id=NEW.faction_id);
END;
CREATE TRIGGER IF NOT EXISTS pn_prop63_member_remove AFTER DELETE ON pn_faction_members BEGIN
 DELETE FROM pn_property_keys WHERE char_id=OLD.char_id AND property_id IN(SELECT property_id FROM pn_property_factions63);
 UPDATE pn_properties SET version=version+1 WHERE id IN(SELECT property_id FROM pn_property_factions63 WHERE faction_id=OLD.faction_id);
END;
CREATE TRIGGER IF NOT EXISTS pn_prop63_member_move AFTER UPDATE OF faction_id,char_id ON pn_faction_members BEGIN
 DELETE FROM pn_property_keys WHERE char_id IN(OLD.char_id,NEW.char_id) AND property_id IN(SELECT property_id FROM pn_property_factions63);
 INSERT OR IGNORE INTO pn_property_keys SELECT property_id,NEW.char_id FROM pn_property_factions63 WHERE faction_id=NEW.faction_id;
 UPDATE pn_properties SET version=version+1 WHERE id IN(SELECT property_id FROM pn_property_factions63 WHERE faction_id IN(OLD.faction_id,NEW.faction_id));
END;''')

 def dispatch_city(path,uid,token,payload,p,s,presences):
  action=path.rsplit('/',1)[-1]
  if not path.startswith('/api/properties/'):return old_city(path,uid,token,payload,p,s,presences)
  if action not in ('buy-faction','transfer-faction','sell-faction','give-key','revoke-key','edit'):
   return old_city(path,uid,token,payload,p,s,presences)
  if not p or not s:raise ValueError('Önce karakterinle şehre bağlan.')
  w.live(p,s);pid=payload.get('id')
  if type(pid)is not int or pid<=0:raise ValueError('Geçerli mülk seç.')
  with api.database()as db:
   row=db.execute('SELECT *FROM pn_properties WHERE id=?',(pid,)).fetchone()
   if not row:raise ValueError('Mülk bulunamadı.')
   faction=db.execute('SELECT *FROM pn_property_factions63 WHERE property_id=?',(pid,)).fetchone()
   if action in ('give-key','revoke-key'):
    if faction:raise ValueError('Birlik mülkünün anahtarları üyelikle yönetilir; birlikten ayrılanın anahtarı kaldırılır.')
    return old_city(path,uid,token,payload,p,s,presences)
   if action=='edit':
    if payload.get('kind',row['kind'])!=row['kind']and payload.get('kind')not in ('apartment','garage','office','market'):raise ValueError('Bu iç mekân paketi yüklü değil. Kullanılabilir türler: daire, garaj, ofis ve market.')
    return old_city(path,uid,token,payload,p,s,presences)
   if p.get('dimension',0)or w.occupation(p['char_id'])[0]or s.get('vehicle_id')or not w.near(s,row,3):raise ValueError('Mülkün dış kapısına yaya olarak yaklaş (3 m).')
   member=db.execute('SELECT m.*,f.name FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id WHERE m.char_id=?',(p['char_id'],)).fetchone()
   if not member or not member['leader']:raise ValueError('Bu işlem birlik liderine açık.')
   fid=member['faction_id']
   if any(q.get('dimension',0)==pid for q in presences.values()):raise ValueError('Önce mülkün boşalmasını bekle.')
   if action=='sell-faction':
    if not faction or faction['faction_id']!=fid:raise ValueError('Bu mülk birliğine ait değil.')
    amount=row['price']//2
    db.execute('UPDATE pn_factions SET bank=bank+? WHERE id=?',(amount,fid))
    db.execute('DELETE FROM pn_property_keys WHERE property_id=?',(pid,))
    db.execute('DELETE FROM pn_property_factions63 WHERE property_id=?',(pid,))
    db.execute('UPDATE pn_properties SET owner=0,locked=1,version=version+1 WHERE id=?',(pid,))
    notice=f'Mülk satıldı; ${amount:,} birlik kasasına yatırıldı.'
   else:
    if row['kind']not in ('apartment','garage','office','market'):raise ValueError('Bu mülkün iç mekân paketi hazır değil; satın alma veya devir yapılamaz.')
    if faction:raise ValueError('Mülk zaten bir birliğe ait.')
    if action=='buy-faction':
     if row['owner']:raise ValueError('Mülkün sahibi var.')
     if db.execute('UPDATE pn_factions SET bank=bank-? WHERE id=? AND bank>=?',(row['price'],fid,row['price'])).rowcount!=1:raise ValueError('Birlik kasasında yeterli para yok.')
    elif row['owner']!=p['char_id']:raise ValueError('Yalnız kendi mülkünü birliğine devredebilirsin.')
    db.execute('INSERT INTO pn_property_factions63 VALUES(?,?,?)',(pid,fid,time.time()))
    db.execute('UPDATE pn_properties SET owner=?,locked=1,version=version+1 WHERE id=?',(-fid,pid))
    db.execute('DELETE FROM pn_property_keys WHERE property_id=?',(pid,))
    db.execute('INSERT INTO pn_property_keys SELECT ?,char_id FROM pn_faction_members WHERE faction_id=?',(pid,fid))
    notice='Mülk '+member['name']+' adına kaydedildi. Anahtarlar birlik üyelerine bağlı.'
   w.audit(db,uid,'property-'+action,dict(id=pid,faction_id=fid))
  return dict(success=True,notice=notice,money=w.wallet(uid))
 city.dispatch=dispatch_city

 def dispatch(path,payload,token):
  with api.LOCK:
   if path=='/api/chat/send':
    args=str(payload.get('message','')).strip().split()
    if args and args[0].lower()=='/addint'and len(args)>1 and args[1].lower()not in('apartment','garage','office','market'):
     raise ValueError('Bu iç mekân paketi yüklü değil. /addint apartment|garage|office|market fiyat ad kullan.')
   result,cookie=previous(path,payload,token)
   if result.get('success')and path in('/api/properties/list','/api/gta/sync'):
    p=api.PRESENCE.get(token)
    if p:
     with api.database()as db:
      member=db.execute('SELECT m.*,f.name FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id WHERE m.char_id=?',(p['char_id'],)).fetchone()
      result['property_faction63']=dict(id=member['faction_id'],name=member['name'],leader=bool(member['leader']))if member else None
      ids=[v['id']for v in result.get('properties',[])]
      owners={row['property_id']:row for row in db.execute('SELECT x.property_id,f.id,f.name FROM pn_property_factions63 x JOIN pn_factions f ON f.id=x.faction_id WHERE x.property_id IN('+','.join('?'for _ in ids)+')',ids)}if ids else{}
      for v in result.get('properties',[]):
       owner=owners.get(v['id'])
       if owner:
        same=bool(member and member['faction_id']==owner['id'])
        v.update(owner_name=owner['name']+' · Birlik',faction_owner=owner['id'],faction_key=same,faction_manage=same and bool(member['leader']))
   return result,cookie
 api.dispatch=dispatch;api.property63_installed=True
 return api
