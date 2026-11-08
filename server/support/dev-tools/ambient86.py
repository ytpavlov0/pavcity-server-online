"""Stable bounded membership for the existing shared pedestrian routes."""
import math
def select(agents,position,previous,limit=6):
 rows=[];retained=set(previous)
 for a in agents:
  point=a.get('point')
  if not point or a['route'].kind!='ped':continue
  distance=math.dist([position[k]for k in('x','y','z')],[point[k]for k in('x','y','z')])
  if math.isfinite(distance)and distance<150:rows.append((distance-(20 if a['id']in retained else 0),a['id'],a))
 return [a for _,_,a in sorted(rows,key=lambda v:(v[0],v[1]))[:limit]]
def install(api):
 if getattr(api,'ambient86_installed',False):return api
 previous=api.dispatch
 def dispatch(path,data,token):
  with api.LOCK:
   result,cookie=previous(path,data,token)
   if path=='/api/gta/sync'and result.get('success')and'ambient188'in result and not getattr(api,'ambient_car_traffic_enabled',False):
    p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
    if p and s:
     agents=[]if p.get('dimension',0)else select(api.ambient188_agents.values(),s,p.get('ambient86_ids',[]))
     p['ambient86_ids']=[a['id']for a in agents]
     result['ambient188']={**result['ambient188'],'peds':[dict(**a['point'],id=a['id'],model='a_m_y_business_01',vehicle_id=0,seat=-2)for a in agents]}
   return result,cookie
 api.dispatch=dispatch;api.ambient86_installed=True;return api
