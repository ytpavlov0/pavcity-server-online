"""UWU counter: bounded inventory purchases, persistent retry receipts and no free needs."""
import copy,json,re,time

COUNTER=dict(id=8901,kind='uwu',name='UWU Café · Kahve ve tatlı',x=-290.23,y=-76.42,z=49.52,radius=4,sprite=93,color=8)
ENTRANCE=dict(x=-281.8,y=-63.5,z=48.53)
MENU={
 'uwu_latte':dict(id=8901,name='UWU · Vanilyalı latte',kg=.25,price=240,color='#f6b8cc',icon='38',kind='drink',value=30),
 'uwu_tea':dict(id=8902,name='UWU · Demleme çay',kg=.3,price=180,color='#bce3d6',icon='70',kind='drink',value=25),
 'uwu_cookie':dict(id=8903,name='UWU · Çikolatalı muffin',kg=.15,price=150,color='#e9bd92',icon='158',kind='food',value=20),
 'uwu_sandwich':dict(id=8904,name='UWU · Özel sandviç',kg=.35,price=310,color='#e5d6ac',icon='167',kind='food',value=35)}

def install(api):
 if getattr(api,'cafe89_installed',False):return api
 from gameplay_v29 import pn_inventory as inv
 from gameplay_v29 import pn_economy as economy
 from gameplay_v29.pn_containers import personal,weight
 from restriction82 import free_actor
 w=api.world;previous=api.dispatch
 economy.PRODUCTS.update(MENU)
 if not any(s['id']==COUNTER['id']for s in w.SERVICES):w.SERVICES.append(dict(COUNTER))
 with api.database()as db:db.execute('CREATE TABLE IF NOT EXISTS pn_cafe_receipts89(char_id INTEGER,request_id TEXT,signature TEXT,result TEXT,created REAL,PRIMARY KEY(char_id,request_id))')
 def dispatch(path,v,token):
  if not path.startswith('/api/cafe89/'):return previous(path,v,token)
  with api.LOCK:
   uid=api.authenticated61(token);api.require_client61(token,v);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
   if not uid or not p or p['user_id']!=uid:raise ValueError('Önce şehre gir.')
   w.live(p,s);free_actor(api,p,time.time());inv.load(p)
   action=path.rsplit('/',1)[-1];near=not p.get('dimension',0)and w.near(s,COUNTER,5)
   if action=='list':return dict(success=True,menu=[dict(key=k,**x)for k,x in MENU.items()],near=near,entrance=ENTRANCE,money=w.wallet(uid)),None
   if action!='buy':raise ValueError('Geçersiz kafe işlemi.')
   key=v.get('item');qty=v.get('quantity');request=v.get('request_id')
   if key not in MENU or type(qty)is not int or not 1<=qty<=10:raise ValueError('Menüden 1–10 adet ürün seç.')
   if not isinstance(request,str)or not re.fullmatch(r'[a-zA-Z0-9-]{16,64}',request):raise ValueError('İşlem kimliği eksik.')
   signature=json.dumps([key,qty]);cid=p['char_id']
   with api.database()as db:
    old=db.execute('SELECT * FROM pn_cafe_receipts89 WHERE char_id=? AND request_id=?',(cid,request)).fetchone()
    if old:
     if old['signature']!=signature:raise ValueError('İşlem kimliği başka bir siparişe ait.')
     return dict(json.loads(old['result']),replayed=True,loadout=inv.view(p),money=w.wallet(uid)),None
   if not near or p.get('elevator176_ready')or s.get('vehicle_id')or w.occupation(cid)[0]:raise ValueError('Sipariş için UWU kafe tezgâhına yaya yaklaş.')
   product=MENU[key];updated=copy.deepcopy(p['loadout']);stock=updated.setdefault('stock',{});count=stock.get(key,0)
   if count+qty>20:raise ValueError('Bu üründen en fazla 20 adet taşıyabilirsin.')
   if weight(personal(p))+product['kg']*qty>(1000 if w.admin(uid)else 30):raise ValueError('Çantanda yeterli yer yok.')
   stock[key]=count+qty;cost=product['price']*qty;version=p.get('loadout_version',1)+1;now=time.time()
   result=dict(success=True,cost=cost,item=key,quantity=qty,notice=f'{qty} × {product["name"]} çantana eklendi.')
   with api.database()as db:
    if not db.in_transaction:db.execute('BEGIN IMMEDIATE')
    if db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(cost,uid,cost)).rowcount!=1:raise ValueError('Sipariş için yeterli paran yok.')
    db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version',(cid,json.dumps(updated),version))
    db.execute('INSERT INTO pn_cafe_receipts89 VALUES(?,?,?,?,?)',(cid,request,signature,json.dumps(result),now))
    db.execute('DELETE FROM pn_cafe_receipts89 WHERE char_id=? AND request_id NOT IN(SELECT request_id FROM pn_cafe_receipts89 WHERE char_id=? ORDER BY created DESC LIMIT 64)',(cid,cid))
    w.audit(db,uid,'uwu-purchase',dict(char_id=cid,item=key,quantity=qty,cost=cost))
   p['loadout']=updated;p['loadout_version']=version
   return dict(result,loadout=inv.view(p),money=w.wallet(uid)),None
 api.dispatch=dispatch;api.cafe89_installed=True;return api
