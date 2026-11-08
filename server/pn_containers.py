"""Persistent, atomic personal/ground/trunk/glovebox transfers. No client prices."""
import json,time,secrets,hashlib
import pn_world as world,pn_inventory as inv,pn_roleplay as rp
def schema(db):
 db.execute('CREATE TABLE IF NOT EXISTS pn_container_items(location TEXT NOT NULL,item TEXT NOT NULL,qty INTEGER NOT NULL CHECK(qty>0),ammo INTEGER NOT NULL DEFAULT 0,tint INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(location,item))')
 db.execute('CREATE TABLE IF NOT EXISTS pn_ground(id TEXT PRIMARY KEY,x REAL NOT NULL,y REAL NOT NULL,z REAL NOT NULL,dimension INTEGER NOT NULL,owner INTEGER NOT NULL,created REAL NOT NULL)')
 db.execute('CREATE INDEX IF NOT EXISTS pn_ground_xy ON pn_ground(dimension,x,y)')
def catalog():
 r={k:dict(key=k,id=v['id'],name=v['name'],kg=v.get('kg',2),color='#efa966',image='/pn/assets-v19/weapons/'+k+'.png',weapon=True) for k,v in inv.WEAPONS.items()}
 for key,id,name,kg,color in [('food',202,'Sandviç',.3,'#d3a273'),('water',201,'Su',.5,'#7fc6de'),('armor',301,'Çelik yelek',4,'#c6ccd0')]:r[key]=dict(key=key,id=id,name=name,kg=kg,color=color,image='/pn/assets-v19/items/'+key+'.png',weapon=False)
 for key,v in inv.WEAPONS.items():
  if v.get('category')!='NULL':r['ammo_'+key]=dict(key='ammo_'+key,id=400+v['slot'],name=v['name']+' mermisi',kg=.3,color='#d4d082',image='/pn/assets-v19/items/ammo.png',weapon=False)
 from pn_economy import PRODUCTS
 for k,v in PRODUCTS.items():r[k]=dict(key=k,id=v['id'],name=v['name'],kg=v['kg'],color=v['color'],image='/pn/assets-v22/items/'+v['icon']+'.png',weapon=False,kind=v['kind'])
 for k,v in r.items():
  if k in inv.WEAPONS:
   cat=inv.WEAPONS[k].get('category','');v['color']='#ad80ed' if 'PISTOL' in cat or k=='pistol' else '#eaac6a' if any(x in cat for x in ('RIFLE','SNIPER')) else '#6fa9e8';v['rarity']='Üst sınıf' if inv.WEAPONS[k]['price']>=100000 else 'Özel'
   v['image']='/pn/assets-v19/weapons/'+k+'.png'
  if k in ('water','food'):v['image']='/pn/assets-v22/items/'+('7' if k=='water' else '167')+'.png'
  if k=='armor':v['image']='/pn/assets-v22/items/88.png'
  if k.startswith('ammo_'):v['image']='/pn/assets-v22/items/53.png'
  if k=='grape':v['image']='/pn/assets-v22/grapes.svg'
 return r
def personal(p):
 state=inv.load(p);rows=[]
 for k,n in state['owned'].items():
  if k in inv.WEAPONS:rows.append(dict(item=k,qty=1,ammo=n,tint=state.get('tints',{}).get(k,0)))
 for k,n in state.get('stock',{}).items():
  if n>0:rows.append(dict(item=k,qty=n,ammo=0,tint=0))
 for k in ('water','food'):
  if p.get(k,3)>0:rows.append(dict(item=k,qty=p.get(k,3),ammo=0,tint=0))
 return rows
def weight(rows):
 c=catalog();return sum(c[r.get('item',r.get('key'))]['kg']*r['qty'] for r in rows if r.get('item',r.get('key')) in c)

def nearby_players(p,state,presences,states):
 now=time.time();rows=[]
 if world.occupation(p['char_id'])[0]:return rows
 for peer in presences.values():
  if peer['char_id']==p['char_id'] or peer.get('world')!='gta' or peer.get('health',0)<=100 or now-peer['last_seen']>=10 or world.occupation(peer['char_id'])[0] or peer.get('dimension',0)!=p.get('dimension',0):continue
  sample=next((s for s in states.values() if s['char_id']==peer['char_id']),None)
  if sample and world.near(state,sample,3):rows.append(dict(server_id=peer['server_id'],name=peer['name'],distance=sum((state[k]-sample[k])**2 for k in ('x','y','z'))**.5))
 return sorted(rows,key=lambda v:v['distance'])[:8]

def auto_context(p,state,presences,states):
 vid,seat=world.occupation(p['char_id'])
 if vid:return ('glove:' if seat in (-1,0) else 'trunk:')+str(vid)
 peers=nearby_players(p,state,presences,states)
 if peers:return 'player:'+str(peers[0]['server_id'])
 candidates=[]
 for row in world.rows(state):
  if not row['active']:continue
  v=world.public(row)
  if not world.near(state,v,3):continue
  try:access('trunk:'+str(row['id']),p,state,presences)
  except ValueError:continue
  candidates.append((sum((v[k]-state[k])**2 for k in ('x','y','z')),row['id']))
 return 'trunk:'+str(min(candidates)[1]) if candidates else 'ground'
def access(context,p,state,presences,source=False):
 if context=='self':return p,1000 if world.admin(p['user_id']) else 30
 if context=='ground':return None,1000
 kind,sep,id=str(context).partition(':')
 if not sep:raise ValueError('Geçersiz envanter alanı.')
 if kind in ('trunk','glove'):
  vid=rp.integer(int(id));row=world.vehicle(vid);v=world.public(row)
  if p.get('dimension',0) or not row['active']:raise ValueError('Araç dış dünyada olmalı.')
  occupied,seat=world.occupation(p['char_id'])
  if kind=='glove':
   if occupied!=vid or seat not in (-1,0):raise ValueError('Torpido için ön koltukta oturmalısın.')
  else:
   if occupied==vid and seat>=1:return None,80
   if occupied or not world.near(state,v,5):raise ValueError('Bagaja yaya olarak yaklaş veya arka koltuğa otur.')
   with world.database() as db:
    key=row['owner']==p['char_id'] or bool(db.execute('SELECT 1 FROM pn_vehicle_access WHERE vehicle_id=? AND char_id=?',(vid,p['char_id'])).fetchone())
   if row['locked']:raise ValueError('Bagaj kilitli; önce araç kilidini aç.')
   key=key or rp.vehicle_access(vid,p['char_id']) or __import__('pn_traffic').has_key(vid,p['char_id'])
   if not v.get('doors',0)&32 and not key:raise ValueError('Bagaj kapağını anahtar sahibi açmalı.')
  return None,80 if kind=='trunk' else 5
 if kind=='drop':
  with world.database() as db:r=db.execute('SELECT * FROM pn_ground WHERE id=?',(id,)).fetchone()
  if not r or r['dimension']!=p.get('dimension',0) or not world.near(state,r,3):raise ValueError('Yerdeki eşyaya yaklaş (3 m).')
  return None,1000
 if kind=='player':
  cid=world.resolve_player_id(int(id),presences);peer=next(v for v in presences.values() if v['char_id']==cid)
  ps=next((s for s in __import__('session_api').GTA_STATE.values() if s['char_id']==cid),None)
  if source or not ps or peer.get('health',0)<=100 or peer.get('dimension',0)!=p.get('dimension',0) or not world.near(state,ps,3) or world.occupation(cid)[0]:raise ValueError('Eşya vereceğin oyuncu yakında ve yaya olmalı.')
  if cid==p['char_id']:raise ValueError('Kendine eşya aktaramazsın.')
  if world.occupation(p['char_id'])[0]:raise ValueError('Eşya vermek için araçtan in.')
  return peer,1000 if world.admin(peer['user_id']) else 30
 raise ValueError('Geçersiz envanter alanı.')
def read(db,context,peer=None):return personal(peer) if peer else [dict(r) for r in db.execute('SELECT item,qty,ammo,tint FROM pn_container_items WHERE location=?',(context,))]
def augmented(rows,context):
 c=catalog();return [dict(**c[r['item']],**{k:v for k,v in r.items() if k!='item'},context=context) for r in rows if r['item'] in c]
def save_personal(db,peer,state,rows):
 import pn_multiplayer as mp
 old=inv.load(peer);updated=json.loads(json.dumps(old));updated['owned']={};updated['stock']={};updated['tints']={};needs={'food':0,'water':0}
 for r in rows:
  k=r['item']
  if k in inv.WEAPONS:updated['owned'][k]=r['ammo'];updated['tints'][k]=r['tint']
  elif k in needs:needs[k]=r['qty']
  else:updated['stock'][k]=r['qty']
 selected=next((k for k,v in inv.WEAPONS.items() if v['slot']==updated['selected']),None)
 updated['clips']={k:min(int(n),inv.clip_capacity(k),updated['owned'][k]) for k,n in updated.get('clips',{}).items() if k in updated['owned']}
 if selected and selected not in updated['owned']:updated['selected']=0
 version=peer.get('loadout_version',1)+1
 db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version',(peer['char_id'],json.dumps(updated),version))
 copy=dict(peer,**needs);mp.save(copy,state,True,db)
 return dict(loadout=updated,loadout_version=version,**needs,saved_at=copy['saved_at'],weapon_ready_at=time.time()+1)
def dispatch(path,uid,token,v,p,state,presences,states):
 import pn_multiplayer as mp
 world.live(p,state);action=path.rsplit('/',1)[-1];c=catalog()
 if action=='list':
  context=v.get('context','ground')
  if context=='auto':context=auto_context(p,state,presences,states)
  peer,limit=access(context,p,state,presences)
  with world.database() as db:
   own=personal(p)
   if context=='ground':
    drops=db.execute('SELECT * FROM pn_ground WHERE dimension=? AND x BETWEEN ? AND ? AND y BETWEEN ? AND ? ORDER BY created DESC LIMIT 32',(p.get('dimension',0),state['x']-3,state['x']+3,state['y']-3,state['y']+3)).fetchall()
    rows=[]
    for d in drops:
     if world.near(state,d,3):rows.extend(augmented(read(db,'drop:'+d['id']),'drop:'+d['id']))
   else:rows=augmented(read(db,context),context)
   keys=[dict(id=r['id'],name=r['name'],item_id=700000+r['id'],type='property-key',image='/pn/assets-v19/items/keys.png') for r in db.execute('SELECT id,name FROM pn_properties WHERE owner=? OR id IN (SELECT property_id FROM pn_property_keys WHERE char_id=?)',(p['char_id'],p['char_id']))]
  nearby=nearby_players(p,state,presences,states)
  recipient=dict(server_id=peer['server_id'],name=peer['name']) if context.startswith('player:') else None
  label=('Ön koltuk · Torpido' if context.startswith('glove:') else 'Arka koltuk · Bagaj' if context.startswith('trunk:') and world.occupation(p['char_id'])[0] else 'Araç bagajı' if context.startswith('trunk:') else 'Oyuncuya ver · '+recipient['name'] if recipient else 'Çevre envanteri')
  return dict(success=True,personal=augmented(own,'self'),items=rows,context=context,context_label=label,recipient=recipient,weight=weight(own),capacity=1000 if world.admin(uid) else 30,container_weight=weight(rows),container_capacity=limit,nearby_players=nearby,keys=keys,loadout=inv.view(p),money=world.wallet(uid))
 if action=='tint':
  key=v.get('item');tint=rp.integer(v.get('tint'),0,7);updated=json.loads(json.dumps(inv.load(p)))
  if key not in updated['owned']:raise ValueError('Bu silaha sahip değilsin.')
  updated.setdefault('tints',{})[key]=tint;version=p.get('loadout_version',1)+1
  with world.database() as db:db.execute('UPDATE pn_loadout SET state=?,version=? WHERE char_id=?',(json.dumps(updated),version,p['char_id']))
  p['loadout']=updated;p['loadout_version']=version
  return dict(success=True,loadout=inv.view(p),notice='Silah rengi kaydedildi.')
 if action!='transfer':raise ValueError('Envanter işlemi bulunamadı.')
 request=v.get('request_id');item=v.get('item');count=rp.integer(v.get('qty',1),1,20);source=v.get('source');target=v.get('target')
 if not isinstance(request,str) or not 16<=len(request)<=80 or item not in c:raise ValueError('Geçersiz aktarım.')
 digest=hashlib.sha256(json.dumps([source,target,item,count],sort_keys=True).encode()).hexdigest()
 with world.database() as db:
  old=db.execute('SELECT digest,result FROM pn_rp_receipts WHERE user_id=? AND key=?',(uid,request)).fetchone()
  if old:
   if old['digest']!=digest:raise ValueError('İşlem kimliği başka aktarımda kullanılmış.')
   return json.loads(old['result'])
 if source==target or source!='self' and target!='self':raise ValueError('Aktarım kişisel çantanla yapılmalı.')
 if p.get('inventory_action') and p['inventory_action']['until']>time.time():raise ValueError('Kullanım işleminin bitmesini bekle.')
 src,src_limit=access(source,p,state,presences,True);dst,limit=access(target,p,state,presences)
 if dst and dst.get('inventory_action') and dst['inventory_action']['until']>time.time():raise ValueError('Alıcının kullanım işlemi sürüyor.')
 mp.rate(token,'storage-transfer',.15);updates=[]
 with world.database() as db:
  src_rows=read(db,source,src);dst_rows=read(db,target,dst);row=next((r for r in src_rows if r['item']==item),None)
  if not row or row['qty']<count:raise ValueError('Bu kadar eşya yok.')
  existing=next((r for r in dst_rows if r['item']==item),None)
  if c[item]['weapon'] and (count!=1 or existing):raise ValueError('Aynı silah bu alanda zaten var.')
  if existing:existing['qty']+=count
  else:dst_rows.append(dict(row,qty=count))
  if weight(dst_rows)>limit or dst and any(r['qty']>20 for r in dst_rows if not c[r['item']]['weapon']):raise ValueError('Envanter ağırlık veya adet sınırı doldu.')
  row['qty']-=count;src_rows=[r for r in src_rows if r['qty']>0]
  location=target
  if target=='ground':
   id=secrets.token_hex(12);location='drop:'+id;db.execute('INSERT INTO pn_ground VALUES(?,?,?,?,?,?,?)',(id,state['x'],state['y'],state['z'],p.get('dimension',0),p['char_id'],time.time()))
  for context,peer,rows in [(source,src,src_rows),(location,dst,dst_rows)]:
   if peer:
    ps=state if peer['char_id']==p['char_id'] else next(s for s in states.values() if s['char_id']==peer['char_id'])
    updates.append((peer,save_personal(db,peer,ps,rows)))
   else:
    db.execute('DELETE FROM pn_container_items WHERE location=?',(context,))
    db.executemany('INSERT INTO pn_container_items VALUES(?,?,?,?,?)',[(context,r['item'],r['qty'],r['ammo'],r['tint']) for r in rows])
    if context.startswith('drop:') and not rows:db.execute('DELETE FROM pn_ground WHERE id=?',(context[5:],))
  result=dict(success=True,notice=c[item]['name']+' aktarıldı.')
  db.execute('INSERT INTO pn_rp_receipts VALUES(?,?,?,?,?)',(uid,request,digest,json.dumps(result),time.time()));world.audit(db,uid,'item-transfer',dict(source=source,target=location,item=item,qty=count))
 for peer,changed in updates:peer.update(changed)
 mp.emote(p,state,c[item]['name']+' '+('yere bıraktı.' if target=='ground' else 'aktardı.'))
 return result
