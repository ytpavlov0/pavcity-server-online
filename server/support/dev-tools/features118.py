"""118 over the live v117 chain: lighter syncs.

Every /api/gta/sync used to re-send the last 100 chat lines (5 minutes) to every player 6–7 times a
second. A client that sends chat_cursor (the newest chat id it has) now only receives newer lines;
clients without it keep the old behaviour. Every sync also carries server_time."""
import time
def install(api):
 if getattr(api,'features118_installed',False):return api
 previous=api.dispatch
 def dispatch(path,v,token):
  if path!='/api/gta/sync':return previous(path,v,token)
  cursor=v.get('chat_cursor') if isinstance(v,dict) else None
  if 'chat_cursor' in v:v={k:x for k,x in v.items() if k!='chat_cursor'}
  result,cookie=previous(path,v,token)
  if result.get('success'):
   result=dict(result,server_time=time.time())
   if type(cursor) is int and cursor>=0 and isinstance(result.get('messages'),list):
    result['messages']=[m for m in result['messages'] if isinstance(m,dict) and m.get('id',0)>cursor]
  return result,cookie
 api.dispatch=dispatch;api.features118_installed=True;return api
