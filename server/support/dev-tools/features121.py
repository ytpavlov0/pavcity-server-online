"""121 over the live v118 chain: account settings.

/api/account121/status   password changes left, email, Discord name (if set)
/api/account121/password {current,new}  needs the current password; 3 changes per account
                         (pn_account121.password_changes); the other sessions of the account are
                         signed out, this one stays.
/api/account121/discord  {name,confirm:true}  set once (Discord username rules), never changed
                         afterwards (staff can clear it in SQL).
Every change is audited."""
import re,time
LIMIT=3;DISCORD=re.compile(r'^(?!.*\.\.)[a-z0-9_.]{2,32}$')
def install(api):
 if getattr(api,'features121_installed',False):return api
 import gameplay_v29.session_api as sa
 w=api.world;previous=api.dispatch
 with w.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_account121(user_id INTEGER PRIMARY KEY,password_changes INTEGER NOT NULL DEFAULT 0,discord TEXT,discord_at REAL,updated REAL NOT NULL DEFAULT 0)')
 def row(db,uid):
  db.execute('INSERT OR IGNORE INTO pn_account121(user_id) VALUES(?)',(uid,));return db.execute('SELECT * FROM pn_account121 WHERE user_id=?',(uid,)).fetchone()
 def status(uid):
  with w.database()as db:
   r=row(db,uid);email=db.execute('SELECT email FROM pn_profiles WHERE user_id=?',(uid,)).fetchone()
   user=db.execute('SELECT username FROM users WHERE id=?',(uid,)).fetchone()
  return dict(success=True,username=user['username']if user else'',password_changes_left=max(0,LIMIT-r['password_changes']),discord=r['discord']or'',email=(email['email']if email else'')or'')
 def dispatch(path,v,token):
  if not path.startswith('/api/account121/'):return previous(path,v,token)
  with api.LOCK:
   uid=api.authenticated61(token)
   if not uid:raise ValueError('Önce giriş yap.')
   action=path.rsplit('/',1)[-1]
   if action=='status':return status(uid),None
   if action=='password':
    current,new=str(v.get('current','')),str(v.get('new',''))
    if not 8<=len(new)<=128:raise ValueError('Yeni şifre 8–128 karakter olmalı.')
    if new==current:raise ValueError('Yeni şifre eskisiyle aynı olamaz.')
    from gameplay_v29.pn_multiplayer import rate
    rate(token,'password121',5)
    with w.database()as db:
     r=row(db,uid)
     if r['password_changes']>=LIMIT:raise ValueError('Şifre değiştirme hakkın doldu (3/3). Destek talebi aç.')
     user=db.execute('SELECT password_hash FROM users WHERE id=?',(uid,)).fetchone()
     if not user or not sa.check_password(current,user['password_hash']):raise ValueError('Mevcut şifre yanlış.')
     db.execute('UPDATE users SET password_hash=? WHERE id=?',(sa.password_hash(new),uid))
     db.execute('UPDATE pn_account121 SET password_changes=password_changes+1,updated=? WHERE user_id=?',(time.time(),uid))
     import hashlib
     keep=hashlib.sha256(token.encode()).hexdigest()
     db.execute('DELETE FROM pn_sessions WHERE user_id=? AND hash<>?',(uid,keep))
     w.audit(db,uid,'password-change121',dict(left=LIMIT-r['password_changes']-1))
    for t,s in list(sa.SESSIONS.items()):
     if s.get('user_id')==uid and t!=token:sa.SESSIONS.pop(t,None)
    return dict(status(uid),notice='Şifren değişti. Kalan değiştirme hakkı: %d. Diğer oturumlar kapatıldı.'%max(0,LIMIT-r['password_changes']-1)),None
   if action=='discord':
    name=str(v.get('name','')).strip().lower()
    if not DISCORD.match(name):raise ValueError('Geçerli bir Discord kullanıcı adı yaz (2–32 karakter: harf, rakam, _ ve .).')
    if v.get('confirm') is not True:raise ValueError('Discord adını onaylaman gerekiyor; sonradan değiştirilemez.')
    with w.database()as db:
     r=row(db,uid)
     if r['discord']:raise ValueError('Discord adın zaten kayıtlı ('+r['discord']+') ve değiştirilemez.')
     db.execute('UPDATE pn_account121 SET discord=?,discord_at=?,updated=? WHERE user_id=?',(name,time.time(),time.time(),uid))
     w.audit(db,uid,'discord121',dict(name=name))
    return dict(status(uid),notice='Discord adın kaydedildi: '+name),None
   raise ValueError('Hesap işlemi bulunamadı.')
 api.dispatch=dispatch;api.features121_installed=True;return api
