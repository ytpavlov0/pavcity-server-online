"""114: staff chat with duty announcements, an admin panel API and weapon-based combat
damage over the live v108 chain.

Staff chat: rank >= 1 writes "/a mesaj". Lines live in pn_chat with scope 'admin' (stock
messages() ignores unknown scopes, so players never receive them) and are merged into
every staff member's sync. Every /aduty toggle posts "NAME [ID] yönetici görevine
girdi/çıktı." there, so the whole team sees who is on duty.
Admin panel: /api/admin114/players lists online players, staff, open reports and recent
anticheat records; /api/admin114/action maps whitelisted panel buttons onto the existing
chat commands, so every rank check and audit stays in pn_admin.
Damage: the stock sync accepts at most one hit per sync (one clock, 0.16 s cadence) and
applies a flat 20 (melee) / 25 (shot). That accepted hit is re-scored by the attacker's
weapon: fists 7 with a 0.55 s cadence, melee weapons 14-30, guns by class with range
falloff. Death and combat bookkeeping follow the re-scored result."""
import math,time,secrets
from collections import deque
STAFF_WINDOW=300
FIST=7;FIST_CADENCE=.55;MELEE_CADENCE=.7;GUN_BUTT=10
MELEE={'knife':30,'bat':24,'crowbar':24,'hammer':24,'golfclub':22,'nightstick':14}
CLASS={'AMMO_PISTOL':18,'AMMO_SMG':13,'AMMO_RIFLE':21,'AMMO_MG':19,'AMMO_SHOTGUN':42,'AMMO_SNIPER':85,'AMMO_MINIGUN':15,'AMMO_STUNGUN':0}
SPECIAL={'pistol50':26,'appistol':14,'microsmg':11,'sawnoffshotgun':48,'heavysniper':100}
ACTIONS={'goto':(2,'/goto {id}'),'gethere':(2,'/gethere {id}'),'revive':(2,'/revive {id}'),'heal':(2,'/sethp {id} 100'),
 'armor':(2,'/setarmor {id} 100'),'jail':(1,'/jail {id} {minutes} {reason}'),'unjail':(1,'/unjail {id}'),
 'kick':(2,'/ban {id} 5 {reason}'),'ban':(2,'/ban {id} {minutes} {reason}'),'money':(2,'/givemoney {id} {amount}'),
 'rank':(4,'/rankver {id} {rank}'),'duty':(1,'/aduty')}
def damage_for(kind,key,info,meters):
 """Health points removed by one accepted hit (armor is applied by the caller)."""
 if kind=='melee':
  if not info:return FIST
  return MELEE.get(key,18)if info.get('category')=='NULL'else GUN_BUTT
 if not info:return 0
 category=info.get('category');base=SPECIAL.get(key,CLASS.get(category,20))
 if category=='AMMO_SHOTGUN':base*=1 if meters<=8 else .55 if meters<=20 else .25
 elif category in('AMMO_PISTOL','AMMO_SMG'):base*=.7 if meters>40 else 1
 elif category in('AMMO_RIFLE','AMMO_MG'):base*=.8 if meters>80 else 1
 return int(round(base))
def install(api):
 if getattr(api,'features114_installed',False):return api
 import gameplay_v29.pn_admin as staff,gameplay_v29.pn_inventory as inv,gameplay_v29.pn_roleplay as rp
 w=api.world;previous=api.dispatch;lines=deque(maxlen=80);ranks={}
 with w.database()as db:
  for r in db.execute("SELECT * FROM pn_chat WHERE scope='admin' AND created>? ORDER BY id",(time.time()-STAFF_WINDOW,)):lines.append(dict(r,admin=0))
 def rank_of(p,fresh=False):
  hit=ranks.get(p['user_id'])
  if fresh or not hit or time.time()-hit[1]>15:hit=ranks[p['user_id']]=(staff.rank(p['user_id']),time.time())
  return hit[0]
 def post(p,body,author=True):
  now=time.time()
  row=dict(char_id=p['char_id']if author else 0,name=p['name']if author else'Sistem',body=body[:240],scope='admin',x=0,y=0,z=0,created=now,admin=0,dimension=0)
  with w.database()as db:row['id']=db.execute('INSERT INTO pn_chat(char_id,name,body,scope,x,y,z,created,admin,dimension)VALUES(?,?,?,?,?,?,?,?,?,?)',tuple(row[k]for k in('char_id','name','body','scope','x','y','z','created','admin','dimension'))).lastrowid
  row['rank_name']=staff.RANKS.get(rank_of(p),'')if author else'';lines.append(row);return row
 def caller(token):
  uid=api.authenticated61(token);p=api.PRESENCE.get(token)
  if not uid or not p or p.get('user_id')!=uid:raise ValueError('Önce karakterinle şehre gir.')
  return uid,p
 def players(token):
  uid,p=caller(token);level=rank_of(p,True)
  if level<1:raise ValueError('Bu panel yalnızca yetkililere açık.')
  now=time.time();rows=[]
  for key,q in api.PRESENCE.items():
   if q.get('world')!='gta'or now-q.get('last_seen',0)>30:continue
   s=api.GTA_STATE.get(key)or{};r=rank_of(q)
   if q.get('hide_admin')and level<4 and q is not p:r=0
   rows.append(dict(server_id=q.get('server_id'),char_id=q['char_id'],name=q['name'],rank=r,rank_name=staff.RANKS.get(r,''),duty=bool(q.get('admin_duty')),
    health=max(0,int(q.get('health',200))-100),armor=int(q.get('armor',0)),dimension=q.get('dimension',0),vehicle=int(s.get('vehicle_id')or 0),afk=int(s.get('afk_seconds',0)),
    jailed=bool(staff.jail(q['char_id'])),me=q is p))
  rows.sort(key=lambda r:r['server_id']or 0)
  with w.database()as db:
   team=[dict(r)for r in db.execute('SELECT s.user_id,s.rank,u.username FROM pn_staff s LEFT JOIN users u ON u.id=s.user_id ORDER BY s.rank DESC,s.user_id')]
   reports=[dict(r)for r in db.execute("SELECT id,name,category,body,created FROM pn_reports WHERE status='open' ORDER BY id DESC LIMIT 15")]
   try:cheats=[dict(r)for r in db.execute("SELECT a.id,a.char_id,a.at,a.kind,c.name||' '||c.surname AS name FROM pn_anticheat108 a LEFT JOIN characters c ON c.id=a.char_id ORDER BY a.id DESC LIMIT 15")]
   except Exception:cheats=[]
  for t in team:t['rank_name']=staff.RANKS.get(t['rank'],'')
  return dict(success=True,rank=level,rank_name=staff.RANKS.get(level,''),duty=bool(p.get('admin_duty')),players=rows,staff=team,reports=reports,anticheat=cheats,
   actions={k:v[0]for k,v in ACTIONS.items()},lines=list(lines)[-30:]),None
 def action(v,token):
  uid,p=caller(token);name=str(v.get('action',''))
  if name not in ACTIONS:raise ValueError('Bilinmeyen panel işlemi.')
  need,template=ACTIONS[name]
  if rank_of(p,True)<need:raise ValueError('Bu işlem için yetkin yetmiyor.')
  def whole(key,lo,hi):
   try:n=int(v.get(key))
   except(TypeError,ValueError):raise ValueError('Geçerli sayı yaz.')
   if not lo<=n<=hi:raise ValueError(f'Değer {lo}–{hi} aralığında olmalı.')
   return n
  fields=dict(id=whole('target',1,999999)if name!='duty'else 0)
  if '{minutes}'in template:fields['minutes']=whole('minutes',0 if name=='ban'else 1,525600 if name=='ban'else 1440)
  if '{amount}'in template:fields['amount']=whole('amount',1,10000000)
  if '{rank}'in template:fields['rank']=whole('rank',0,3)
  if '{reason}'in template:
   fields['reason']=' '.join(str(v.get('reason','')).split())[:120]
   if len(fields['reason'])<3:raise ValueError('Sebep yaz (en az 3 karakter).')
  result,cookie=dispatch('/api/chat/send',dict(message=template.format(**fields),scope='local',request_id=secrets.token_hex(16)),token)
  if result.get('success')and name not in('duty',):
   with api.LOCK:post(p,'panel · '+template.format(**fields).split(' ',1)[0]+' #'+str(fields['id'])+(' · '+fields['reason']if fields.get('reason')else''))
  return result,cookie
 def staff_chat(v,token):
  uid,p=caller(token);text=str(v.get('message','')).strip()[2:].strip()
  if rank_of(p,True)<1:raise ValueError('Yetkili sohbeti yalnızca yetkililere açık.')
  if not 1<=len(text)<=200:raise ValueError('Kullanım: /a mesaj (1–200 karakter)')
  import gameplay_v29.pn_multiplayer as mp
  mp.rate(token,'chat',.6);p['activity_at']=time.time();post(p,text)
  return dict(success=True),None
 def rescore(token,p,before,started,result):
  """Re-score the one hit the stock sync accepted (if any) by the attacker's weapon."""
  if p.get('last_hit_time',0)==before['hit_time']:return result
  victim=next(((k,q)for k,(q,snap)in before['targets'].items()if q.get('damage_sequence',0)!=snap['seq']),None)
  if not victim:return result
  key,q=victim;snap=before['targets'][key][1];t=api.GTA_STATE.get(key);me=api.GTA_STATE.get(token)or{}
  if not t:return result
  melee=q.get('damage_kind')==1;now=time.time()
  weapon=next(((k,i)for k,i in inv.WEAPONS.items()if i.get('hash')==me.get('weapon')),(None,None))
  meters=math.dist([me.get(k,0)for k in('x','y','z')],[t.get(k,0)for k in('x','y','z')])
  amount=damage_for('melee'if melee else'shoot',weapon[0],weapon[1],meters)
  if melee:
   cadence=FIST_CADENCE if not weapon[1]else MELEE_CADENCE
   if now-p.get('melee114_at',0)<cadence:amount=0
   else:p['melee114_at']=now
  stock_dead=q.get('health',200)<=100
  health,armor=snap['health'],snap['armor']
  if amount and not melee:
   absorbed=min(amount,armor);armor-=absorbed;amount-=absorbed
  health=max(0,health-amount)
  q['health']=t['health']=health;q['armor']=t['armor']=armor
  if health==snap['health']and armor==snap['armor']:q['damage_sequence']=t['damage_sequence']=snap['seq']
  dead=health<=100
  if dead and not stock_dead and snap['health']>100:
   q.setdefault('dead_at',now);rp.combat_event(q['char_id'],q.get('life_id',0),p['char_id'])
  elif not dead and stock_dead:
   if not snap['dead']:q.pop('dead_at',None)
   with w.database()as db:db.execute('DELETE FROM pn_combat_events WHERE target=? AND attacker=? AND created>=?',(q['char_id'],p['char_id'],started))
  result['players']=[dict(r,health=health,armor=armor)if r.get('char_id')==q['char_id']else r for r in result.get('players',[])]
  return result
 def dispatch(path,v,token):
  if path=='/api/admin114/players':
   with api.LOCK:return players(token)
  if path=='/api/admin114/action':return action(v,token)
  if path=='/api/chat/send':
   message=str(v.get('message','')).strip();head=message.split(' ',1)[0].lower()
   if head=='/a':
    with api.LOCK:return staff_chat(v,token)
   if head=='/apanel':
    with api.LOCK:uid,p=caller(token);ok=rank_of(p,True)>=1
    if not ok:raise ValueError('Yetkili paneli yalnızca yetkililere açık.')
    return dict(success=True,notice='Yetkili paneli: F9 tuşu veya HUD üzerindeki YETKİLİ düğmesi.',admin_panel114=True),None
   if head=='/aduty':
    with api.LOCK:
     p=api.PRESENCE.get(token);was=bool(p and p.get('admin_duty'))
     result,cookie=previous(path,v,token);p=api.PRESENCE.get(token)
     if result.get('success')and p and bool(p.get('admin_duty'))!=was:
      post(p,f"{p['name']} [{p.get('server_id')}] yönetici görevine {'girdi'if p.get('admin_duty')else'çıktı'}.",author=False)
     return result,cookie
   return previous(path,v,token)
  if path!='/api/gta/sync':return previous(path,v,token)
  with api.LOCK:
   p=api.PRESENCE.get(token);hits=v.get('hits')if isinstance(v.get('hits'),list)else[]
   before=None
   if p and hits:
    wanted={h.get('target')for h in hits if isinstance(h,dict)}
    before=dict(hit_time=p.get('last_hit_time',0),targets={k:(q,dict(seq=q.get('damage_sequence',0),health=q.get('health',200),armor=q.get('armor',0),dead='dead_at'in q))for k,q in api.PRESENCE.items()if q.get('char_id')in wanted and k!=token})
   started=time.time();result,cookie=previous(path,v,token);p=api.PRESENCE.get(token)
   if not result.get('success')or not p:return result,cookie
   if before and before['targets']:
    try:result=rescore(token,p,before,started,result)
    except Exception:pass  # balance must never break movement sync
   if lines and isinstance(result.get('messages'),list)and rank_of(p)>=1:
    cutoff=time.time()-STAFF_WINDOW;extra=[dict(r)for r in lines if r['created']>cutoff]
    if extra:result=dict(result,messages=sorted(result['messages']+extra,key=lambda m:m['id'])[-120:])
   return result,cookie
 api.dispatch=dispatch;api.features114_installed=True;api.features114_lines=lines;return api
