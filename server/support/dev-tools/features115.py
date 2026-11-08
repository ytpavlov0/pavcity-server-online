"""115: player-to-player trade commands, PAV Puan (PP) and report context over the live v114 chain.

/paragonder ID MİKTAR   hand cash to a player within 5 m (wallet → wallet, ledger on both sides)
/pp · /ppgonder ID MİKTAR   PAV Puan balance and account-to-account transfer (online target)
/ppver ID MİKTAR · /ppal ID MİKTAR   founder-only PP grant / removal, every change in pn_pp_ledger115
/aracımısat ID FİYAT · /araçkabul [TEKLİF_ID] · /araçreddet [TEKLİF_ID]   Turkish spellings of the live
   vehicle_trade99 sale (seller in the driver seat, buyer within 5 m, 90 s offer); accepting or
   rejecting without an ID takes the newest pending offer, donate cars are refused and the buyer
   gets a private note.
Reports: every /api/reports/create also stores the reporter's situation (server ID, position,
dimension, vehicle, health/armor, players within 50 m) in pn_report_context115; staff read it
through /api/reports115/context."""
import json,math,time
NEAR=5.0
GIVE=('/paragonder','/paragönder','/paraver');PP_SEND=('/ppgonder','/ppgönder')
SELL=('/aracımısat','/aracimisat','/araçımısat','/aracsat','/araçsat');ACCEPT=('/araçkabul','/arackabul','/aracikabul','/aracımıal');REJECT=('/araçreddet','/aracreddet')
def install(api):
 if getattr(api,'features115_installed',False):return api
 import gameplay_v29.pn_admin as staff,gameplay_v29.pn_roleplay as rp,gameplay_v29.pn_multiplayer as mp
 w=api.world;previous=api.dispatch
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_pp115(user_id INTEGER PRIMARY KEY,balance INTEGER NOT NULL DEFAULT 0 CHECK(balance>=0))')
  db.execute('CREATE TABLE IF NOT EXISTS pn_pp_ledger115(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,delta INTEGER NOT NULL,kind TEXT NOT NULL,other_user INTEGER NOT NULL DEFAULT 0,actor INTEGER NOT NULL,created REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_report_context115(report_id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,char_id INTEGER NOT NULL,server_id INTEGER,x REAL,y REAL,z REAL,dimension INTEGER,vehicle_id INTEGER,health INTEGER,armor INTEGER,nearby TEXT NOT NULL,created REAL NOT NULL)')
 def money(n):return '$'+f'{n:,}'.replace(',','.')
 def number(value,lo,hi,label):
  try:n=int(str(value).replace('.','').replace('$',''))
  except(TypeError,ValueError):raise ValueError(label+' sayı olmalı.')
  if not lo<=n<=hi:raise ValueError(f'{label} {lo}–{hi:,} arasında olmalı.'.replace(',','.'))
  return n
 def me(token):
  p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
  if not p or not s or p.get('world')!='gta':raise ValueError('Önce karakterinle şehre gir.')
  return p,s
 def peer(arg,p,self_ok=False):
  cid=w.resolve_player_id(arg,api.PRESENCE)
  if cid==p['char_id']and not self_ok:raise ValueError('Kendini hedef alamazsın.')
  pair=next(((k,q)for k,q in api.PRESENCE.items()if q['char_id']==cid and time.time()-q.get('last_seen',0)<20),None)
  if not pair:raise ValueError('Oyuncu şu anda çevrim içi değil.')
  return pair[1],api.GTA_STATE.get(pair[0])
 def close(p,s,q,t,limit=NEAR):
  if not t or q.get('dimension',0)!=p.get('dimension',0)or math.dist([s[k]for k in('x','y','z')],[t[k]for k in('x','y','z')])>limit:
   raise ValueError(f"{q['name']} yanında olmalı ({int(limit)} m).")
 def private(p,q,body):
  """A server note in the receiver's PM channel (PM toast + ding on the client)."""
  with w.database()as db:
   mid=db.execute("INSERT INTO pn_chat(char_id,name,body,scope,x,y,z,created) VALUES(?,?,'','local',0,0,0,0)",(p['char_id'],p['name'])).lastrowid
   db.execute('DELETE FROM pn_chat WHERE id=?',(mid,))
   db.execute('INSERT INTO pn_private_chat VALUES(?,?,?,?,?,?,?)',(mid,p['char_id'],q['char_id'],p['name'],q['name'],body[:240],time.time()))
 def pp_balance(db,uid):
  db.execute('INSERT OR IGNORE INTO pn_pp115(user_id) VALUES(?)',(uid,));return db.execute('SELECT balance FROM pn_pp115 WHERE user_id=?',(uid,)).fetchone()[0]
 def pp_move(db,uid,delta,kind,other,actor):
  pp_balance(db,uid)
  if not db.execute('UPDATE pn_pp115 SET balance=balance+? WHERE user_id=? AND balance+?>=0',(delta,uid,delta)).rowcount:raise ValueError('Yeterli PP yok.')
  db.execute('INSERT INTO pn_pp_ledger115(user_id,delta,kind,other_user,actor,created)VALUES(?,?,?,?,?,?)',(uid,delta,kind,other,actor,time.time()))
 def give_cash(token,args):
  p,s=me(token)
  if len(args)!=2:raise ValueError('Kullanım: /paragonder OYUNCU_ID MİKTAR')
  q,t=peer(args[0],p);n=number(args[1],1,1000000,'Miktar')
  if p.get('health',200)<=100:raise ValueError('Yaralıyken para veremezsin.')
  if q['user_id']==p['user_id']:raise ValueError('Kendi hesabındaki karaktere para gönderemezsin.')
  close(p,s,q,t);mp.rate(token,'give-cash115',3)
  with w.database()as db:
   rp.debit(db,'pn_wallet','user_id',p['user_id'],n)
   db.execute('INSERT OR IGNORE INTO pn_wallet(user_id,balance) VALUES(?,0)',(q['user_id'],));db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(n,q['user_id']))
   rp.ledger(db,p['user_id'],p['char_id'],'cash-give',n,dict(target=q['char_id']));rp.ledger(db,q['user_id'],q['char_id'],'cash-received',n,dict(sender=p['char_id']))
  mp.emote(p,s,f"{q['name']} kişisine bir miktar nakit uzattı.");private(p,q,f'Sana {money(n)} nakit verdi.')
  return dict(success=True,money=w.wallet(p['user_id']),notice=f"{q['name']} [{q['server_id']}] kişisine {money(n)} verdin.")
 def pp_command(token,cmd,args):
  p,s=me(token);uid=p['user_id']
  if cmd=='/pp':
   if args:raise ValueError('Kullanım: /pp')
   with w.database()as db:b=pp_balance(db,uid);rows=[dict(r)for r in db.execute('SELECT delta,kind,created FROM pn_pp_ledger115 WHERE user_id=? ORDER BY id DESC LIMIT 5',(uid,))]
   return dict(success=True,pp=b,notice=f'PAV Puan bakiyen: {b:,} PP'.replace(',','.'),info=dict(title='PAV Puan (PP)',rows=[['Bakiye',f'{b:,} PP'.replace(',','.')]]+[[{'pp-send':'Gönderildi','pp-received':'Alındı','pp-grant':'Yetkili ekledi','pp-take':'Yetkili düştü'}.get(r['kind'],r['kind']),('+'if r['delta']>0 else'')+str(r['delta'])+' PP']for r in rows]))
  if len(args)!=2:raise ValueError(f'Kullanım: {cmd} OYUNCU_ID MİKTAR')
  q,_=peer(args[0],p,cmd not in PP_SEND);n=number(args[1],1,1000000,'Miktar')
  if cmd in PP_SEND:
   if q['user_id']==uid:raise ValueError('Kendi hesabına PP gönderemezsin.')
   mp.rate(token,'pp115',3)
   with w.database()as db:pp_move(db,uid,-n,'pp-send',q['user_id'],uid);pp_move(db,q['user_id'],n,'pp-received',uid,uid);left=pp_balance(db,uid)
   private(p,q,f'Sana {n:,} PAV Puan (PP) gönderdi.'.replace(',','.'))
   return dict(success=True,pp=left,notice=f"{q['name']} [{q['server_id']}] kişisine {n:,} PP gönderdin. Kalan: {left:,} PP".replace(',','.'))
  if staff.rank(uid)<4:raise ValueError('PP ekleme/düşme yalnızca sunucu kurucusuna açık.')
  delta=n if cmd=='/ppver'else -n
  with w.database()as db:pp_move(db,q['user_id'],delta,'pp-grant'if delta>0 else'pp-take',0,uid);b=pp_balance(db,q['user_id']);w.audit(db,uid,'pp115',dict(target=q['user_id'],delta=delta))
  return dict(success=True,notice=f"{q['name']} · {('+'if delta>0 else'')}{delta:,} PP · yeni bakiye {b:,} PP".replace(',','.'))
 def sell(token,args):
  """Turkish spellings of the live vehicle_trade99 offer (seller in the driver seat, buyer
  within 5 m); donate cars are refused here and the buyer also gets a private note."""
  p,s=me(token)
  if len(args)!=2:raise ValueError('Kullanım: /aracımısat OYUNCU_ID FİYAT · aracının sürücü koltuğunda ol, alıcı 5 m içinde olsun.')
  vid=w.occupation(p['char_id'])[0]
  if vid:
   with w.database()as db:
    if db.execute('SELECT 1 FROM pn_donate_vehicles WHERE vehicle_id=?',(vid,)).fetchone():raise ValueError('Donate araçları satılamaz.')
  result,cookie=previous('/api/chat/send',dict(message='/aracimisat '+' '.join(args),scope='local'),token)
  if result.get('success'):
   try:
    q,_=peer(args[0],p);private(p,q,'Sana aracını '+money(number(args[1],1,1000000000,'Fiyat'))+' karşılığında satmak istiyor. Kabul: /araçkabul · Ret: /araçreddet · Ayrıntı: /teklifler (90 sn)')
   except Exception:pass
  return result,cookie
 def answer(token,cmd,args):
  p,_=me(token)
  if len(args)>1:raise ValueError('Kullanım: '+cmd+' [TEKLİF_ID]')
  if not args:
   with w.database()as db:row=db.execute("SELECT id FROM pn_vehicle_sale84 WHERE buyer=? AND status='pending' AND expires>? ORDER BY created DESC LIMIT 1",(p['char_id'],time.time())).fetchone()
   if not row:raise ValueError('Bekleyen araç teklifin yok. Teklifler 90 sn geçerli; /teklifler ile bak.')
   args=[row['id']]
  return previous('/api/chat/send',dict(message=('/arackabul 'if cmd in ACCEPT else'/aracreddet ')+args[0],scope='local'),token)
 def context(v,token):
  uid=api.authenticated61(token)
  if not uid or staff.rank(uid)<1:raise ValueError('Rapor ayrıntıları yalnızca yetkililere açık.')
  rid=number(v.get('id'),1,2147483647,'Rapor')
  with w.database()as db:row=db.execute('SELECT * FROM pn_report_context115 WHERE report_id=?',(rid,)).fetchone()
  if not row:return dict(success=True,context=None),None
  row=dict(row);row['nearby']=json.loads(row['nearby']);return dict(success=True,context=row),None
 def remember_report(token,result):
  p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
  if not p or not result.get('id'):return
  near=[]
  if s:
   for k,q in api.PRESENCE.items():
    t=api.GTA_STATE.get(k)
    if q is p or not t or q.get('dimension',0)!=p.get('dimension',0)or time.time()-q.get('last_seen',0)>20:continue
    d=math.dist([s[c]for c in('x','y','z')],[t[c]for c in('x','y','z')])
    if d<=50:near.append(dict(server_id=q.get('server_id'),char_id=q['char_id'],name=q['name'],meters=round(d,1)))
  near.sort(key=lambda r:r['meters'])
  with w.database()as db:db.execute('INSERT OR REPLACE INTO pn_report_context115 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(result['id'],p['user_id'],p['char_id'],p.get('server_id'),*(round(s[c],2)if s else None for c in('x','y','z')),p.get('dimension',0),int(s.get('vehicle_id')or 0)if s else 0,max(0,int(p.get('health',200))-100),int(p.get('armor',0)),json.dumps(near[:12]),time.time()))
 def dispatch(path,v,token):
  if path=='/api/reports115/context':
   with api.LOCK:return context(v,token)
  if path=='/api/reports/create':
   with api.LOCK:
    result,cookie=previous(path,v,token)
    if result.get('success'):
     try:remember_report(token,result)
     except Exception:pass  # context is best effort; the report itself is already stored
    return result,cookie
  if path=='/api/chat/send':
   parts=str(v.get('message','')).strip().split();cmd=parts[0].lower()if parts else''
   if cmd in GIVE or cmd in PP_SEND or cmd in('/pp','/ppver','/ppal')or cmd in SELL or cmd in ACCEPT or cmd in REJECT:
    with api.LOCK:
     if cmd in GIVE:return give_cash(token,parts[1:]),None
     if cmd in SELL:return sell(token,parts[1:])
     if cmd in ACCEPT or cmd in REJECT:return answer(token,cmd,parts[1:])
     return pp_command(token,cmd,parts[1:]),None
  return previous(path,v,token)
 api.dispatch=dispatch;api.features115_installed=True;return api
