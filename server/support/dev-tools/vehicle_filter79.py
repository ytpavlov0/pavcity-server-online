"""Retain corrupt record protection while admitting registered street models."""
def install(api):
 if getattr(api,'gameplay35_installed',False):return api
 import gameplay_v29.pn_traffic as traffic
 world=api.world;old_rows,old_dispatch=world.rows,world.dispatch
 def unavailable(model):return model not in world.SPAWN_MODELS and model not in traffic.ROAD_MODELS
 def reason(model):return f'Geçersiz eski model adı: {model}. Araç kaydı korunuyor; yönetici modelini düzeltmeli.'
 def rows(state):return [r for r in old_rows(state)if not unavailable(r['model'])]
 def dispatch(path,uid,token,payload,p,state,presences):
  action=path.rsplit('/',1)[-1]
  if action in ('retrieve','enter'):
   with world.database()as db:r=db.execute('SELECT model FROM pn_vehicles WHERE id=?',(payload.get('id'),)).fetchone()
   if r and unavailable(r['model']):raise ValueError(reason(r['model']))
  result=old_dispatch(path,uid,token,payload,p,state,presences)
  if action=='garage'and'vehicles'in result:
   result=dict(result,vehicles=[dict(v,available=False,unavailable_reason=reason(v['model']))if unavailable(v['model'])else v for v in result['vehicles']])
  return result
 world.rows=rows;world.dispatch=dispatch;api.gameplay35_installed=True
 return api
