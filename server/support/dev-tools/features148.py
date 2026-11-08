"""148: one SQLite connection per periodic request (sync, voice send/poll, presence, phone/jobs status).

/api/gta/sync passes through ~60 dispatch layers. Layers that touch the database outside
session_api's own pn_storage.request() scope each opened a fresh SQLite connection (13-15 per
sync), and the first statement on every fresh connection re-parses the 231-object schema
(~3.5 ms on this VDS). Under api.LOCK that made one sync cost 70-100 ms and capped the server at
~10-14 syncs/s for everyone together. Running these periodic paths inside one pn_storage.request()
lets every nested database() block reuse the thread's connection: nested blocks become savepoints
and each top-level block still commits on exit, exactly as inside session_api.dispatch today.
No lock is added and no request or response field changes, so every client build keeps working."""
PATHS = frozenset(('/api/gta/sync', '/api/gta/voice', '/api/gta/voice/poll', '/api/gta/presence', '/api/phone/status', '/api/jobs/status'))
def install(api):
 if getattr(api,'features148_installed',False):return api
 import gameplay_v29.pn_storage as storage  # importable only after the v30 base install() added its path
 previous=api.dispatch
 def dispatch(path,v,token):
  if path not in PATHS:return previous(path,v,token)
  with storage.request():return previous(path,v,token)
 api.dispatch=dispatch;api.features148_installed=True;return api
