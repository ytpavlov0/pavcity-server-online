"""174: vehicles never drop out of a player's list because of the per-cell row cache (features160, 1 s since 167).

The bridge deletes a bound native car the moment its id is missing from the HTTP vehicle list (pn_native_bridge,
`for (const [id,v] of vehicles) if(!active.has(id)) drop101(v.handle,true)`). With the cached cell lists a traffic car
adopted with G (traffic-register) could be missing for up to 1 s, and crossing into a neighbouring cell could show an
older list without a car that is right next to the player -> the car and the NPC in it vanished. The uncached rows()
always added every VEHICLE_CACHE car within 400 m; this layer restores that on top of the cache: any active car the
server holds in VEHICLE_CACHE within 400 m and not in the cached rows is fetched (one indexed SELECT per missing id)
and appended. The same exclusions as the filters below the cache apply: ambient188 cars that are not taken (hidden
while server car traffic is off) and models that are neither SPAWN_MODELS nor ROAD_MODELS. Stats: api.features174_stats."""
import importlib,math
def install(api):
 if getattr(api,'features174_installed',False):return api
 world=api.world;traffic=importlib.import_module(api.__package__+'.pn_traffic')
 STATS={'merged':0,'calls':0}
 old_rows=world.rows
 def rows(state):
  out=old_rows(state);STATS['calls']+=1
  try:sx,sy,sz=float(state['x']),float(state['y']),float(state['z'])
  except Exception:return out
  have={r['id']for r in out};missing=[]
  for vid,f in list(world.VEHICLE_CACHE.items()):
   if vid in have or not isinstance(f,dict):continue
   if f.get('ambient188')and not f.get('ambient188_taken'):continue
   try:
    if(float(f['x'])-sx)**2+(float(f['y'])-sy)**2+(float(f['z'])-sz)**2>400.0*400.0:continue
   except Exception:continue
   missing.append(vid)
  if missing:
   with world.database()as db:
    for vid in missing[:24]:
     row=db.execute('SELECT * FROM pn_vehicles WHERE id=? AND active=1',(vid,)).fetchone()
     if row and(row['model']in world.SPAWN_MODELS or row['model']in traffic.ROAD_MODELS):out.append(dict(row));STATS['merged']+=1
  return out
 world.rows=rows
 api.features174_stats=STATS;api.features174_installed=True;return api
