"""Original RP-only games: server RNG, bounded house liability and atomic receipts.

No cash payments, third-party scripts or schemas are installed on import.
"""
import json,math,re,secrets,time
clock=time.time
VENUE=dict(id=34001,kind='casino',name='PAV Oyun Salonu',sprite=679,color=2,radius=5,x=-558.3,y=284.3,z=82.18)
HORSES=[dict(id=0,name='Pamukkale',weight=450,odds=2.0),dict(id=1,name='Ege Rüzgârı',weight=290,odds=3.4),dict(id=2,name='Gece Yıldızı',weight=180,odds=5.2),dict(id=3,name='Şimşek',weight=80,odds=9.0)]
REDS={1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
def install(api):
 if getattr(api,'casino34_installed',False):return api
 original=api.dispatch;world=api.world
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_casino34_house(id INTEGER PRIMARY KEY CHECK(id=1),balance INTEGER NOT NULL CHECK(balance>=0),reserved INTEGER NOT NULL DEFAULT 0 CHECK(reserved>=0))')
  db.execute('INSERT OR IGNORE INTO pn_casino34_house VALUES(1,1000000,0)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_casino34_races(id INTEGER PRIMARY KEY,winner INTEGER NOT NULL,finish REAL NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_casino34_plays(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,char_id INTEGER NOT NULL,request TEXT NOT NULL,signature TEXT NOT NULL,game TEXT NOT NULL,stake INTEGER NOT NULL,choice TEXT NOT NULL,outcome TEXT,payout INTEGER NOT NULL DEFAULT 0,reserved INTEGER NOT NULL DEFAULT 0,race INTEGER,created REAL NOT NULL,settled REAL,UNIQUE(user_id,request))')
  db.execute('CREATE INDEX IF NOT EXISTS pn_casino34_pending ON pn_casino34_plays(race,settled)')
 def snapshot(row):
  return dict(id=row['id'],game=row['game'],stake=row['stake'],choice=json.loads(row['choice']),settled=row['settled']is not None,outcome=json.loads(row['outcome'])if row['outcome']else None,payout=row['payout']if row['settled']is not None else None,race=row['race'],created=row['created'])
 def settle(db,now):
  rows=db.execute('SELECT p.*,r.winner FROM pn_casino34_plays p JOIN pn_casino34_races r ON r.id=p.race WHERE p.settled IS NULL AND r.finish<=? LIMIT 1000',(now,)).fetchall()
  for r in rows:
   choice=json.loads(r['choice']);payout=int(round(r['stake']*HORSES[choice]['odds']))if choice==r['winner']else 0
   if not db.execute('UPDATE pn_casino34_plays SET outcome=?,payout=?,settled=? WHERE id=? AND settled IS NULL',(json.dumps(dict(winner=r['winner'])),payout,now,r['id'])).rowcount:continue
   db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(payout,r['user_id']))
   db.execute('UPDATE pn_casino34_house SET balance=balance-?,reserved=reserved-? WHERE id=1',(payout,r['reserved']))
   world.audit(db,r['user_id'],'casino34-settle',dict(play=r['id'],payout=payout))
 def at(p,s):
  world.live(p,s)
  if getattr(api,'services178_installed',False):
   with api.database()as db:r=db.execute('SELECT cuffed,prone FROM pn_restrictions178 WHERE char_id=? AND life=? AND dimension=? AND until>?',(p['char_id'],p.get('life_id',0),p.get('dimension',0),clock())).fetchone()
   if r and(r['cuffed']or r['prone']):raise ValueError('Kısıtlıyken oyun masası kullanılamaz.')
  if p.get('dimension',0)or s.get('vehicle_id')or world.occupation(p['char_id'])[0]or not world.near(s,VENUE,5)or p.get('inventory_action')or p.get('cuffed')or p.get('restrained'):raise ValueError('Oyun masasına hayatta, serbest ve yaya yaklaş (5 m).')
 def race(db,now):
  rid=int(now//40);start=rid*40;row=db.execute('SELECT * FROM pn_casino34_races WHERE id=?',(rid,)).fetchone()
  if not row:
   draw=secrets.randbelow(1000);winner=0
   for h in HORSES:
    if draw<h['weight']:winner=h['id'];break
    draw-=h['weight']
   db.execute('INSERT OR IGNORE INTO pn_casino34_races VALUES(?,?,?)',(rid,winner,start+35));row=db.execute('SELECT * FROM pn_casino34_races WHERE id=?',(rid,)).fetchone()
  return dict(id=rid,start=start,close=start+20,finish=row['finish'],winner=row['winner']if now>=row['finish']else None,open=now<start+20,horses=[{k:v for k,v in h.items()if k!='weight'}for h in HORSES])
 last_settle=[0]
 def dispatch(path,payload,token):
  with api.LOCK:
   now=clock()
   if not path.startswith('/api/casino34/'):
    result,cookie=original(path,payload,token)
    if path=='/api/gta/sync'and result.get('success'):
     if now-last_settle[0]>1:
      with api.database()as db:settle(db,now)
      last_settle[0]=now
     if not api.PRESENCE.get(token,{}).get('dimension',0):result=dict(result,services=result.get('services',[])+[VENUE])
    return result,cookie
   checked,cookie=original('/api/auth/me',{},token)
   if not checked.get('success'):return checked,cookie
   uid=checked['user_id'];p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token);action=path.rsplit('/',1)[-1]
   with api.database()as db:
    settle(db,now)
    if action=='list':
     history=[snapshot(r)for r in db.execute('SELECT * FROM pn_casino34_plays WHERE user_id=? ORDER BY id DESC LIMIT 20',(uid,))]
     wallet=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()
     return dict(success=True,venue=VENUE,money=wallet[0]if wallet else 0,race=race(db,now),server_now=now,history=history,limits=dict(min=10,max=5000),currency='Sadece oyun içi RP parası'),None
    if action not in ('play','race-bet'):raise ValueError('Oyun işlemi bulunamadı.')
    request=payload.get('request_id')
    if not isinstance(request,str)or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}',request):raise ValueError('Geçerli işlem kimliği gerekli.')
    game='horses'if action=='race-bet'else payload.get('game');stake=payload.get('stake');choice=payload.get('choice')
    if type(stake)is not int or not 10<=stake<=5000:raise ValueError('Bahis 10–5000 oyun parası olmalı.')
    if game=='roulette':
     if type(choice)is int and 0<=choice<=36:multiple=36
     elif type(choice)is str and choice in ('red','black','even','odd'):multiple=2
     else:raise ValueError('Sayı0–36, kırmızı/siyah veya tek/çift seç.')
    elif game=='slots':
     if choice is not None:raise ValueError('Slot seçimi geçersiz.')
     multiple=20
    elif game=='horses':
     if type(choice)is not int or not 0<=choice<4:raise ValueError('Geçerli at seç.')
     if type(payload.get('race_id'))is not int:raise ValueError('Yarış kimliği gerekli.')
     multiple=HORSES[choice]['odds']
    else:raise ValueError('Geçersiz oyun.')
    signature=json.dumps([game,stake,choice,payload.get('race_id')if game=='horses'else None],separators=(',',':'));prior=db.execute('SELECT * FROM pn_casino34_plays WHERE user_id=? AND request=?',(uid,request)).fetchone()
    if prior:
     if prior['signature']!=signature:raise ValueError('Bu işlem kimliği farklı bir bahiste kullanılmış.')
     return dict(success=True,already_used=True,play=snapshot(prior),money=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()[0],server_now=now),None
    at(p,s)
    recent=db.execute('SELECT created FROM pn_casino34_plays WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    if recent and now-recent[0]<1:raise ValueError('Önceki oyunun sonucunu bekle.')
    r=race(db,now)if game=='horses'else None
    if r and r['id']!=payload['race_id']:raise ValueError('Yarış değişti. Listeyi yenile; paran harcanmadı.')
    if r and not r['open']:raise ValueError('Bu yarışın bahisleri kapandı. Yeni yarışı bekle.')
    if r and db.execute('SELECT 1 FROM pn_casino34_plays WHERE user_id=? AND race=?',(uid,r['id'])).fetchone():raise ValueError('Bir yarışta tek bahis yapabilirsin.')
    house=db.execute('SELECT * FROM pn_casino34_house WHERE id=1').fetchone();maximum=int(round(stake*multiple))
    if house['balance']-house['reserved']+stake<maximum:raise ValueError('Masanın kasası bu bahsi karşılamıyor. Daha düşük miktar seç.')
    # This conditional write acquires the SQLite writer lock and rechecks the
    # latest liability, including bets accepted by the other origin/process.
    if not db.execute('UPDATE pn_casino34_house SET balance=balance+?,reserved=reserved+? WHERE id=1 AND balance-reserved+?>=?',(stake,maximum,stake,maximum)).rowcount:raise ValueError('Masanın kasası bu bahsi karşılamıyor. Daha düşük miktar seç.')
    if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(stake,uid,stake)).rowcount:raise ValueError('Yeterli oyun paran yok.')
    outcome=None;payout=0;reserved=maximum if r else 0
    if game=='roulette':
     number=secrets.randbelow(37);color='green'if number==0 else'red'if number in REDS else'black';win=choice==number if type(choice)is int else color==choice if choice in ('red','black')else number!=0 and number%2==(0 if choice=='even'else 1);payout=stake*multiple if win else 0;outcome=dict(number=number,color=color)
    elif game=='slots':
     reels=[secrets.randbelow(6)for _ in range(3)];mult=20 if reels==[5,5,5]else 10 if len(set(reels))==1 else 2 if reels.count(0)==2 else 1 if reels.count(0)==1 else 0;payout=stake*mult;outcome=dict(reels=reels,multiplier=mult)
    pid=db.execute('INSERT INTO pn_casino34_plays(user_id,char_id,request,signature,game,stake,choice,outcome,payout,reserved,race,created,settled)VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid,p['char_id'],request,signature,game,stake,json.dumps(choice),json.dumps(outcome)if outcome is not None else None,payout,reserved,r['id']if r else None,now,None if r else now)).lastrowid
    if not r:db.execute('UPDATE pn_casino34_house SET balance=balance-?,reserved=reserved-? WHERE id=1',(payout,maximum))
    db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(payout,uid));world.audit(db,uid,'casino34-bet',dict(play=pid,game=game,stake=stake,payout=payout))
    row=db.execute('SELECT * FROM pn_casino34_plays WHERE id=?',(pid,)).fetchone();money=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()[0]
    return dict(success=True,play=snapshot(row),money=money,server_now=now,notice='Bahis yarışa kaydedildi.'if r else'Sonuç kaydedildi.'),None
 api.dispatch=dispatch;api.casino34_installed=True;return api
