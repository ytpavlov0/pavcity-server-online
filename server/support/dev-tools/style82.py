"""Separate, priced appearance services with atomic wallet/appearance receipts."""
import copy,hashlib,json,re,time

BARBER={'hair':500,'hairColor':250,'beard':250,'eyebrow':200,'eye':1000}
CLOTHING={'top':1200,'pants':800,'shoes':600,'torso':0,'undershirt':300,'texture':200}
SHOPS=[dict(id=82001+i,kind='clothing',name=name,sprite=73,color=2,radius=3,x=x,y=y,z=z)for i,(name,x,y,z)in enumerate([
 ('PAV Giyim · Legion',73.8,-1392.8,29.38),('PAV Giyim · Rockford',-709.6,-153.9,37.42),('PAV Giyim · Vespucci',-1193.3,-768.5,17.32)])]

def install(api):
 if getattr(api,'style82_installed',False):return api
 w,previous=api.world,api.dispatch
 with api.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_style_receipts82(user_id INTEGER NOT NULL,request_id TEXT NOT NULL,signature TEXT NOT NULL,result TEXT NOT NULL,PRIMARY KEY(user_id,request_id))')
 def actor(token,payload,studio=False):
  uid=api.authenticated61(token)
  if not uid:raise ValueError('Önce hesabına giriş yap.')
  api.require_client61(token,payload)
  p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
  cid=payload.get('char_id')if studio else p.get('char_id')if p else 0
  if type(cid)is not int:raise ValueError('Geçerli karakter seç.')
  with api.database()as db:owned=db.execute('SELECT 1 FROM characters WHERE id=? AND user_id=? AND id NOT IN(SELECT char_id FROM pn_character_archive)',(cid,uid)).fetchone()
  if not owned:raise ValueError('Karakter bulunamadı.')
  if not studio:
   if not p or not s:raise ValueError('Önce karakterinle şehre gir.')
   w.live(p,s)
   from restriction82 import free_actor
   free_actor(api,p,time.time())
   if p.get('dimension',0)or s.get('vehicle_id')or w.occupation(cid)[0]or p.get('cuffed')or p.get('restrained'):raise ValueError('Mağazaya hayatta, serbest ve yaya gel.')
  elif p or any(peer.get('user_id')==uid and time.time()-peer.get('last_seen',0)<30 for peer in api.PRESENCE.values()):raise ValueError('Şehirdeyken berber veya kıyafet mağazasını kullan.')
  return uid,cid,p,s
 def context(kind,s):
  if kind=='barber'and any(w.near(s,x,3)for x in w.BARBERS):return BARBER
  if kind=='clothing'and any(w.near(s,x,3)for x in SHOPS):return CLOTHING
  raise ValueError('Bu işlem için ilgili berbere / kıyafet mağazasına yaklaş (3 m).')
 def commit(uid,cid,p,kind,payload,prices):
  rid=payload.get('request_id')
  if not isinstance(rid,str)or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}',rid):raise ValueError('Geçerli işlem kimliği gerekli.')
  raw=payload.get('appearance');new=w.appearance(raw)
  signature=hashlib.sha256(json.dumps([cid,kind,new],sort_keys=True,separators=(',',':')).encode()).hexdigest()
  with api.database()as db:
   db.execute('BEGIN IMMEDIATE')
   prior=db.execute('SELECT signature,result FROM pn_style_receipts82 WHERE user_id=? AND request_id=?',(uid,rid)).fetchone()
   if prior:
    if prior['signature']!=signature:raise ValueError('İşlem kimliği farklı bir görünümde kullanılmış.')
    return dict(json.loads(prior['result']),replayed=True)
   row=db.execute('SELECT appearance,version FROM pn_character WHERE char_id=?',(cid,)).fetchone();old=w.appearance(json.loads(row['appearance'])if row else None);version=row['version']if row else 1
   if payload.get('appearance_version',version)!=version:raise ValueError('Görünümün değişmiş. Mağazayı yeniden aç; ücret kesilmedi.')
   changed=[key for key in new if new[key]!=old[key]]
   if kind!='studio'and any(key not in prices for key in changed):raise ValueError('Bu mağazada yalnız ilgili saç / kıyafet parçaları değiştirilebilir.')
   cost=sum(prices.get(key,0)for key in changed)
   if kind=='studio'and any(key not in prices for key in changed):cost+=5000
   if cost and not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(cost,uid,cost)).rowcount:raise ValueError('Bakiyen yetersiz. Değişiklik kaydedilmedi ve ücret kesilmedi.')
   if changed:
    db.execute('INSERT INTO pn_character VALUES(?,?,?) ON CONFLICT(char_id)DO UPDATE SET appearance=excluded.appearance,version=excluded.version',(cid,json.dumps(new),version+1));version+=1
   money=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()[0]
   result=dict(success=True,appearance=new,appearance_version=version,money=money,charged=cost,notice=('Görünüm kaydedildi · $'+format(cost,',')if changed else 'Görünüm zaten aynı; ücret kesilmedi.'))
   w.audit(db,uid,'style82',dict(char_id=cid,kind=kind,changed=changed,cost=cost))
   db.execute('INSERT INTO pn_style_receipts82 VALUES(?,?,?,?)',(uid,rid,signature,json.dumps(result)))
  if p:p.update(appearance=new,appearance_version=version)
  return result
 def dispatch(path,payload,token):
  with api.LOCK:
   if path=='/api/character/appearance':
    uid,cid,p,s=actor(token,payload,True)
    return commit(uid,cid,None,'studio',payload,{**BARBER,**CLOTHING}),None
   if path.startswith('/api/style82/'):
    uid,cid,p,s=actor(token,payload);kind=payload.get('kind');prices=context(kind,s)
    if path.endswith('/list'):return dict(success=True,kind=kind,prices=prices,money=w.wallet(uid),**w.character(cid)),None
    if path.endswith('/buy'):return commit(uid,cid,p,kind,payload,prices),None
    raise ValueError('Görünüm işlemi bulunamadı.')
   result,cookie=previous(path,payload,token)
   if path=='/api/gta/sync'and result.get('success')and not api.PRESENCE.get(token,{}).get('dimension',0):result=dict(result,services=result.get('services',[])+SHOPS)
   return result,cookie
 api.dispatch=dispatch;api.style82_installed=True
 return api
