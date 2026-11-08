"""Refresh retains its tab lease; expired predecessor leases can leave safely."""
import time

def install(api):
 if getattr(api,'session82_installed',False):return api
 previous=api.dispatch
 def dispatch(path,payload,token):
  with api.LOCK:
   if path=='/api/lobby/leave':
    uid=api.authenticated61(token);p=api.PRESENCE.get(token)
    if uid and p and p.get('user_id')==uid and p.get('client61')and payload.get('client61')!=p['client61']:
     if time.time()-p.get('last_seen',0)<30:raise ValueError('Hesabın başka sekmede etkin. Diğer oyun sekmesini kapat; bağlantı kesildikten 30 saniye sonra tekrar dene.')
     # Same authenticated account, expired lease. Delegate the normal save/leave
     # transaction; do not forge a join, change character ownership or discard state.
     payload={**payload,'client61':p['client61']}
   return previous(path,payload,token)
 api.dispatch=dispatch;api.session82_installed=True
 return api
