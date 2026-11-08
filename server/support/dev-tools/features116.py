"""116 over the live v115 chain.

/fixveh: the stock repair raised repair_epoch and body but left the door/window bitmasks set, so
every client kept those doors open (and re-opened them on stream-in). Any vehicle whose
repair_epoch grows during a chat command now also gets doors=0 and windows=0 (persisted).
/admincommands: rows are grouped by area, show the minimum rank and a usage example."""
import time
RANK={1:'Moderatör+',2:'Yönetici+',3:'Baş yönetici+',4:'Kurucu'}
GROUPS=[('Oyuncu yönetimi',['/goto','/gethere','/revive','/sethp','/setarmor','/sethunger','/setthirst','/changename','/stats','/admins']),
 ('Ceza ve moderasyon',['/jail','/unjail','/ban','/unban','/a','/aduty','/hideadmin','/apanel']),
 ('Araçlar',['/veh','/getcar','/gotocar','/fixveh','/flipcar','/afuelveh']),
 ('Ekonomi ve VIP',['/givemoney','/setvip','/vipver','/ppver','/ppal','/donatearacver','/donatearaciptal']),
 ('Silah ve eşya',['/makeweapon','/makeammo','/silahid']),
 ('Dünya',['/settime','/setweather','/addint','/godmode','/fly']),
 ('Yetki',['/rankver'])]
EXAMPLES={'/goto':'/goto 12','/gethere':'/gethere 12','/revive':'/revive 12','/sethp':'/sethp 12 100','/setarmor':'/setarmor 12 100','/jail':'/jail 12 30 RDM','/ban':'/ban 12 1440 hile','/unban':'/unban kullaniciadi',
 '/givemoney':'/givemoney 12 5000','/fixveh':'/fixveh (bindiğin araç) · /fixveh 84','/getcar':'/getcar 84','/veh':'/veh sultan','/setvip':'/setvip 12 3 30','/rankver':'/rankver 12 2','/settime':'/settime 21 30','/setweather':'/setweather RAIN',
 '/afuelveh':'/afuelveh 12 1','/makeweapon':'/makeweapon pistol 12','/ppver':'/ppver 12 100','/a':'/a mesaj','/changename':'/changename 12 Ad Soyad'}
MIN={'/admins':1,'/stats':0,'/jail':1,'/unjail':1,'/a':1,'/apanel':1,'/rankver':4,'/setvip':4,'/vipver':4,'/ppver':4,'/ppal':4,'/donatearacver':4,'/donatearaciptal':4}
def install(api):
 if getattr(api,'features116_installed',False):return api
 w=api.world;previous=api.dispatch
 def details(rows):
  have={str(r[0]).split()[0]:r for r in rows if r}
  extra=[['/a mesaj','Yetkili sohbeti (yalnız yetkililer görür)'],['/apanel','Yetkili paneli · F9'],['/ppver ID miktar','PAV Puan ekle'],['/ppal ID miktar','PAV Puan düş']]
  for r in extra:have.setdefault(r[0].split()[0],r)
  out=[];used=set()
  for title,cmds in GROUPS:
   block=[(c,have[c])for c in cmds if c in have]
   if not block:continue
   out.append(['— '+title+' —',''])
   for c,(name,desc) in block:
    used.add(c);hint=RANK.get(MIN.get(c,2),'')
    out.append([name,desc+(' · '+hint if hint else'')+(' · Örn: '+EXAMPLES[c] if c in EXAMPLES else'')])
  rest=[r for c,r in have.items() if c not in used]
  if rest:out.append(['— Diğer —',''])
  out.extend(rest);return out
 def dispatch(path,v,token):
  if path!='/api/chat/send':return previous(path,v,token)
  head=str(v.get('message','')).strip().split(' ',1)[0].lower()
  if head=='/fixveh':
   with api.LOCK:
    before={vid:(f or{}).get('repair_epoch',0)for vid,f in list(w.VEHICLE_CACHE.items())}
    result,cookie=previous(path,v,token)
    if result.get('success'):
     for vid,f in list(w.VEHICLE_CACHE.items()):
      if f and f.get('repair_epoch',0)!=before.get(vid,f.get('repair_epoch',0)-1):
       f.update(doors=0,windows=0);w.persist_vehicle(vid)
    return result,cookie
  result,cookie=previous(path,v,token)
  if head=='/admincommands'and result.get('success')and isinstance(result.get('info'),dict):
   result=dict(result,info=dict(result['info'],title='Yetkili komutları · kategori, yetki ve örnek',rows=details(result['info'].get('rows')or[])))
  return result,cookie
 api.dispatch=dispatch;api.features116_installed=True;return api
