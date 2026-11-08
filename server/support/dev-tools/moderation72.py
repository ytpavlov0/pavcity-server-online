"""Server-authorised spectator sessions, revoked immediately with duty/rank."""
import time
def install(api):
 if getattr(api,'moderation72_installed',False):return api
 import gameplay_v29.pn_admin as staff
 import gameplay_v29.pn_commands as commands
 import gameplay_v29.pn_multiplayer as mp
 w=api.world;previous=api.dispatch;old=commands.command
 public=('char_id','server_id','name','x','y','z','heading','speed','health','armor','vx','vy','vz','weapon','flags','aim','vehicle_id','seat','appearance','appearance_version','damage_sequence','damage_kind','melee_target','carried_by','fly','crouched','country','vip','vip_name','seatbelt','admin_duty','staff_rank','dimension','last_seen')
 def stop(p):p.pop('recon72',None);p.pop('recon72_origin',None)
 def valid(p):
  if not p or not p.get('admin_duty') or staff.rank(p['user_id'])<2:return False
  cid=p.get('recon72');q=next((v for v in api.PRESENCE.values() if v['char_id']==cid and v.get('world')=='gta' and time.time()-v.get('last_seen',0)<20),None)
  return q if q and q['char_id']!=p['char_id'] and staff.rank(q['user_id'])<staff.rank(p['user_id']) else False
 def command(cmd,args,uid,p,s,peers):
  if cmd not in ('/recon','/reconoff'):return old(cmd,args,uid,p,s,peers)
  if staff.rank(uid)<2 or not p.get('admin_duty'):raise ValueError('İzleme için yönetici görevi gerekli: /aduty')
  if p.get('client_platform')=='mobile':raise ValueError('Gizli izlemeyi PC yönetici istemcisinden başlat.')
  if cmd=='/reconoff' or not args:stop(p);return dict(success=True,notice='Gizli izleme kapatıldı.')
  if len(args)!=1:raise ValueError('Kullanım: /recon OYUNCU_ID · Çıkış: /reconoff')
  if p.get('dimension') or w.occupation(p['char_id'])[0] or s.get('vehicle_id') or staff.jail(p['char_id']):raise ValueError('İzlemeyi dışarıda, yaya ve serbestken başlat.')
  cid=w.resolve_player_id(args[0],peers);p['recon72']=cid
  q=valid(p)
  if not q:stop(p);raise ValueError('Oyuncu çevrim dışı, kendin veya eşit/üst yetkili.')
  p.setdefault('recon72_origin',{k:s[k] for k in ('x','y','z','heading')})
  with api.database() as db:w.audit(db,uid,'recon72',dict(target=cid))
  return dict(success=True,notice=q['name']+' gizli izleniyor. Çıkış: /reconoff')
 def dispatch(path,v,token):
  with api.LOCK:
   p=api.PRESENCE.get(token)
   for actor in api.PRESENCE.values():
    if actor.get('recon72') and not valid(actor):stop(actor)
   if p and p.get('recon72') and path.startswith(('/api/vehicles/','/api/inventory/','/api/properties/','/api/customs72/','/api/property72/')) and not path.endswith(('/list','/status','/seat-state200')):raise ValueError('Önce /reconoff ile izlemeyi bitir.')
   if p and p.get('recon72') and path=='/api/gta/sync':v={**v,**p['recon72_origin'],'hits':[],'shots53':[],'flags':0,'weapon':0,'vx':0,'vy':0,'vz':0,'speed':0,'vehicle_sample':None}
   result,cookie=previous(path,v,token)
   for actor in api.PRESENCE.values():
    if actor.get('recon72') and not valid(actor):stop(actor)
   p=api.PRESENCE.get(token)
   if path in ('/api/gta/sync','/api/gta/roster') and result.get('success'):
    ghosts={a['char_id'] for a in api.PRESENCE.values() if a.get('recon72') and valid(a)}
    own=p['char_id'] if p else 0
    result['players']=[r for r in result.get('players',[]) if r.get('char_id') not in ghosts or r.get('char_id')==own]
    result['recon72']=None
    q=valid(p) if p and p.get('recon72') else None
    target_state=next((s for t,s in api.GTA_STATE.items() if api.PRESENCE.get(t) is q),None) if q else None
    if q and target_state:
     result['recon72']={k:target_state.get(k,q.get(k)) for k in ('char_id','server_id','name','x','y','z','heading','dimension')}
     # Camera interest never changes the observing character's real coordinates.
     peers=[s for s in mp.active(api.GTA_STATE) if s.get('dimension',0)==q.get('dimension',0) and s['char_id']!=own and s['char_id'] not in ghosts and w.near(s,target_state,250)]
     peers.sort(key=lambda s:sum((s[k]-target_state[k])**2 for k in ('x','y','z')))
     own_row=next((r for r in result['players'] if r.get('char_id')==own),None)
     result['players']=([own_row] if own_row else [])+[{k:s[k] for k in public if k in s} for s in peers[:32]]
     result['vehicles']=[w.public(row) for row in w.rows(target_state)][:48]
   return result,cookie
 commands.command=command;api.dispatch=dispatch;api.moderation72_installed=True
 return api
