"""128 over the live v122 chain: native cash settlement and downtime fuel.

/api/cash128/native {spent,gained}: the bridge mirrors the wallet into the Story cash stats so native
services (escorts, vending, strip club, …) work with the player's money. What the game spent is taken
from the wallet (never below 0, at most $2.000 per report); cash the game handed out (NPC drops,
robberies) is added up to $1.000 per report and $5.000 per character per hour
(pn_cash128). One report per second per session; everything is audited.
Downtime fuel: vehicles left with the engine on burned up to a day of fuel when the server came back
(fuel is charged from the last update while the engine is on). At start-up nobody sits in a car, so
every engine is switched off once."""
import time,datetime
SPEND_MAX=2000;GAIN_MAX=1000;GAIN_HOUR=5000
def install(api):
 if getattr(api,'features128_installed',False):return api
 w=api.world;previous=api.dispatch;last={}
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_cash128(char_id INTEGER NOT NULL,hour TEXT NOT NULL,gained INTEGER NOT NULL DEFAULT 0,spent INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(char_id,hour))')
  n=db.execute("UPDATE pn_vehicles SET state=json_set(state,'$.engine',json('false')) WHERE json_extract(state,'$.engine')=1").rowcount
  if n:w.audit(db,0,'engine-off128',dict(vehicles=n))
 w.VEHICLE_CACHE.clear()
 def amount(v,key):
  x=v.get(key,0)
  if type(x)is not int or x<0:raise ValueError('Geçersiz tutar.')
  return x
 def settle(token,v):
  uid=api.authenticated61(token);p=api.PRESENCE.get(token)
  if not p or not api.GTA_STATE.get(token):raise ValueError('Önce karakterinle şehre gir.')
  spent,gained=amount(v,'spent'),amount(v,'gained')
  now=time.time()
  if now-last.get(token,0)<.9:raise ValueError('Çok hızlı.')
  last[token]=now
  if len(last)>2048:
   for k in [k for k,t in last.items() if now-t>600]:last.pop(k,None)
  cid=p['char_id'];hour=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H')
  spent=min(spent,SPEND_MAX);gained=min(gained,GAIN_MAX);capped=False;notes=[]
  with w.database()as db:
   db.execute('INSERT OR IGNORE INTO pn_cash128(char_id,hour) VALUES(?,?)',(cid,hour))
   row=db.execute('SELECT gained FROM pn_cash128 WHERE char_id=? AND hour=?',(cid,hour)).fetchone()
   room=max(0,GAIN_HOUR-row['gained'])
   if gained>room:gained,capped=room,True
   if spent:
    bal=db.execute('SELECT balance FROM pn_wallet WHERE user_id=?',(uid,)).fetchone()
    spent=min(spent,max(0,bal['balance']if bal else 0))
    if spent:db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=?',(spent,uid));notes.append('Harcama: $'+f'{spent:,}'.replace(',','.'))
   if gained:db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(gained,uid));notes.append('Nakit alındı: +$'+f'{gained:,}'.replace(',','.'))
   db.execute('UPDATE pn_cash128 SET gained=gained+?,spent=spent+? WHERE char_id=? AND hour=?',(gained,spent,cid,hour))
   if spent or gained or capped:w.audit(db,uid,'native-cash128',dict(char_id=cid,spent=spent,gained=gained,capped=capped,reported=[v.get('spent'),v.get('gained')]))
  if capped:notes.append('Saatlik nakit toplama sınırına ulaştın ($'+f'{GAIN_HOUR:,}'.replace(',','.')+').')
  return dict(success=True,money=w.wallet(uid),spent=spent,gained=gained,capped=capped,notice=' · '.join(notes))
 def dispatch(path,v,token):
  if path=='/api/cash128/native':
   with api.LOCK:return settle(token,v),None
  return previous(path,v,token)
 api.dispatch=dispatch;api.features128_installed=True;return api
