"""Reviewable trade cards and seller receipts; the existing atomic transfer remains authoritative."""
import time

def install(api):
 if getattr(api,'vehicle_trade91_installed',False):return api
 previous=api.dispatch;cache={}
 with api.database()as db:db.execute('CREATE INDEX IF NOT EXISTS pn_sale91_seller ON pn_vehicle_sale84(seller,created)')
 def listing(cid):
  now=time.time()
  with api.database()as db:
   rows=[dict(r)for r in db.execute('''SELECT o.*,v.model,v.plate,
    sc.name||' '||sc.surname AS seller_name,bc.name||' '||bc.surname AS buyer_name
    FROM pn_vehicle_sale84 o JOIN pn_vehicles v ON v.id=o.vehicle_id
    JOIN characters sc ON sc.id=o.seller JOIN characters bc ON bc.id=o.buyer
    WHERE (o.buyer=? OR o.seller=?) AND o.created>? ORDER BY o.created DESC LIMIT 16''',(cid,cid,now-600))]
  for r in rows:
   r['currency']='USD';r['incoming']=r['buyer']==cid
   if r['status']=='pending'and r['expires']<=now:r['status']='expired'
  return dict(success=True,offers=rows,server_time=now)
 def dispatch(path,v,token):
  if path=='/api/trade91/list':
   with api.LOCK:
    uid=api.authenticated61(token);api.require_client61(token,v);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
    if not uid or not p or uid!=p['user_id']:raise ValueError('Önce şehre gir.')
    api.world.live(p,s);return listing(p['char_id']),None
  result,cookie=previous(path,v,token)
  if result.get('success')and path=='/api/chat/send'and str(v.get('message','')).strip().split(' ',1)[0].lower()in('/aracimisat','/arackabul','/aracreddet'):cache.clear()
  if result.get('success')and path=='/api/gta/sync':
   p=api.PRESENCE.get(token)
   if p:
    cid=p['char_id'];now=time.monotonic();old=cache.get(cid)
    if not old or now-old[0]>=3:
     old=(now,[r for r in listing(cid)['offers']if not r['incoming']and r['status']in('accepted','rejected')]);cache[cid]=old
     while len(cache)>256:cache.pop(next(iter(cache)))
    result['sale_results91']=old[1]
  return result,cookie
 api.dispatch=dispatch;api.vehicle_trade91_installed=True;return api
