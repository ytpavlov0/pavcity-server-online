"""Capture missing native paint only from an acknowledged, living driver.

Observations fill missing paint, never override an existing or purchased color.
No schema changes, startup row rewrites, grants or new mutation endpoint.
"""
import importlib

def index(value):return type(value)is int and 0<=value<=160
def rgb(value):return value is None or type(value)is list and len(value)==3 and all(type(v)is int and 0<=v<=255 for v in value)

def install(api):
 if getattr(api,'vehicle_paint43_installed',False):return api
 world=api.world;validate=world.validate_sample;original_sample=world.sample
 economy=importlib.import_module(api.__package__+'.pn_economy');original=economy.dispatch
 def sample(p,state,payload):
  accepted=validate(p,state,payload)
  if accepted is None:return None
  packet=payload.get('vehicle_sample',{});paint=packet.get('paint43')
  if not isinstance(paint,dict)or p.get('health',200)<=100 or state.get('health',200)<=100 or p.get('dimension',0):return accepted
  with api.database()as db:rest=db.execute('SELECT * FROM pn_restrictions178 WHERE char_id=?',(p['char_id'],)).fetchone()
  if rest and rest['life']==p.get('life_id',0)and rest['dimension']==p.get('dimension',0)and rest['until']>__import__('time').time()and (rest['cuffed']or rest['prone']):return accepted
  if type(payload.get('life_id'))is not int or payload['life_id']!=p.get('life_id',0):return accepted
  vid,seat=world.occupation(p['char_id'])
  current=world.public(world.vehicle(vid))
  if type(packet.get('epoch_protocol'))is not int or packet['epoch_protocol']!=181 or any(type(packet.get(name))is not int or packet[name]!=current.get(key,0)for name,key in [('pose_applied_epoch','pose_epoch'),('repair_applied_epoch','repair_epoch')]):return accepted
  if not all(index(paint.get(k))and rgb(paint.get(k+'_rgb'))for k in ('primary','secondary')):return accepted
  mods=dict(accepted.get('mods',{}))
  for key in ('primary','secondary'):
   if key not in mods:
    mods[key]=paint[key]
    if paint.get(key+'_rgb')is not None:mods[key+'_rgb']=list(paint[key+'_rgb'])
  accepted['mods']=mods
  return accepted
 def save_sample(p,state,payload):
  vid,seat=world.occupation(p['char_id']);before=None;save_time=world.SAVED_AT.get(vid)
  if vid and seat==-1:before=dict(world.VEHICLE_CACHE.get(vid,{}).get('mods',{}))
  result=original_sample(p,state,payload)
  if before is not None and world.VEHICLE_CACHE.get(vid,{}).get('mods',{})!=before and world.SAVED_AT.get(vid)==save_time:world.persist_vehicle(vid)
  return result
 def dispatch(path,uid,token,v,p,state,presences):
  # The legacy tuning table contains purchases. Preserve sampled factory paint
  # while buying unrelated upgrades; a purchased indexed color clears that RGB.
  before={};vid=0
  if path=='/api/tuning/buy'and p:
   vid,seat=world.occupation(p['char_id'])
   if vid:before=dict(world.public(world.vehicle(vid)).get('mods',{}))
  result=original(path,uid,token,v,p,state,presences)
  if before and vid and path=='/api/tuning/buy'and result.get('success'):
   mods={**before,**result['mods']}
   if v.get('part')in ('primary','secondary'):mods.pop(v['part']+'_rgb',None)
   with api.database()as db:db.execute('UPDATE pn_vehicle_upgrades SET state=? WHERE vehicle_id=?',(__import__('json').dumps(mods),vid))
   world.VEHICLE_CACHE[vid]['mods']=mods;world.persist_vehicle(vid);result=dict(result,mods=mods)
  return result
 world.validate_sample=sample;world.sample=save_sample;economy.dispatch=dispatch;api.vehicle_paint43_installed=True
 return api
