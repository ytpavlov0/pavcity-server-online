"""Complete the ordinary peer wire fields in the authorised72 spectator view."""
def install(api):
 if getattr(api,'recon73_installed',False):return api
 previous=api.dispatch
 def dispatch(path,values,token):
  with api.LOCK:
   result,cookie=previous(path,values,token)
   if result.get('success') and result.get('recon72'):
    states={s.get('char_id'):s for s in api.GTA_STATE.values()}
    for row in result.get('players',[]):
     state=states.get(row.get('char_id'),{})
     for key in ('aim_x','aim_y','aim_z','weapon_tint','speaking_until'):
      if key in state:row[key]=state[key]
     for key in ('aim_x','aim_y','aim_z'):row.setdefault(key,0)
   return result,cookie
 api.dispatch=dispatch;api.recon73_installed=True
 return api
