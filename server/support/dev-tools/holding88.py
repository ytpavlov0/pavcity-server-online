"""Company identity and ledger for owned offices; existing office geometry and income remain shared."""
import json,re,secrets,time
from marina88 import boat_name

def company_name(value):
 try:return boat_name(value)
 except ValueError:raise ValueError("Şirket adı 2–28 harf/rakam olmalı.")

def install(api):
 if getattr(api,'holding88_installed',False):return api
 from restriction82 import free_actor
 w=api.world;previous=api.dispatch
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_companies88(id INTEGER PRIMARY KEY AUTOINCREMENT,office_id INTEGER UNIQUE NOT NULL,owner INTEGER UNIQUE NOT NULL,name TEXT NOT NULL,balance INTEGER NOT NULL DEFAULT 0 CHECK(balance>=0),created REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_company_staff88(company_id INTEGER,char_id INTEGER UNIQUE,issued_key INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(company_id,char_id))')
  db.execute('CREATE TABLE IF NOT EXISTS pn_company_invites88(id TEXT PRIMARY KEY,company_id INTEGER,target INTEGER,expires REAL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_company_ledger88(id INTEGER PRIMARY KEY AUTOINCREMENT,company_id INTEGER,char_id INTEGER,kind TEXT,amount INTEGER,note TEXT,created REAL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_company_receipts88(char_id INTEGER,request_id TEXT,signature TEXT,result TEXT,created REAL,PRIMARY KEY(char_id,request_id))')
 def actor(token,v):
  uid=api.authenticated61(token);api.require_client61(token,v);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
  if not uid or not p or p['user_id']!=uid:raise ValueError('Önce şehre gir.')
  w.live(p,s);free_actor(api,p,time.time());return uid,p,s
 def owned(db,cid):return db.execute('SELECT c.*,p.x,p.y,p.z,p.kind,p.owner AS property_owner FROM pn_companies88 c JOIN pn_properties p ON p.id=c.office_id WHERE c.owner=?',(cid,)).fetchone()
 def company(db,cid):return db.execute('SELECT c.*,p.x,p.y,p.z,p.kind,p.owner AS property_owner FROM pn_companies88 c JOIN pn_properties p ON p.id=c.office_id WHERE c.owner=? OR c.id IN(SELECT company_id FROM pn_company_staff88 WHERE char_id=?)',(cid,cid)).fetchone()
 def near(p,s,row):
  if row['kind']!='office'or row['property_owner']!=row['owner']:raise ValueError('Ofisin mülkiyeti değişmiş; yönetici kontrolü gerekli.')
  if p.get('dimension',0)!=row['office_id']and(p.get('dimension',0)or not w.near(s,row,5)):raise ValueError('İşlem için şirket ofisine git.')
 def name(cid):
  # Character labels are already normalized by the game database.
  for p in api.PRESENCE.values():
   if p['char_id']==cid:return p['name']
  return 'Karakter #'+str(cid)
 def listing(p):
  cid=p['char_id']
  with api.database()as db:
   r=company(db,cid);offices=[dict(v)for v in db.execute("SELECT id,name,x,y,z,price FROM pn_properties WHERE kind='office' AND owner=? ORDER BY id",(cid,))]
   invites=[dict(v)for v in db.execute('SELECT i.id,c.name,c.owner,i.expires FROM pn_company_invites88 i JOIN pn_companies88 c ON c.id=i.company_id WHERE i.target=? AND i.expires>? ORDER BY i.expires DESC LIMIT 8',(cid,time.time()))]
   if r:
    r=dict(r);r['leader']=r['owner']==cid;r['members']=[dict(char_id=r['owner'],name=name(r['owner']),role='CEO')]+[dict(char_id=v['char_id'],name=name(v['char_id']),role='Çalışan')for v in db.execute('SELECT char_id FROM pn_company_staff88 WHERE company_id=?',(r['id'],))]
    r['ledger']=[dict(v)for v in db.execute('SELECT kind,amount,note,created,char_id FROM pn_company_ledger88 WHERE company_id=? ORDER BY id DESC LIMIT 30',(r['id'],))]
  return dict(success=True,company=r,offices=offices,invites=invites,money=w.wallet(p['user_id']),registration_fee=10000)
 def dispatch(path,v,token):
  if path.startswith('/api/holding88/'):
   with api.LOCK:
    uid,p,s=actor(token,v);cid=p['char_id'];action=path.rsplit('/',1)[-1];now=time.time()
    if action=='list':return listing(p),None
    if action not in('create','rename','deposit','withdraw','invite','accept','decline','remove','leave','close'):raise ValueError('Geçersiz şirket işlemi.')
    rid=v.get('request_id')
    if not isinstance(rid,str)or not re.fullmatch(r'[a-zA-Z0-9-]{16,64}',rid):raise ValueError('İşlem kimliği gerekli.')
    sig=json.dumps([action,{k:x for k,x in v.items()if k not in('request_id','client61')}],sort_keys=True,ensure_ascii=False)
    with api.database()as db:
     old=db.execute('SELECT signature,result FROM pn_company_receipts88 WHERE char_id=? AND request_id=?',(cid,rid)).fetchone()
     if old:
      if old['signature']!=sig:raise ValueError('İşlem kimliği başka bir isteğe ait.')
      return dict(json.loads(old['result']),replayed=True),None
     if not db.in_transaction:db.execute('BEGIN IMMEDIATE')
     row=company(db,cid);co=0;amount=0;note=''
     if action=='create':
      if row:raise ValueError('Zaten bir şirkette bulunuyorsun.')
      office=db.execute("SELECT * FROM pn_properties WHERE id=? AND owner=? AND kind='office'",(v.get('office_id'),cid)).fetchone()
      if not office:raise ValueError('Şirket kurmak için kendi ofisin gerekli.')
      near(p,s,dict(office,office_id=office['id'],property_owner=office['owner']))
      title=company_name(v.get('name'))
      if db.execute('UPDATE pn_wallet SET balance=balance-10000 WHERE user_id=? AND balance>=10000',(uid,)).rowcount!=1:raise ValueError('Kuruluş ücreti $10.000.')
      co=db.execute('INSERT INTO pn_companies88(office_id,owner,name,created) VALUES(?,?,?,?)',(office['id'],cid,title,now)).lastrowid;amount=-10000;note=title+' kuruldu.'
     elif action in('accept','decline'):
      invite=db.execute('SELECT i.*,c.office_id,c.owner FROM pn_company_invites88 i JOIN pn_companies88 c ON c.id=i.company_id WHERE i.id=? AND i.target=? AND i.expires>?',(v.get('invite_id'),cid,now)).fetchone()
      if not invite:raise ValueError('Şirket daveti bulunamadı veya süresi doldu.')
      co=invite['company_id']
      if action=='accept':
       if row:raise ValueError('Önce mevcut şirketinden ayrıl.')
       office=db.execute('SELECT * FROM pn_properties WHERE id=? AND owner=?',(invite['office_id'],invite['owner'])).fetchone()
       if not office:raise ValueError('Şirket ofisi artık kullanılamıyor.')
       if db.execute('SELECT count(*) FROM pn_company_staff88 WHERE company_id=?',(co,)).fetchone()[0]>=12:raise ValueError('Şirket çalışan sınırı 12.')
       issued=not db.execute('SELECT 1 FROM pn_property_keys WHERE property_id=? AND char_id=?',(invite['office_id'],cid)).fetchone()
       db.execute('INSERT OR IGNORE INTO pn_property_keys VALUES(?,?)',(invite['office_id'],cid));db.execute('INSERT INTO pn_company_staff88 VALUES(?,?,?)',(co,cid,int(issued)));note='Şirkete katıldın; ofis anahtarın envanterinde.'
      else:note='Şirket davetini reddettin.'
      db.execute('DELETE FROM pn_company_invites88 WHERE id=?',(invite['id'],))
     else:
      if not row:raise ValueError('Bir şirkette değilsin.')
      row=dict(row);co=row['id'];leader=row['owner']==cid
      if action!='leave'and not leader:raise ValueError('Bu işlem yalnız CEO için kullanılabilir.')
      if action!='leave':near(p,s,row)
      if action in('deposit','withdraw'):
       amount=v.get('amount')
       if type(amount)is not int or not 1<=amount<=100000000:raise ValueError('Tutar 1–100.000.000 arasında tam sayı olmalı.')
       if action=='deposit':
        if db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(amount,uid,amount)).rowcount!=1:raise ValueError('Cüzdan bakiyen yetersiz.')
        db.execute('UPDATE pn_companies88 SET balance=balance+? WHERE id=?',(amount,co));note='Şirket kasasına para yatırıldı.'
       else:
        if db.execute('UPDATE pn_companies88 SET balance=balance-? WHERE id=? AND balance>=?',(amount,co,amount)).rowcount!=1:raise ValueError('Şirket kasası yetersiz.')
        db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(amount,uid));amount=-amount;note='Şirket kasasından para çekildi.'
      elif action=='rename':db.execute('UPDATE pn_companies88 SET name=? WHERE id=?',(company_name(v.get('name')),co));note='Şirket adı güncellendi.'
      elif action=='invite':
       target=next((q for q in api.PRESENCE.values()if q['server_id']==v.get('server_id')and now-q.get('last_seen',0)<30),None)
       if not target or target['char_id']==cid:raise ValueError('Çevrimiçi başka bir oyuncunun ID’sini yaz.')
       if company(db,target['char_id']):raise ValueError('Oyuncu zaten bir şirkette.')
       db.execute('DELETE FROM pn_company_invites88 WHERE expires<? OR(company_id=? AND target=?)',(now,co,target['char_id']))
       if db.execute('SELECT count(*) FROM pn_company_invites88 WHERE company_id=?',(co,)).fetchone()[0]>=12:raise ValueError('Bekleyen davet sınırı 12.')
       db.execute('INSERT INTO pn_company_invites88 VALUES(?,?,?,?)',(secrets.token_hex(16),co,target['char_id'],now+300));note='Davet gönderildi. Oyuncu /holding panelinden 5 dakika içinde kabul edebilir.'
      elif action in('remove','leave'):
       target=cid if action=='leave'else v.get('char_id')
       if target==row['owner']:raise ValueError('CEO ayrılmak için önce şirketi kapatmalı.')
       member=db.execute('SELECT * FROM pn_company_staff88 WHERE company_id=? AND char_id=?',(co,target)).fetchone()
       if not member:raise ValueError('Çalışan bulunamadı.')
       if member['issued_key']:db.execute('DELETE FROM pn_property_keys WHERE property_id=? AND char_id=?',(row['office_id'],target))
       db.execute('DELETE FROM pn_company_staff88 WHERE company_id=? AND char_id=?',(co,target));note='Şirket üyeliği ve şirketin verdiği anahtar kaldırıldı.'
      elif action=='close':
       if v.get('confirm_name')!=row['name']:raise ValueError('Kapatmak için şirket adını aynen yaz.')
       for member in db.execute('SELECT * FROM pn_company_staff88 WHERE company_id=?',(co,)).fetchall():
        if member['issued_key']:db.execute('DELETE FROM pn_property_keys WHERE property_id=? AND char_id=?',(row['office_id'],member['char_id']))
       amount=-row['balance'];db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(row['balance'],uid))
       db.execute('DELETE FROM pn_company_staff88 WHERE company_id=?',(co,));db.execute('DELETE FROM pn_company_invites88 WHERE company_id=?',(co,));db.execute('DELETE FROM pn_companies88 WHERE id=?',(co,));note='Şirket kapatıldı; kasa cüzdanına iade edildi. Ofis mülkiyetin korundu.'
     db.execute('INSERT INTO pn_company_ledger88(company_id,char_id,kind,amount,note,created) VALUES(?,?,?,?,?,?)',(co,cid,action,amount,note,now));w.audit(db,uid,'holding88-'+action,dict(company_id=co,amount=amount))
     result=dict(success=True,notice=note,money=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()[0])
     db.execute('INSERT INTO pn_company_receipts88 VALUES(?,?,?,?,?)',(cid,rid,sig,json.dumps(result),now));db.execute('DELETE FROM pn_company_receipts88 WHERE char_id=? AND request_id NOT IN(SELECT request_id FROM pn_company_receipts88 WHERE char_id=? ORDER BY created DESC LIMIT 64)',(cid,cid))
    return result,None
  if path in('/api/properties/sell','/api/properties/transfer-faction','/api/properties/edit','/api/chat/send'):
   with api.LOCK:
    pid=v.get('id')
    if path=='/api/chat/send':
     args=str(v.get('message','')).split()
     if len(args)>1 and args[0].lower()in('/delint','/setinttype','/setintowner'):
      try:pid=int(args[1])
      except ValueError:pass
     else:pid=None
    if type(pid)is int:
     with api.database()as db:co=db.execute('SELECT id FROM pn_companies88 WHERE office_id=?',(pid,)).fetchone()
     if co:raise ValueError('Önce bu ofise bağlı şirketi /holding üzerinden kapat.')
  return previous(path,v,token)
 api.dispatch=dispatch;api.holding88_installed=True;return api
