"""Explicit-install police/EMS/faction service extension. No import-time DB work.

Client coordinates are observations validated by the existing multiplayer layer,
not a server physics simulation. Custody transitions always require the victim's
geometry-ready ticket; this extension never accepts client destination XYZ.
"""
import copy, hashlib, importlib, json, math, re, secrets, time

PD = dict(id=17801, kind='police', name='LSPD · Görev / teçhizat', x=441.1, y=-981.9, z=30.69, radius=3)
EMS = dict(id=17802, kind='medical', name='Pillbox · Sağlık görevi', x=307.2, y=-595.3, z=43.28, radius=3)
JAIL = dict(x=1690.5, y=2565.5, z=45.6, heading=180, dimension=1780000, geometry={'kind':'outdoor','ipl':''})

def install(api):
    if getattr(api, 'services178_installed', False): return api
    package=api.__package__; rp=importlib.import_module(package+'.pn_roleplay'); staff=importlib.import_module(package+'.pn_admin'); inv=importlib.import_module(package+'.pn_inventory'); city=importlib.import_module(package+'.pn_city'); mp=importlib.import_module(package+'.pn_multiplayer'); world=api.world
    original=api.dispatch
    with api.database() as db:
        rp.schema(db)
        db.execute('CREATE TABLE IF NOT EXISTS pn_restrictions178(char_id INTEGER PRIMARY KEY,life INTEGER NOT NULL,dimension INTEGER NOT NULL,cuffed INTEGER NOT NULL,prone INTEGER NOT NULL,actor INTEGER NOT NULL,until REAL NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS pn_custody178(char_id INTEGER PRIMARY KEY,source TEXT NOT NULL,target TEXT NOT NULL,until REAL NOT NULL,reason TEXT NOT NULL,actor INTEGER NOT NULL,phase TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1)')
        db.execute('CREATE TABLE IF NOT EXISTS pn_service_receipts178(user_id INTEGER NOT NULL,nonce TEXT NOT NULL,digest TEXT NOT NULL,result TEXT NOT NULL,created REAL NOT NULL,PRIMARY KEY(user_id,nonce))')
        db.execute('CREATE TABLE IF NOT EXISTS pn_dispatch178(id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,x REAL NOT NULL,y REAL NOT NULL,z REAL NOT NULL,dimension INTEGER NOT NULL,created REAL NOT NULL)')
        # Named defaults carry no member/leader grants. Existing matching names
        # or tags must agree in kind; never silently take over a civilian group.
        for point,tag,kind in [(PD,'LSPD','police'),(EMS,'LSFD','medical')]:
            row=db.execute('SELECT * FROM pn_factions WHERE tag=?',(tag,)).fetchone()
            if row and row['kind']!=kind: continue
            if not row:
                fid=db.execute('INSERT INTO pn_factions(name,tag,kind,created) VALUES(?,?,?,?)',(point['name'].split(' · ')[0],tag,kind,time.time())).lastrowid
                db.executemany('INSERT INTO pn_faction_ranks VALUES(?,?,?,0)',[(fid,i,'Lider' if i==1 else 'Rütbe '+str(i))for i in range(1,21)])
            else: fid=row['id']
            existing=db.execute('SELECT faction_id FROM pn_faction_duty WHERE id=?',(point['id'],)).fetchone()
            if not existing:
                db.execute('INSERT INTO pn_faction_duty VALUES(?,?,?,?,?,?,?,?)',(point['id'],fid,point['name'],point['x'],point['y'],point['z'],20,50 if kind=='police'else 0))
    def live(token):
        p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
        if not p or not s or p.get('world')!='gta':raise ValueError('Önce şehre bağlan.')
        if time.time()-s.get('last_seen',0)>30:raise ValueError('Şehir bağlantısını yenileyip tekrar dene.')
        return p,s
    def member(p,kind=None,duty=False,db=None):
        if db is None:
            with api.database() as conn:return member(p,kind,duty,conn)
        m=rp.membership(db,p['char_id'])
        if not m or kind and m['kind']!=kind:raise ValueError('Bu işlem için uygun birlik üyeliğin yok.')
        if duty:
            point=db.execute('SELECT faction_id FROM pn_faction_duty WHERE id=?',(p.get('faction_duty',0),)).fetchone()
            if not point or point['faction_id']!=m['faction_id']:raise ValueError('Önce birlik görevine gir.')
            rest=restrict(p,db)
            if rest and(rest['cuffed']or rest['prone']):raise ValueError('Kısıtlıyken görev yetkisi kullanılamaz.')
        return m
    def restrict(p,db=None):
        if db is None:
            with api.database()as conn:return restrict(p,conn)
        r=db.execute('SELECT * FROM pn_restrictions178 WHERE char_id=?',(p['char_id'],)).fetchone()
        if r and (r['life']!=p.get('life_id',0) or r['dimension']!=p.get('dimension',0) or r['until']<=time.time()):
            db.execute('DELETE FROM pn_restrictions178 WHERE char_id=?',(p['char_id'],));return None
        return dict(r) if r else None
    def point(p,s):
        dim=p.get('dimension',0);geometry={'kind':'outdoor','ipl':''}
        if dim:
            with api.database()as db:prop=db.execute('SELECT kind FROM pn_properties WHERE id=?',(dim,)).fetchone()
            if not prop or prop['kind']not in city.INTERIOR_TYPES:raise ValueError('Bu boyuttan güvenli geri dönüş hazırlanamadı.')
            geometry={'kind':'property','type':prop['kind'],'ipl':city.INTERIOR_TYPES[prop['kind']].get('ipl','')}
        return {**{k:s[k]for k in ('x','y','z','heading')},'dimension':dim,'geometry':geometry}
    def near(p,s,q,t,r=3):return p.get('dimension',0)==q.get('dimension',0) and math.dist([s[k]for k in ('x','y','z')],[t[k]for k in ('x','y','z')])<=r
    def target(payload,p,s):
        cid=world.resolve_player_id(payload.get('server_id'),api.PRESENCE)
        pair=next(((q,api.GTA_STATE.get(tok))for tok,q in api.PRESENCE.items()if q.get('char_id')==cid),None)
        if not pair or not pair[1]or cid==p['char_id']:raise ValueError('Geçerli yakındaki oyuncuyu seç.')
        q,t=pair
        if not near(p,s,q,t)or time.time()-t.get('last_seen',0)>10:raise ValueError('Oyuncu aynı boyutta 3 metre içinde olmalı.')
        if p.get('health',0)<=100 or q.get('health',0)<=100 or s.get('vehicle_id')or t.get('vehicle_id'):raise ValueError('İkiniz de hayatta ve yaya olmalısınız.')
        if type(payload.get('target_life'))is not int or payload.get('target_life')!=q.get('life_id',0):raise ValueError('Oyuncunun hayatı değişti; hedefi yeniden seç.')
        return q,t
    def receipt(db,uid,cid,path,v):
        nonce=v.get('request_id')
        if not isinstance(nonce,str)or not re.fullmatch('[A-Za-z0-9_-]{12,80}',nonce):raise ValueError('İşlem kimliği gerekli.')
        digest=hashlib.sha256(json.dumps([cid,path,{k:x for k,x in v.items()if k!='request_id'}],sort_keys=True,allow_nan=False).encode()).hexdigest()
        old=db.execute('SELECT digest,result FROM pn_service_receipts178 WHERE user_id=? AND nonce=?',(uid,nonce)).fetchone()
        if old and old['digest']!=digest:raise ValueError('İşlem kimliği başka işlemde kullanılmış.')
        return nonce,digest,json.loads(old['result'])if old else None
    def remember(db,uid,nonce,digest,result):db.execute('INSERT INTO pn_service_receipts178 VALUES(?,?,?,?,?)',(uid,nonce,digest,json.dumps(result),time.time()))
    def state_view(p,s,db=None,private=False):
        if db is None:
            with api.database()as conn:return state_view(p,s,conn,private)
        r=restrict(p,db);j=db.execute('SELECT until,reason,phase,version FROM pn_custody178 WHERE char_id=?',(p['char_id'],)).fetchone()
        custody=dict(j)if j else None
        if custody:
            custody['expired']=custody['phase']=='pending'and custody['until']<=time.time()
            custody['needs_transition']=not custody['expired']and(custody['phase']!='inside'or custody['until']<=time.time()or p.get('dimension',0)!=JAIL['dimension'])
        result=dict(cuffed=bool(r and r['cuffed']),prone=bool(r and r['prone']),life_id=p.get('life_id',0))
        if private:
            m=rp.membership(db,p['char_id']);duty=db.execute('SELECT faction_id FROM pn_faction_duty WHERE id=?',(p.get('faction_duty',0),)).fetchone();active=bool(m and duty and duty['faction_id']==m['faction_id'])
            result.update(custody=custody,role=dict(kind=m['kind'],rank=m['rank'],faction_id=m['faction_id'],on_duty=active)if m else None,police_tools=bool(m and m['kind']=='police'and active and not result['cuffed']and not result['prone']and p.get('health',0)>100))
        return result
    def held(p,s,payload):
        with api.database()as db:j=db.execute('SELECT phase,target FROM pn_custody178 WHERE char_id=?',(p['char_id'],)).fetchone()
        if not j or j['phase']=='pending':return payload
        target_point=json.loads(j['target'])
        candidate=[payload.get(k,s[k])for k in ('x','y','z')]
        if not all(type(n)in(int,float)and math.isfinite(n)for n in candidate):raise ValueError('Geçersiz hareket örneği.')
        # Custody is isolated from the main dimension and bounded until release
        # geometry has been prepared. An expired sentence never blind-warps.
        if math.hypot(candidate[0]-target_point['x'],candidate[1]-target_point['y'])>25 or abs(candidate[2]-target_point['z'])>3 or j['phase']=='arriving':
            payload=dict(payload,**{k:s[k]for k in ('x','y','z')},vx=0,vy=0,vz=0,speed=0,hits=[])
        return payload
    def dispatch(path,payload,token):
        with api.LOCK:
            raw=str(payload.get('message','')).strip();cmd=raw.split()[0].lower()if raw else '';args=raw.split()[1:]
            commands=('/factions','/setfacitonleader','/setfactionleader','/pduty','/mduty')
            ours=path.startswith('/api/services178/')or path=='/api/chat/send'and cmd in commands
            if not ours:
                p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token);rest=restrict(p)if p and s else None
                before_ammo=copy.deepcopy(p.get('loadout',{}).get('owned',{}))if p else {}
                if p and s:
                    with api.database()as db:j=db.execute('SELECT phase FROM pn_custody178 WHERE char_id=?',(p['char_id'],)).fetchone()
                    if j and j['phase']!='pending'and path.startswith(('/api/vehicles/enter','/api/elevators/use','/api/properties/enter')):raise ValueError('Önce nezarethane tahliyesini tamamla.')
                    if path=='/api/gta/sync':payload=held(p,s,payload)
                    if path=='/api/factions/duty'and p.get('dimension',0):raise ValueError('Görev dolabı dış dünya boyutunda kullanılabilir.')
                if rest and (rest['cuffed']or rest['prone']):
                    if path.startswith(('/api/inventory/','/api/vehicles/enter','/api/elevators/use','/api/properties/enter')):raise ValueError('Kısıtlıyken bu işlem yapılamaz.')
                    if path=='/api/gta/sync':
                        payload=dict(payload,hits=[],flags=int(payload.get('flags',0))&~(1|2|32),weapon=inv.UNARMED)
                        if rest['prone']:payload.update({k:s[k]for k in ('x','y','z')});payload.update(vx=0,vy=0,vz=0,speed=0)
                        else:
                            elapsed=min(1,max(.05,time.time()-s.get('last_seen',time.time())));distance=math.hypot(float(payload.get('x',s['x']))-s['x'],float(payload.get('y',s['y']))-s['y'])
                            if distance>1.5*elapsed+.25:payload.update({k:s[k]for k in ('x','y','z')});payload.update(vx=0,vy=0,vz=0,speed=0)
                result,cookie=original(path,payload,token);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
                if result.get('success')and p and s and path=='/api/gta/sync':
                    with api.database()as db:
                        own=state_view(p,s,db,True);result=dict(result,services178=own)
                        for peer in result.get('players',[]):
                            actor=next((q for q in api.PRESENCE.values()if q.get('char_id')==peer.get('char_id')),None)
                            if actor:peer.update(state_view(actor,s,db))
                        result['services']=result.get('services',[])+[dict(PD),dict(EMS)]
                        # Only an accepted decrease in server-owned ammunition can
                        # produce an alert; neither arbitrary XYZ nor raw hits do.
                        after=p.get('loadout',{}).get('owned',{})
                        if not(rest and(rest['cuffed']or rest['prone']))and any(after.get(k,0)<v for k,v in before_ammo.items())and time.time()-p.get('shot_alert178',0)>8:
                            p['shot_alert178']=time.time();db.execute('INSERT INTO pn_dispatch178(kind,x,y,z,dimension,created) VALUES(?,?,?,?,?,?)',('Silah sesi',s['x'],s['y'],s['z'],p.get('dimension',0),time.time()))
                            db.execute('DELETE FROM pn_dispatch178 WHERE created<?',(time.time()-600,))
                        try:member(p,'police',True,db);result['dispatch178']=[dict(row)for row in db.execute('SELECT id,kind,x,y,z,created FROM pn_dispatch178 WHERE created>? AND dimension=? ORDER BY id DESC LIMIT 20',(time.time()-300,p.get('dimension',0)))]
                        except ValueError:result['dispatch178']=[]
                return result,cookie
            auth,cookie=original('/api/auth/me',{},token)
            if not auth.get('success'):return auth,cookie
            p,s=live(token);uid=auth['user_id'];cid=p['char_id'];now=time.time()
            if cmd=='/factions':
                with api.database()as db:
                    rows=[]
                    for f in db.execute('SELECT id,name,kind FROM pn_factions ORDER BY id LIMIT 500'):
                        leaders=[' '.join((r['name'],r['surname']))for r in db.execute('SELECT c.name,c.surname FROM pn_faction_members m JOIN characters c ON c.id=m.char_id WHERE m.faction_id=? AND m.leader=1 ORDER BY m.char_id',(f['id'],))];rows.append([f['id'],f['name'],f['kind'],', '.join(leaders)or 'Lider atanmamış'])
                return dict(success=True,info=dict(title='Birlikler · ID / Ad / Tür / Lider',rows=rows)),None
            if cmd in ('/setfacitonleader','/setfactionleader'):
                if staff.rank(uid)<2:raise ValueError('Yönetici yetkisi gerekli.')
                if len(args)!=2 or not all(x.isdecimal()for x in args):raise ValueError('Kullanım: /setfactionleader birlik_id oyuncu_id')
                fid=int(args[0]);target_id=world.resolve_player_id(int(args[1]),api.PRESENCE)
                with api.database()as db:
                    f=db.execute('SELECT * FROM pn_factions WHERE id=?',(fid,)).fetchone()
                    if not f:raise ValueError('Birlik bulunamadı.')
                    old=rp.membership(db,target_id)
                    if old and old['faction_id']!=fid:raise ValueError('Oyuncu başka birlikte; önce üyeliği normal yolla kaldırılmalı.')
                    db.execute('UPDATE pn_faction_members SET leader=0 WHERE faction_id=?',(fid,));db.execute('INSERT INTO pn_faction_members VALUES(?,?,1,1,?) ON CONFLICT(char_id) DO UPDATE SET rank=1,leader=1',(target_id,fid,now));world.audit(db,uid,'faction-leader178',dict(faction=fid,char=target_id))
                return dict(success=True,notice='Birlik lideri atandı.'),None
            if cmd in ('/pduty','/mduty'):
                kind='police'if cmd=='/pduty'else'medical';m=member(p,kind)
                with api.database()as db:points=[dict(r)for r in db.execute('SELECT * FROM pn_faction_duty WHERE faction_id=? ORDER BY id',(m['faction_id'],))]
                choice=next((r for r in points if not p.get('dimension',0)and rp.near(s,r,3)),None)
                if not choice:raise ValueError('Görev dolabına 3 metre içinde yaklaş.')
                return original('/api/factions/duty',{'point':choice['id'],'request_id':secrets.token_hex(16)},token)
            action=path.removeprefix('/api/services178/')
            if action=='status':return dict(success=True,**state_view(p,s,private=True)),None
            if action in ('custody-list','custody-release'):
                m=member(p,'police',True)
                if p.get('dimension',0)or not rp.near(s,PD,3):raise ValueError('LSPD işlem masasına yaklaş.')
                with api.database()as db:
                    if action=='custody-list':
                        rows=[dict(r)for r in db.execute('SELECT j.char_id,j.until,j.reason,j.phase,j.version,c.name,c.surname FROM pn_custody178 j JOIN characters c ON c.id=j.char_id ORDER BY j.until LIMIT 200')]
                        return dict(success=True,cases=rows),None
                    if m['rank']>5:raise ValueError('Tahliye için yetkili polis rütbesi gerekli.')
                    nonce,digest,old=receipt(db,uid,cid,path,payload)
                    if old:return old,None
                    target_id=payload.get('char_id');version=payload.get('version')
                    if type(target_id)is not int or type(version)is not int:raise ValueError('Vaka listesinden geçerli kayıt seç.')
                    row=db.execute('SELECT phase,version FROM pn_custody178 WHERE char_id=?',(target_id,)).fetchone()
                    if not row or row['version']!=version:raise ValueError('Nezarethane kaydı değişti; listeyi yenile.')
                    if row['phase']=='pending':db.execute('DELETE FROM pn_custody178 WHERE char_id=?',(target_id,))
                    else:db.execute('UPDATE pn_custody178 SET until=?,version=version+1 WHERE char_id=?',(now,target_id))
                    result=dict(success=True,notice='Tahliye hazırlığı açıldı; hedef oyuncu zemin onayından sonra çıkar.');remember(db,uid,nonce,digest,result);world.audit(db,uid,'custody-release178',dict(target=target_id))
                return result,None
            if action in ('armory-list','armory-buy'):
                m=member(p,duty=True)
                if m['kind']not in ('police','medical'):raise ValueError('Resmî görev teçhizatı bu birliğe açık değil.')
                with api.database()as db:duty=db.execute('SELECT * FROM pn_faction_duty WHERE id=?',(p.get('faction_duty',0),)).fetchone()
                if not duty or p.get('dimension',0)or not rp.near(s,duty,3)or s.get('vehicle_id')or p.get('health',0)<=100:raise ValueError('Görev dolabında, hayatta ve yaya olmalısın.')
                stock={'pistol':5000,'ammo_pistol':350,'armor':1200}if m['kind']=='police'else{'bandage':500}
                if action=='armory-list':return dict(success=True,items=[dict(key=k,cost=v)for k,v in stock.items()],bank=m['bank'],faction_id=m['faction_id']),None
                key=payload.get('item')
                if key not in stock:raise ValueError('Bu teçhizat görevine uygun değil.')
                inv.load(p);updated=copy.deepcopy(p['loadout']);version=p.get('loadout_version',1)+1
                with api.database()as db:
                    nonce,digest,old=receipt(db,uid,cid,path,payload)
                    if old:return old,None
                    if key=='pistol':
                        if key in updated['owned']:raise ValueError('Bu silah zaten çantanda.')
                        updated['owned'][key]=inv.clip_capacity(key);updated.setdefault('clips',{})[key]=inv.clip_capacity(key)
                    else:
                        count=updated.setdefault('stock',{}).get(key,0)
                        if count>=20:raise ValueError('Teçhizat paketi sınırı dolu.')
                        updated['stock'][key]=count+1
                    containers=importlib.import_module(package+'.pn_containers')
                    check=dict(p,loadout=updated)
                    if containers.weight(containers.personal(check))>30:raise ValueError('Çantanda teçhizat için yeterli yer yok.')
                    if not db.execute('UPDATE pn_factions SET bank=bank-? WHERE id=? AND bank>=?',(stock[key],m['faction_id'],stock[key])).rowcount:raise ValueError('Birlik kasası yetersiz; ücretsiz teçhizat verilmedi.')
                    db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version',(cid,json.dumps(updated),version));result=dict(success=True,notice='Teçhizat birlik kasasından satın alındı.',cost=stock[key],item=key);remember(db,uid,nonce,digest,result);world.audit(db,uid,'armory-buy178',dict(item=key,cost=stock[key],faction=m['faction_id']))
                p['loadout']=updated;p['loadout_version']=version;return result,None
            if action=='release':
                member(p,'police',True);q,t=target(payload,p,s)
                with api.database()as db:
                    nonce,digest,old=receipt(db,uid,cid,path,payload)
                    if old:return old,None
                    row=db.execute('SELECT phase FROM pn_custody178 WHERE char_id=?',(q['char_id'],)).fetchone()
                    if not row:raise ValueError('Nezarethane kaydı bulunamadı.')
                    if row['phase']=='pending':db.execute('DELETE FROM pn_custody178 WHERE char_id=?',(q['char_id'],))
                    else:db.execute('UPDATE pn_custody178 SET until=?,version=version+1 WHERE char_id=?',(now,q['char_id']))
                    result=dict(success=True,notice='Tahliye hazırlığı açıldı; hedef zemin onayı gerekli.');remember(db,uid,nonce,digest,result)
                return result,None
            if action in ('cuff','prone','jail-offer'):
                member(p,'police',True);q,t=target(payload,p,s)
                with api.database()as db:
                    nonce,digest,old=receipt(db,uid,cid,path,payload)
                    if old:return old,None
                    rest=restrict(q,db)or dict(cuffed=0,prone=0)
                    if action=='jail-offer':
                        if not rest['cuffed']or p.get('dimension',0)or not rp.near(s,PD,7):raise ValueError('Kelepçeli hedefi LSPD nezarethane girişine getir.')
                        seconds=payload.get('seconds');reason=str(payload.get('reason','')).strip()
                        if type(seconds)is not int or not 30<=seconds<=3600 or not 5<=len(reason)<=160:raise ValueError('Süre 30–3600 saniye, gerekçe 5–160 karakter olmalı.')
                        if db.execute('SELECT 1 FROM pn_custody178 WHERE char_id=?',(q['char_id'],)).fetchone():raise ValueError('Oyuncunun nezarethane işlemi zaten var.')
                        source=point(q,t);db.execute('INSERT INTO pn_custody178 VALUES(?,?,?,?,?,?,?,1)',(q['char_id'],json.dumps(source),json.dumps(JAIL),now+seconds,reason,cid,'pending'))
                        result=dict(success=True,notice='Nezarethane hazırlığı hedef oyuncuya gönderildi; zemin onayı bekleniyor.')
                    else:
                        if type(payload.get('enabled'))is not bool:raise ValueError('Açık veya kapalı durum seç.')
                        rest['cuffed'if action=='cuff'else'prone']=int(payload['enabled'])
                        if action=='prone'and rest['prone']and not rest['cuffed']:raise ValueError('Önce kelepçe gerekli.')
                        if action=='cuff'and not rest['cuffed']:rest['prone']=0
                        db.execute('INSERT INTO pn_restrictions178 VALUES(?,?,?,?,?,?,?) ON CONFLICT(char_id) DO UPDATE SET life=excluded.life,dimension=excluded.dimension,cuffed=excluded.cuffed,prone=excluded.prone,actor=excluded.actor,until=excluded.until',(q['char_id'],q.get('life_id',0),q.get('dimension',0),rest['cuffed'],rest['prone'],cid,now+1800));result=dict(success=True,notice='Kelepçe / yere yatma durumu kaydedildi.',**state_view(q,t,db))
                    remember(db,uid,nonce,digest,result);world.audit(db,uid,'service-'+action,dict(target=q['char_id']))
                if action!='jail-offer':mp.emote(p,s,'kelepçe / yere yatırma işlemi yaptı.')
                return result,None
            if action.startswith('transition/'):
                step=action.split('/')[-1]
                used=p.get('custody_used178');ticket=payload.get('ticket')
                if step=='confirm'and used and used.get('confirmed')and ticket==used['ticket']and used['life']==p.get('life_id',0):return dict(success=True,confirmed=True,already_confirmed=True),None
                if step=='use'and used and ticket==used['ticket']:
                    if used.get('rolled_back')or used['life']!=p.get('life_id',0):raise ValueError('Geçiş hayatı değişti.')
                    return dict(success=True,already_used=True,spawn={k:s[k]for k in ('x','y','z','heading')}|dict(health=p['health'],armor=p.get('armor',0)),life_id=p['life_id'],dimension=p.get('dimension',0)),None
                if step=='rollback':
                    ready=p.get('custody_ready178')
                    if ready and isinstance(ticket,str)and secrets.compare_digest(ticket,ready['ticket']):
                        p.pop('custody_ready178',None);p['custody_cancelled178']=ticket
                        return dict(success=True,cancelled_before_use=True,spawn={k:s[k]for k in ('x','y','z','heading')}|dict(health=p['health'],armor=p.get('armor',0)),life_id=p.get('life_id',0),dimension=p.get('dimension',0)),None
                    if ticket==p.get('custody_cancelled178')and isinstance(ticket,str):return dict(success=True,cancelled_before_use=True,spawn={k:s[k]for k in ('x','y','z','heading')}|dict(health=p['health'],armor=p.get('armor',0)),life_id=p.get('life_id',0),dimension=p.get('dimension',0)),None
                    if not used or used.get('confirmed')or not isinstance(ticket,str)or not secrets.compare_digest(ticket,used['ticket']):raise ValueError('Geri dönüş bileti bulunamadı.')
                    if used.get('rolled_back'):
                        if used['rollback_life']!=p.get('life_id',0):raise ValueError('Geri dönüş hayatı değişti.')
                        return dict(success=True,already_rolled_back=True,spawn={k:s[k]for k in ('x','y','z','heading')}|dict(health=p['health'],armor=p.get('armor',0)),life_id=p['life_id'],dimension=p.get('dimension',0)),None
                    if now-used['at']>30 or used['life']!=p.get('life_id',0)or p.get('dimension',0)!=used['target']['dimension']or s.get('vehicle_id')or math.hypot(s['x']-used['target']['x'],s['y']-used['target']['y'])>5:raise ValueError('Geri dönüş koşulları değişti.')
                    back=city.teleport(p,s,used['source'],used['source']['dimension'])
                    with api.database()as db:db.execute('UPDATE pn_custody178 SET phase=?,version=version+1 WHERE char_id=?',(used['previous_phase'],cid))
                    used.update(rolled_back=True,rollback_life=p['life_id']);return dict(success=True,**back),None
                with api.database()as db:row=db.execute('SELECT * FROM pn_custody178 WHERE char_id=?',(cid,)).fetchone()
                if not row:raise ValueError('Bekleyen nezarethane geçişi yok.')
                leaving=row['phase']=='releasing'or row['phase']=='inside'and now>=row['until'];target_point=json.loads(row['source']if leaving else row['target'])
                if step=='confirm':
                    if not used or not isinstance(ticket,str)or not secrets.compare_digest(ticket,used['ticket'])or used.get('rolled_back')or used['life']!=p.get('life_id',0):raise ValueError('Varış bileti değişti.')
                    if not near(p,s,{'dimension':used['target']['dimension']},used['target'],3):raise ValueError('Varış noktasında değilsin.')
                    with api.database()as db:
                        if used['leaving']:db.execute('DELETE FROM pn_custody178 WHERE char_id=?',(cid,))
                        else:db.execute("UPDATE pn_custody178 SET phase='inside',version=version+1 WHERE char_id=?",(cid,))
                    used['confirmed']=True;return dict(success=True,confirmed=True),None
                if step=='prepare':
                    if row['phase']=='inside'and not leaving and p.get('dimension',0)==JAIL['dimension']:raise ValueError('Nezarethane süren devam ediyor.')
                    if row['phase']=='pending'and row['until']<now:raise ValueError('Nezarethane teklifi sona erdi; görevli yeniden hazırlamalı.')
                    ticket=secrets.token_hex(16);source=({**JAIL,**{k:s[k]for k in ('x','y','z','heading')}}if p.get('dimension',0)==JAIL['dimension']else point(p,s))
                    p['custody_ready178']=dict(ticket=ticket,version=row['version'],life=p.get('life_id',0),dimension=p.get('dimension',0),until=now+20,leaving=leaving,target=target_point,source=source)
                    return dict(success=True,ticket=ticket,target=target_point,expires_in=20),None
                ready=p.get('custody_ready178');ticket=payload.get('ticket')
                if step=='cancel':
                    if ready and isinstance(ticket,str)and secrets.compare_digest(ticket,ready['ticket']):p.pop('custody_ready178',None)
                    return dict(success=True,cancelled=True),None
                if step!='use'or not ready or not isinstance(ticket,str)or not secrets.compare_digest(ticket,ready['ticket'])or payload.get('ready')is not True:raise ValueError('Geçerli zemin hazırlık bileti gerekli.')
                if ready['until']<now or ready['life']!=p.get('life_id',0)or ready['dimension']!=p.get('dimension',0)or ready['version']!=row['version']or s.get('vehicle_id')or p.get('health',0)<=100:raise ValueError('Geçiş durumu değişti; yeniden hazırla.')
                if not leaving and not near(p,s,{'dimension':ready['source']['dimension']},ready['source'],3):raise ValueError('Nezarethane kaynağından uzaklaştın.')
                result=city.teleport(p,s,ready['target'],ready['target']['dimension']);p['custody_used178']=dict(ticket=ticket,life=p['life_id'],source=ready['source'],target=ready['target'],leaving=leaving,previous_phase=row['phase'],at=now);p.pop('custody_ready178',None)
                with api.database()as db:
                    db.execute('UPDATE pn_custody178 SET phase=?,version=version+1 WHERE char_id=?',('releasing'if leaving else'arriving',cid))
                    db.execute('DELETE FROM pn_restrictions178 WHERE char_id=?',(cid,))
                return dict(success=True,notice='Nezarethane geçişi doğrulandı.',**result),None
            raise ValueError('Hizmet işlemi bulunamadı.')
    api.dispatch=dispatch;api.services178_installed=True;return api
