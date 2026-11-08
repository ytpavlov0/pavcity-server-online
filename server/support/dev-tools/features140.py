"""140 over the live v135 chain: staff property (interior) commands in chat.

/interiors [arama]      every property: id, name, interior type, owner, price, lock, players inside (rank 2+)
/delint ID [zorla]      deletes a property and its keys (rank 2+); refused while someone is inside, and while items
                        lie on the floor inside unless 'zorla' is given (those items are removed with it)."""
import re
def install(api):
 if getattr(api,'features140_installed',False):return api
 w=api.world;previous=api.dispatch
 import gameplay_v29.pn_admin as staff
 import gameplay_v29.pn_city as city
 def me(token):
  uid=api.authenticated61(token);p=api.PRESENCE.get(token)
  if not uid or not p:raise ValueError('Önce karakterinle şehre gir.')
  if staff.rank(uid)<2:raise ValueError('Yönetici yetkisi gerekli.')
  return uid,p
 def inside(id):return sum(1 for x in api.PRESENCE.values() if x.get('dimension',0)==id)
 def interiors(token,args):
  uid,p=me(token);q=' '.join(args).strip().lower()
  with w.database()as db:
   rows=[dict(r)for r in db.execute("SELECT p.id,p.name,p.kind,p.price,p.owner,p.locked,COALESCE(c.name||' '||c.surname,'') owner_name FROM pn_properties p LEFT JOIN characters c ON c.id=p.owner ORDER BY p.id")]
  if q:rows=[r for r in rows if q in r['name'].lower()or q in r['owner_name'].lower()or q==str(r['id'])]
  out=[['#'+str(r['id']),r['name'],city.INTERIOR_TYPES.get(r['kind'],{}).get('name',r['kind']),(r['owner_name'].strip()or'#'+str(r['owner']))if r['owner']else'Satılık','$'+format(r['price'],',').replace(',','.'),'Kilitli'if r['locked']else'Açık',('İçeride '+str(inside(r['id'])))if inside(r['id'])else'']for r in rows[:200]]
  return dict(success=True,info=dict(title='Mülkler · %d kayıt%s'%(len(rows),' · "'+q+'"'if q else''),rows=out or[['—','Mülk bulunamadı.']]),notice='%d mülk listelendi. Silmek için /delint ID'%len(rows))
 def delint(token,args):
  uid,p=me(token)
  if not args or not re.fullmatch(r'\d{1,9}',args[0])or(len(args)>1 and args[1].lower()!='zorla')or len(args)>2:raise ValueError('Kullanım: /delint MÜLK_ID [zorla] · liste: /interiors')
  id=int(args[0]);force=len(args)==2
  if inside(id):raise ValueError('Mülk #%d içinde oyuncu var; önce çıkmalarını bekle.'%id)
  with w.database()as db:
   row=db.execute('SELECT id,name,owner,kind,price FROM pn_properties WHERE id=?',(id,)).fetchone()
   if not row:raise ValueError('Mülk #%d bulunamadı.'%id)
   items=db.execute('SELECT COUNT(*) FROM pn_ground WHERE dimension=?',(id,)).fetchone()[0]
   if items and not force:raise ValueError('Mülk #%d içinde yerde %d eşya var. Yine de silmek için: /delint %d zorla'%(id,items,id))
   keys=db.execute('DELETE FROM pn_property_keys WHERE property_id=?',(id,)).rowcount
   if items:db.execute('DELETE FROM pn_ground WHERE dimension=?',(id,))
   db.execute('DELETE FROM pn_properties WHERE id=?',(id,))
   w.audit(db,uid,'delint140',dict(property=id,name=row['name'],owner=row['owner'],kind=row['kind'],price=row['price'],keys=keys,ground_items=items))
  return dict(success=True,notice='Mülk #%d (%s) silindi%s.'%(id,row['name'],(' · %d anahtar'%keys if keys else'')+(' · yerdeki %d eşya'%items if items else'')))
 def dispatch(path,v,token):
  if path=='/api/chat/send'and isinstance(v,dict):
   parts=str(v.get('message','')).strip().split()
   if parts and parts[0].lower()in('/interiors','/delint'):
    with api.LOCK:return(interiors if parts[0].lower()=='/interiors'else delint)(token,parts[1:]),None
  return previous(path,v,token)
 api.dispatch=dispatch;api.features140_installed=True;return api
