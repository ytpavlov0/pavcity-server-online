"""V20 character country, staff inventory grants and synchronized environment."""
import json,secrets,time
from pathlib import Path
import online_engine,pn_world as world,pn_admin as staff,pn_inventory as inventory
COUNTRIES=json.loads((Path(online_engine.__file__).parent/'support/countries-v20.json').read_text(encoding='utf8'))
WEATHER=('EXTRASUNNY','CLEAR','CLOUDS','SMOG','FOGGY','OVERCAST','RAIN','THUNDER','CLEARING','NEUTRAL','SNOW','BLIZZARD','SNOWLIGHT','XMAS')
def schema(db):
 db.execute('CREATE TABLE IF NOT EXISTS pn_character_country(char_id INTEGER PRIMARY KEY,code TEXT NOT NULL)')
 db.execute("CREATE TABLE IF NOT EXISTS pn_environment(singleton INTEGER PRIMARY KEY CHECK(singleton=1),hour INTEGER NOT NULL,minute INTEGER NOT NULL,weather TEXT NOT NULL,changed REAL NOT NULL)")
 db.execute('INSERT OR IGNORE INTO pn_environment VALUES(1,12,0,?,?)',('EXTRASUNNY',time.time()))
def country(cid,code=None):
 with world.database() as db:
  if code is not None:
   if code not in COUNTRIES:raise ValueError('Geçersiz ülke kodu.')
   db.execute('INSERT INTO pn_character_country VALUES(?,?) ON CONFLICT(char_id) DO UPDATE SET code=excluded.code',(cid,code))
  row=db.execute('SELECT code FROM pn_character_country WHERE char_id=?',(cid,)).fetchone()
  if not row:
   legacy=db.execute('SELECT p.country FROM pn_profiles p JOIN characters c ON c.user_id=p.user_id WHERE c.id=?',(cid,)).fetchone()
   code=legacy['country'] if legacy and legacy['country'] in COUNTRIES and legacy['country']!='other' else secrets.choice([c for c in COUNTRIES if c!='other'])
   db.execute('INSERT INTO pn_character_country VALUES(?,?)',(cid,code));return code
  return row['code']
def environment():
 with world.database() as db:r=dict(db.execute('SELECT * FROM pn_environment WHERE singleton=1').fetchone())
 seconds=int(r['hour']*3600+r['minute']*60+(time.time()-r['changed'])*30)%86400
 return dict(hour=seconds//3600,minute=seconds//60%60,second=seconds%60,weather=r['weather'])
def command(cmd,args,uid,p,state,presences):
 if cmd=='/donate':
  if args:raise ValueError('Kullanım: /donate')
  return dict(success=True,open_donate=True,notice='Donate araç teslimatların açılıyor.')
 if cmd in ('/donatearacver','/donatearaciptal'):
  if staff.rank(uid)!=4:raise ValueError('Donate araç atamasını yalnızca sunucu kurucusu yapabilir.')
  with world.database() as db:
   if cmd=='/donatearacver':
    if len(args)!=2:raise ValueError('Kullanım: /donatearacver OYUNCU_ID MODEL · Modeller: '+', '.join(world.DONATE_MODELS))
    cid=world.resolve_player_id(args[0],presences);peer=next(v for v in presences.values() if v['char_id']==cid);model=args[1].lower()
    if model not in world.DONATE_MODELS:raise ValueError('Teslim edilebilir modeller: '+', '.join(world.DONATE_MODELS))
    from pn_multiplayer import rate
    rate('donate:'+str(uid),'donate-grant',2)
    count=db.execute('SELECT COUNT(*) FROM pn_donate_vehicles WHERE user_id=? AND vehicle_id IS NULL AND revoked_at IS NULL',(peer['user_id'],)).fetchone()[0]
    if count>=20:raise ValueError('Bu hesabın 20 bekleyen teslimatı var.')
    grant=db.execute('INSERT INTO pn_donate_vehicles(user_id,model,granted_by,created) VALUES(?,?,?,?)',(peer['user_id'],model,uid,time.time())).lastrowid
    world.audit(db,uid,'donate-grant',dict(grant=grant,target_user=peer['user_id'],model=model))
    return dict(success=True,grant_id=grant,notice=peer['name']+' · '+world.DONATE_MODELS[model]['name']+' tanımlandı (#'+str(grant)+'). Oyuncu /donate ile garajına alabilir.')
   if len(args)!=1:raise ValueError('Kullanım: /donatearaciptal TESLİMAT_ID')
   grant=staff.number(args[0],1,2147483647)
   changed=db.execute('UPDATE pn_donate_vehicles SET revoked_at=? WHERE id=? AND vehicle_id IS NULL AND revoked_at IS NULL',(time.time(),grant)).rowcount
   if not changed:raise ValueError('Bekleyen teslimat bulunamadı. Teslim edilmiş araç bu komutla silinmez.')
   world.audit(db,uid,'donate-revoke',dict(grant=grant))
   return dict(success=True,notice='Bekleyen donate teslimatı iptal edildi (#'+str(grant)+').')
 if cmd in ('/meslekayril','/meslekayrıl','/meslekayiril','/meslekiptal','/meslekdurum'):
  if args:raise ValueError('Kullanım: '+cmd)
  import pn_roleplay
  with world.database() as db:
   if cmd=='/meslekdurum':
    active=pn_roleplay.job_action(db,'status',uid,p['char_id'],{},state,p)['active']
    return dict(success=True,active_job=active,notice=(active['name']+' · '+active['step_title']+' · '+active['instruction']) if active else 'Aktif mesleğin yok. /meslek ile meslek merkezini aç.')
   if not db.execute('SELECT 1 FROM pn_job_runs WHERE char_id=? AND completed IS NULL',(p['char_id'],)).fetchone():return dict(success=True,active_job=None,notice='Aktif mesleğin yok. /meslek ile yeni işe başlayabilirsin.')
   result=pn_roleplay.job_action(db,'cancel',uid,p['char_id'],{},state,p)
   world.audit(db,uid,'job-cancel-command',dict(char_id=p['char_id']))
  return dict(success=True,active_job=result['active'],notice=result['notice'])
 if cmd=='/afuelveh':
  if staff.rank(uid)<2:raise ValueError('Yönetici yetkisi gerekli.')
  if len(args)!=2:raise ValueError('Kullanım: /afuelveh OYUNCU_ID MİKTAR (0–100 veya 0–1 oran)')
  cid=world.resolve_player_id(args[0],presences);vid,seat=world.occupation(cid)
  if not vid:raise ValueError('Oyuncu bir araçta oturmuyor.')
  try:value=float(args[1])
  except (ValueError,TypeError):raise ValueError('Geçerli yakıt miktarı yaz.')
  if not __import__('math').isfinite(value) or not 0<=value<=100:raise ValueError('Yakıt 0–100 veya 0–1 oran olmalı.')
  amount=value*100 if value<=1 else value
  row=world.vehicle(vid);world.public(row);fields=dict(world.VEHICLE_CACHE.get(vid,json.loads(row['state'])));fields['fuel']=amount;fields['fuel_at']=time.time()
  if not amount:fields['engine']=False
  world.VEHICLE_CACHE[vid]=fields;world.persist_vehicle(vid)
  with world.database() as db:world.audit(db,uid,cmd,dict(target=cid,vehicle=vid,fuel=amount))
  return dict(success=True,notice='Oyuncunun araç yakıtı %'+str(round(amount))+' olarak ayarlandı.')
 if cmd=='/ulkesec':
  if not args:return dict(success=True,open_country=True,notice='Ülke seçim paneli açılıyor.')
  if len(args)!=1:raise ValueError('Kullanım: /ulkesec ülke_kodu')
  code=country(p['char_id'],args[0].lower())
  return dict(success=True,notice='Ülken: '+COUNTRIES[code])
 if cmd in ('/settime','/setweather'):
  if staff.rank(uid)<2:raise ValueError('Yönetici yetkisi gerekli.')
  with world.database() as db:
   if cmd=='/settime':
    if not 1<=len(args)<=2:raise ValueError('Kullanım: /settime saat [dakika]')
    hour=staff.number(args[0],0,23);minute=staff.number(args[1],0,59) if len(args)==2 else 0
    db.execute('UPDATE pn_environment SET hour=?,minute=?,changed=? WHERE singleton=1',(hour,minute,time.time()))
   else:
    if len(args)!=1 or args[0].upper() not in WEATHER:raise ValueError('Hava türleri: '+', '.join(WEATHER))
    now=environment();db.execute('UPDATE pn_environment SET hour=?,minute=?,weather=?,changed=? WHERE singleton=1',(now['hour'],now['minute'],args[0].upper(),time.time()))
   world.audit(db,uid,cmd,dict(args=args))
  return dict(success=True,notice='Şehir '+('saati' if cmd=='/settime' else 'havası')+' güncellendi.')
 if cmd not in ('/makeweapon','/makeammo','/silahid'):return None
 if staff.rank(uid)<2:raise ValueError('Silah üretme yöneticiye açık.')
 if cmd=='/silahid':return dict(success=True,info=dict(title='Silah ID kataloğu',rows=[[v['id'],v['name']] for v in inventory.WEAPONS.values()]))
 if not args or len(args)>(2 if cmd=='/makeweapon' else 3):raise ValueError('Kullanım: '+cmd+' SILAH_ID'+(' [OYUNCU_ID]' if cmd=='/makeweapon' else ' [PAKET_ADEDİ] [OYUNCU_ID]'))
 id=staff.number(args[0],1,2**32-1);key=next((k for k,v in inventory.WEAPONS.items() if v['id']==id or v['hash']==id),None)
 if not key:raise ValueError('Silah ID bulunamadı; /silahid ile listeyi aç.')
 target=args[1] if cmd=='/makeweapon' and len(args)>1 else args[2] if cmd=='/makeammo' and len(args)>2 else None
 cid=world.resolve_player_id(target,presences) if target else p['char_id'];peer=next(v for v in presences.values() if v['char_id']==cid)
 if staff.rank(peer['user_id'])>staff.rank(uid):raise ValueError('Üst yetkiliye işlem yapamazsın.')
 updated=json.loads(json.dumps(inventory.load(peer)))
 if cmd=='/makeweapon':
  if key in updated['owned']:raise ValueError('Bu silah zaten envanterde.')
  updated['owned'][key]=0;updated['selected']=inventory.WEAPONS[key]['slot']
 else:
  if inventory.WEAPONS[key].get('category')=='NULL':raise ValueError('Bu eşyaya mermi paketi takılmaz.')
  count=staff.number(args[1],1,20) if len(args)>1 else 1;stock=updated.setdefault('stock',{});item='ammo_'+key
  if stock.get(item,0)+count>20:raise ValueError('Mermi paketi sınırı 20.')
  stock[item]=stock.get(item,0)+count
 version=peer.get('loadout_version',1)+1
 with world.database() as db:
  db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version',(cid,json.dumps(updated),version));world.audit(db,uid,cmd,dict(target=cid,weapon=key,args=args))
 peer['loadout']=updated;peer['loadout_version']=version;peer['weapon_ready_at']=time.time()+1
 return dict(success=True,notice=inventory.WEAPONS[key]['name']+(' envantere üretildi.' if cmd=='/makeweapon' else ' mermi paketi envantere üretildi.'),loadout=inventory.view(peer) if cid==p['char_id'] else None)
