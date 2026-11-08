"""Small shared service marker adapter. No player identities or grants added."""
def install(api):
 if getattr(api,'gameplay40_installed',False):return api
 previous=api.dispatch
 def dispatch(path,payload,token):
  result,cookie=previous(path,payload,token)
  if path=='/api/gta/sync'and result.get('success'):
   icons={'police':(60,3),'medical':(61,1),'casino':(679,2),'cafe':(52,8)}
   result=dict(result,services=[dict(s,sprite=icons[s['kind']][0],color=icons[s['kind']][1])if s.get('kind')in icons else s for s in result.get('services',[])])
  return result,cookie
 api.dispatch=dispatch;api.gameplay40_installed=True;return api
