"""160: sync and join cost cuts, measured on the live chain over a DB snapshot (scratchpad prof160.py, 8 clustered players).

Before: one /api/gta/sync cost 48 ms median under api.LOCK (8 players x ~4 syncs/s demanded = 1.5 s of lock per second:
every request, chat line and /api/status waited 400-500 ms in the queue). 25 ms of that was pn_world.view re-reading
~49 vehicle rows from SQLite on every sync and json-parsing each row's state even when VEHICLE_CACHE already held it
(the default argument of dict.get is evaluated eagerly); 3.6 ms were two fsync commits (journal_mode=delete);
a join ran multiplayer.schema() = 897 SQL statements (CREATE IF NOT EXISTS x 231 objects + INSERT OR IGNORE for every
user and character) = 36 ms under the lock, so a 100-viewer join wave stalled everyone.
Now: (1) world.rows results are shared per 150 m cell for 0.5 s (moving vehicles still come from VEHICLE_CACHE, so only
lock/owner/new-vehicle changes can lag <= 0.5 s); (2) pn_world's json.loads memoizes parsed vehicle states by string
and hands out copies; (3) schema() runs at most once per 30 s per module (reserve() still records new identities at
register/character creation, so nothing is lost); (4) journal_mode=WAL once + synchronous=NORMAL per connection.
No request or response field changes. Stats: api.features160_stats (served in /pn/server-capabilities-v160.json)."""
import importlib,time,types
ROWS_TTL=.5;SCHEMA_TTL=30
def install(api):
 if getattr(api,'features160_installed',False):return api
 package=api.__package__;mp=importlib.import_module(package+'.pn_multiplayer');rp=importlib.import_module(package+'.pn_roleplay');storage=importlib.import_module(package+'.pn_storage');world=api.world;engine=storage.engine
 STATS={'rows_sql':0,'rows_cached':0,'schema_runs':0,'schema_skipped':0,'json_parsed':0,'json_cached':0,'journal':''}
 # 1) vehicle rows shared per cell for ROWS_TTL (callers get copies; public() may annotate them)
 old_rows=world.rows;cells={}
 def rows(state):
  key=(int(state['x']//150),int(state['y']//150),int(state['z']//150));now=time.time();hit=cells.get(key)
  if hit and now-hit[0]<ROWS_TTL:STATS['rows_cached']+=1;return[dict(r)for r in hit[1]]
  result=old_rows(state);STATS['rows_sql']+=1;cells[key]=(now,result)
  if len(cells)>256:
   for k in[k for k,(t,_)in cells.items()if now-t>=ROWS_TTL]:cells.pop(k,None)
  return[dict(r)for r in result]
 world.rows=rows
 # 2) memoized json.loads for pn_world (vehicle state strings repeat every sync while a vehicle is parked)
 real=world.json;memo={}
 def loads(s,**kw):
  if kw or not isinstance(s,str)or len(s)>4096:return real.loads(s,**kw)
  v=memo.get(s)
  if v is None:
   v=real.loads(s);STATS['json_parsed']+=1
   if len(memo)>2048:memo.clear()
   memo[s]=v
  else:STATS['json_cached']+=1
  return dict(v)if isinstance(v,dict)else(list(v)if isinstance(v,list)else v)
 shim=types.SimpleNamespace(**{k:getattr(real,k)for k in dir(real)if not k.startswith('_')});shim.loads=loads;world.json=shim
 # 3) schema() at most once per SCHEMA_TTL per module
 def once_per_ttl(old):
  last=[0.]
  def schema(db):
   now=time.time()
   if now-last[0]<SCHEMA_TTL:STATS['schema_skipped']+=1;return
   last[0]=now;STATS['schema_runs']+=1;return old(db)
  return schema
 mp.schema=once_per_ttl(mp.schema);rp.schema=once_per_ttl(rp.schema)
 # 4) WAL once, synchronous=NORMAL on every connection (a commit no longer waits for two fsyncs)
 old_get=engine.get_db
 def get_db():
  c=old_get()
  try:c.execute('PRAGMA synchronous=NORMAL')
  except Exception:pass
  return c
 engine.get_db=get_db
 try:
  c=old_get();STATS['journal']=c.execute('PRAGMA journal_mode=WAL').fetchone()[0]
  # kept open for the life of the process: closing the LAST connection checkpoints and deletes the WAL (2.6 ms per
  # request when every request opens its own connection); with an anchor connection checkpoints run only at the
  # automatic 1000-page threshold
  api.features160_anchor=c
 except Exception as e:STATS['journal']='error:'+str(e)[:80]
 api.features160_stats=STATS;api.features160_installed=True;return api
