"""Register the independently streamed Buffalo; no complimentary ownership grants."""
MODEL='pavbufvi'
NAME='Bravado Buffalo · VI tarzı'
PRICE=285000
def install(api):
 if getattr(api,'buffalo93_installed',False):return api
 api.world.SPAWN_MODELS.add(MODEL);api.world.CATALOG[MODEL]=PRICE
 previous=api.dispatch
 def dispatch(path,v,token):
  result,cookie=previous(path,v,token)
  if path=='/api/vehicles/catalog'and result.get('success'):
   for row in result.get('catalog',[]):
    if row['model']==MODEL:row.update(name=NAME,currency='USD',author='GRtanto',source='https://www.gta5-mods.com/vehicles/gta-vi-style-buffalo-stx-replace')
  return result,cookie
 api.dispatch=dispatch;api.buffalo93_installed=True;return api
