"""Server-owned need commands, audited atomically; compact mutation receipts."""
import copy,time
def install(api):
 if getattr(api,'admin84_installed',False):return api
 import gameplay_v29.pn_commands as commands
 import gameplay_v29.pn_admin as staff
 import gameplay_v29.pn_multiplayer as mp
 w=api.world;old=commands.command;previous=api.dispatch
 names={'/sethunger':'hunger','/setthirst':'thirst','/setthrist':'thirst','/setaclik':'hunger','/setsusuzluk':'thirst'}
 def command(cmd,args,uid,p,s,presences):
  if cmd not in names:return old(cmd,args,uid,p,s,presences)
  if staff.rank(uid)<2 or not p.get('admin_duty'):raise ValueError('Yönetici yetkisi ve /aduty gerekli.')
  w.live(p,s)
  if len(args)!=2:raise ValueError('Kullanım: '+cmd+' OYUNCU_ID 0–100')
  cid=w.resolve_player_id(args[0],presences);value=staff.number(args[1],0,100)
  target=next(((token,q)for token,q in presences.items()if q['char_id']==cid and time.time()-q.get('last_seen',0)<30),None)
  if not target:raise ValueError('Oyuncu çevrimiçi değil.')
  token,q=target;state=api.GTA_STATE.get(token)
  if not state:raise ValueError('Oyuncu dünyası henüz hazır değil.')
  field=names[cmd];candidate=copy.deepcopy(q);candidate[field]=value;candidate['needs_at']=time.time()
  with api.database()as db:
   db.execute('BEGIN IMMEDIATE');mp.save(candidate,state,True,connection=db)
   w.audit(db,uid,'needs84',dict(command=cmd,char_id=cid,field=field,value=value))
  q[field]=value;q['needs_at']=candidate['needs_at'];q['saved_at']=candidate['saved_at']
  return dict(success=True,notice=q['name']+' · '+('Tokluk'if field=='hunger'else'Su')+' %'+str(value)+' olarak ayarlandı.')
 def dispatch(path,v,token):
  result,cookie=previous(path,v,token)
  if path=='/api/chat/send'and result.get('success'):
   cmd=str(v.get('message','')).strip().split(' ',1)[0].lower()
   if cmd=='/admincommands'and result.get('info'):
    result['info']['rows'] += [['/sethunger ID 0–100','Tokluk ayarla'],['/setthirst ID 0–100','Su ayarla · /setthrist de geçerli']]
   if cmd in {'/sethp','/setarmor','/revive','/afuelveh','/fixveh','/setfuel'} and result.get('info',{}).get('title')=='Yönetici işlemi':
    result.pop('info');result.setdefault('notice',cmd+' tamamlandı.')
  return result,cookie
 commands.command=command;api.dispatch=dispatch;api.admin84_installed=True;return api
