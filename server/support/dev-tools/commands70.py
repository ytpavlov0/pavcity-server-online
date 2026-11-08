"""Server-authorized places, vehicle colours and complete character stats."""
import copy
import json
import math
import time


def install(api):
    if getattr(api, 'commands70_installed', False):
        return api
    import gameplay_v29.pn_commands as commands
    import gameplay_v29.pn_admin as staff
    import gameplay_v29.pn_city as city
    import gameplay_v29.pn_roleplay as rp
    w = api.world
    old = commands.command
    with api.database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pn_places70(id INTEGER PRIMARY KEY AUTOINCREMENT,code TEXT UNIQUE,name TEXT NOT NULL,pose TEXT NOT NULL,created_by INTEGER NOT NULL)')
        seeds = [('spawn','Şehir başlangıcı',dict(x=215.7,y=-915.7,z=30.69,heading=90)),
                 ('hospital','Pillbox Hastanesi',{**w.HOSPITALS[0],'heading':0})]
        seeds += [('service:'+str(s['id']),s['name'],{k:s.get(k,0) for k in ('x','y','z','heading')}) for s in w.SERVICES]
        seeds += [('job:'+key,'Meslek · '+job['name'],{k:job['hub'].get(k,0) for k in ('x','y','z','heading')}) for key,job in rp.JOBS.items()]
        for code,name,pose in seeds:
            db.execute('INSERT OR IGNORE INTO pn_places70(code,name,pose,created_by) VALUES(?,?,?,0)',(code,name,json.dumps(pose)))

    def admin(uid,p,state):
        if staff.rank(uid)<2 or not p.get('admin_duty'):
            raise ValueError('Bu komut için yönetici görevine gir: /aduty')
        w.live(p,state)

    def command(cmd,args,uid,p,state,presences):
        if cmd == '/stats':
            if args: raise ValueError('Kullanım: /stats')
            with api.database() as db:
                cars = list(db.execute('SELECT id,model,plate,active FROM pn_vehicles WHERE owner=? ORDER BY id',(p['char_id'],)))
            rows = [['İsim',p['name']],['Şehir ID',p['server_id']],['Karakter kaydı',p['char_id']],['Cüzdan',f'${w.wallet(uid):,}']]
            rows += [['Araç #'+str(v['id']),v['model'].upper()+' · '+v['plate']+' · '+('Dışarıda' if v['active'] else 'Garajda')] for v in cars]
            if not cars: rows.append(['Araçlar','Kayıtlı aracın yok.'])
            return dict(success=True,info=dict(title='Karakter ve araç kayıtları',rows=rows))
        if cmd in ('/gotoplace','/places','/addplace'):
            admin(uid,p,state)
            if cmd=='/places' or cmd=='/gotoplace' and not args:
                with api.database() as db:
                    rows=[[r['id'],r['name']] for r in db.execute('SELECT id,name FROM pn_places70 ORDER BY id')]
                return dict(success=True,info=dict(title='/gotoplace YER_ID · Yönetici noktaları',rows=rows))
            if cmd=='/addplace':
                name=' '.join(args).strip()
                if not 2<=len(name)<=60: raise ValueError('Kullanım: /addplace Yer adı (2–60 karakter)')
                if p.get('dimension') or w.occupation(p['char_id'])[0] or state.get('vehicle_id'):
                    raise ValueError('Noktayı dışarıda ve yaya oluştur.')
                pose={k:float(state.get(k,0)) for k in ('x','y','z','heading')}
                if not all(math.isfinite(v) for v in pose.values()): raise ValueError('Konum henüz hazır değil.')
                with api.database() as db:
                    db.execute('BEGIN IMMEDIATE')
                    id=db.execute('INSERT INTO pn_places70(name,pose,created_by) VALUES(?,?,?)',(name,json.dumps(pose),uid)).lastrowid
                    w.audit(db,uid,'addplace',dict(id=id,name=name,pose=pose))
                return dict(success=True,notice=f'Yer #{id} kaydedildi · {name}. /gotoplace {id}')
            if len(args)!=1: raise ValueError('Kullanım: /gotoplace YER_ID · Liste: /places')
            id=staff.number(args[0],1,2147483647)
            if staff.jail(p['char_id']): raise ValueError('Hapiste ışınlanma kullanılamaz.')
            if w.occupation(p['char_id'])[0] or state.get('vehicle_id'): raise ValueError('Önce araçtan in.')
            if p.get('dimension') or (p.get('property45_used') or {}).get('phase')=='pending': raise ValueError('Önce bulunduğun iç mekândan çık ve geçişi tamamla.')
            with api.database() as db:
                r=db.execute('SELECT * FROM pn_places70 WHERE id=?',(id,)).fetchone()
                if not r: raise ValueError('Yer bulunamadı. /places ile listele.')
                w.audit(db,uid,'gotoplace',dict(id=id,char_id=p['char_id']))
            result=city.teleport(p,state,json.loads(r['pose']),0)
            return dict(success=True,notice=r['name']+' konumuna gidildi.',**result)
        if cmd in ('/acolorveh','/colorveh'):
            admin(uid,p,state)
            if not 2<=len(args)<=3: raise ValueError('Kullanım: /acolorveh ARAÇ_ID ANA_RENK [İKİNCİ_RENK] · Renkler 0–160. İkinci rengin kapladığı parça modele bağlıdır.')
            vid=staff.number(args[0],1,2147483647)
            colours=[staff.number(v,0,160) for v in args[1:]]
            row=w.vehicle(vid)
            fields=copy.deepcopy(w.VEHICLE_CACHE.get(vid,json.loads(row['state'])))
            mods=fields.setdefault('mods',{})
            for key,value in zip(('primary','secondary'),colours):
                mods[key]=value
                mods.pop(key+'_rgb',None)
            with api.database() as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('INSERT INTO pn_vehicle_upgrades VALUES(?,?,1) ON CONFLICT(vehicle_id) DO UPDATE SET state=excluded.state,version=version+1',(vid,json.dumps(mods)))
                db.execute('UPDATE pn_vehicles SET state=?,updated=? WHERE id=?',(json.dumps(fields),time.time(),vid))
                w.audit(db,uid,'acolorveh',dict(vehicle_id=vid,colours=colours))
            w.VEHICLE_CACHE[vid]=fields
            w.SAVED_AT[vid]=time.time()
            return dict(success=True,notice=f'Araç #{vid} renkleri kaydedildi.',vehicle=w.public(w.vehicle(vid)))
        return old(cmd,args,uid,p,state,presences)

    commands.command=command
    previous=api.dispatch
    def dispatch(path,payload,token):
        if path=='/api/chat/send':
            parts=str(payload.get('message','')).strip().split()
            if len(parts)>1 and parts[0].lower()=='/addint':
                aliases={'ev':'apartment','daire':'apartment','apartman':'apartment','apartmen':'apartment','ofis':'office','garaj':'garage'}
                parts[1]=aliases.get(parts[1].lower(),parts[1].lower())
                payload={**payload,'message':' '.join(parts)}
        return previous(path,payload,token)
    api.dispatch=dispatch
    api.commands70_installed=True
    return api
