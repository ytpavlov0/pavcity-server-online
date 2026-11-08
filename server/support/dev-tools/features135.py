"""135 over the live v134 chain: club NPCs you can meet and text.

Six city NPCs live at the clubs (Vanilla Unicorn, Bahama Mamas, Tequi-la-la). They are characters of a
system account that cannot sign in (password hash '!'), so the phone's normal contacts, threads and
message store work unchanged; each has a 7000xxxx number.
/api/npc135/near   the NPCs at the club you stand in (8 m)
/api/npc135/meet   {id}  adds the number to your contacts and starts the acquaintance (pn_npc135)
Texting a met NPC (normal /api/phone/message) gets a Turkish reply chosen from what you wrote; every
reply raises closeness (max once a minute, 0–100). Unknown senders get a polite brush-off."""
import time,random,re
CLUBS={'unicorn':dict(name='Vanilla Unicorn',x=128.0,y=-1298.0,z=29.2),'bahama':dict(name='Bahama Mamas',x=-1388.0,y=-586.0,z=30.2),'tequila':dict(name='Tequi-la-la',x=-565.0,y=276.0,z=83.0)}
PERSONAS=[('selin','Selin','Aydın','unicorn',70000001),('melis','Melis','Kara','unicorn',70000002),('deniz','Deniz','Yıldız','bahama',70000003),('arda','Arda','Demir','bahama',70000004),('ece','Ece','Şahin','tequila',70000005),('kaan','Kaan','Öztürk','tequila',70000006)]
LINES={
 'hello':['Selam! Seni gördüğüme sevindim 😊','Heyy, nasılsın?','Merhaba, kulüpten hatırlıyorum seni.'],
 'how':['İyiyim, bu akşam yine kulüpteyim. Sen?','Biraz yorgunum ama sen yazınca keyiflendim.','Her zamanki gibi; müzik, ışıklar, kalabalık.'],
 'meet':['Bu akşam kulübe gel, bir şeyler içeriz.','Gelirsen haber ver, kapıda karşılarım.','Bu gece doluyuz ama sana yer açarım 😉'],
 'compliment':['Teşekkür ederim, sen de fena değilsin 😄','Bunu duymak güzel.','Utandırma beni şimdi.'],
 'money':['Para konuşmayalım, keyfimize bakalım.','Bana içki ısmarlaman yeter 😄'],
 'bye':['Görüşürüz, kendine iyi bak!','İyi geceler 🌙','Sonra yazarım.'],
 'default':['Hmm, anlat bakalım.','Haha, ciddi misin?','Kulüpte konuşalım bunu.','Şu an biraz meşgulüm ama sonra yazarım.','Tamam 🙂']}
KEYS=[('bye',r'görüşürüz|iyi geceler|bay|hoşça'),('hello',r'^\s*(selam|merhaba|hey|sa|slm|mrb)'),('how',r'nasılsın|naber|ne yapıyorsun|napıyorsun'),('meet',r'buluş|gel|kulüp|akşam|bu gece|görüşelim|içki'),('compliment',r'güzel|tatlı|yakışıklı|harika|çok iyi'),('money',r'para|\$|dolar|ücret')]
def install(api):
 if getattr(api,'features135_installed',False):return api
 w=api.world;previous=api.dispatch;rng=random.Random();ids={}
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_npc135(char_id INTEGER NOT NULL,persona TEXT NOT NULL,closeness INTEGER NOT NULL DEFAULT 0,met REAL NOT NULL,last_reply REAL NOT NULL DEFAULT 0,PRIMARY KEY(char_id,persona))')
  cols={r[1]for r in db.execute('PRAGMA table_info(users)')}
  sysu=db.execute("SELECT id FROM users WHERE username='pav_npc_system'").fetchone()
  if not sysu:
   fields={'username':'pav_npc_system'}
   for k in('password_hash','password'):
    if k in cols:fields[k]='!'
   if 'created_at'in cols:fields['created_at']=time.time()
   db.execute('INSERT INTO users(%s) VALUES(%s)'%(','.join(fields),','.join('?'*len(fields))),tuple(fields.values()))
   sysu=db.execute("SELECT id FROM users WHERE username='pav_npc_system'").fetchone()
  uid=sysu['id']
  for key,first,last,club,number in PERSONAS:
   row=db.execute('SELECT char_id FROM pn_phone_numbers WHERE number=?',(number,)).fetchone()
   if row:ids[key]=row['char_id'];continue
   cid=db.execute("INSERT INTO characters(user_id,name,surname,role,gender,created_at) VALUES(?,?,?,'npc',?,?)",(uid,first,last,'male'if key in('arda','kaan')else'female',time.time())).lastrowid
   db.execute('INSERT INTO pn_phone_numbers(char_id,number) VALUES(?,?)',(cid,number));ids[key]=cid
 by_number={p[4]:p for p in PERSONAS};by_key={p[0]:p for p in PERSONAS}
 def me(token):
  uid=api.authenticated61(token);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
  if not uid or not p or not s:raise ValueError('Önce karakterinle şehre gir.')
  return uid,p,s
 def club_at(s,p):
  if p.get('dimension',0):return None
  return next((k for k,c in CLUBS.items() if ((s['x']-c['x'])**2+(s['y']-c['y'])**2)**.5<9 and abs(s['z']-c['z'])<6),None)
 def reply(body,closeness,first):
  low=body.lower()
  kind=next((k for k,rx in KEYS if re.search(rx,low)),'default')
  line=rng.choice(LINES[kind])
  if closeness>=60 and kind in('meet','default')and rng.random()<.4:line+=' Seni özledim bu arada.'
  return line
 def act(action,token,v):
  uid,p,s=me(token);cid=p['char_id'];club=club_at(s,p)
  with w.database()as db:
   if action=='near':
    if not club:return dict(success=True,club=None,people=[])
    met={r['persona']:r['closeness']for r in db.execute('SELECT persona,closeness FROM pn_npc135 WHERE char_id=?',(cid,))}
    return dict(success=True,club=dict(key=club,name=CLUBS[club]['name']),people=[dict(id=k,name=f+' '+l,met=k in met,closeness=met.get(k,0),number=n if k in met else None)for k,f,l,c,n in PERSONAS if c==club])
   if action=='meet':
    key=v.get('id');pz=by_key.get(key)
    if not pz:raise ValueError('Kişi bulunamadı.')
    if club!=pz[3]:raise ValueError('%s şu an %s’da; oraya git.'%(pz[1],CLUBS[pz[3]]['name']))
    if db.execute('SELECT 1 FROM pn_npc135 WHERE char_id=? AND persona=?',(cid,key)).fetchone():raise ValueError('%s ile zaten tanışıyorsun.'%pz[1])
    now=time.time();db.execute('INSERT INTO pn_npc135(char_id,persona,met) VALUES(?,?,?)',(cid,key,now))
    db.execute('INSERT OR IGNORE INTO pn_phone_contacts(char_id,number,name) VALUES(?,?,?)',(cid,pz[4],pz[1]+' '+pz[2]))
    db.execute('INSERT INTO pn_phone_messages(sender,target,body,created) VALUES(?,?,?,?)',(ids[key],cid,'Tanıştığımıza memnun oldum, ben %s 😊 Numaram bu, yaz istersen.'%pz[1],now))
    w.audit(db,uid,'npc-meet135',dict(persona=key))
    return dict(success=True,notice='%s ile tanıştın. Numarası rehberine eklendi (%d).'%(pz[1],pz[4]))
  raise ValueError('İşlem bulunamadı.')
 def dispatch(path,v,token):
  if path.startswith('/api/npc135/'):
   with api.LOCK:return act(path.rsplit('/',1)[-1],token,v if isinstance(v,dict)else{}),None
  if path=='/api/phone/message'and isinstance(v,dict)and v.get('number')in by_number:
   with api.LOCK:
    result,cookie=previous(path,v,token)
    p=api.PRESENCE.get(token)
    if result.get('success')and p:
     pz=by_number[v['number']];key=pz[0];now=time.time()
     with w.database()as db:
      rel=db.execute('SELECT * FROM pn_npc135 WHERE char_id=? AND persona=?',(p['char_id'],key)).fetchone()
      if not rel:text='Kusura bakma, seni tanıyamadım. Kulüpte tanışalım önce.'
      else:
       text=reply(str(v.get('body','')),rel['closeness'],pz[1])
       if now-rel['last_reply']>60:db.execute('UPDATE pn_npc135 SET closeness=MIN(100,closeness+2),last_reply=? WHERE char_id=? AND persona=?',(now,p['char_id'],key))
      db.execute('INSERT INTO pn_phone_messages(sender,target,body,created) VALUES(?,?,?,?)',(ids[key],p['char_id'],text,now+1))
    return result,cookie
  return previous(path,v,token)
 api.dispatch=dispatch;api.features135_installed=True;return api
