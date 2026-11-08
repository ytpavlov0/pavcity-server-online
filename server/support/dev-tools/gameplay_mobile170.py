"""Narrow extension to pinned V28: shared recovery policy and public duty rank.

No credentials, permission grants, role setters or alternative world registry.
"""
import time
def install(api):
 if getattr(api,'mobile170_installed',False):return api
 original=api.dispatch;world=api.world;multi=api.multiplayer;staff=api.staff
 storage=__import__(api.__package__+'.pn_storage',fromlist=['request'])
 def dispatch(path,payload,token):
  with api.LOCK,storage.request():
   if path.startswith('/api/mdc/'):
    from mdc170 import dispatch as terminal
    return terminal(api,path,payload,token,original)
   if path=='/api/inventory/use-cancel' and payload.get('action_id'):
    checked,_=original('/api/auth/me',{},token)
    if not checked.get('success'):return checked,None
    task=api.PRESENCE.get(token,{}).get('inventory_action')
    if not task or task.get('id')!=payload['action_id']:return dict(success=True,notice='Önceki işlem zaten kapandı.'),None
   if path=='/api/gta/respawn':
    # Validate the same account/ban/session policy before even serving a retry.
    checked,_=original('/api/auth/me',{},token)
    if not checked.get('success'):return checked,None
    p=api.PRESENCE.get(token);state=api.GTA_STATE.get(token);life=payload.get('life_id')
    previous=p.get('recovery170') if p else None
    if type(life)is int and previous and previous['from_life']==life:return previous['response'],None
    if life is not None and (type(life)is not int or not p or life!=p.get('life_id',0)):raise ValueError('Eski yaralanma kaydı. Şehri tekrar eşitle.')
    old_life=p.get('life_id',0) if p else 0
    # Original endpoint owns injury/delay/jail/seat/carry validation and spawn.
    with api.database() as db:
     result,cookie=original(path,payload,token)
     if not result.get('success'):return result,cookie
     uid=checked['user_id'];balance=world.wallet(uid);charge=min(2500,max(0,int(balance)//10))
     if charge:db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(charge,uid,charge))
     lost={key:min(1,max(0,int(p.get(key,0)))) for key in ('water','food')}
     for key,amount in lost.items():p[key]=max(0,int(p.get(key,0))-amount)
     p['health']=125;state['health']=125;p['respawn_spawn']['health']=125
     p['hunger']=max(30,p.get('hunger',100));p['thirst']=max(30,p.get('thirst',100))
     state.update(health=125,hunger=p['hunger'],thirst=p['thirst'],food=p.get('food',0),water=p.get('water',0))
     multi.save(p,state,True);world.audit(db,uid,'hospital-recovery170',dict(char_id=p['char_id'],life=old_life,charge=charge,lost=lost))
     result.update(spawn=dict(p['respawn_spawn']),money=world.wallet(uid),recovery=dict(from_life=old_life,charge=charge,lost=lost,health=25),notice=f"Hastanede %25 canla uyandın. Nakit kesintisi ${charge}; kayıp: {lost['water']} su, {lost['food']} yiyecek. Silahların korundu.")
     p['recovery170']=dict(from_life=old_life,response=result)
     return result,cookie
   result,cookie=original(path,payload,token)
   if path=='/api/gta/sync' and result.get('success') and token in api.GTA_STATE:api.GTA_STATE[token]['crouched']=payload.get('crouched')is True
   if path in ('/api/gta/sync','/api/gta/roster') and result.get('success'):
    # Only visible duty ranks are public, including the current server-side
    # hide-admin setting. The client never supplies its own rank.
    presence={p.get('char_id'):p for p in api.PRESENCE.values()}
    result=dict(result);players=[]
    for row in result.get('players',[]):
     p=presence.get(row.get('char_id'));level=staff.rank(p['user_id']) if p and row.get('admin_duty') and not p.get('hide_admin') else 0
     players.append(dict(row,staff_rank=level,crouched=next((s.get('crouched',False)for s in api.GTA_STATE.values()if s.get('char_id')==row.get('char_id')),False)))
    result['players']=players
   return result,cookie
 api.dispatch=dispatch;api.mobile170_installed=True;return api
