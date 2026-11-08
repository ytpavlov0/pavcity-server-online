"""Door controls, staff tools and guarded country changes; layered over71."""
import copy, json, re, time, unicodedata

def install(api):
    if getattr(api,'city72_installed',False):return api
    import gameplay_v29.pn_city as city
    import gameplay_v29.pn_commands as commands
    import gameplay_v29.pn_admin as staff
    import gameplay_v29.pn_multiplayer as mp
    import gameplay_v29.pn_traffic as traffic
    import gameplay_v29.pn_roleplay as rp
    w=api.world;previous=api.dispatch;old_command=commands.command;old_staff=staff.command
    old_public=w.public;register=traffic.register
    with api.database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pn_country72(char_id INTEGER PRIMARY KEY,changes INTEGER NOT NULL DEFAULT 0 CHECK(changes>=0))')
        db.execute('CREATE TABLE IF NOT EXISTS pn_property_lights72(property_id INTEGER PRIMARY KEY,enabled INTEGER NOT NULL DEFAULT 1)')

    def actor(token,values):
        uid=api.authenticated61(token)
        if not uid:raise ValueError('Önce giriş yap.')
        api.require_client61(token,values)
        p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
        if not p or p['user_id']!=uid:raise ValueError('Önce karakterinle şehre bağlan.')
        w.live(p,s);return uid,p,s

    def admin(uid,p,s,level=2):
        if staff.rank(uid)<level or not p.get('admin_duty'):raise ValueError('Yönetici yetkisi ve /aduty gerekli.')
        w.live(p,s)

    def paint(value):
        if not isinstance(value,dict):return None
        out={}
        for key in ('primary','secondary'):
            n=value.get(key);rgb=value.get(key+'_rgb')
            if type(n)is not int or not 0<=n<=160:raise ValueError('Trafik aracının renk bilgisi geçersiz.')
            if rgb is not None and (type(rgb)is not list or len(rgb)!=3 or any(type(v)is not int or not 0<=v<=255 for v in rgb)):raise ValueError('Trafik aracının özel rengi geçersiz.')
            out[key]=n
            if rgb is not None:out[key+'_rgb']=rgb
        return out

    def public(row):
        result=old_public(row)
        # Unknown ambient paint must remain on the existing native entity. The
        # model's deterministic factory palette is only appropriate for spawns.
        if result.get('street'):
            defaults=result.pop('factory_paint66',{}).get('default_sides',[])
            result['mods']={k:v for k,v in result.get('mods',{}).items() if k not in defaults}
        return result

    def register72(uid,token,values,p,s):
        observed=paint(values.get('paint43'))
        with api.database() as db:exists=db.execute('SELECT id FROM pn_vehicles WHERE plate=?',(str(values.get('plate','')).strip().upper(),)).fetchone()
        result=register(uid,token,values,p,s)
        if observed is not None and not exists:
            vid=result['vehicle']['id'];row=w.vehicle(vid)
            fields=copy.deepcopy(w.VEHICLE_CACHE.get(vid,json.loads(row['state'])))
            fields['mods']={**fields.get('mods',{}),**observed}
            with api.database() as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('UPDATE pn_vehicles SET state=? WHERE id=?',(json.dumps(fields),vid))
                w.audit(db,uid,'traffic-paint72',dict(id=vid,paint=observed))
            w.VEHICLE_CACHE[vid]=fields;w.SAVED_AT[vid]=time.time()
            result['vehicle']=w.public(w.vehicle(vid))
        return result

    def property_view(p,s,pid=None):
        dim=p.get('dimension',0)
        with api.database() as db:
            if dim:row=db.execute('SELECT * FROM pn_properties WHERE id=?',(dim,)).fetchone() if pid is None or pid==dim else None
            elif pid is not None:row=db.execute('SELECT * FROM pn_properties WHERE id=?',(pid,)).fetchone()
            else:
                rows=db.execute('SELECT * FROM pn_properties WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ?', (s['x']-3,s['x']+3,s['y']-3,s['y']+3)).fetchall()
                row=min((v for v in rows if w.near(s,v,3)),key=lambda v:sum((v[k]-s[k])**2 for k in ('x','y','z')),default=None)
            if not row:return None
            row=dict(row);anchor=city.INTERIOR_TYPES.get(row['kind']) if dim else row
            if not anchor:return None
            key=row['owner']==p['char_id'] or bool(db.execute('SELECT 1 FROM pn_property_keys WHERE property_id=? AND char_id=?',(row['id'],p['char_id'])).fetchone())
            light=db.execute('SELECT enabled FROM pn_property_lights72 WHERE property_id=?',(row['id'],)).fetchone()
        return dict(id=row['id'],name=row['name'],kind=row['kind'],inside=bool(dim),locked=bool(row['locked']),can_lock=key,version=row['version'],lights=bool(light[0]) if light else True,anchor={k:anchor.get(k,0) for k in ('x','y','z','heading')},distance=round(sum((s[k]-anchor[k])**2 for k in ('x','y','z'))**.5,2))

    def door(uid,p,s,values,action):
        if type(values.get('id'))is not int or values['id']<=0:raise ValueError('Geçerli mülk seç.')
        v=property_view(p,s,values.get('id'))
        if not v or v['id']!=values.get('id') or v['distance']>2:raise ValueError('Kapı işaretinin üzerine yaya yaklaş (2 m).')
        if s.get('vehicle_id') or w.occupation(p['char_id'])[0]:raise ValueError('Araçtan in.')
        if not v['can_lock']:raise ValueError('Bu mülkün anahtarı sende yok.')
        with api.database() as db:
            db.execute('BEGIN IMMEDIATE')
            if action=='lock':
                if type(values.get('version'))is not int or values['version']!=v['version']:raise ValueError('Kapının durumu değişti; yeniden dene.')
                if db.execute('UPDATE pn_properties SET locked=1-locked,version=version+1 WHERE id=? AND version=?',(v['id'],v['version'])).rowcount!=1:raise ValueError('Kapının durumu değişti; yeniden dene.')
                notice='Kapı açıldı.' if v['locked'] else 'Kapı kilitlendi.'
            else:
                if not v['inside']:raise ValueError('Işığı içeriden kontrol et.')
                enabled=values.get('enabled')
                if type(enabled)is not bool:raise ValueError('Işık durumu geçersiz.')
                db.execute('INSERT INTO pn_property_lights72 VALUES(?,?) ON CONFLICT(property_id) DO UPDATE SET enabled=excluded.enabled',(v['id'],int(enabled)))
                notice='Ev ışıkları '+('açıldı.' if enabled else 'kapatıldı.')
            w.audit(db,uid,'property72-'+action,dict(id=v['id']))
        return dict(success=True,notice=notice,property72=property_view(p,s,v['id']))

    def country(uid,p,code):
        cid=p['char_id']
        if not isinstance(code,str) or code not in commands.COUNTRIES:raise ValueError('Geçerli ülke seç.')
        current=commands.country(cid)
        with api.database() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT OR IGNORE INTO pn_country72 VALUES(?,0)',(cid,))
            used=db.execute('SELECT changes FROM pn_country72 WHERE char_id=?',(cid,)).fetchone()[0]
            if current!=code:
                if used>=2:rp.debit(db,'pn_wallet','user_id',uid,1000000)
                db.execute('UPDATE pn_character_country SET code=? WHERE char_id=?',(code,cid))
                db.execute('UPDATE pn_country72 SET changes=changes+1 WHERE char_id=?',(cid,))
                w.audit(db,uid,'country72',dict(char_id=cid,country=code,price=1000000 if used>=2 else 0))
                used+=1
        return dict(success=True,countries=commands.COUNTRIES,country=code,free_changes=max(0,2-used),next_price=1000000 if used>=2 else 0,money=w.wallet(uid),notice='Ülke kaydedildi. Kalan ücretsiz değişiklik: '+str(max(0,2-used)))

    def custom(cmd,args,uid,p,s,peers):
        if cmd=='/setvehcolor':return old_command('/acolorveh',args,uid,p,s,peers)
        if cmd=='/ulkesec' and args:
            if len(args)!=1:raise ValueError('Kullanım: /ulkesec ülke_kodu')
            return country(uid,p,args[0].lower())
        if cmd in ('/isikac','/ışıkac','/ışık aç','/isikkapat','/ışıkkapat'):
            v=property_view(p,s)
            if not v or not v['inside']:raise ValueError('Önce evine gir.')
            if not v['can_lock']:raise ValueError('Bu mülkün anahtarı sende yok.')
            # Light controls work anywhere inside the authorised home.
            with api.database() as db:
                enabled=cmd not in ('/isikkapat','/ışıkkapat')
                db.execute('INSERT INTO pn_property_lights72 VALUES(?,?) ON CONFLICT(property_id) DO UPDATE SET enabled=excluded.enabled',(v['id'],int(enabled)))
                w.audit(db,uid,'property72-light',dict(id=v['id'],enabled=enabled))
            return dict(success=True,notice='Işıklar '+('açıldı.' if enabled else 'kapatıldı.'))
        if cmd in ('/intlist','/interiorlar'):
            admin(uid,p,s)
            return dict(success=True,info=dict(title='Yüklü iç mekânlar · /addint ŞABLON_ID fiyat ad',rows=[[i+1,k+' · '+v['name']] for i,(k,v) in enumerate(city.INTERIOR_TYPES.items())]))
        if cmd=='/addint' and args and args[0].isdigit():
            admin(uid,p,s);keys=list(city.INTERIOR_TYPES)
            kind=keys[staff.number(args[0],1,len(keys))-1]
            return old_command(cmd,[kind,*args[1:]],uid,p,s,peers)
        if cmd=='/addint':admin(uid,p,s)
        if cmd in ('/delint','/gotoint','/intler'):
            admin(uid,p,s)
            if cmd=='/intler' or not args:
                with api.database() as db:rows=[[r['id'],r['name']+' · '+r['kind']] for r in db.execute('SELECT id,name,kind FROM pn_properties ORDER BY id')]
                return dict(success=True,info=dict(title='Mülkler · /gotoint ID · /delint ID',rows=rows))
            if len(args)!=1:raise ValueError('Kullanım: '+cmd+' MÜLK_ID')
            pid=staff.number(args[0],1,2147483647)
            if p.get('dimension') or s.get('vehicle_id') or w.occupation(p['char_id'])[0]:raise ValueError('Önce iç mekândan çık ve yaya ol.')
            if staff.jail(p['char_id']):raise ValueError('Hapiste bu işlem yapılamaz.')
            with api.database() as db:
                db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT * FROM pn_properties WHERE id=?',(pid,)).fetchone()
                if not row:raise ValueError('Mülk bulunamadı.')
                if cmd=='/delint':
                    if any(q.get('dimension')==pid or any((q.get(k) or {}).get('id')==pid and (q.get(k) or {}).get('phase') in ('prepared','pending') for k in ('property45_ready','property45_used')) for q in peers.values()):raise ValueError('İçeride veya giriş hazırlığında oyuncu var. Önce boşalt.')
                    for table in ('pn_property_keys','pn_property_factions63','pn_property_lights72','pn_property_recovery45'):
                        db.execute('DELETE FROM '+table+' WHERE property_id=?',(pid,))
                    db.execute('DELETE FROM pn_properties WHERE id=?',(pid,))
                w.audit(db,uid,cmd[1:],dict(id=pid,name=row['name']))
            if cmd=='/delint':return dict(success=True,notice=f'Mülk #{pid} ve anahtarları kalıcı silindi.')
            return dict(success=True,notice=f'Mülk #{pid} dış kapısına gidildi.',**city.teleport(p,s,dict(row),0))
        return old_command(cmd,args,uid,p,s,peers)

    def staff_command(uid,token,values,p,peers,states):
        parts=str(values.get('message','')).strip().split();cmd=parts[0].lower() if parts else ''
        if cmd in ('/yetkiver','/yetkiverk'):values={**values,'message':'/rankver '+' '.join(parts[1:])}
        if cmd=='/godmode' and p and p.get('admin_duty') and staff.rank(uid)>=2:return dict(success=True,notice='Yönetici görevinde hasar koruması açık. Görevden /aduty ile çıkabilirsin.')
        if cmd in ('/yetkililer','/adminrehber'):
            if staff.rank(uid)<1:raise ValueError('Bu rehber yetkililere açık.')
            rows=[['1 · Moderatör','Raporlar, yetkili listesi ve destek'],['2 · Yönetici','/aduty, /goto, /gethere, /gotoint ID, /delint ID, /intler, /setvehcolor'],['3 · Baş yönetici','Yönetici araçları ve moderasyon'],['4 · Kurucu','/yetkiver OYUNCU_ID 0–3, VIP ve donate yetkileri']]
            rows += [[q['name']+' · ID '+str(q['server_id']),staff.RANKS[staff.rank(q['user_id'])]+(' · Görevde' if q.get('admin_duty') else ' · Görev dışı')] for q in peers.values() if time.time()-q.get('last_seen',0)<30 and staff.rank(q['user_id']) and not q.get('hide_admin')]
            return dict(success=True,info=dict(title='Yetkili rehberi ve çevrimiçi ekip',rows=rows))
        before=bool(p.get('admin_duty')) if p else False
        result=old_staff(uid,token,values,p,peers,states)
        if p and cmd=='/aduty' and result and result.get('success') and staff.rank(uid)>=2:
            if not before:p['godmode_before72']=bool(p.get('godmode'))
            p['godmode']=True if p.get('admin_duty') else p.pop('godmode_before72',False)
        return result

    def normalize(s):
        s=unicodedata.normalize('NFKD',s.casefold().replace('ı','i'))
        return ''.join(c for c in s if not unicodedata.combining(c))
    def chat_guard(p,message):
        parts=message.split(None,1);cmd=parts[0].lower() if parts else ''
        if cmd.startswith('/') and cmd not in ('/me','/do','/b','/ooc','/pm','/p','/r','/f'):return
        text=parts[1] if cmd.startswith('/') and len(parts)>1 else message
        folded=normalize(text);compact=re.sub('[^a-z0-9]','',folded)
        deity=re.search(r'\b(?:allah|tanri)[a-z]{0,8}\b',folded)
        abuse=re.search(r'\b(?:s[\W_]*[i1][\W_]*k(?:eyim|erim|tir|tigim|im|iyim|iyorum|mis|ti|icem)?|amk|amq|orospu)\b',folded)
        joined=re.search(r'\b(?:allah|tanri)[a-z]{0,6}(?:sikeyim|sikerim|sikim|sikiyim|amk|amq)\b',folded)
        if joined or deity and abuse and abs(deity.start()-abuse.start())<64:raise ValueError('Dini değerlere hakaret içeren mesaj gönderilemez.')
        now=time.monotonic();events=[v for v in p.get('chat72',[]) if now-v[0]<10]
        if len(events)>=5:raise ValueError('Sohbet çok hızlı. Birkaç saniye bekle.')
        if any(v[1]==compact and now-v[0]<8 for v in events):raise ValueError('Aynı mesajı art arda gönderemezsin.')
        events.append((now,compact));p['chat72']=events

    def dispatch(path,values,token):
        with api.LOCK:
            p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
            if path.startswith('/api/property72/'):
                uid,p,s=actor(token,values);action=path.rsplit('/',1)[-1]
                if action=='status':return dict(success=True,property72=property_view(p,s)),None
                if (p.get('property45_used') or {}).get('phase')=='pending':raise ValueError('Önce iç mekânın yükleme onayını bekle.')
                if action in ('lock','light'):return door(uid,p,s,values,action),None
                if action=='sleep-start':
                    v=property_view(p,s)
                    if not v or not v['inside'] or v['kind']!='apartment' or not v['can_lock']:raise ValueError('Uyumak için anahtarın olan bir eve gir.')
                    if s.get('vehicle_id') or w.occupation(p['char_id'])[0] or p.get('inventory_action'):raise ValueError('Önce devam eden işlemi bitir.')
                    p['sleep72']=dict(start=time.monotonic(),life=p.get('life_id'),dimension=p['dimension'],pose={k:s[k] for k in ('x','y','z')})
                    return dict(success=True,duration=30),None
                if action=='sleep-cancel':p.pop('sleep72',None);return dict(success=True),None
                if action=='sleep-finish':
                    run=p.get('sleep72')
                    if not run or run['life']!=p.get('life_id') or run['dimension']!=p.get('dimension') or time.monotonic()-run['start']<30 or not w.near(s,run['pose'],.75):raise ValueError('Dinlenme tamamlanmadı veya yerinden ayrıldın.')
                    p.pop('sleep72',None);p['rested72']=p.get('rested72',0)+1
                    return dict(success=True,rested72=p['rested72'],notice='Dinlendin; enerjin yenilendi.'),None
                raise ValueError('Mülk işlemi bulunamadı.')
            if path=='/api/properties/lock':
                uid,p,s=actor(token,values)
                if (p.get('property45_used') or {}).get('phase')=='pending':raise ValueError('Önce iç mekânın yükleme onayını bekle.')
                v=property_view(p,s,values.get('id'))
                return door(uid,p,s,{**values,'version':values.get('version',v['version'] if v else 0)},'lock'),None
            if path=='/api/properties/give-key' and p and s:
                cid=w.resolve_player_id(values.get('server_id'),api.PRESENCE)
                target=next((q for q in api.PRESENCE.values() if q['char_id']==cid and time.time()-q.get('last_seen',0)<20),None)
                target_state=next((api.GTA_STATE.get(t) for t,q in api.PRESENCE.items() if q is target),None)
                if not target or not target_state or target.get('dimension',0)!=p.get('dimension',0) or not w.near(s,target_state,3):raise ValueError('Anahtar vereceğin oyuncu aynı yerde ve 3 metre içinde olmalı.')
            if path=='/api/character/country' and values.get('country') is not None:
                uid,p,s=actor(token,values);return country(uid,p,values['country']),None
            if path=='/api/account/save' and p and 'country' in values:
                # An account email edit cannot bypass the paid character policy.
                if values['country']!=commands.country(p['char_id']):raise ValueError('Ülkeni /ulkesec panelinden değiştir; ilk 2 değişiklik ücretsiz, sonrası $1.000.000.')
            if path=='/api/chat/send' and p:
                api.authenticated61(token);api.require_client61(token,values)
                chat_guard(p,str(values.get('message','')).strip())
                parts=str(values.get('message','')).strip().split()
                if len(parts)>1 and parts[0].lower()=='/addint':
                    keys=list(city.INTERIOR_TYPES)
                    if parts[1].isdigit():
                        admin(p['user_id'],p,s);parts[1]=keys[staff.number(parts[1],1,len(keys))-1]
                        values={**values,'message':' '.join(parts)}
                    elif len(parts)>=5 and parts[2].isdigit() and int(parts[2])<50000 and parts[3].isdigit():
                        admin(p['user_id'],p,s);kind=keys[staff.number(parts[2],1,len(keys))-1]
                        if parts[1]!=kind:raise ValueError('Şablon ID bu türle eşleşmiyor. /intlist ile yüklü şablonları gör.')
                        values={**values,'message':' '.join([parts[0],parts[1],*parts[3:]])}
            if path=='/api/gta/sync' and p and p.get('admin_duty') and staff.rank(p['user_id'])>=2:p['godmode']=True
            if path=='/api/tuning/buy' and values.get('part')=='wheels' and p:
                vid,_=w.occupation(p['char_id'])
                if vid and w.vehicle(vid)['model']=='pavtofas':raise ValueError('Doğan özel jant geometrisi kullanır. Stok jant takılamaz; ücret kesilmedi.')
            result,cookie=previous(path,values,token)
            p,s=api.PRESENCE.get(token),api.GTA_STATE.get(token)
            if path=='/api/gta/sync' and p and s and p.get('sleep72'):
                run=p['sleep72']
                if run['life']!=p.get('life_id') or run['dimension']!=p.get('dimension') or not w.near(s,run['pose'],.75):p.pop('sleep72',None)
            if result.get('success') and p and s and path in ('/api/gta/sync','/api/properties/list'):
                result['property72']=property_view(p,s)
                result['rested72']=p.get('rested72',0)
            if path=='/api/character/country' and p and result.get('success'):
                with api.database() as db:r=db.execute('SELECT changes FROM pn_country72 WHERE char_id=?',(p['char_id'],)).fetchone()
                used=r[0] if r else 0;result.update(free_changes=max(0,2-used),next_price=1000000 if used>=2 else 0)
            return result,cookie
    w.public=public;traffic.register=register72;commands.command=custom;staff.command=staff_command;api.dispatch=dispatch
    api.property_view72=property_view;api.city72_installed=True
    return api
