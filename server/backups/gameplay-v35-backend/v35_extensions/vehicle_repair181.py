"""Explicit-install vehicle repair/pose fence; no role or repair grants.

Epoch-capable renderers acknowledge applied repair/pose versions. Old clients
retain a bounded three-second compatibility fence for in-flight samples.
"""
import importlib,time

def install(api):
 if getattr(api,'vehicle_repair181_installed',False):return api
 city=importlib.import_module(api.__package__+'.pn_city');world=api.world
 command,validate=city.admin_command,world.validate_sample
 fences={}
 def admin(cmd,args,uid,p,state,presences):
  result=command(cmd,args,uid,p,state,presences)
  if cmd in ('/fixveh','/flipcar') and result and result.get('success'):
   vid=city.pointer(args[0])if args else world.occupation(p['char_id'])[0]
   current=world.public(world.vehicle(vid))
   fences[vid]=dict(pose=current.get('pose_epoch',0),repair=current.get('repair_epoch',0),body=cmd=='/fixveh',until=time.monotonic()+3)
  return result
 def sample(p,state,payload):
  accepted=validate(p,state,payload)
  if accepted is None:return None
  packet=payload.get('vehicle_sample',{});vid=packet.get('id');fence=fences.get(vid)
  if not fence:return accepted
  modern=type(packet.get('epoch_protocol'))is int and packet['epoch_protocol']==181
  pose_ack=type(packet.get('pose_applied_epoch'))is int and packet['pose_applied_epoch']==fence['pose']
  repair_ack=not fence['body']or type(packet.get('repair_applied_epoch'))is int and packet['repair_applied_epoch']==fence['repair']
  if modern and pose_ack and repair_ack or not modern and time.monotonic()>=fence['until']:
   fences.pop(vid,None);return accepted
  current=world.public(world.vehicle(vid))
  # Keep current server corrections; other authenticated driver fields retain
  # their normal validation. An old acknowledgement cannot clear a new fence.
  for key in ('rx','ry','rz','vx','vy','vz'):accepted[key]=current.get(key,0)
  if fence['body']:accepted['body']=current.get('body',1000)
  return accepted
 city.admin_command=admin;world.validate_sample=sample
 api.vehicle_repair181_installed=True
 return api
