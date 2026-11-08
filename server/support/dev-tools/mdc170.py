"""RP police terminal. Existing server duty/faction authorizes every operation."""
import re,time,json,hashlib
def schema(db):
 db.execute("CREATE TABLE IF NOT EXISTS pn_mdc170_cases(id INTEGER PRIMARY KEY,author INTEGER NOT NULL,subject INTEGER NOT NULL DEFAULT 0,vehicle INTEGER NOT NULL DEFAULT 0,title TEXT NOT NULL,body TEXT NOT NULL,wanted INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'open',version INTEGER NOT NULL DEFAULT 1,created REAL NOT NULL,updated REAL NOT NULL)")
 db.execute('CREATE TABLE IF NOT EXISTS pn_mdc170_receipts(actor INTEGER NOT NULL,request_id TEXT NOT NULL,digest TEXT NOT NULL,result TEXT NOT NULL,PRIMARY KEY(actor,request_id))')
 db.execute('CREATE INDEX IF NOT EXISTS pn_mdc170_subject ON pn_mdc170_cases(subject,status)')
def dispatch(api,path,payload,token,original):
 checked,_=original('/api/auth/me',{},token)
 if not checked.get('success'):return checked,None
 p=api.PRESENCE.get(token);state=api.GTA_STATE.get(token)
 if not p or not state or p.get('world')!='gta':raise ValueError('MDC için karakterinle şehre bağlan.')
 world=api.world
 with api.database()as db:
  member=db.execute("SELECT f.kind,m.faction_id,m.rank FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id WHERE m.char_id=?",(p['char_id'],)).fetchone()
  staff=api.staff.rank(checked['user_id'])>=2 and p.get('admin_duty')
  point=db.execute('SELECT faction_id,min_rank FROM pn_faction_duty WHERE id=?',(p.get('faction_duty',0),)).fetchone()
  police=member and member['kind']=='police' and point and point['faction_id']==member['faction_id'] and member['rank']<=point['min_rank']
  allowed=bool(staff or police)
  if path=='/api/mdc/status':return dict(success=True,allowed=allowed,operator=p['name'],reason='' if allowed else 'MDC yalnız görevdeki polis ve görevdeki yöneticilere açıktır.'),None
  if not allowed:raise ValueError('Bu işlem için polis görevi veya yönetici görevi gerekli.')
  if p.get('health',200)<=100:raise ValueError('Yaralıyken MDC kullanamazsın.')
  schema(db);action=path.removeprefix('/api/mdc/')
  if action=='search':
   kind=payload.get('kind');query=str(payload.get('query','')).strip()
   if not 2<=len(query)<=48:raise ValueError('Arama 2–48 karakter olmalı.')
   api.multiplayer.rate(token,'mdc-search',.4)
   pattern='%'+query.replace('!','!!').replace('%','!%').replace('_','!_')+'%'
   if kind=='people':
    rows=[dict(r)for r in db.execute("SELECT id,name,surname FROM characters WHERE name||' '||surname LIKE ? ESCAPE '!' OR CAST(id AS TEXT)=? ORDER BY id LIMIT 20",(pattern,query))]
    for row in rows:
     row['online']=any(v.get('char_id')==row['id']and time.time()-v.get('last_seen',0)<20 for v in api.PRESENCE.values());row['wanted']=db.execute("SELECT COUNT(*) FROM pn_mdc170_cases WHERE subject=? AND wanted=1 AND status='open'",(row['id'],)).fetchone()[0]
   elif kind=='vehicles':rows=[dict(r)for r in db.execute("SELECT v.id,v.model,v.plate,c.name,c.surname FROM pn_vehicles v LEFT JOIN characters c ON c.id=v.owner WHERE v.plate LIKE ? ESCAPE '!' ORDER BY v.id DESC LIMIT 20",(pattern,))]
   else:raise ValueError('Geçersiz arama türü.')
   world.audit(db,checked['user_id'],'mdc-search',dict(kind=kind,query=query,results=len(rows)));return dict(success=True,rows=rows),None
  if action=='cases':
   rows=[dict(r)for r in db.execute('SELECT k.*,c.name,c.surname FROM pn_mdc170_cases k LEFT JOIN characters c ON c.id=k.author ORDER BY k.updated DESC LIMIT 30')];return dict(success=True,cases=rows),None
  if action not in ('create','close'):raise ValueError('MDC işlemi bulunamadı.')
  key=payload.get('request_id')
  if not isinstance(key,str)or not re.fullmatch(r'[a-zA-Z0-9_-]{12,80}',key):raise ValueError('İşlem kimliği gerekli.')
  digest=hashlib.sha256(json.dumps([action,payload],sort_keys=True,allow_nan=False).encode()).hexdigest();previous=db.execute('SELECT * FROM pn_mdc170_receipts WHERE actor=? AND request_id=?',(p['char_id'],key)).fetchone()
  if previous:
   if previous['digest']!=digest:raise ValueError('İşlem kimliği başka istekte kullanılmış.')
   return json.loads(previous['result']),None
  api.multiplayer.rate(token,'mdc-change',.5);now=time.time()
  if action=='create':
   title=str(payload.get('title','')).strip();body=str(payload.get('body','')).strip();subject=payload.get('subject',0);vehicle=payload.get('vehicle',0)
   if not 3<=len(title)<=80 or not 5<=len(body)<=2000:raise ValueError('Başlık 3–80, açıklama 5–2000 karakter olmalı.')
   if type(subject)is not int or type(vehicle)is not int or subject<0 or vehicle<0:raise ValueError('Geçersiz karakter veya araç ID.')
   if subject and not db.execute('SELECT 1 FROM characters WHERE id=?',(subject,)).fetchone():raise ValueError('Karakter bulunamadı.')
   if vehicle and not db.execute('SELECT 1 FROM pn_vehicles WHERE id=?',(vehicle,)).fetchone():raise ValueError('Araç bulunamadı.')
   wanted=payload.get('wanted')is True
   if wanted and not subject:raise ValueError('Aranma kaydı için karakter ID gerekli.')
   cid=db.execute('INSERT INTO pn_mdc170_cases(author,subject,vehicle,title,body,wanted,created,updated) VALUES(?,?,?,?,?,?,?,?)',(p['char_id'],subject,vehicle,title,body,int(wanted),now,now)).lastrowid
   result=dict(success=True,id=cid,notice='RP dosyası kaydedildi. Aranma kaydı otomatik para veya hapis cezası uygulamaz.')
  else:
   cid=payload.get('id');version=payload.get('version')
   if type(cid)is not int or type(version)is not int:raise ValueError('Geçersiz dosya kaydı.')
   if not db.execute("UPDATE pn_mdc170_cases SET status='closed',wanted=0,version=version+1,updated=? WHERE id=? AND version=? AND status='open'",(now,cid,version)).rowcount:raise ValueError('Dosya değişmiş veya kapanmış. Listeyi yenile.')
   result=dict(success=True,id=cid,notice='Dosya kapatıldı.')
  db.execute('INSERT INTO pn_mdc170_receipts VALUES(?,?,?,?)',(p['char_id'],key,digest,json.dumps(result)));world.audit(db,checked['user_id'],'mdc-'+action,dict(case_id=cid));return result,None
