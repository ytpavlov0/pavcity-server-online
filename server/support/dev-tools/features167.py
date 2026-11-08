"""167: the two biggest items under api.LOCK in the live stack sample of 31 Oct (v166, 2 min, 11 players, lock held 51 %):
 * 9.3 %: pn_world.public() re-saves every active vehicle it shows every 3 s (UPDATE state+updated). Parked cars rewrote
   the same JSON forever (and kept `updated` fresh, the cause of the traffic cap of 162). persist_vehicle now skips the
   write when the vehicle state is unchanged since this process last wrote it (fuel_at, a pure bookkeeping timestamp, is
   ignored in the comparison); SAVED_AT is still advanced, so callers see the usual cadence. Any real change (driving,
   engine, damage, fuel burn, mods, lock state lives in its own column) is written as before.
 * 8.2 %: pn_world.rows (json_extract scan over pn_vehicles) re-ran for every 150 m cell every 0.5 s. The cell list is
   now kept 1.0 s (features160.ROWS_TTL); moving cars still come from VEHICLE_CACHE every sync, only a car newly
   entering a cell's top list can appear up to 1 s later.
Stats: api.features167_stats."""
import time
ROWS_TTL=1.0
def install(api):
 if getattr(api,'features167_installed',False):return api
 world=api.world;STATS={'persist_written':0,'persist_skipped':0};LAST={}
 import features160;features160.ROWS_TTL=ROWS_TTL
 old=world.persist_vehicle
 def persist_vehicle(vid):
  f=world.VEHICLE_CACHE.get(vid)
  if f is None:return old(vid)
  try:key=world.json.dumps({k:v for k,v in f.items()if k!='fuel_at'},sort_keys=True)
  except Exception:return old(vid)
  if LAST.get(vid)==key:
   world.SAVED_AT[vid]=time.time();STATS['persist_skipped']+=1;return
  r=old(vid);LAST[vid]=key;STATS['persist_written']+=1
  if len(LAST)>20000:LAST.clear()
  return r
 world.persist_vehicle=persist_vehicle
 api.features167_stats=STATS;api.features167_installed=True;return api
