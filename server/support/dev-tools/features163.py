"""163: sync CPU cut (31 Oct, 11 players: requests waited 0.5-2.2 s for api.LOCK, server at ~125 % CPU = the "2-3 s lag").

Measured on the live chain over a DB copy, 11 clustered players, 27.5 ms per sync under the lock (profiled):
 * ~4 ms: features148 opens a new SQLite connection per request; the first statement on a fresh connection re-parses the
   231-object schema. Now request() takes a connection from a small pool (any open transaction is rolled back before
   reuse, which is what close() did), so nested database() blocks / commits behave exactly as before.
 * ~11 ms: pn_world.view built ~93 vehicles through 7 wrapper layers (public -> factory paint -> vehicles71 -> city72 ->
   customs72 -> vehicle_trade99 -> marina88) and then kept only the nearest 48 within 400 m. (a) rows() now pre-selects
   those same 48 (same order, same 400 m rule, positions from VEHICLE_CACHE or the stored state, which public() does not
   change); (b) the outermost per-vehicle function is cached per vehicle while nothing about it changed: same row
   (owner/model/plate/locked/active), same VEHICLE_CACHE object (every driver sample / action replaces it), same driver
   seat, at most CACHE_TTL old. Callers get a shallow copy (view() only sets top-level keys).
Stats: api.features163_stats."""
import importlib,threading,time,math
from contextlib import contextmanager
POOL_MAX=8;CACHE_TTL=1.0;KEEP=48;RADIUS=400
def install(api):
 if getattr(api,'features163_installed',False):return api
 storage=importlib.import_module(api.__package__+'.pn_storage');world=api.world
 STATS={'pool_reused':0,'pool_new':0,'pool_rolled_back':0,'rows_in':0,'rows_kept':0,'public_hits':0,'public_misses':0}
 # 1) pooled per-request connection
 POOL=[];PLOCK=threading.Lock();LOCAL=storage.LOCAL;engine=storage.engine
 @contextmanager
 def request():
  if getattr(LOCAL,'db',None)is not None:
   yield;return
  with PLOCK:db=POOL.pop()if POOL else None
  if db is None:db=engine.get_db();STATS['pool_new']+=1
  else:STATS['pool_reused']+=1
  LOCAL.db=db;LOCAL.depth=0;LOCAL.serial=0
  try:yield
  finally:
   LOCAL.db=None;LOCAL.depth=0;reuse=False
   try:
    if db.in_transaction:db.rollback();STATS['pool_rolled_back']+=1
    reuse=True
   except Exception:reuse=False
   with PLOCK:
    if reuse and len(POOL)<POOL_MAX:POOL.append(db);db=None
   if db is not None:
    try:db.close()
    except Exception:pass
 storage.request=request
 # 2) rows: keep only what view() would keep (nearest KEEP within RADIUS, ties by higher id first)
 old_rows=world.rows
 def pos(r):
  f=world.VEHICLE_CACHE.get(r['id'])
  if f is None:
   try:f=world.json.loads(r['state'])
   except Exception:return None
  try:return float(f['x']),float(f['y']),float(f['z'])
  except Exception:return None
 def rows(state):
  out=old_rows(state);STATS['rows_in']+=len(out)
  try:sx,sy,sz=float(state['x']),float(state['y']),float(state['z'])
  except Exception:return out
  keep=[]
  for r in out:
   q=pos(r)
   if q is None:keep.append((-1.,0,r));continue   # unknown: let view() decide, as before
   d2=(q[0]-sx)**2+(q[1]-sy)**2+(q[2]-sz)**2
   if d2<=RADIUS*RADIUS:keep.append((d2,-r['id'],r))
  keep.sort(key=lambda t:(t[0],t[1]))
  res=[t[2]for t in keep[:KEEP+sum(1 for t in keep if t[0]<0)]];STATS['rows_kept']+=len(res);return res
 world.rows=rows
 # 3) per-vehicle public cache
 old_public=world.public;cache={}
 def public(row):
  vid=row['id'];now=time.monotonic();fields=world.VEHICLE_CACHE.get(vid);drv=world.SEATS.get((vid,-1),{}).get('char_id',0)
  key=(row['owner'],row['model'],row['plate'],row['locked'],row['active'],id(fields),drv)
  hit=cache.get(vid)
  if hit and hit[0]==key and hit[1] is fields and now-hit[2]<CACHE_TTL:
   STATS['public_hits']+=1;return dict(hit[3])
  result=old_public(row);STATS['public_misses']+=1
  after=world.VEHICLE_CACHE.get(vid)
  cache[vid]=((row['owner'],row['model'],row['plate'],row['locked'],row['active'],id(after),drv),after,now,dict(result))
  if len(cache)>4096:
   for k in[k for k,v in cache.items()if now-v[2]>=CACHE_TTL]:cache.pop(k,None)
  return result
 world.public=public
 api.features163_stats=STATS;api.features163_installed=True;return api
