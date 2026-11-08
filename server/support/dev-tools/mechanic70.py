"""Persistent mechanic grants and server-timed, cancellable workshop work."""
import copy,json,time,secrets,math

def install(api):
    if getattr(api,'mechanic70_installed',False):return api
    import gameplay_v29.pn_commands as commands
    import gameplay_v29.pn_admin as staff
    import gameplay_v29.pn_economy as economy
    import gameplay_v29.pn_roleplay as rp
    w=api.world;previous=api.dispatch;old_command=commands.command;work={}
    with api.database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pn_mechanic70(char_id INTEGER PRIMARY KEY,granted_by INTEGER NOT NULL,created REAL NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS pn_mechanic_receipts70(char_id INTEGER NOT NULL,id TEXT NOT NULL,result TEXT NOT NULL,PRIMARY KEY(char_id,id))')
    def command(cmd,args,uid,p,s,peers):
        if cmd=='/mekanikver':
            if staff.rank(uid)<2 or not p.get('admin_duty'):raise ValueError('Yönetici görevinde olmalısın: /aduty')
            if not 1<=len(args)<=2:raise ValueError('Kullanım: /mekanikver OYUNCU_ID [1=ver / 0=kaldır]')
            cid=w.resolve_player_id(args[0],peers);enabled=staff.number(args[1],0,1) if len(args)>1 else 1
            with api.database() as db:
                db.execute('BEGIN IMMEDIATE')
                if enabled:db.execute('INSERT INTO pn_mechanic70 VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET granted_by=excluded.granted_by,created=excluded.created',(cid,uid,time.time()))
                else:db.execute('DELETE FROM pn_mechanic70 WHERE char_id=?',(cid,))
                w.audit(db,uid,'mechanic-grant70',dict(char_id=cid,enabled=enabled))
            if not enabled:work.pop(cid,None)
            return dict(success=True,notice='Mekanik yetkisi '+('verildi.' if enabled else 'kaldırıldı.'))
        return old_command(cmd,args,uid,p,s,peers)
    def permission(db,p):
        if not db.execute('SELECT 1 FROM pn_mechanic70 WHERE char_id=?',(p['char_id'],)).fetchone():raise ValueError('Mekanik yetkin yok. Yönetici /mekanikver ile atayabilir.')
    def eligible(p,s,vid):
        w.live(p,s)
        if p.get('dimension') or p.get('health',0)<=100 or s.get('vehicle_id') or w.occupation(p['char_id'])[0]:raise ValueError('Dışarıda, hayatta ve yaya olmalısın.')
        row=w.vehicle(vid);car=copy.deepcopy(w.VEHICLE_CACHE.get(vid,json.loads(row['state'])))
        if not row['active'] or not w.near(s,car,4):raise ValueError('Aracın 4 metre yakınına gel.')
        if any(v==vid for v,seat in w.SEATS) or car.get('engine') or math.hypot(*(car.get(k,0) for k in ('vx','vy','vz')))>.3 or s.get('speed',0)>.5:raise ValueError('Motoru kapat, araçtan in ve aracın durmasını bekle.')
        return row,car
    def action(uid,p,s,verb,v):
        cid=p['char_id'];now=time.time()
        with api.database() as db:
            permission(db,p)
            if verb=='list':return dict(success=True,vehicles=[w.public(r) for r in w.rows(s) if w.near(s,w.VEHICLE_CACHE.get(r['id'],json.loads(r['state'])),6)],options=economy.TUNING,repair_fee=250,duration=12,workshops=[x for x in economy.STORES if x['kind']=='tuning'])
            if verb=='cancel':work.pop(cid,None);return dict(success=True,notice='Çalışma iptal edildi.')
            if verb=='start':
                vid=rp.integer(v.get('vehicle_id'),1,2147483647);row,car=eligible(p,s,vid)
                if cid in work:raise ValueError('Önce devam eden çalışmayı tamamla veya iptal et.')
                part=v.get('part','repair');value=None;fee=250
                if part!='repair':
                    if part not in economy.TUNING:raise ValueError('Geçersiz modifiye.')
                    if row['owner']!=cid and not db.execute('SELECT 1 FROM pn_vehicle_access WHERE vehicle_id=? AND char_id=?',(vid,cid)).fetchone():raise ValueError('Modifiye için sahibinin araç anahtarını sana vermesi gerekir.')
                    if not any(w.near(s,x,x['radius']) and w.near(car,x,x['radius']) for x in economy.STORES if x['kind']=='tuning'):raise ValueError('Modifiyeyi mekanik atölyesinde yap.')
                    opt=economy.TUNING[part];value=rp.integer(v.get('value'),opt['min'],opt['max']);fee=opt['price']
                if w.wallet(uid)<fee:raise ValueError(f'Malzeme için ${fee} gerekiyor. Ücret yalnız tamamlandığında kesilir.')
                item=dict(id=secrets.token_hex(16),vehicle_id=vid,part=part,value=value,fee=fee,started=now,life=p.get('life_id'),source={k:s[k] for k in ('x','y','z')},pose_epoch=car.get('pose_epoch',0),owner=row['owner'])
                work[cid]=item
                return dict(success=True,work={**item,'duration':12},notice='Çalışma başladı; 12 saniye aracın yanında bekle.')
            if verb!='finish':raise ValueError('Geçersiz mekanik işlemi.')
            id=str(v.get('id',''))
            receipt=db.execute('SELECT result FROM pn_mechanic_receipts70 WHERE char_id=? AND id=?',(cid,id)).fetchone()
            if receipt:return json.loads(receipt['result'])
            item=work.get(cid)
            if not item or item['id']!=id:raise ValueError('Çalışma iptal olmuş; yeniden başlat.')
            row,car=eligible(p,s,item['vehicle_id'])
            if p.get('life_id')!=item['life'] or now-item['started']>45 or not w.near(s,item['source'],1) or car.get('pose_epoch',0)!=item['pose_epoch'] or row['owner']!=item['owner']:work.pop(cid,None);raise ValueError('Konum, araç veya karakter değişti; çalışma iptal edildi.')
            if now-item['started']<12:raise ValueError('Çalışma henüz bitmedi.')
            if item['part']!='repair' and row['owner']!=cid and not db.execute('SELECT 1 FROM pn_vehicle_access WHERE vehicle_id=? AND char_id=?',(row['id'],cid)).fetchone():raise ValueError('Araç anahtarı artık sende değil.')
            if not db.in_transaction:db.execute('BEGIN IMMEDIATE')
            rp.debit(db,'pn_wallet','user_id',uid,item['fee'])
            if item['part']=='repair':car.update(body=1000,repair_epoch=car.get('repair_epoch',0)+1,pose_epoch=car.get('pose_epoch',0)+1)
            else:
                car.setdefault('mods',{})[item['part']]=item['value']
                car['mods'].pop(item['part']+'_rgb',None)
                db.execute('INSERT INTO pn_vehicle_upgrades VALUES(?,?,1) ON CONFLICT(vehicle_id) DO UPDATE SET state=excluded.state,version=version+1',(row['id'],json.dumps(car['mods'])))
            db.execute('UPDATE pn_vehicles SET state=?,updated=? WHERE id=?',(json.dumps(car),now,row['id']))
            result=dict(success=True,notice=f"Araç #{row['id']} işlemi tamamlandı · ${item['fee']} malzeme.")
            db.execute('INSERT INTO pn_mechanic_receipts70 VALUES(?,?,?)',(cid,id,json.dumps(result)))
            w.audit(db,uid,'mechanic-work70',dict(vehicle=row['id'],part=item['part'],value=item['value'],fee=item['fee']))
        w.VEHICLE_CACHE[row['id']]=car;w.SAVED_AT[row['id']]=now;work.pop(cid,None)
        return result
    def dispatch(path,v,token):
        with api.LOCK:
            if path.startswith('/api/mechanic70/'):
                uid=api.authenticated61(token);p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
                if not uid or not p or not s:return dict(success=False,error='Önce şehre gir.'),None
                api.require_client61(token,v)
                return action(uid,p,s,path.rsplit('/',1)[-1],v),None
            p=api.PRESENCE.get(token)
            if p and path in ('/api/lobby/leave','/api/auth/logout'):
                work.pop(p['char_id'],None)
            if p and p['char_id'] in work and path in ('/api/inventory/use-start','/api/vehicles/enter','/api/properties/enter','/api/elevators/use'):
                raise ValueError('Önce mekanik çalışmasını tamamla veya iptal et.')
            result,cookie=previous(path,v,token)
            p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
            if p and p['char_id'] in work:
                item=work[p['char_id']]
                if path in ('/api/gta/join','/api/lobby/leave','/api/auth/logout') or not s or not w.near(s,item['source'],1) or p.get('life_id')!=item['life'] or s.get('vehicle_id') or time.time()-item['started']>45:work.pop(p['char_id'],None)
            return result,cookie
    commands.command=command;api.dispatch=dispatch;api.mechanic70_work=work;api.mechanic70_installed=True
    return api
