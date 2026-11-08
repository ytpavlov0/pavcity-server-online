"""Persisted company deliveries. Server-selected checkpoints, times, rewards and single settlement."""
import json,re,secrets,time,math
CONTRACTS={
 'documents':dict(name='Şehir içi evrak dağıtımı',reward=1500,points=[dict(x=-42.8,y=-58.9,z=63.5,title='Evrakları teslim al'),dict(x=-501.8,y=-670.5,z=33.2,title='İlk müşteriye teslim et'),dict(x=290.1,y=-1071.3,z=29.4,title='Son müşteriye teslim et')]),
 'supplies':dict(name='İşletme tedarik sevkiyatı',reward=2200,points=[dict(x=1201.,y=-1276.,z=35.2,title='Depodan siparişi teslim al'),dict(x=1144.2,y=-1647.6,z=36.4,title='İlk teslimat'),dict(x=1098.1,y=-2000.4,z=31.,title='Son teslimat')])}

def install(api):
 if getattr(api,'company_work92_installed',False):return api
 from restriction82 import free_actor
 w=api.world;previous=api.dispatch
 with api.database()as db:
  db.execute('''CREATE TABLE IF NOT EXISTS pn_company_runs92(id TEXT PRIMARY KEY,company_id INTEGER,char_id INTEGER,contract TEXT,step INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'active',life INTEGER,started REAL,step_at REAL,ready_at REAL NOT NULL DEFAULT 0,expires REAL,reward INTEGER)''')
  db.execute("CREATE UNIQUE INDEX IF NOT EXISTS pn_company_run92_co ON pn_company_runs92(company_id)WHERE status='active'")
  db.execute("CREATE UNIQUE INDEX IF NOT EXISTS pn_company_run92_actor ON pn_company_runs92(char_id)WHERE status='active'")
  db.execute('CREATE INDEX IF NOT EXISTS pn_company_run92_history ON pn_company_runs92(company_id,started)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_company_work_receipts92(char_id INTEGER,request_id TEXT,signature TEXT,result TEXT,created REAL,PRIMARY KEY(char_id,request_id))')
 def company(db,cid):return db.execute('''SELECT c.*,p.x,p.y,p.z,p.owner AS property_owner,p.kind FROM pn_companies88 c JOIN pn_properties p ON p.id=c.office_id
  WHERE c.owner=? OR c.id IN(SELECT company_id FROM pn_company_staff88 WHERE char_id=?)''',(cid,cid)).fetchone()
 def expire(db,now):
  db.execute("UPDATE pn_company_runs92 SET status='expired',ready_at=0 WHERE status='active'AND expires<=?",(now,))
  db.execute("UPDATE pn_company_runs92 SET status='cancelled',ready_at=0 WHERE status='active'AND NOT EXISTS(SELECT 1 FROM pn_companies88 c WHERE c.id=pn_company_runs92.company_id AND(c.owner=pn_company_runs92.char_id OR EXISTS(SELECT 1 FROM pn_company_staff88 s WHERE s.company_id=c.id AND s.char_id=pn_company_runs92.char_id)))")
 def row_view(r):
  if not r:return None
  r=dict(r);contract=CONTRACTS[r['contract']];r['name']=contract['name'];r['target']=contract['points'][min(r['step'],len(contract['points'])-1)];r['steps']=len(contract['points']);return r
 def near_office(p,s,c):
  if c['property_owner']!=c['owner']or c['kind']!='office':raise ValueError('Şirket ofisi artık kullanılamıyor.')
  if p.get('dimension',0)!=c['office_id']and(p.get('dimension',0)or not w.near(s,c,5)):raise ValueError('Sözleşmeyi şirket ofisinden başlat.')
 def valid(p,s,row):
  if row['life']!=p.get('life_id',0):raise ValueError('Yaşam durumun değişti. Sözleşmeyi iptal edip yeniden başlat.')
  if p.get('dimension',0)or p.get('admin_duty')or p.get('fly')or p.get('elevator176_ready'):raise ValueError('Teslimat dış dünyada, normal oyun durumunda yapılmalı.')
  if s.get('vehicle_id')or w.occupation(p['char_id'])[0]or abs(s.get('speed',0))>.5:raise ValueError('Teslimat için araçtan in ve dur.')
  target=CONTRACTS[row['contract']]['points'][row['step']]
  if not w.near(s,target,4):raise ValueError('Teslimat noktasına 4 metre içinde yaklaş.')
 def dispatch(path,v,token):
  if not path.startswith('/api/holding92/'):return previous(path,v,token)
  with api.LOCK:
   uid=api.authenticated61(token);api.require_client61(token,v);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token);now=time.time()
   if not uid or not p or p['user_id']!=uid:raise ValueError('Önce şehre gir.')
   w.live(p,s);free_actor(api,p,now);cid=p['char_id'];act=path.rsplit('/',1)[-1]
   with api.database()as db:
    if not db.in_transaction:db.execute('BEGIN IMMEDIATE')
    expire(db,now);c=company(db,cid)
    if act=='list':
     active=db.execute("SELECT * FROM pn_company_runs92 WHERE char_id=? AND status='active'",(cid,)).fetchone()
     latest=db.execute('SELECT started FROM pn_company_runs92 WHERE company_id=? ORDER BY started DESC LIMIT 1',(c['id'],)).fetchone()if c else None
     return dict(success=True,company=dict(id=c['id'],name=c['name'],balance=c['balance'])if c else None,active=row_view(active),catalog=[dict(key=k,name=x['name'],reward=x['reward'],steps=len(x['points']))for k,x in CONTRACTS.items()],cooldown_until=latest['started']+600 if latest else 0,company_busy=bool(c and db.execute("SELECT 1 FROM pn_company_runs92 WHERE company_id=? AND status='active'",(c['id'],)).fetchone()),server_time=now),None
    if act not in('start','begin','deliver','cancel'):raise ValueError('Geçersiz şirket işi.')
    rid=v.get('request_id')
    if not isinstance(rid,str)or not re.fullmatch(r'[a-zA-Z0-9-]{16,64}',rid):raise ValueError('İşlem kimliği gerekli.')
    sig=json.dumps([act,{k:x for k,x in v.items()if k not in('client61','request_id')}],sort_keys=True)
    prior=db.execute('SELECT * FROM pn_company_work_receipts92 WHERE char_id=? AND request_id=?',(cid,rid)).fetchone()
    if prior:
     if prior['signature']!=sig:raise ValueError('İşlem kimliği başka bir isteğe ait.')
     return dict(json.loads(prior['result']),replayed=True),None
    if act=='start':
     if not c:raise ValueError('Önce bir şirkete katıl veya kendi şirketini kur.')
     near_office(p,s,c)
     if s.get('vehicle_id')or w.occupation(cid)[0]or abs(s.get('speed',0))>.5:raise ValueError('Sözleşme için araçtan in ve dur.')
     if p.get('admin_duty')or p.get('fly')or p.get('elevator176_ready'):raise ValueError('Önce normal oyun durumuna dön.')
     key=v.get('contract')
     if key not in CONTRACTS:raise ValueError('Listeden bir sözleşme seç.')
     if db.execute("SELECT 1 FROM pn_job_runs WHERE char_id=? AND completed IS NULL",(cid,)).fetchone():raise ValueError('Önce aktif mesleğini tamamla veya bırak.')
     if db.execute("SELECT 1 FROM pn_company_runs92 WHERE status='active'AND(company_id=? OR char_id=?)",(c['id'],cid)).fetchone():raise ValueError('Şirketin veya karakterinin zaten aktif bir sözleşmesi var.')
     if db.execute('SELECT 1 FROM pn_company_runs92 WHERE company_id=? AND started>?',(c['id'],now-600)).fetchone():raise ValueError('Şirket yeni sözleşme için 10 dakikalık aralığı beklemeli.')
     ident=secrets.token_hex(16);reward=CONTRACTS[key]['reward']
     db.execute('INSERT INTO pn_company_runs92(id,company_id,char_id,contract,life,started,step_at,expires,reward) VALUES(?,?,?,?,?,?,?,?,?)',(ident,c['id'],cid,key,p.get('life_id',0),now,now,now+1800,reward));note='Şirket sözleşmesi başladı. İlk noktaya GPS ile git.'
    else:
     row=db.execute('SELECT * FROM pn_company_runs92 WHERE id=? AND char_id=?',(v.get('run'),cid)).fetchone()
     if not row:raise ValueError('Sözleşme bulunamadı.')
     ident=row['id']
     if row['status']!='active':raise ValueError('Bu sözleşme artık aktif değil.')
     if act=='cancel':db.execute("UPDATE pn_company_runs92 SET status='cancelled',ready_at=0 WHERE id=?",(ident,));note='Sözleşme iptal edildi; ücret ödenmedi.'
     else:
      if not c or c['id']!=row['company_id']:raise ValueError('Şirket üyeliğin değişmiş.')
      valid(p,s,row);target=CONTRACTS[row['contract']]['points'][row['step']]
      if act=='begin':
       if row['step']:
        prior_point=CONTRACTS[row['contract']]['points'][row['step']-1];minimum=max(20,math.dist([target[k]for k in('x','y','z')],[prior_point[k]for k in('x','y','z')])/70)
       else:minimum=20
       if now-row['step_at']<minimum:raise ValueError('Güzergâhın asgari süresi henüz dolmadı.')
       if not row['ready_at']:db.execute('UPDATE pn_company_runs92 SET ready_at=? WHERE id=?',(now+8,ident))
       note='Teslimat hazırlanıyor. 8 saniye sonra aynı noktada tamamla.'
      else:
       if not row['ready_at']or now<row['ready_at']:raise ValueError('Önce hazırlığı başlat ve sürenin bitmesini bekle.')
       step=row['step']+1
       if step==len(CONTRACTS[row['contract']]['points']):
        if db.execute("UPDATE pn_company_runs92 SET status='completed',step=?,ready_at=0 WHERE id=? AND status='active'",(step,ident)).rowcount!=1:raise ValueError('Sözleşme zaten tamamlandı.')
        if db.execute('UPDATE pn_companies88 SET balance=balance+? WHERE id=?',(row['reward'],row['company_id'])).rowcount!=1:raise ValueError('Şirket artık mevcut değil.')
        db.execute('INSERT INTO pn_company_ledger88(company_id,char_id,kind,amount,note,created) VALUES(?,?,?,?,?,?)',(row['company_id'],cid,'contract92',row['reward'],CONTRACTS[row['contract']]['name'],now));note=f"Sözleşme tamamlandı. Şirket kasasına ${row['reward']:,} USD yatırıldı."
       else:db.execute('UPDATE pn_company_runs92 SET step=?,step_at=?,ready_at=0 WHERE id=?',(step,now,ident));note='Teslimat kaydedildi. Sıradaki noktaya git.'
    w.audit(db,uid,'company-work92-'+act,dict(run=ident,char_id=cid))
    result=dict(success=True,notice=note,run=row_view(db.execute('SELECT * FROM pn_company_runs92 WHERE id=?',(ident,)).fetchone()))
    db.execute('INSERT INTO pn_company_work_receipts92 VALUES(?,?,?,?,?)',(cid,rid,sig,json.dumps(result),now));db.execute('DELETE FROM pn_company_work_receipts92 WHERE char_id=? AND request_id NOT IN(SELECT request_id FROM pn_company_work_receipts92 WHERE char_id=? ORDER BY created DESC LIMIT 64)',(cid,cid));return result,None
 api.dispatch=dispatch;api.company_work92_installed=True;return api
