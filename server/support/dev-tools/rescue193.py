"""193: dead means dead until help comes, even across a page reload.
192 made /api/gta/respawn wait 60 s for medics, but a reload (F5) during that minute went through the 191 join
recovery: charged, then put at the hospital with 25 % health, so the wait could be skipped. The server now remembers
each death (time and place, from the sync) while the player stays down. A dead character that joins again within 10
minutes of that death comes back unconscious where it fell (health 100 = down) with the same death time, so the medic
window, /canlandir, the NPC paramedic and the hospital button carry on as before. An older death keeps the 191 terms
(hospital, 10 % / max $2,500)."""
import time
KEEP=600
def install(api,v191,now=time.time):
 if getattr(api,'rescue193_installed',False):return api
 DEATHS={};old=api.dispatch;orig_recover=v191.recover;STATS={'kept_down':0}
 def recover(api_,token,result):
  p=api_.PRESENCE.get(token);d=DEATHS.get(p['char_id'])if p else None
  if d and now()-d['at']<KEEP:
   p['health']=100;p['dead_at']=d['at'];STATS['kept_down']+=1
   spawn=dict(result.get('spawn')or{},**d['pos'],health=100,armor=0)
   return dict(result,spawn=spawn,down193=True,notice='Hâlâ baygınsın: sağlık ekibini bekle, sonra hastanede doğabilir ya da NPC sağlıkçı çağırabilirsin.')
  return orig_recover(api_,token,result)
 v191.recover=recover
 def dispatch(path,*a,**k):
  out=old(path,*a,**k)
  if path=='/api/gta/sync':
   try:
    token=a[1]if len(a)>1 else k.get('token','')
    with api.LOCK:
     p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
     if p and s:
      if p.get('health',200)<=100 and 'dead_at'in p:
       if p['char_id']not in DEATHS or DEATHS[p['char_id']]['at']!=p['dead_at']:DEATHS[p['char_id']]=dict(at=p['dead_at'],pos={k2:s[k2]for k2 in('x','y','z','heading')})
      elif p.get('health',200)>100:DEATHS.pop(p['char_id'],None)
    if len(DEATHS)>2000:
     for cid in[c for c,d in DEATHS.items()if now()-d['at']>KEEP]:DEATHS.pop(cid,None)
   except Exception:pass
  return out
 api.dispatch=dispatch;api.rescue193_installed=True;api.rescue193=dict(deaths=DEATHS,stats=STATS)
 return api
