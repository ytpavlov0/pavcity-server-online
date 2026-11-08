"""Repair only the distinctive old packed-vector/yaw/altitude encoding.

Preserve position, ownership, health, tuning and real rollover rotations.
Keep original state in SQL so the narrowly matched migration is reviewable.
"""
import json,math,time
def repair(s):
 keys=('rx','ry','rz','heading','z')
 if not all(type(s.get(k))in(int,float)and math.isfinite(s[k])for k in keys):return s
 if abs(s['rx'])>=30 or abs((s['ry']-s['heading']+180)%360-180)>=.1 or abs(s['rz']-s['z'])>=.05:return s
 if abs(s['ry'])<.0001 and abs(s['rz']-s['heading'])<.0001:return s
 return dict(s,ry=0,rz=s['heading'])

def install(api):
 if getattr(api,'rotation79_installed',False):return api
 w=api.world;count=0
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_vehicle_rotation79(vehicle_id INTEGER PRIMARY KEY,original_state TEXT NOT NULL,repaired_state TEXT NOT NULL,created REAL NOT NULL)')
  for row in db.execute('SELECT id,state FROM pn_vehicles').fetchall():
   original=json.loads(row['state']);fixed=repair(original)
   if fixed==original:continue
   fixed['pose_epoch']=int(original.get('pose_epoch',0))+1
   encoded=json.dumps(fixed)
   db.execute('INSERT OR IGNORE INTO pn_vehicle_rotation79 VALUES(?,?,?,?)',(row['id'],row['state'],encoded,time.time()))
   db.execute('UPDATE pn_vehicles SET state=? WHERE id=?',(encoded,row['id']))
   w.VEHICLE_CACHE.pop(row['id'],None);count+=1
 previous=w.validate_sample
 def validate(p,state,payload):
  result=previous(p,state,payload)
  return repair(result)if result is not None else result
 w.validate_sample=validate;api.rotation79_installed=True;api.rotation79_migrated=count
 return api
