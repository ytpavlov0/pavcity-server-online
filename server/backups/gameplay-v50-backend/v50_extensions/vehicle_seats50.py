"""Actor-only immediate seat snapshots and protocol200 generation fences.
No schema, grants or stored-account mutation on installation.
"""
import secrets

def install(api):
 if getattr(api,'vehicle_seats50_installed',False):return api
 world=api.world;old_remove=world.remove_seat;old_vehicle=world.dispatch;old_sample=world.validate_sample;original=api.dispatch;counter=[secrets.randbits(40)<<8]
 def actors(cid):return[p for p in api.PRESENCE.values()if p.get('char_id')==cid]
 def epoch(p):
  if type(p.get('seat_epoch'))is not int:counter[0]+=1;p['seat_epoch']=counter[0]
  return p['seat_epoch']
 def align(cid,bump=False):
  vid,seat=world.occupation(cid)
  for p in actors(cid):
   if bump:counter[0]+=1;p['seat_epoch']=counter[0]
   epoch(p)
   if not vid:p['seatbelt']=False
  for s in api.GTA_STATE.values():
   if s.get('char_id')==cid:s.update(vehicle_id=vid,seat=seat,seatbelt=bool(vid and next((p.get('seatbelt',False)for p in actors(cid)),False)))
 def remove(key):
  entry=world.SEATS.get(key);cid=entry.get('char_id')if entry else None;old_remove(key)
  if cid is not None:align(cid,True)
 def observed(p,**extra):
  vid,seat=world.occupation(p['char_id']);return dict(success=True,vehicle_id=vid,seat=seat,seat_epoch=epoch(p),seat_protocol=200,observation_only=True,**extra)
 def vehicle(path,uid,token,data,p,s,presences):
  if not p:return old_vehicle(path,uid,token,data,p,s,presences)
  action=path.rsplit('/',1)[-1];before=world.occupation(p['char_id'])
  if path=='/api/vehicles/seat-state200':
   world.live(p,s);return observed(p)
  if path=='/api/vehicles/enter'and data.get('epoch_protocol')==200:
   if type(data.get('id'))is not int or type(data.get('life_id'))is not int or type(data.get('seat_epoch'))is not int:raise ValueError('Araç koltuk sürümü gerekli; durumu yenile.')
   identity=(data['id'],data.get('seat'),data['life_id'],data['seat_epoch'])
   if data['life_id']!=p.get('life_id',0):raise ValueError('Karakter yaşamı değişti; araç durumunu yenile.')
   if p.get('last_enter200')==identity:
    r=observed(p,already_entered=True)
    if r['vehicle_id']:r['vehicle']=world.public(world.vehicle(r['vehicle_id']))
    return r
   if data['seat_epoch']!=epoch(p):raise ValueError('Koltuk değişti; eski binme isteği uygulanmadı.')
   result=old_vehicle(path,uid,token,data,p,s,presences)
   if world.occupation(p['char_id'])!=before:align(p['char_id'],True)
   else:align(p['char_id'])
   p['last_enter200']=identity;p['seat_protocol200_enabled']=True;return dict(result,seat_epoch=epoch(p),seat_protocol=200)
  if path=='/api/vehicles/exit'and data.get('epoch_protocol')==200:
   names=('id','seat','life_id','seat_epoch')
   if any(type(data.get(n))is not int for n in names)or data['id']<1 or not -1<=data['seat']<=7:raise ValueError('Araç koltuk sürümü gerekli; durumu yenile.')
   identity=tuple(data[n]for n in names)
   if data['life_id']!=p.get('life_id',0):raise ValueError('Karakter yaşamı değişti; araç durumunu yenile.')
   if p.get('last_exit200')==identity:return observed(p,already_exited=True)
   if (data['id'],data['seat'])!=before or data['seat_epoch']!=epoch(p):raise ValueError('Koltuk değişti; eski inme isteği uygulanmadı.')
   result=old_vehicle(path,uid,token,data,p,s,presences);align(p['char_id']);p['last_exit200']=identity;p['seat_protocol200_enabled']=True;return dict(result,**{k:v for k,v in observed(p).items()if k!='success'})
  result=old_vehicle(path,uid,token,data,p,s,presences)
  if action in('enter','exit')and result.get('success'):
   after=world.occupation(p['char_id'])
   if action=='enter'and before!=after:align(p['char_id'],True)
   else:align(p['char_id'])
   result=dict(result,seat_epoch=epoch(p),seat_protocol=200)
  return result
 def sample(p,s,data):
  packet=data.get('vehicle_sample')
  if isinstance(packet,dict)and(p.get('seat_protocol200_enabled')or data.get('seat_protocol')==200 or 'seat_epoch'in packet):
   if type(packet.get('seat_epoch'))is not int or packet['seat_epoch']!=epoch(p):return None
  return old_sample(p,s,data)
 def dispatch(path,data,token):
  with api.LOCK:
   p=api.PRESENCE.get(token)
   if p and p.get('seat_protocol200_enabled')and path in('/api/vehicles/enter','/api/vehicles/exit')and data.get('epoch_protocol')!=200:raise ValueError('Güncel koltuk sürümü gerekli; araç durumunu yenile.')
   if p and data.get('seat_protocol')==200:p['seat_protocol200_enabled']=True
   result,cookie=original(path,data,token);p=api.PRESENCE.get(token)
   if not result.get('success')or not p or p.get('world')!='gta':return result,cookie
   if path=='/api/gta/join':
    align(p['char_id'],True)
    if data.get('seat_protocol')==200:p['seat_protocol200_enabled']=True
   if path.startswith('/api/gta/')or path in('/api/vehicles/enter','/api/vehicles/exit','/api/vehicles/seat-state200'):
    # world.view can clean an expired seat after peer rows were constructed.
    # Copy final authoritative occupancy into every outgoing actor row.
    vid,seat=world.occupation(p['char_id']);result=dict(result,seat_epoch=epoch(p),seat_protocol=200,life_id=p.get('life_id',0),vehicle_id=vid,seat=seat)
    if 'players'in result:
     rows=[]
     for q in result['players']:
      vid,seat=world.occupation(q['char_id']);peer=next(iter(actors(q['char_id'])),None);rows.append(dict(q,vehicle_id=vid,seat=seat,seat_epoch=epoch(peer)if peer else 0))
     result['players']=rows
   return result,cookie
 world.remove_seat=remove;world.dispatch=vehicle;world.validate_sample=sample;api.dispatch=dispatch;api.vehicle_seats50_installed=True;return api
