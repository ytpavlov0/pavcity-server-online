"""Published luxury prices and once-per-period owned-office income."""
import time
PRICES={'pavtofas':3000000,'pavbus':4000000,'audquattros':10000000,'skyline':15000000,'i8':20000000,'g65':25000000,'banshee':9000000,'comet2':8000000,'zentorno':18000000,'adder':22000000,'turismor':16000000,'t20':25000000}
def install(api):
 if getattr(api,'economy72_installed',False):return api
 w=api.world;previous=api.dispatch
 w.CATALOG.update(PRICES)
 with api.database() as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_office_bonus72(user_id INTEGER NOT NULL,period INTEGER NOT NULL,amount INTEGER NOT NULL,PRIMARY KEY(user_id,period))')
  # Old completed periods are never paid retroactively during a rollout.
  db.execute('INSERT OR IGNORE INTO pn_office_bonus72 SELECT user_id,period,0 FROM pn_payroll61 WHERE period>0')
 def dispatch(path,v,token):
  with api.LOCK:
   result,cookie=previous(path,v,token);p=api.PRESENCE.get(token)
   status=result.get('payroll61')
   if result.get('success') and p and status and status['period']>0:
    uid=p['user_id'];period=status['period']
    cached=p.get('office72_cache')
    if cached and cached['period']==period:
     result['payroll61']={**status,'amount':cached['amount'],'office_bonus':cached['bonus']}
     return result,cookie
    with api.database() as db:
     db.execute('BEGIN IMMEDIATE')
     receipt=db.execute('SELECT amount FROM pn_office_bonus72 WHERE user_id=? AND period=?',(uid,period)).fetchone()
     record=db.execute('SELECT * FROM pn_payroll61 WHERE user_id=?',(uid,)).fetchone()
     if not receipt:
      count=db.execute("SELECT count(*) FROM pn_properties WHERE owner=? AND kind='office'",(p['char_id'],)).fetchone()[0]
      bonus=min(3,count)*500
      db.execute('INSERT INTO pn_office_bonus72 VALUES(?,?,?)',(uid,period,bonus))
      if bonus:
       db.execute('UPDATE pn_payroll61 SET amount=amount+? WHERE user_id=?',(bonus,uid))
       if record['paid_period']>=period:
        db.execute('UPDATE pn_bank SET balance=balance+? WHERE user_id=?',(bonus,uid))
        db.execute('INSERT INTO pn_rp_ledger(user_id,char_id,kind,amount,detail,created) VALUES(?,?,?,?,?,?)',(uid,p['char_id'],'office72',bonus,'Saatlik ofis geliri · dönem '+str(period),time.time()))
       w.audit(db,uid,'office-bonus72',dict(period=period,amount=bonus))
     else:bonus=receipt[0]
     amount=db.execute('SELECT amount FROM pn_payroll61 WHERE user_id=?',(uid,)).fetchone()[0]
     bank=db.execute('SELECT balance FROM pn_bank WHERE user_id=?',(uid,)).fetchone()
    status={**status,'amount':amount,'office_bonus':bonus};result['payroll61']=status
    p['office72_cache']=dict(period=period,amount=amount,bonus=bonus)
    if p.get('payroll61_cache'):p['payroll61_cache']=(p['payroll61_cache'][0],status)
    if bank:result['bank']=bank[0]
   if path=='/api/vehicles/donate-list' and result.get('success'):
    for row in result.get('catalog',[]):row['price']=PRICES.get(row['model'],w.CATALOG.get(row['model']))
   return result,cookie
 api.dispatch=dispatch;api.economy72_installed=True
 return api
