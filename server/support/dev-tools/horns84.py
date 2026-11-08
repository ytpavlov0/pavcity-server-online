"""Purchased horns use supplied sounds; proximity and driver lease are authoritative."""
import json,time,math
from pathlib import Path
def install(api):
 if getattr(api,'horns84_installed',False):return api
 import gameplay_v29.pn_economy as economy
 from restriction82 import free_actor
 catalog=json.loads((Path(__file__).resolve().parents[2]/'support/fixes84/assets/horns.json').read_text());allowed={0}|{r['id']for r in catalog};w=api.world;previous=api.dispatch;held={};last={}
 economy.TUNING['custom_horn']=dict(name='Havalı korna',price=15000,min=0,max=max(allowed))
 def dispatch(path,v,token):
  if path in('/api/customs72/buy','/api/tuning/buy')and v.get('part')=='custom_horn'and(type(v.get('value'))is not int or v['value']not in allowed):raise ValueError('Pakette bulunan bir korna seç.')
  if path=='/api/horns84/catalog':return dict(success=True,horns=catalog,price=15000),None
  if path=='/api/horns84/state':
   with api.LOCK:
    uid=api.authenticated61(token);api.require_client61(token,v);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
    if not uid or not p or p['user_id']!=uid:raise ValueError('Önce şehre gir.')
    w.live(p,s)
    if v.get('on')is False:held.pop(p['char_id'],None);return dict(success=True),None
    if v.get('on')is not True:raise ValueError('Korna durumu geçersiz.')
    free_actor(api,p,time.time())
    vid,seat=w.occupation(p['char_id'])
    if not vid or seat!=-1 or vid!=v.get('id'):raise ValueError('Korna için sürücü koltuğunda olmalısın.')
    row=w.public(w.vehicle(vid));kind=row.get('mods',{}).get('custom_horn',0)
    if kind not in allowed or not kind:raise ValueError('Bu araçta özel korna takılı değil.')
    now=time.monotonic()
    if now-last.get(p['char_id'],-1e9)<.15:return dict(success=True,accepted=False),None
    last[p['char_id']]=now;old=held.get(p['char_id']);held[p['char_id']]=dict(id=vid,kind=kind,x=s['x'],y=s['y'],z=s['z'],dimension=p.get('dimension',0),until=now+1.5,started=old['started']if old and old['kind']==kind and old['id']==vid else time.time())
    for cid in list(held):
     if held[cid]['until']<=now:held.pop(cid,None);last.pop(cid,None)
    return dict(success=True),None
  result,cookie=previous(path,v,token)
  if path=='/api/gta/sync'and result.get('success'):
   p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token);now=time.monotonic()
   for cid in list(held):
    if held[cid]['until']<=now:held.pop(cid,None);last.pop(cid,None)
   if p and s:result['horns84']=[{k:r[k]for k in('id','kind','x','y','z','started')}for cid,r in held.items()if r['until']>now and r['dimension']==p.get('dimension',0)and w.occupation(cid)==(r['id'],-1)and math.dist([s[k]for k in('x','y','z')],[r[k]for k in('x','y','z')])<70][:8]
  return result,cookie
 api.dispatch=dispatch;api.horns84_installed=True;return api
