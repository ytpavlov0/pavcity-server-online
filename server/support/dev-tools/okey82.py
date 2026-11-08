"""The supplied PAV Okey rules, adapted to authenticated web multiplayer.

Four real players; no public bot/test endpoint. The database owns deck, private
hands, turn, deadlines and score. Replies contain only the requesting hand.
"""
import itertools,json,re,secrets,time
from functools import lru_cache
clock=time.time

def face(uid,indicator):
 if uid>=104:return indicator
 return uid//26,(uid%26)//2+1

def winning(hand,indicator):
 if len(hand)!=14 or len(set(hand))!=14 or any(type(x)is not int or not 0<=x<106 for x in hand):return None
 return winning_cached(tuple(sorted(hand)),tuple(indicator))

@lru_cache(maxsize=1024)
def winning_cached(hand,indicator):
 counts=[0]*52;jokers=0;okey=(indicator[0],indicator[1]%13+1)
 for uid in hand:
  c,n=face(uid,indicator)
  if uid<104 and(c,n)==okey:jokers+=1
  else:counts[c*13+n-1]+=1
 odd=sum(v%2 for v in counts)
 if jokers>=odd and(jokers-odd)%2==0:return 'pairs'
 @lru_cache(maxsize=8192)
 def solve(values,j):
  first=next((i for i,n in enumerate(values)if n),None)
  if first is None:return j==0
  c,n=divmod(first,13);n+=1;a=list(values);a[first]-=1
  others=[color*13+n-1 for color in range(4)if color!=c and a[color*13+n-1]]
  for size in range(len(others)+1):
   for selected in itertools.combinations(others,size):
    for target in (3,4):
     need=target-1-size
     if not 0<=need<=j:continue
     b=a.copy()
     for i in selected:b[i]-=1
     if solve(tuple(b),j-need):return True
  runs=[list(range(start,end+1))for start in range(1,min(n,11)+1)for end in range(max(start+2,n),14)if start<=n<=end]
  if n in(1,12,13):runs.append([12,13,1])
  for run in runs:
   b=a.copy();need=0
   for number in run:
    if number==n:continue
    i=c*13+number-1
    if b[i]:b[i]-=1
    else:need+=1
   if need<=j and solve(tuple(b),j-need):return True
  return False
 return 'standard'if solve(tuple(counts),jokers)else None

def fresh():return dict(phase='lobby',seats=[None]*4,host=0,mode='free',scores=[0]*4,team_scores=[0,0],hands={},deck=[],discard=[],indicator=None,turn=0,step=None,deadline=0,version=1,message='Dört gerçek oyuncu oturup hazır olmalı.',match_done=False)

def deal(t,now):
 deck=list(range(106));secrets.SystemRandom().shuffle(deck);index=next(i for i in range(len(deck)-1,-1,-1)if deck[i]<104);indicator=deck.pop(index)
 while True:
  dice=[secrets.randbelow(6)+1 for _ in range(4)];high=max(dice)
  if dice.count(high)==1:break
 dealer=dice.index(high);hands={str(s['cid']):[]for s in t['seats']}
 for _ in range(14):
  for s in t['seats']:hands[str(s['cid'])].append(deck.pop())
 hands[str(t['seats'][dealer]['cid'])].append(deck.pop())
 if t.get('match_done'):t['scores']=[0]*4;t['team_scores']=[0,0];t['match_done']=False
 t.update(phase='dealing',round=t.get('round',0)+1,hands=hands,deck=deck,discard=[],indicator=indicator,turn=dealer,step='discard',deadline=now+5.2,dice=dice,message='Taşlar dağıtılıyor…')

def reset_round(t,message):
 t.update(phase='lobby',hands={},deck=[],discard=[],indicator=None,step=None,deadline=0,message=message)
 for s in t['seats']:
  if s:s['ready']=False

def draw_tile(t,source):
 if source=='discard':
  if not t['discard']:raise ValueError('Yerden alınacak taş yok.')
  return t['discard'].pop()
 if source!='deck':raise ValueError('Deste veya son atılan taşı seç.')
 if not t['deck']and len(t['discard'])>1:
  t['deck']=t['discard'][:-1];t['discard']=t['discard'][-1:];secrets.SystemRandom().shuffle(t['deck'])
 return t['deck'].pop()if t['deck']else None

def advance(t,now):
 changed=False
 for i,s in enumerate(t['seats']):
  if s and now-s['seen']>45:t['seats'][i]=None;changed=True
 if changed:
  reset_round(t,'Bağlantısı kesilen oyuncu masadan ayrıldı; el iptal edildi.');t['host']=next((s['cid']for s in t['seats']if s),0)
 if t['phase']=='countdown'and now>=t['deadline']:deal(t,now);changed=True
 elif t['phase']=='dealing'and now>=t['deadline']:t.update(phase='playing',deadline=now+30,message='İlk oyuncu taş atmalı.');changed=True
 elif t['phase']=='round_end'and now>=t['deadline']:
  if t['match_done']:reset_round(t,t['message']+' Yeni maç için hazır ol.');changed=True
  elif all(t['seats']):deal(t,now);changed=True
  else:reset_round(t,'Oyuncu eksik; lobiye dönüldü.');changed=True
 elif t['phase']=='playing'and now>=t['deadline']:
  hand=t['hands'][str(t['seats'][t['turn']]['cid'])]
  if t['step']=='draw':
   tile=draw_tile(t,'deck')
   if tile is None:reset_round(t,'Taşlar tükendi; el berabere bitti.');return True
   hand.append(tile)
  t['discard'].append(hand.pop(secrets.randbelow(len(hand))));t.update(turn=(t['turn']+1)%4,step='draw',deadline=now+30,message='Süre doldu; sistem otomatik taş çekip attı.');changed=True
 return changed

def snapshot(t,cid):
 indicator=face(t['indicator'],(0,1))if t['indicator']is not None else None
 def tile(uid):
  c,n=face(uid,indicator or(0,1));return dict(id=uid,color=c,number=n,fake=uid>=104,joker=uid<104 and indicator is not None and(c,n)==(indicator[0],indicator[1]%13+1))
 mine=next((i for i,s in enumerate(t['seats'])if s and s['cid']==cid),None);hand=t['hands'].get(str(cid),[])if mine is not None else[]
 can=[]
 if t['phase']=='playing'and mine==t['turn']and t['step']=='discard'and len(hand)==15:
  can=[uid for uid in hand if winning([v for v in hand if v!=uid],indicator)]
 return dict(id=t['id'],round=t.get('round',0),version=t['version'],phase=t['phase'],host=t['host'],mode=t['mode'],scores=t['scores'],team_scores=t['team_scores'],turn=t['turn'],step=t['step'],deadline=t['deadline'],message=t['message'],match_done=t['match_done'],dice=t.get('dice',[]),deck_remaining=len(t['deck']),indicator=tile(t['indicator'])if indicator else None,okey=dict(color=indicator[0],number=indicator[1]%13+1)if indicator else None,last_discard=tile(t['discard'][-1])if t['discard']else None,seats=[dict(seat=i,char_id=s['cid'],name=s['name'],ready=s['ready'],count=len(t['hands'].get(str(s['cid']),[])))if s else None for i,s in enumerate(t['seats'])],my_seat=mine,hand=[tile(uid)for uid in hand],finish_tiles=can,server_now=clock())

def install(api):
 if getattr(api,'okey82_installed',False):return api
 from v40_extensions.casino34 import VENUE
 w,previous=api.world,api.dispatch
 with api.database()as db:
  db.execute('CREATE TABLE IF NOT EXISTS pn_okey82(id INTEGER PRIMARY KEY,state TEXT NOT NULL)')
  db.execute('CREATE TABLE IF NOT EXISTS pn_okey_receipts82(user_id INTEGER NOT NULL,request_id TEXT NOT NULL,signature TEXT NOT NULL,table_id INTEGER NOT NULL,PRIMARY KEY(user_id,request_id))')
  db.execute('CREATE TABLE IF NOT EXISTS pn_okey_matches82(id INTEGER PRIMARY KEY AUTOINCREMENT,table_id INTEGER NOT NULL,winner INTEGER NOT NULL,mode TEXT NOT NULL,scores TEXT NOT NULL,created REAL NOT NULL)')
  for i in range(1,4):db.execute('INSERT OR IGNORE INTO pn_okey82 VALUES(?,?)',(i,json.dumps(dict(fresh(),id=i))))
 def actor(token,payload,near=True):
  uid=api.authenticated61(token);p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
  if not uid or not p or not s or p.get('user_id')!=uid:raise ValueError('Önce karakterinle şehre gir.')
  api.require_client61(token,payload)
  if near:
   w.live(p,s)
   from restriction82 import free_actor
   free_actor(api,p,clock())
   if p.get('dimension',0)or s.get('vehicle_id')or w.occupation(p['char_id'])[0]or p.get('cuffed')or p.get('restrained')or not w.near(s,VENUE,5):raise ValueError('Okey için oyun salonuna hayatta, serbest ve yaya yaklaş (5 m).')
  return uid,p,s
 def save(db,t):db.execute('UPDATE pn_okey82 SET state=? WHERE id=?',(json.dumps(t),t['id']))
 def dispatch(path,payload,token):
  with api.LOCK:
   if path=='/api/chat/send'and re.match(r'^/aokeysil\b',str(payload.get('message',''))):
    parts=payload['message'].split()
    if len(parts)!=2 or not parts[1].isdigit():raise ValueError('Kullanım: /aokeysil MASA_ID')
    path='/api/okey82/admin-reset';payload={**payload,'id':int(parts[1]),'request_id':payload.get('request_id')or secrets.token_hex(16)}
   if not path.startswith('/api/okey82/'):
    result,cookie=previous(path,payload,token)
    if path=='/api/gta/sync'and result.get('success')and not api.PRESENCE.get(token,{}).get('dimension',0):result=dict(result,services=result.get('services',[])+[dict(VENUE,id=82090,kind='okey',name='PAV Okey Salonu · 3 masa')])
    return result,cookie
   action=path.rsplit('/',1)[-1];uid,p,s=actor(token,payload,action not in('list','state','leave','admin-reset'));cid=p['char_id'];now=clock()
   if action=='admin-reset'and(not w.admin(uid)or not p.get('admin_duty')):raise ValueError('Bu işlem için yönetici yetkisi ve açık /aduty gerekli.')
   with api.database()as db:
    db.execute('BEGIN IMMEDIATE');tables=[json.loads(row['state'])for row in db.execute('SELECT state FROM pn_okey82 ORDER BY id')]
    for t in tables:
     if advance(t,now):t['version']+=1;save(db,t)
    mine=next((t for t in tables if any(seat and seat['uid']==uid for seat in t['seats'])),None)
    if action=='list':return dict(success=True,tables=[snapshot(t,cid)for t in tables],my_table=mine['id']if mine else None),None
    tid=payload.get('id')
    if type(tid)is not int or tid not in(1,2,3):raise ValueError('Geçerli masa ID seç (1–3).')
    t=next(t for t in tables if t['id']==tid);seat=next((i for i,v in enumerate(t['seats'])if v and v['cid']==cid and v['uid']==uid),None)
    if action=='state':
     if seat is not None:
      try:actor(token,payload,True)
      except ValueError:
       t['seats'][seat]=None;reset_round(t,'Oyuncu salondan ayrıldı; el iptal edildi.');t['host']=next((v['cid']for v in t['seats']if v),0);t['version']+=1
      else:t['seats'][seat]['seen']=now
      save(db,t)
     return dict(success=True,table=snapshot(t,cid)),None
    rid=payload.get('request_id')
    if not isinstance(rid,str)or not re.fullmatch(r'[A-Za-z0-9_-]{16,80}',rid):raise ValueError('Geçerli işlem kimliği gerekli.')
    signature=json.dumps([action,tid,{k:payload.get(k)for k in('seat','tile','source','ready','mode','order')}],sort_keys=True)
    prior=db.execute('SELECT signature FROM pn_okey_receipts82 WHERE user_id=? AND request_id=?',(uid,rid)).fetchone()
    if prior:
     if prior['signature']!=signature:raise ValueError('Bu işlem kimliği farklı bir hamlede kullanılmış.')
     return dict(success=True,table=snapshot(t,cid),replayed=True),None
    if action not in('join','leave','admin-reset')and payload.get('version')!=t['version']:raise ValueError('Masa güncellendi; elini yenileyip tekrar dene.')
    if action=='join':
     if mine:raise ValueError('Zaten bir masadasın. Önce o masadan kalk.')
     index=payload.get('seat')
     if type(index)is not int or not 0<=index<4 or t['seats'][index]:raise ValueError('Bu sandalye dolu veya geçersiz.')
     if t['phase']!='lobby':raise ValueError('Bu masada el sürüyor.')
     t['seats'][index]=dict(uid=uid,cid=cid,name=p['name'],ready=False,seen=now)
     if not t['host']:t['host']=cid
    elif action=='admin-reset':t=dict(fresh(),id=tid,version=t['version'],message='Yönetici masayı güvenli biçimde sıfırladı.');w.audit(db,uid,'okey82-reset',dict(table_id=tid))
    else:
     if seat is None:raise ValueError('Bu masada oturmuyorsun.')
     t['seats'][seat]['seen']=now
     if action=='leave':
      t['seats'][seat]=None;reset_round(t,'Oyuncu masadan kalktı; el iptal edildi.');t['host']=next((v['cid']for v in t['seats']if v),0)
     elif action=='mode':
      if t['phase']!='lobby'or t['host']!=cid or payload.get('mode')not in('free','team'):raise ValueError('Masa sahibi lobide serbest / eşli modu seçebilir.')
      t['mode']=payload['mode']
     elif action=='ready':
      if t['phase']not in('lobby','countdown')or type(payload.get('ready'))is not bool:raise ValueError('Şu anda hazır durumu değiştirilemez.')
      t['seats'][seat]['ready']=payload['ready']
      if t['phase']=='countdown':t.update(phase='lobby',deadline=0,message='Hazır durumu değişti; geri sayım iptal edildi.')
      if all(v and v['ready']for v in t['seats']):t.update(phase='countdown',deadline=now+8,message='Dört oyuncu hazır. Oyun 8 saniye sonra başlıyor.')
     elif action=='order':
      hand=t['hands'].get(str(cid),[]);order=payload.get('order')
      if not isinstance(order,list)or len(order)!=len(hand)or any(type(v)is not int for v in order)or sorted(order)!=sorted(hand):raise ValueError('Yalnız kendi taşlarını sıralayabilirsin.')
      t['hands'][str(cid)]=order
     elif action in('draw','discard','finish'):
      if t['phase']!='playing'or t['turn']!=seat:raise ValueError('Şu anda sıra sende değil.')
      hand=t['hands'][str(cid)];indicator=face(t['indicator'],(0,1))
      if action=='draw':
       if t['step']!='draw'or len(hand)!=14:raise ValueError('Önce elindeki fazla taşı at.')
       tile=draw_tile(t,payload.get('source'))
       if tile is None:reset_round(t,'Deste tükendi; el berabere bitti.')
       else:hand.append(tile);t.update(step='discard',deadline=now+30,message='Bir taş at veya geçerli elini bitir.')
      else:
       tile=payload.get('tile')
       if t['step']!='discard'or len(hand)!=15 or type(tile)is not int or tile not in hand:raise ValueError('Atacağın taş elinde olmalı; önce taş çek.')
       remainder=[v for v in hand if v!=tile];kind=winning(remainder,indicator)if action=='finish'else None
       if action=='finish'and not kind:raise ValueError('Elin henüz geçerli perlere veya yedi çifte ayrılmıyor.')
       hand.remove(tile);t['discard'].append(tile)
       if kind:
        points=(4 if kind=='pairs'else 2)*(2 if tile<104 and face(tile,indicator)==(indicator[0],indicator[1]%13+1)else 1);t['scores'][seat]+=points;t['team_scores'][seat%2]+=points
        won=(t['team_scores'][seat%2]if t['mode']=='team'else t['scores'][seat])>=10
        t.update(phase='round_end',deadline=now+7,match_done=won,message=p['name']+' '+('yedi çift'if kind=='pairs'else 'per')+' ile bitirdi · +'+str(points)+' puan'+(' · MAÇI KAZANDI'if won else ''))
        if won:db.execute('INSERT INTO pn_okey_matches82(table_id,winner,mode,scores,created)VALUES(?,?,?,?,?)',(tid,cid,t['mode'],json.dumps(t['scores']),now))
       else:t.update(turn=(seat+1)%4,step='draw',deadline=now+30,message='Sıradaki oyuncu taş çekmeli.')
     else:raise ValueError('Okey işlemi bulunamadı.')
    t['version']+=1;save(db,t);db.execute('INSERT INTO pn_okey_receipts82 VALUES(?,?,?,?)',(uid,rid,signature,tid))
    return dict(success=True,table=snapshot(t,cid)),None
 api.dispatch=dispatch;api.okey82_installed=True
 return api
