"""187: short-lived SELECT cache for the game server's SQLite connections.

A sync ran ~47 small SELECTs (restrictions, staff rank, custody, jail, country, environment, faction, wallet, calls ...)
inside the global lock. Under load every statement hands the GIL away and waits to get it back, so the lock is held
far longer than the work takes. Identical SELECTs (same SQL, same parameters) now come from memory for up to TTL
seconds; any write that changes a table drops that table's entries at once.

Correctness rules:
- every connection the server opens comes from online_engine.get_db (checked); all of them are wrapped;
- a write (INSERT/UPDATE/DELETE/REPLACE) bumps the table generation when it runs and again when its transaction ends
  (commit, rollback, `with db`, close), so readers on other connections never keep a pre-commit value;
- a result is stored only if no write touched its tables while the SELECT ran (generation check);
- a connection with uncommitted writes to a table always reads that table from SQLite (sees its own writes);
- DDL, PRAGMA, ATTACH, executescript/executemany clear everything; SELECTs with now/random/changes are never cached;
- results are row tuples / sqlite3.Row objects (immutable); every fetch gets its own list.
TTL (30 s) bounds staleness only for writes made by another process (maintenance scripts); every write of this
process invalidates immediately."""
import re,time,threading,sqlite3
TTL=30.0;MAX=20000
_LOCK=threading.Lock();_CACHE={};_GEN={};_ALL=[0]
STATS={'hits':0,'misses':0,'stored':0,'bypass':0,'invalidations':0,'flushes':0,'savepoints':0,'savepoints_deferred':0}
import collections
SQLN=collections.Counter()  # statements that reached SQLite (misses, bypasses, writes), first 400 texts
def _count(kind,sql):
 k=kind+' '+' '.join(sql.split())[:160]
 if k in SQLN or len(SQLN)<400:SQLN[k]+=1
_TABLES=re.compile(r'\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)',re.I)
_WRITE=re.compile(r'^\s*(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|REPLACE\s+INTO|UPDATE(?:\s+OR\s+\w+)?|DELETE\s+FROM)\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)',re.I)
_VOLATILE=re.compile(r"now|random|changes\(|last_insert_rowid|current_|julianday|strftime|datetime|date\(|time\(",re.I)
_TXEND=re.compile(r'^\s*(COMMIT|END|ROLLBACK(?!\s+TO\b))\b',re.I)
_SAFE=re.compile(r'^\s*(BEGIN|SAVEPOINT|RELEASE)\b',re.I)
_TARGETS=re.compile(r'(?:INSERT(?:\s+OR\s+\w+)?\s+INTO|REPLACE\s+INTO|UPDATE(?:\s+OR\s+\w+)?|DELETE\s+FROM)\s+["`\[]?([A-Za-z_][A-Za-z0-9_]*)',re.I)
_COMMA=re.compile(r'\bFROM\s+[A-Za-z_]\w*(?:\s+(?:AS\s+)?[A-Za-z_]\w*)?\s*,',re.I)
TRIG={}  # table -> tables its triggers write
def load_triggers(c):
 m={}
 for tbl,body in c.execute("SELECT tbl_name,sql FROM sqlite_master WHERE type='trigger'").fetchall():
  body=body or'';i=body.upper().find('BEGIN')  # the header says "AFTER UPDATE ON t"; targets are in the body
  m.setdefault(tbl.lower(),set()).update(t.lower()for t in _TARGETS.findall(body[i:]if i>=0 else body))
 with _LOCK:TRIG.clear();TRIG.update(m)
def _gens(tables):return(_ALL[0],)+tuple(_GEN.get(t,0)for t in tables)
def bump(tables):
 tables=set(tables)
 for t in list(tables):tables|=TRIG.get(t,set())
 # O(1): entries of these tables stop matching their stored generations (checked on every hit)
 with _LOCK:
  for t in tables:_GEN[t]=_GEN.get(t,0)+1
  if tables:STATS['invalidations']+=1
def flush():
 with _LOCK:_ALL[0]+=1;_CACHE.clear();STATS['flushes']+=1
class Rows:
 __slots__=('_rows','_i','description')
 lastrowid=None;rowcount=-1
 def __init__(self,rows,description):self._rows=rows;self._i=0;self.description=description
 def fetchone(self):
  if self._i>=len(self._rows):return None
  self._i+=1;return self._rows[self._i-1]
 def fetchall(self):r=list(self._rows[self._i:]);self._i=len(self._rows);return r
 def fetchmany(self,size=1):r=list(self._rows[self._i:self._i+size]);self._i+=len(r);return r
 def __iter__(self):
  while self._i<len(self._rows):
   self._i+=1;yield self._rows[self._i-1]
 def close(self):pass
_SP=re.compile(r'^\s*(SAVEPOINT|RELEASE|ROLLBACK\s+TO)\s+(pav_sp_\d+)\s*$',re.I)
NOOP=Rows((),None)
class Conn:
 """Also defers pn_storage's nested savepoints (SAVEPOINT/RELEASE pav_sp_N around every nested `database()` block,
 ~60 statements per sync): a savepoint is created only when a write follows it; RELEASE / ROLLBACK TO of a
 savepoint that was never needed are no-ops (nothing was written after it)."""
 __slots__=('_c','_dirty','_pend')
 def __init__(self,c):object.__setattr__(self,'_c',c);object.__setattr__(self,'_dirty',set());object.__setattr__(self,'_pend',[])
 def __getattr__(self,n):return getattr(self._c,n)
 def __setattr__(self,n,v):setattr(self._c,n,v)
 def _end(self):
  self._pend.clear();d=set(self._dirty);self._dirty.clear()
  if d:bump(d)
 def _materialize(self):
  while self._pend:
   name=self._pend.pop(0);self._c.execute('SAVEPOINT '+name);STATS['savepoints']+=1
 def execute(self,sql,params=()):
  if type(sql)is not str:self._materialize();return self._c.execute(sql,params)
  sp=_SP.match(sql)if not params else None
  if sp:
   kind,name=sp.group(1).upper(),sp.group(2)
   if kind=='SAVEPOINT':self._pend.append(name);STATS['savepoints_deferred']+=1;return NOOP
   if name in self._pend:
    i=self._pend.index(name)
    # nothing was written since this savepoint: RELEASE drops it, ROLLBACK TO keeps it
    del self._pend[i+1 if kind!='RELEASE'else i:];return NOOP
   self._pend.clear()  # pending ones are nested inside a created savepoint
   if kind!='RELEASE':
    # writes after it are undone, the transaction goes on: keep _dirty (own reads must not use the cache)
    d=set(self._dirty)
    try:return self._c.execute(sql,params)
    finally:
     if d:bump(d)
   return self._c.execute(sql,params)
  head=sql.lstrip()[:12].upper()
  if head.startswith('SELECT'):
   tables=frozenset(t.lower()for t in _TABLES.findall(sql))
   if not tables or _VOLATILE.search(sql)or tables&self._dirty or any(q in sql for q in'"`[')or _COMMA.search(sql)or any(t in TRIG.get(d,())for d in self._dirty for t in tables):
    STATS['bypass']+=1;_count('bypass',sql);return self._c.execute(sql,params)
   try:key=(sql,tuple(params)if isinstance(params,(list,tuple))else tuple(sorted(params.items()))if isinstance(params,dict)else params,self._c.row_factory)
   except TypeError:STATS['bypass']+=1;return self._c.execute(sql,params)
   now=time.monotonic()
   with _LOCK:
    hit=_CACHE.get(key)
    if hit and hit[0]>now and hit[3]==_gens(hit[2]):STATS['hits']+=1;return Rows(hit[1],hit[4])
    gens=_gens(tables)
   _count('miss',sql);cur=self._c.execute(sql,params);rows=tuple(cur.fetchall());desc=cur.description
   with _LOCK:
    STATS['misses']+=1
    if gens==_gens(tables):
     if len(_CACHE)>=MAX:_CACHE.clear()
     _CACHE[key]=(now+TTL,rows,tables,gens,desc);STATS['stored']+=1
   return Rows(rows,desc)
  m=_WRITE.match(sql)
  if m:
   _count('write',sql);t=m.group(1).lower();self._materialize()
   try:cur=self._c.execute(sql,params)
   except BaseException:self._dirty.add(t);self._dirty.update(TRIG.get(t,()));bump({t});raise
   # rowcount 0: nothing changed (INSERT OR IGNORE of an existing row, UPDATE without a match): nothing to drop.
   # Bumping after the statement is enough: other connections cannot see it before commit, and _end bumps again.
   if cur.rowcount!=0:self._dirty.add(t);self._dirty.update(TRIG.get(t,()));bump({t})
   return cur
  if _TXEND.match(sql):
   try:return self._c.execute(sql,params)
   finally:self._end()
  if _SAFE.match(sql):return self._c.execute(sql,params)
  # PRAGMA, CREATE, DROP, ALTER, ATTACH, VACUUM, WITH ... and anything unrecognised
  _count('other',sql);flush();self._materialize()
  try:return self._c.execute(sql,params)
  finally:
   if 'TRIGGER'in sql.upper():load_triggers(self._c)
 def executemany(self,sql,seq):
  self._materialize();m=_WRITE.match(sql)if type(sql)is str else None
  if m:t=m.group(1).lower();self._dirty.add(t);self._dirty.update(TRIG.get(t,()));bump({t})
  else:flush()
  return self._c.executemany(sql,seq)
 def executescript(self,script):
  flush();self._materialize()
  try:return self._c.executescript(script)
  finally:self._dirty.clear();flush()
 def commit(self):
  try:return self._c.commit()
  finally:self._end()
 def rollback(self):
  try:return self._c.rollback()
  finally:self._end()
 def close(self):
  try:return self._c.close()
  finally:self._end()
 def __enter__(self):self._c.__enter__();return self
 def __exit__(self,*exc):
  try:return self._c.__exit__(*exc)
  finally:self._end()
def install(engine):
 if getattr(engine,'db187',False):return
 orig=engine.get_db
 c=orig()
 try:load_triggers(c)
 finally:c.close()
 def get_db(*a,**k):return Conn(orig(*a,**k))
 engine.get_db=get_db;engine.db187=True
