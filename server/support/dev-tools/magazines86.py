"""Prepared magazines conserve ammunition independently of native loose rounds."""
import copy, json, secrets, time

def install(api):
 if getattr(api,'magazines86_installed',False):return api
 from gameplay_v29 import pn_inventory as inv
 from restriction82 import free_actor
 w=api.world;old=inv.dispatch;view=inv.view;sample=inv.sample
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_magazine_receipts86(char_id INTEGER,action_id TEXT,created REAL,PRIMARY KEY(char_id,action_id))')
 def magazines(p,key):return inv.load(p).get('magazines86',{}).get(key,[])
 def info(p,full=True):
  r=view(p,full);r['magazines86']={k:list(v)for k,v in inv.load(p).get('magazines86',{}).items()if v};return r
 def clear(p):p.pop('inventory_action',None);p.pop('activity',None)
 def check(p,s,key):
  w.live(p,s);free_actor(api,p,time.time())
  if w.occupation(p['char_id'])[0] or s.get('vehicle_id') or p.get('elevator176_ready'):raise ValueError('Şarjör için araçtan in ve geçişi tamamla.')
  load=inv.load(p)
  if key not in inv.WEAPONS or key not in load['owned'] or load['selected']!=inv.WEAPONS[key]['slot'] or inv.clip_capacity(key)<=1:raise ValueError('Önce uyumlu silahı kuşan.')
 def possible(p,key,op):
  r=info(p);load=p['loadout'];mags=magazines(p,key)
  if op=='pack':
   if sum(len(v)for v in load.get('magazines86',{}).values())>=6:raise ValueError('En fazla 6 hazır şarjör taşıyabilirsin.')
   if r['ammo']<=r['clip'] and load.get('stock',{}).get('ammo_'+key,0)<1:raise ValueError('Şarjör doldurmak için yedek mermi veya paket gerekiyor.')
  elif op=='load':
   if not mags:raise ValueError('Hazır şarjörün yok.')
   if r['clip']>=r['clip_capacity']:raise ValueError('Şarjörün zaten dolu.')
   if r['ammo']+max(mags)>999:raise ValueError('Önce yedek mermi miktarını azalt.')
  elif op=='unpack':
   if not mags:raise ValueError('Boşaltılacak hazır şarjör yok.')
   if r['ammo']+mags[-1]>999:raise ValueError('Yedek mermi sınırı 999.')
  else:raise ValueError('Geçersiz şarjör işlemi.')
 def dispatch(path,uid,token,data,p,s):
  action=path.rsplit('/',1)[-1];item=data.get('item');task=p.get('inventory_action');inv.load(p)
  if action=='use-start':
   op=key=None
   if isinstance(item,str) and item.startswith('magazine86:'):
    parts=item.split(':')
    if len(parts)!=3:raise ValueError('Geçersiz şarjör.')
    _,op,key=parts
   elif isinstance(item,str) and item.startswith('ammo_') and magazines(p,item[5:]):op,key='load',item[5:]
   if op:
    if task:raise ValueError('Önce devam eden işlemi bitir.')
    check(p,s,key);possible(p,key,op);now=time.time();duration=3 if op=='pack' else 2
    p['inventory_action']=dict(id=secrets.token_hex(16),item='ammo_'+key,magazine86=op,key=key,started=now,until=now+duration,duration=duration,life=p.get('life_id',0),dimension=p.get('dimension',0),position={k:s[k]for k in('x','y','z')},slot=p['loadout']['selected'],version=p['loadout_version'])
    p['activity']=dict(kind='reload',until=now+duration)
    return dict(success=True,action_id=p['inventory_action']['id'],duration=duration,kind='reload',walking=True,label={'pack':'Şarjör dolduruluyor','load':'Hazır şarjör takılıyor','unpack':'Şarjör boşaltılıyor'}[op])
  if action=='use-finish':
   identifier=data.get('action_id')
   if not isinstance(identifier,str) or len(identifier)>64:raise ValueError('Geçersiz işlem kimliği.')
   with api.database()as db:done=db.execute('SELECT 1 FROM pn_magazine_receipts86 WHERE char_id=? AND action_id=?',(p['char_id'],identifier)).fetchone()
   if done:return dict(success=True,already_finished=True,loadout=info(p),notice='Şarjör işlemi zaten tamamlandı.')
   if task and task.get('magazine86'):
    if identifier!=task['id']:raise ValueError('İşlem kimliği eşleşmedi.')
    now=time.time();key=task['key'];op=task['magazine86']
    # free_actor checks other actions. This action is checked explicitly below.
    activity=p.pop('activity',None);pending=p.pop('inventory_action',None)
    try:check(p,s,key)
    except BaseException:raise
    else:p['inventory_action']=pending;p['activity']=activity
    if now>task['until']+10 or p.get('life_id',0)!=task['life'] or p.get('dimension',0)!=task['dimension'] or p['loadout_version']!=task['version'] or not w.near(s,task['position'],min(14,(now-task['started'])*3.1+1.5)) or abs(s['z']-task['position']['z'])>2.5:
     clear(p);raise ValueError('Şarjör işlemi iptal edildi; mermi harcanmadı.')
    if now<task['until']:raise ValueError('Şarjör işlemi henüz bitmedi.')
    possible(p,key,op);r=info(p);candidate=copy.deepcopy(p);load=candidate['loadout'];mags=load.setdefault('magazines86',{}).setdefault(key,[]);stock=load.setdefault('stock',{});capacity=inv.clip_capacity(key)
    if op=='pack':
     reserve=max(0,r['ammo']-r['clip']);rounds=min(capacity,reserve)
     if not rounds:
      stock['ammo_'+key]-=1;rounds=capacity
     else:load['owned'][key]-=rounds
     mags.append(rounds)
    elif op=='unpack':load['owned'][key]+=mags.pop()
    else:
     rounds=mags.pop(mags.index(max(mags)));load['owned'][key]+=rounds-r['clip'];load.setdefault('clips',{})[key]=rounds
     if r['clip']:mags.append(r['clip'])
    candidate['loadout_version']=p['loadout_version']+1
    with api.database()as db:
     if not db.in_transaction:db.execute('BEGIN IMMEDIATE')
     db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version',(p['char_id'],json.dumps(load),candidate['loadout_version']))
     db.execute('INSERT INTO pn_magazine_receipts86 VALUES(?,?,?)',(p['char_id'],identifier,now))
     db.execute('DELETE FROM pn_magazine_receipts86 WHERE char_id=? AND action_id NOT IN (SELECT action_id FROM pn_magazine_receipts86 WHERE char_id=? ORDER BY created DESC LIMIT 32)',(p['char_id'],p['char_id']))
     w.audit(db,uid,'magazine86',dict(char_id=p['char_id'],operation=op,weapon=key,rounds=rounds if op!='unpack' else None))
    p.update(loadout=load,loadout_version=candidate['loadout_version'],weapon_ready_at=now+1);clear(p)
    return dict(success=True,loadout=info(p),notice={'pack':'Hazır şarjör envanterine eklendi.','unpack':'Mermiler yedek haznene aktarıldı.','load':'Hazır şarjör takıldı; eski şarjör korundu.'}[op])
  if action in('equip','quick-use') and task and task.get('magazine86'):clear(p)
  return old(path,uid,token,data,p,s)
 def observe(p,data):
  task=p.get('inventory_action')
  if task and task.get('magazine86'):
   r=info(p)
   if data.get('weapon',r['weapon'])!=r['weapon'] or type(data.get('ammo'))is int and data['ammo']<r['ammo']:clear(p)
  return sample(p,data)
 inv.dispatch=dispatch;inv.view=info;inv.sample=observe;api.magazines86_installed=True
 return api
