"""Account-private Story Mode save bundles. Never merge offline state into RP wallets."""
import base64,binascii,hashlib,json,math,time,zlib
MAX_BYTES=24*1024*1024
def bundle(value):
 if not isinstance(value,list)or len(value)>64:raise ValueError('En fazla 64 kayıt dosyası yüklenebilir.')
 seen=set();total=0;rows=[]
 for row in value:
  if not isinstance(row,dict):raise ValueError('Geçersiz kayıt dosyası.')
  path=row.get('path');stamp=row.get('mtime');data=row.get('data')
  if not isinstance(path,str)or not path.startswith('/userdata/Documents/')or len(path)>240 or any(x in path for x in ['\\','\x00',':'])or any(x in ('','.','..')for x in path.split('/')[1:])or path in seen:raise ValueError('Geçersiz kayıt yolu.')
  if type(stamp)not in(int,float)or not math.isfinite(stamp)or not 0<=stamp<=(time.time()+86400)*1000:raise ValueError('Geçersiz kayıt tarihi.')
  if not isinstance(data,str)or len(data)>12*1024*1024:raise ValueError('Kayıt dosyası fazla büyük.')
  try:raw=base64.b64decode(data,validate=True)
  except (ValueError,binascii.Error):raise ValueError('Geçersiz kayıt verisi.')
  if len(raw)>8*1024*1024:raise ValueError('Tek kayıt en fazla 8 MiB olabilir.')
  total+=len(raw)
  if total>MAX_BYTES:raise ValueError('Toplam kayıt sınırı 24 MiB.')
  seen.add(path);rows.append(dict(path=path,mtime=stamp,data=data))
 rows.sort(key=lambda x:x['path']);encoded=json.dumps(rows,separators=(',',':')).encode();return rows,encoded,total
def install(api):
 if getattr(api,'offline94_installed',False):return api
 previous=api.dispatch
 with api.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_offline94(user_id INTEGER PRIMARY KEY,revision INTEGER NOT NULL,payload BLOB NOT NULL,sha256 TEXT NOT NULL,bytes INTEGER NOT NULL,files INTEGER NOT NULL,updated REAL NOT NULL)')
 def dispatch(path,v,token):
  if not path.startswith('/api/offline94/'):return previous(path,v,token)
  with api.LOCK:
   uid=api.authenticated61(token)
   if not uid:raise ValueError('Kayıtların için önce hesabına giriş yap.')
   action=path.rsplit('/',1)[-1]
   with api.database()as db:
    row=db.execute('SELECT * FROM pn_offline94 WHERE user_id=?',(uid,)).fetchone()
    def meta(r):return dict(revision=r['revision'],sha256=r['sha256'],bytes=r['bytes'],files=r['files'],updated=r['updated'])if r else dict(revision=0,bytes=0,files=0,updated=0)
    if action=='status':return dict(success=True,**meta(row)),None
    if action=='get':return dict(success=True,**meta(row),records=json.loads(zlib.decompress(row['payload']))if row else[]),None
    if action!='put':raise ValueError('Geçersiz kayıt işlemi.')
    rows,encoded,total=bundle(v.get('records'));digest=hashlib.sha256(encoded).hexdigest()
    if row and row['sha256']==digest:return dict(success=True,**meta(row),unchanged=True),None
    expected=v.get('revision')
    if type(expected)is not int or expected!=(row['revision']if row else 0):raise ValueError('Bulut kaydı başka sekmede değişti. Durumu yenile ve tekrar incele.')
    if row and time.time()-row['updated']<5:raise ValueError('Kayıt yüklendi. Yeni yedek için 5 saniye bekle.')
    if not rows:raise ValueError('Boş kayıt bulut yedeğini silemez.')
    if not db.in_transaction:db.execute('BEGIN IMMEDIATE')
    revision=expected+1;now=time.time();db.execute('INSERT INTO pn_offline94 VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id)DO UPDATE SET revision=excluded.revision,payload=excluded.payload,sha256=excluded.sha256,bytes=excluded.bytes,files=excluded.files,updated=excluded.updated',(uid,revision,zlib.compress(encoded,3),digest,total,len(rows),now))
    api.world.audit(db,uid,'offline94-backup',dict(revision=revision,bytes=total,files=len(rows),sha256=digest))
    return dict(success=True,revision=revision,bytes=total,files=len(rows),updated=now,sha256=digest),None
 api.dispatch=dispatch;api.offline94_installed=True;return api
