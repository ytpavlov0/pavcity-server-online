"""122 over the live v121 chain: weapon stock, weapon rights and police confiscation.

Stock: every gun shop weapon has a random daily stock (pn_weapon_stock122, 0–4 pieces, some days
none), rolled once per UTC day; /api/inventory/buy is refused when it is out ("yarın yenilenir")
and takes one piece when it succeeds.
Rights: a bought weapon carries 3 rights (pn_weapon_rights122). /silahhak lists them, /silahhakal
SİLAH buys one more right at the gun shop for 60% of the weapon price (at most 5).
Confiscation: /elkoy ID — an on-duty police officer (or staff on duty) within 5 m of a cuffed
player takes one right from each of that player's weapons; a weapon at 0 rights is removed from
the inventory. Every step is audited."""
import random,time,datetime,math
RIGHTS=3;MAX_RIGHTS=5;RIGHT_PRICE=.6
def install(api):
 if getattr(api,'features122_installed',False):return api
 import gameplay_v29.pn_inventory as inv,gameplay_v29.pn_admin as staff
 w=api.world;previous=api.dispatch
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_weapon_stock122(weapon TEXT PRIMARY KEY,stock INTEGER NOT NULL,day TEXT NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_weapon_rights122(char_id INTEGER NOT NULL,weapon TEXT NOT NULL,rights INTEGER NOT NULL,bought INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(char_id,weapon))')
 def today():return datetime.datetime.now(datetime.timezone.utc).date().isoformat()
 def roll(db):
  day=today()
  if db.execute('SELECT 1 FROM pn_weapon_stock122 WHERE day=? LIMIT 1',(day,)).fetchone():return
  rng=random.Random(day)
  for key,item in inv.WEAPONS.items():
   if item.get('category') in(None,'NULL','AMMO_GRENADE','AMMO_STICKYBOMB','AMMO_SMOKEGRENADE','AMMO_BZGAS','AMMO_MOLOTOV','AMMO_FIREEXTINGUISHER','AMMO_PETROLCAN','AMMO_FLARE'):n=99
   else:n=rng.choice([0,1,1,2,2,3,4])
   db.execute('INSERT INTO pn_weapon_stock122 VALUES(?,?,?) ON CONFLICT(weapon) DO UPDATE SET stock=excluded.stock,day=excluded.day',(key,n,day))
 def rights(db,cid,key):
  r=db.execute('SELECT rights FROM pn_weapon_rights122 WHERE char_id=? AND weapon=?',(cid,key)).fetchone()
  if r is None:db.execute('INSERT INTO pn_weapon_rights122(char_id,weapon,rights) VALUES(?,?,?)',(cid,key,RIGHTS));return RIGHTS
  return r['rights']
 def me(token):
  p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
  if not p or not s:raise ValueError('Önce karakterinle şehre gir.')
  return p,s
 def owned(p):return [k for k in inv.load(p)['owned'] if k in inv.WEAPONS]
 def remove(q,key):
  load=inv.load(q);load['owned'].pop(key,None)
  for part in('clips','tints'):load.get(part,{}).pop(key,None)
  if load.get('selected')==inv.WEAPONS[key]['slot']:load['selected']=0
  q['loadout']=load;inv.persist(q);q['weapon_ready_at']=time.time()+1
 def list_rights(token):
  p,_=me(token)
  with w.database()as db:rows=[[inv.WEAPONS[k].get('name',k),'%d/%d hak'%(rights(db,p['char_id'],k),MAX_RIGHTS)]for k in owned(p)]
  return dict(success=True,info=dict(title='Silah hakların',rows=rows or[['Durum','Silahın yok.']]),notice='Polis her el koyduğunda 1 hak düşer; 0 olunca silah gider. Ek hak: /silahhakal SİLAH (silahçıda).')
 def buy_right(token,args,uid):
  p,s=me(token)
  if len(args)!=1:raise ValueError('Kullanım: /silahhakal SİLAH_ANAHTARI (ör. pistol)')
  key=args[0].lower()
  if key not in owned(p):raise ValueError('Bu silah sende yok.')
  if not inv.at_shop(s,p):raise ValueError('Ek hak için silahçı NPC yanına yaya yaklaş.')
  with w.database()as db:
   n=rights(db,p['char_id'],key)
   if n>=MAX_RIGHTS:raise ValueError('Bu silahın hakkı zaten en fazla (%d).'%MAX_RIGHTS)
   cost=int(inv.WEAPONS[key]['price']*RIGHT_PRICE)
   if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(cost,uid,cost)).rowcount:raise ValueError('Yeterli paran yok ($%s gerekli).'%f'{cost:,}'.replace(',','.'))
   db.execute('UPDATE pn_weapon_rights122 SET rights=rights+1,bought=bought+1 WHERE char_id=? AND weapon=?',(p['char_id'],key))
   w.audit(db,uid,'weapon-right122',dict(char_id=p['char_id'],weapon=key,cost=cost))
  return dict(success=True,money=w.wallet(uid),notice='%s için 1 hak alındı (%d/%d).'%(inv.WEAPONS[key].get('name',key),n+1,MAX_RIGHTS))
 def police(db,p):
  if staff.rank(p['user_id'])>=2 and p.get('admin_duty'):return True
  return bool(p.get('faction_duty'))and bool(db.execute("SELECT 1 FROM pn_faction_members m JOIN pn_factions f ON f.id=m.faction_id WHERE m.char_id=? AND f.kind='police'",(p['char_id'],)).fetchone())
 def confiscate(token,args,uid):
  p,s=me(token)
  if len(args)!=1:raise ValueError('Kullanım: /elkoy OYUNCU_ID')
  cid=w.resolve_player_id(args[0],api.PRESENCE)
  pair=next(((k,q)for k,q in api.PRESENCE.items()if q['char_id']==cid),None)
  if not pair or cid==p['char_id']:raise ValueError('Oyuncu bulunamadı.')
  q,t=pair[1],api.GTA_STATE.get(pair[0])
  if not t or q.get('dimension',0)!=p.get('dimension',0)or math.dist([s[k]for k in('x','y','z')],[t[k]for k in('x','y','z')])>5:raise ValueError('Kişinin yanında olmalısın (5 m).')
  out=[]
  with w.database()as db:
   if not police(db,p):raise ValueError('El koyma yalnız görevdeki polise açık (/pduty).')
   r=db.execute('SELECT cuffed,until FROM pn_restrictions178 WHERE char_id=?',(cid,)).fetchone()
   if not r or not r['cuffed']or r['until']<time.time():raise ValueError('Önce kişiyi kelepçele.')
   guns=owned(q)
   if not guns:raise ValueError(q['name']+' üzerinde silah yok.')
   for key in guns:
    n=rights(db,cid,key)-1;name=inv.WEAPONS[key].get('name',key)
    if n<=0:db.execute('DELETE FROM pn_weapon_rights122 WHERE char_id=? AND weapon=?',(cid,key));out.append((key,name,0))
    else:db.execute('UPDATE pn_weapon_rights122 SET rights=? WHERE char_id=? AND weapon=?',(n,cid,key));out.append((key,name,n))
   w.audit(db,uid,'confiscate122',dict(target=cid,weapons=[[k,n]for k,_,n in out]))
  for key,_,n in out:
   if n<=0:remove(q,key)
  text=', '.join(name+(' (el konuldu, silindi)'if n<=0 else' (%d hak kaldı)'%n)for _,name,n in out)
  return dict(success=True,notice=q['name']+' · '+text)
 def dispatch(path,v,token):
  if path=='/api/inventory/buy':
   key=v.get('weapon')
   with api.LOCK:
    with w.database()as db:
     roll(db);row=db.execute('SELECT stock FROM pn_weapon_stock122 WHERE weapon=?',(key,)).fetchone()
    if row is not None and row['stock']<=0:raise ValueError('Bu silah bugün stokta yok. Stok her gün 03:00’te (UTC 00:00) yenilenir.')
    result,cookie=previous(path,v,token)
    if result.get('success'):
     p=api.PRESENCE.get(token)
     with w.database()as db:
      if row is not None and row['stock']<99:db.execute('UPDATE pn_weapon_stock122 SET stock=stock-1 WHERE weapon=? AND stock>0',(key,))
      if p:db.execute('INSERT INTO pn_weapon_rights122(char_id,weapon,rights) VALUES(?,?,?) ON CONFLICT(char_id,weapon) DO UPDATE SET rights=excluded.rights,bought=0',(p['char_id'],key,RIGHTS))
     result=dict(result,notice=str(result.get('notice',''))+' · %d hak'%RIGHTS)
    return result,cookie
  if path=='/api/weapons122/stock':
   with api.LOCK:
    with w.database()as db:roll(db);rows=[dict(r)for r in db.execute('SELECT weapon,stock FROM pn_weapon_stock122')]
   return dict(success=True,stock={r['weapon']:r['stock']for r in rows},day=today()),None
  if path=='/api/chat/send':
   parts=str(v.get('message','')).strip().split();cmd=parts[0].lower()if parts else''
   if cmd in('/silahhak','/silahhakal','/elkoy'):
    with api.LOCK:
     uid=api.authenticated61(token)
     if cmd=='/silahhak':return list_rights(token),None
     if cmd=='/silahhakal':return buy_right(token,parts[1:],uid),None
     return confiscate(token,parts[1:],uid),None
  return previous(path,v,token)
 api.dispatch=dispatch;api.features122_installed=True;return api
