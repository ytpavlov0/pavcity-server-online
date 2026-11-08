"""188 backend: 187 + admin tools, interior rescue and the vehicle lifecycle (vehicles188.py).
- /getpos: position, heading, dimension, property (id, name, interior type) and vehicle, plus a copy-ready line.
- /asifredegis kullanıcıadı yeni_şifre (rank >= 3): sets a new password, ends every session of that account and
  takes its character out of the city. The password is never echoed, logged, audited or put into chat.
- /interiorids: the interior types with their numbers; /addint takes that number as well as the type name
  (/addint 2 250000 Ad, /addint garaj 2 250000 Ad). A brand-new interior needs its geometry package first.
- Interior rescue: a player whose dimension is a property but who is more than 60 m from that interior for 3 s
  (fell through an interior that did not load) is put at the property's door outside. /kurtar does it on request
  (rank >= 2 on duty: /kurtar ID for someone else).
- /gotoplace works for on-duty admins inside an interior too (the interior is left first).
- /pmkapat, /pmac (VIP or staff): with PM closed, a /pm to you is refused with "PM'si kapalı"; staff can still write
  (they are told it was closed). Stored per character in pn_pmoff188; an expired VIP receives messages again.
- Vehicle lifecycle, /park for key holders and from inside the car, coast188 samples: see vehicles188.py."""
from pathlib import Path
import sys,time,math,json,threading,contextlib
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v187 as previous
import vehicles188
host=previous.host;API=previous.API
STATS={'pm_refused':0,'getpos':0,'password_changes':0,'rescued_auto':0,'rescued_cmd':0,'gotoplace_inside':0}
FALL=60.0;FALL_FOR=3.0;GRACE=12.0
def install():
 api=previous.install()
 if getattr(api,'v188_installed',False):return api
 import importlib
 adm=importlib.import_module(api.__package__+'.pn_admin');city=importlib.import_module(api.__package__+'.pn_city');w=api.world
 vehicles188.install(api)
 FAR={}  # token -> first time seen far from its interior
 def prop(db,pid):return db.execute('SELECT id,name,kind,x,y,z,heading FROM pn_properties WHERE id=?',(pid,)).fetchone()
 def leave_interior(p,s,row,why):
  """Same end state as a finished exit: outside at the door, dimension 0, no pending transition or recovery row."""
  for k in('property45_used','property45_ready','elevator176_ready'):p.pop(k,None)
  door={'x':float(row['x']),'y':float(row['y']),'z':float(row['z'])+.2,'heading':float(row['heading'])}
  result=city.teleport(p,s,door,0)
  with w.database()as db:
   db.execute('DELETE FROM pn_property_recovery45 WHERE char_id=? AND user_id=?',(p['char_id'],p['user_id']))
   w.audit(db,p['user_id'],'interior-rescue188',dict(property=row['id'],reason=why))
  return result
 def check_fall(token,p,s):
  pid=p.get('dimension',0)
  if not pid or not s:FAR.pop(token,None);return
  item=p.get('property45_used')
  if item and item.get('phase')=='pending':FAR.pop(token,None);return
  if time.time()-p.get('respawned_at',0)<GRACE:FAR.pop(token,None);return
  with w.database()as db:row=prop(db,pid)
  if not row or row['kind']not in city.INTERIOR_TYPES:return
  t=city.INTERIOR_TYPES[row['kind']]
  try:d=math.dist((s['x'],s['y'],s['z']),(t['x'],t['y'],t['z']))
  except(KeyError,TypeError):return
  if not math.isfinite(d)or d<=FALL:FAR.pop(token,None);return
  # an elevator may lead somewhere else inside the same dimension: near one of its ends is fine too
  try:
   with w.database()as db:ends=[e for r in db.execute('SELECT a,b FROM pn_elevators176')for e in(r['a'],r['b'])]
  except Exception:ends=[]
  for e in ends:
   try:e=json.loads(e)
   except(TypeError,ValueError):continue
   if isinstance(e,dict)and e.get('dimension',0)==pid and all(isinstance(e.get(k),(int,float))for k in('x','y','z'))and math.dist((s['x'],s['y'],s['z']),(e['x'],e['y'],e['z']))<=FALL:
    FAR.pop(token,None);return
  first=FAR.setdefault(token,time.time())
  if time.time()-first<FALL_FOR:return
  FAR.pop(token,None);leave_interior(p,s,row,'fell');STATS['rescued_auto']+=1
 with w.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_pmoff188(char_id INTEGER PRIMARY KEY,since REAL NOT NULL)')
  PMOFF={r[0]for r in db.execute('SELECT char_id FROM pn_pmoff188')}
 def vip(uid):
  try:
   with w.database()as db:r=db.execute('SELECT vip,vip_until FROM pn_profiles WHERE user_id=?',(uid,)).fetchone()
   return bool(r and r['vip']and(not r['vip_until']or r['vip_until']>time.time()))
  except Exception:return False
 def pm_closed(peer):
  """Closed only while the receiver may close it (VIP or staff); an expired VIP gets messages again."""
  return peer.get('char_id')in PMOFF and(vip(peer['user_id'])or rank(peer)>=1)
 def rank(p):
  try:return adm.rank(p['user_id'])
  except Exception:return 0
 def info(title,rows,notice=None):return dict(success=True,notice=notice or title,info=dict(title=title,rows=rows))
 def command(token,parts):
  head=parts[0].lower();p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
  if not p:raise ValueError('Oturum bulunamadı.')
  if head=='/getpos':
   if not s:raise ValueError('Konum henüz hazır değil; şehre girdikten sonra dene.')
   x,y,z,h=(float(s.get(k,0))for k in('x','y','z','heading'))
   rows=[['Konum','%.2f, %.2f, %.2f'%(x,y,z)],['Yön','%.1f°'%h],['Dimension',str(p.get('dimension',0))]]
   if p.get('dimension',0):
    with w.database()as db:row=prop(db,p['dimension'])
    rows.append(['Mülk',('#%d %s · %s'%(row['id'],row['name'],city.INTERIOR_TYPES.get(row['kind'],{}).get('name',row['kind'])))if row else'(mülk değil)'])
   vid,seat=w.occupation(p['char_id'])
   if vid:rows.append(['Araç','#%d · koltuk %d'%(vid,seat)])
   line='%.2f, %.2f, %.2f, %.1f'%(x,y,z,h);rows.append(['Kopyala',line])
   STATS['getpos']+=1
   return info('Konum bilgisi',rows,'Konum: '+line+(' · dim '+str(p.get('dimension'))if p.get('dimension')else''))
  if head in('/asifredegis','/aşifredeğiş','/asifredeğiş','/aşifredegis'):
   if rank(p)<3:raise ValueError('Bu komut için baş yönetici yetkisi gerekli.')
   if len(parts)!=3:raise ValueError('Kullanım: /asifredegis kullanıcıadı yeni_şifre (şifrede boşluk olmaz)')
   name,pw=parts[1],parts[2]
   if not 8<=len(pw)<=128:raise ValueError('Yeni şifre 8–128 karakter olmalı.')
   with w.database()as db:
    u=db.execute('SELECT id,username FROM users WHERE username=? COLLATE NOCASE',(name,)).fetchone()
    if not u:raise ValueError('Kullanıcı bulunamadı.')
    db.execute('UPDATE users SET password_hash=? WHERE id=?',(api.password_hash(pw),u['id']))
    db.execute('DELETE FROM pn_sessions WHERE user_id=?',(u['id'],))
    w.audit(db,p['user_id'],'password-change188',dict(user_id=u['id']))
   ended=0
   for t,sess in list(api.SESSIONS.items()):
    if isinstance(sess,dict)and sess.get('user_id')==u['id']:api.SESSIONS.pop(t,None);ended+=1
   for t,q in list(api.PRESENCE.items()):
    if q.get('user_id')==u['id']and t!=token:
     try:w.release(q['char_id'])
     except Exception:pass
     api.PRESENCE.pop(t,None);api.GTA_STATE.pop(t,None)
   STATS['password_changes']+=1
   return dict(success=True,notice='%s hesabının şifresi değiştirildi; %d açık oturum kapatıldı.'%(u['username'],ended)+(' Kendi oturumun da kapandı, yeniden giriş yap.'if u['id']==p['user_id']else''))
  if head in('/pmkapat','/pmac','/pmaç'):
   if not(vip(p['user_id'])or rank(p)>=1):raise ValueError('PM kapatma VIP oyunculara özeldir.')
   off=head=='/pmkapat'
   with w.database()as db:
    if off:db.execute('INSERT OR REPLACE INTO pn_pmoff188 VALUES(?,?)',(p['char_id'],time.time()))
    else:db.execute('DELETE FROM pn_pmoff188 WHERE char_id=?',(p['char_id'],))
   if off:PMOFF.add(p['char_id'])
   else:PMOFF.discard(p['char_id'])
   return dict(success=True,notice='Özel mesajların kapalı; sana PM gönderenlere "PM\'si kapalı" denecek. Açmak için /pmac'if off else'Özel mesajların açık.')
  if head=='/interiorids':
   if rank(p)<2:raise ValueError('Yönetici yetkisi gerekli.')
   keys=list(city.INTERIOR_TYPES)
   rows=[['#%d · %s'%(i+1,city.INTERIOR_TYPES[k]['name']),'%s · %.1f, %.1f, %.1f'%(k,city.INTERIOR_TYPES[k]['x'],city.INTERIOR_TYPES[k]['y'],city.INTERIOR_TYPES[k]['z'])]for i,k in enumerate(keys)]
   rows.append(['Kullanım','/addint ID fiyat ad · ör. /addint 2 250000 Vinewood Garajı (bulunduğun yerde kapı olur)'])
   rows.append(['Not','Yeni bir iç mekân tasarımı eklemek için önce o mekânın zemin/sahne paketi hazırlanmalı.'])
   return info('İç mekân numaraları',rows,'%d iç mekân türü var.'%len(keys))
  if head=='/kurtar':
   target=p;tok=token
   if len(parts)>1:
    if rank(p)<2 or not p.get('admin_duty'):raise ValueError('Başkasını kurtarmak için yönetici görevinde ol: /aduty')
    cid=w.resolve_player_id(parts[1],api.PRESENCE)
    tok=next((k for k,v in api.PRESENCE.items()if v.get('char_id')==cid),None)
    if not tok:raise ValueError('Oyuncu bulunamadı.')
    target=api.PRESENCE[tok]
   ts=api.GTA_STATE.get(tok)
   if not target.get('dimension',0)or not ts:raise ValueError('Bir mülkün içinde görünmüyor; kurtarma gerekmiyor.')
   last=target.get('rescue188_at',0)
   if tok==token and time.time()-last<30:raise ValueError('Biraz bekle (30 sn).')
   with w.database()as db:row=prop(db,target['dimension'])
   if not row:raise ValueError('Mülk bulunamadı.')
   result=leave_interior(target,ts,row,'command');target['rescue188_at']=time.time();STATS['rescued_cmd']+=1
   return dict(success=True,notice='%s mülkün kapısına çıkarıldı.'%(row['name']),**(result if tok==token else{}))
  return None
 old=api.dispatch
 def dispatch(path,*a,**k):
  payload=a[0]if a else k.get('payload',{});token=a[1]if len(a)>1 else k.get('token','')
  if path=='/api/gta/sync'and isinstance(payload,dict):
   # inside v187's gate (re-entrant): queueing on api.LOCK outside it brought the lock convoy back (60 players:
   # sync wait 0.16 s -> 1.6 s in the load test)
   owned=getattr(api.LOCK,'_is_owned',lambda:False)()
   with(previous.GATE if previous.GATE is not None and not owned else contextlib.nullcontext()):
    q=api.PRESENCE.get(token);c=payload.get('coast188')
    if q and(q.get('dimension',0)or token in FAR or isinstance(c,dict)):  # the lock only when there is work
     with api.LOCK:
      p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
      if p:
       try:check_fall(token,p,s)
       except Exception:pass
       if isinstance(c,dict):
        try:api.vehicles188_coast(p,s,c)
        except Exception:pass
    out=old(path,*a,**k)
    try:
     api.vehicles188_drivers()
     if api.vehicles188_due():
      with api.LOCK:api.vehicles188_tick()
    except Exception:pass
   return out
  if path=='/api/chat/send'and isinstance(payload,dict)and isinstance(payload.get('message'),str):
   parts=payload['message'].strip().split();head=parts[0].lower()if parts else''
   if head in('/getpos','/asifredegis','/aşifredeğiş','/asifredeğiş','/aşifredegis','/interiorids','/kurtar','/pmkapat','/pmac','/pmaç'):
    with api.LOCK:return command(token,parts),None
   if head=='/pm'and len(parts)>=3 and PMOFF:
    with api.LOCK:
     me=api.PRESENCE.get(token)
     try:cid=w.resolve_player_id(parts[1],api.PRESENCE)
     except Exception:cid=None
     peer=next((q for q in api.PRESENCE.values()if q.get('char_id')==cid),None)if cid else None
     if me and peer and peer is not me and pm_closed(peer):
      if rank(me)<1:STATS['pm_refused']+=1;raise ValueError('%s adlı oyuncunun PM\'si kapalı.'%peer.get('name','Oyuncu'))
      out=old(path,*a,**k)
      if isinstance(out[0],dict)and out[0].get('success'):out=(dict(out[0],notice=str(out[0].get('notice',''))+' (PM\'si kapalı; yetkili olarak iletildi.)'),)+tuple(out[1:])
      return out
   if head=='/park':
    with api.LOCK:
     p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token);uid=p and p.get('user_id')
     if not(p and s):raise ValueError('Oturum bulunamadı.')
     if len(parts)>2:raise ValueError('Kullanım: /park [araç ID]')
     return api.vehicles188_park(uid,p,s,parts[1:]),None
   if head=='/addint'and len(parts)>=4:
    keys=list(city.INTERIOR_TYPES)
    names={'ev':'apartment','daire':'apartment','apartman':'apartment','apartment':'apartment','ofis':'office','office':'office','garaj':'garage','garage':'garage'}
    pick=None;rest=None
    if parts[1].isdigit()and len(parts[1])<=2:pick=int(parts[1]);rest=parts[2:]
    elif len(parts)>=5 and parts[2].isdigit()and len(parts[2])<=2:
     pick=int(parts[2]);rest=parts[3:]
     base=names.get(parts[1].lower(),parts[1].lower())
     if 1<=pick<=len(keys)and keys[pick-1]!=base and base in keys:raise ValueError('#%d bir %s; tür ile numara uyuşmuyor. /interiorids'%(pick,city.INTERIOR_TYPES[keys[pick-1]]['name']))
    if pick is not None:
     if not 1<=pick<=len(keys):raise ValueError('Geçersiz iç mekân numarası. /interiorids ile listele.')
     payload=dict(payload,message=' '.join(['/addint',keys[pick-1],*rest]));a=(payload,)+tuple(a[1:])
   if head=='/gotoplace'and len(parts)==2:
    with api.LOCK:
     p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
     if p and s and p.get('dimension',0)and rank(p)>=2 and p.get('admin_duty'):
      with w.database()as db:
       place=db.execute('SELECT 1 FROM pn_places70 WHERE id=?',(parts[1],)).fetchone()if parts[1].isdigit()else None
       row=prop(db,p['dimension'])
      if place and row:leave_interior(p,s,row,'gotoplace');STATS['gotoplace_inside']+=1
  return old(path,*a,**k)
 api.dispatch=dispatch;api.v188_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v188.json':
   return self.json51(200,dict(backend_release='v188',base_release='v187',v188=STATS,vehicles188=vehicles188.STATS,v187=previous.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v188.db'):p.error('Disposable -v188.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes188.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous
 for _ in range(25):pp=pp.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
