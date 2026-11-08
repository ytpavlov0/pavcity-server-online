"""Read-only property permission fence before native streaming; no tickets/schema."""
import importlib

def install(api):
 if getattr(api,'property_preflight48_installed',False):return api
 city=importlib.import_module(api.__package__+'.pn_city');world=api.world;original=city.dispatch
 def check(uid,p,s,payload):
  if not p or p.get('world')!='gta':raise ValueError('Önce karakterinle şehre bağlan.')
  world.live(p,s)
  pid=payload.get('id')
  if type(pid)is not int or pid<1:raise ValueError('Geçerli mülk seç.')
  if p.get('dimension',0):raise ValueError('Önce bulunduğun mülkten çık.')
  if world.occupation(p['char_id'])[0]or s.get('vehicle_id'):raise ValueError('Mülkün kapısına yaya yaklaş.')
  with api.database()as db:
   r=db.execute('SELECT *FROM pn_properties WHERE id=?',(pid,)).fetchone()
   if not r:raise ValueError('Mülk bulunamadı.')
   row=dict(r)
   if not world.near(s,row,3):raise ValueError('Mülkün dış kapısına 3 metre içinde yaklaş.')
   key=row['owner']==p['char_id']or bool(db.execute('SELECT 1 FROM pn_property_keys WHERE property_id=?AND char_id=?',(pid,p['char_id'])).fetchone())
   if row['locked']and not key:raise ValueError('Kapı kilitli; anahtarın yok. Satılık mülkü önce satın almalısın.'if not row['owner']else'Kapı kilitli; anahtarın yok.')
   if row['kind']not in('apartment','garage','office','market'):raise ValueError('Bu iç mekân paketi hazır değil.')
  t=city.INTERIOR_TYPES[row['kind']]
  return dict(success=True,id=pid,version=row['version'],life_id=p.get('life_id',0),target={**t,'dimension':pid,'geometry':dict(kind='property',type=row['kind'],ipl=t.get('ipl',''))},observation_only=True)
 def dispatch(path,uid,token,payload,p,s,presences):
  if path=='/api/properties/preflight48':
   with api.LOCK:return check(uid,p,s,payload)
  if path=='/api/properties/enter'and 'preflight_version'in payload:
   with api.LOCK:
    ready=check(uid,p,s,payload)
    if type(payload['preflight_version'])is not int or payload['preflight_version']!=ready['version']or type(payload.get('preflight_life'))is not int or payload['preflight_life']!=ready['life_id']:raise ValueError('Mülk veya karakter değişti; kapıyı yeniden aç.')
    return original(path,uid,token,payload,p,s,presences)
  return original(path,uid,token,payload,p,s,presences)
 city.dispatch=dispatch;api.property_preflight48_installed=True;return api
