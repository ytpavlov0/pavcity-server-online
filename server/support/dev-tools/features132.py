"""132 over the live v130 chain: phone group chats (the phone's "Gruplar" app, WhatsApp-style).

/api/groups132/list                 my groups with the last message and unread count
/api/groups132/create {name,numbers} a group with up to 15 other phone numbers (creator is admin)
/api/groups132/thread {id,after?}    the last 60 messages (or those after an id); marks them read
/api/groups132/send   {id,body}      1–400 characters, at most one message per 0.6 s
/api/groups132/add    {id,number}    admins add a member (16 at most)
/api/groups132/leave  {id}           leave; the last member leaving deletes the group
Members are characters with a phone number; everything lives in SQL (pn_groups132*)."""
import time,re
MAX_MEMBERS=16;MAX_GROUPS=20
def install(api):
 if getattr(api,'features132_installed',False):return api
 w=api.world;previous=api.dispatch;last={}
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_groups132(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,owner INTEGER NOT NULL,created REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_group_members132(group_id INTEGER NOT NULL,char_id INTEGER NOT NULL,admin INTEGER NOT NULL DEFAULT 0,joined REAL NOT NULL,last_read INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(group_id,char_id))')
  db.execute('CREATE INDEX IF NOT EXISTS pn_group_members132_char ON pn_group_members132(char_id)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_group_messages132(id INTEGER PRIMARY KEY AUTOINCREMENT,group_id INTEGER NOT NULL,char_id INTEGER NOT NULL,name TEXT NOT NULL,body TEXT NOT NULL,created REAL NOT NULL)')
  db.execute('CREATE INDEX IF NOT EXISTS pn_group_messages132_g ON pn_group_messages132(group_id,id)')
 def me(token):
  uid=api.authenticated61(token);p=api.PRESENCE.get(token)
  if not uid or not p:raise ValueError('Önce karakterinle şehre gir.')
  with w.database()as db:row=db.execute('SELECT number FROM pn_phone_numbers WHERE char_id=?',(p['char_id'],)).fetchone()
  if not row:raise ValueError('Grup sohbeti için telefon numaran olmalı.')
  return uid,p,row['number']
 def member(db,gid,cid):
  if type(gid)is not int:raise ValueError('Grup seçilmedi.')
  m=db.execute('SELECT * FROM pn_group_members132 WHERE group_id=? AND char_id=?',(gid,cid)).fetchone()
  if not m:raise ValueError('Bu grubun üyesi değilsin.')
  return m
 def by_number(db,n):
  if type(n)is not int or not 20000000<=n<=80000000:raise ValueError('Telefon numarasını kontrol et.')
  r=db.execute('SELECT char_id FROM pn_phone_numbers WHERE number=?',(n,)).fetchone()
  if not r:raise ValueError('%d numarası kayıtlı değil.'%n)
  return r['char_id']
 def numbers_of(db,gid):
  return[dict(number=r['number'],name=r['name'],admin=bool(r['admin']))for r in db.execute("SELECT n.number,c.name||' '||c.surname AS name,m.admin FROM pn_group_members132 m JOIN pn_phone_numbers n ON n.char_id=m.char_id JOIN characters c ON c.id=m.char_id WHERE m.group_id=? ORDER BY m.admin DESC,m.joined",(gid,))]
 def act(action,token,v):
  uid,p,num=me(token);cid=p['char_id']
  with w.database()as db:
   if action=='list':
    rows=db.execute('''SELECT g.id,g.name,m.admin,m.last_read,(SELECT COUNT(*) FROM pn_group_members132 x WHERE x.group_id=g.id) members,
     (SELECT id FROM pn_group_messages132 WHERE group_id=g.id ORDER BY id DESC LIMIT 1) last_id FROM pn_groups132 g JOIN pn_group_members132 m ON m.group_id=g.id WHERE m.char_id=? ORDER BY COALESCE(last_id,0) DESC,g.id DESC''',(cid,)).fetchall()
    out=[]
    for r in rows:
     msg=db.execute('SELECT name,body,created,char_id FROM pn_group_messages132 WHERE id=?',(r['last_id'],)).fetchone()if r['last_id']else None
     unread=db.execute('SELECT COUNT(*) FROM pn_group_messages132 WHERE group_id=? AND id>? AND char_id NOT IN (?,0)',(r['id'],r['last_read'],cid)).fetchone()[0]
     out.append(dict(id=r['id'],name=r['name'],admin=bool(r['admin']),members=r['members'],unread=unread,last=dict(name=msg['name'],body=msg['body'][:80],created=msg['created'],mine=msg['char_id']==cid)if msg else None))
    return dict(success=True,groups=out,unread=sum(g['unread']for g in out))
   if action=='create':
    name=re.sub(r'\s+',' ',str(v.get('name',''))).strip();nums=v.get('numbers')
    if not 2<=len(name)<=24:raise ValueError('Grup adı 2–24 karakter olmalı.')
    if not isinstance(nums,list)or len(nums)>MAX_MEMBERS-1:raise ValueError('En fazla %d kişi ekleyebilirsin.'%(MAX_MEMBERS-1))
    if db.execute('SELECT COUNT(*) FROM pn_group_members132 WHERE char_id=?',(cid,)).fetchone()[0]>=MAX_GROUPS:raise ValueError('En fazla %d gruba üye olabilirsin.'%MAX_GROUPS)
    others={by_number(db,n)for n in nums}-{cid}
    now=time.time();gid=db.execute('INSERT INTO pn_groups132(name,owner,created)VALUES(?,?,?)',(name,cid,now)).lastrowid
    db.execute('INSERT INTO pn_group_members132(group_id,char_id,admin,joined)VALUES(?,?,1,?)',(gid,cid,now))
    for o in others:db.execute('INSERT OR IGNORE INTO pn_group_members132(group_id,char_id,admin,joined)VALUES(?,?,0,?)',(gid,o,now))
    db.execute('INSERT INTO pn_group_messages132(group_id,char_id,name,body,created)VALUES(?,?,?,?,?)',(gid,0,'Sistem','%s grubu oluşturdu.'%p['name'],now))
    w.audit(db,uid,'group-create132',dict(group=gid,members=len(others)+1))
    return dict(success=True,id=gid,notice='“%s” grubu oluşturuldu.'%name)
   gid=v.get('id');m=member(db,gid,cid)
   if action=='thread':
    after=v.get('after')
    if type(after)is int and after>0:rows=db.execute('SELECT * FROM pn_group_messages132 WHERE group_id=? AND id>? ORDER BY id LIMIT 100',(gid,after)).fetchall()
    else:rows=list(reversed(db.execute('SELECT * FROM pn_group_messages132 WHERE group_id=? ORDER BY id DESC LIMIT 60',(gid,)).fetchall()))
    if rows:db.execute('UPDATE pn_group_members132 SET last_read=MAX(last_read,?) WHERE group_id=? AND char_id=?',(rows[-1]['id'],gid,cid))
    g=db.execute('SELECT * FROM pn_groups132 WHERE id=?',(gid,)).fetchone()
    return dict(success=True,id=gid,name=g['name'],admin=bool(m['admin']),members=numbers_of(db,gid),messages=[dict(id=r['id'],char_id=r['char_id'],name=r['name'],body=r['body'],created=r['created'],mine=r['char_id']==cid,system=r['char_id']==0)for r in rows])
   if action=='send':
    body=str(v.get('body','')).strip()
    if not 1<=len(body)<=400:raise ValueError('Mesaj 1–400 karakter olmalı.')
    now=time.time()
    if now-last.get(cid,0)<.6:raise ValueError('Biraz yavaş yaz.')
    last[cid]=now
    if len(last)>4096:last.clear()
    mid=db.execute('INSERT INTO pn_group_messages132(group_id,char_id,name,body,created)VALUES(?,?,?,?,?)',(gid,cid,p['name'],body,now)).lastrowid
    db.execute('UPDATE pn_group_members132 SET last_read=? WHERE group_id=? AND char_id=?',(mid,gid,cid))
    return dict(success=True,id=mid)
   if action=='add':
    if not m['admin']:raise ValueError('Yalnız grup yöneticisi kişi ekleyebilir.')
    if db.execute('SELECT COUNT(*) FROM pn_group_members132 WHERE group_id=?',(gid,)).fetchone()[0]>=MAX_MEMBERS:raise ValueError('Grup dolu (%d kişi).'%MAX_MEMBERS)
    o=by_number(db,v.get('number'))
    if db.execute('SELECT 1 FROM pn_group_members132 WHERE group_id=? AND char_id=?',(gid,o)).fetchone():raise ValueError('Bu kişi zaten grupta.')
    now=time.time();db.execute('INSERT INTO pn_group_members132(group_id,char_id,admin,joined)VALUES(?,?,0,?)',(gid,o,now))
    who=db.execute("SELECT name||' '||surname n FROM characters WHERE id=?",(o,)).fetchone()['n']
    db.execute('INSERT INTO pn_group_messages132(group_id,char_id,name,body,created)VALUES(?,?,?,?,?)',(gid,0,'Sistem','%s, %s kişisini ekledi.'%(p['name'],who),now))
    return dict(success=True,notice=who+' gruba eklendi.')
   if action=='leave':
    now=time.time();db.execute('DELETE FROM pn_group_members132 WHERE group_id=? AND char_id=?',(gid,cid))
    left=db.execute('SELECT char_id,admin FROM pn_group_members132 WHERE group_id=? ORDER BY joined',(gid,)).fetchall()
    if not left:
     db.execute('DELETE FROM pn_group_messages132 WHERE group_id=?',(gid,));db.execute('DELETE FROM pn_groups132 WHERE id=?',(gid,))
    else:
     if m['admin']and not any(r['admin']for r in left):db.execute('UPDATE pn_group_members132 SET admin=1 WHERE group_id=? AND char_id=?',(gid,left[0]['char_id']))
     db.execute('INSERT INTO pn_group_messages132(group_id,char_id,name,body,created)VALUES(?,?,?,?,?)',(gid,0,'Sistem','%s gruptan ayrıldı.'%p['name'],now))
    return dict(success=True,notice='Gruptan ayrıldın.')
  raise ValueError('Grup işlemi bulunamadı.')
 def dispatch(path,v,token):
  if path.startswith('/api/groups132/'):
   with api.LOCK:return act(path.rsplit('/',1)[-1],token,v if isinstance(v,dict)else{}),None
  return previous(path,v,token)
 api.dispatch=dispatch;api.features132_installed=True;return api
