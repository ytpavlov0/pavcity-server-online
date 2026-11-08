"""Production work, persisted experience and safe fleet returns."""
import copy
import importlib
import json
import time

PRODUCTION = {
 'watermelon': dict(name='Çiftçilik · Karpuz', legal=True, reward=650, seconds=25,
   hub=dict(x=2447.8,y=4977.4,z=46.8), points=[dict(x=2454.1,y=4970.7,z=46.8),dict(x=2461.1,y=4963.7,z=46.8)],
   finish=dict(x=2447.8,y=4977.4,z=46.8), item='watermelon', quantity=1, required_level=1),
 'tomato': dict(name='Çiftçilik · Domates', legal=True, reward=500, seconds=20,
   hub=dict(x=1928.6,y=4806.6,z=44.5), points=[dict(x=1935.4,y=4812.4,z=44.5),dict(x=1943.0,y=4819.0,z=44.5)],
   finish=dict(x=1928.6,y=4806.6,z=44.5), item='tomato', quantity=3, required_level=1),
 'winery': dict(name='Bağcılık · Şarap üretimi', legal=True, reward=1000, seconds=35,
   hub=dict(x=-1887.3,y=2034.6,z=140.8), points=[dict(x=-1838.3,y=2055.5,z=140.9),dict(x=-1808.0,y=2065.2,z=138.5),dict(x=-1887.3,y=2034.6,z=140.8)],
   finish=dict(x=-1901.4,y=2081.4,z=140.4), item='wine', quantity=2, required_level=2),
}


def install(api):
    if getattr(api,'jobs69_installed',False):return api
    rp=importlib.import_module(api.__package__+'.pn_roleplay')
    city=importlib.import_module(api.__package__+'.pn_city')
    inv=importlib.import_module(api.__package__+'.pn_inventory')
    economy=importlib.import_module(api.__package__+'.pn_economy')
    containers=importlib.import_module(api.__package__+'.pn_containers')
    w=api.world
    old_action,old_view,old_services=rp.job_action,rp.job_view,rp.services
    old_return,old_borrow=city.return_job_car,city.borrow_job_car
    old_api=api.dispatch
    with api.database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pn_job_xp69(char_id INTEGER PRIMARY KEY,xp INTEGER NOT NULL DEFAULT 0)')
        db.execute('CREATE TABLE IF NOT EXISTS pn_work69(run TEXT PRIMARY KEY,step INTEGER NOT NULL,started REAL NOT NULL)')
    # Append markers without renumbering any existing services/NPC identity.
    original_services=old_services()
    rp.JOBS.update(copy.deepcopy(PRODUCTION))
    for key,num,name,kg,color in [('watermelon',6901,'Karpuz',2,'#83b24d'),('tomato',6902,'Domates',.25,'#ed684e'),('wine',6903,'Şişelenmiş şarap',.75,'#ba8bca')]:
        economy.PRODUCTS[key]=dict(id=num,name=name,kg=kg,price=0,color=color,icon='14',kind='material')
    def services():
        return original_services+[dict(id=6901+i,kind='job',name=j['name'],job=k,sprite=478,color=2,radius=5,**j['hub']) for i,(k,j) in enumerate(PRODUCTION.items())]
    rp.services=services

    def progression(db,cid):
        row=db.execute('SELECT xp FROM pn_job_xp69 WHERE char_id=?',(cid,)).fetchone()
        xp=row[0] if row else 0
        thresholds=[0,300,900,1800,3000]
        level=sum(xp>=n for n in thresholds)
        return dict(xp=xp,level=level,next_xp=thresholds[level] if level<5 else None)

    def work_valid(p,s,target):
        return (p.get('health',0)>100 and not p.get('dimension',0) and not p.get('admin_duty')
                and time.time()-min(p.get('last_seen',0),s.get('last_seen',0))<=10
                and not p.get('fly') and not s.get('vehicle_id') and not w.occupation(p['char_id'])[0]
                and abs(s.get('speed',0))<=.5 and rp.near(s,target,4))

    def view(row,target_state=None):
        result=old_view(row,target_state)
        if row and row['job'] in PRODUCTION:
            with api.database() as db:
                work=db.execute('SELECT * FROM pn_work69 WHERE run=? AND step=?',(row['id'],row['step'])).fetchone()
                result['progression']=progression(db,row['char_id'])
            job=PRODUCTION[row['job']]
            result.update(production=True,work_started=bool(work),ready_at=work['started']+job['seconds'] if work else None,
                instruction='İşaretin 4 metre içinde yaya dur. Çalışmayı başlat, süre bitene kadar burada kal; sonra adımı tamamla.')
            result['step_title']=('Ürünleri alıcıya teslim et' if row['step']==len(job['points']) else
                (['Üzüm topla','Üzüm topla','Presle ve şişele'][row['step']] if row['job']=='winery' else 'Ürün topla · '+str(row['step']+1)))
        return result

    def stock(db,p,changes):
        updated=copy.deepcopy(inv.load(p));items=updated.setdefault('stock',{})
        weight=containers.weight(containers.personal(p))
        for key,qty in changes.items():
            value=items.get(key,0)+qty
            if value<0:raise ValueError('Üretim veya teslimat için gereken ürün çantanda eksik.')
            if value>20:raise ValueError('Bu üründen en fazla 20 adet taşıyabilirsin.')
            weight+=economy.PRODUCTS[key]['kg']*qty
            if value:items[key]=value
            else:items.pop(key,None)
        if weight>30:raise ValueError('Çantanda üretim için yeterli yer yok.')
        p['loadout_version']=economy.stock_save(db,p,updated);p['loadout']=updated

    def action(db,verb,uid,cid,v,state,p):
        row=db.execute('SELECT * FROM pn_job_runs WHERE char_id=? AND completed IS NULL',(cid,)).fetchone()
        key=row['job'] if row else v.get('job')
        if verb=='start' and key in PRODUCTION:
            if progression(db,cid)['level']<PRODUCTION[key]['required_level']:
                raise ValueError('Şarap üretimi için meslek seviyesi 2 gerekli. Tamamlanan işlerden deneyim kazan.')
            if state.get('vehicle_id') or w.occupation(cid)[0]:raise ValueError('Üretim mesleğine yaya başla.')
        if key in PRODUCTION and verb in ('begin-work','complete-step'):
            if not row or row['id']!=v.get('run'):raise ValueError('Aktif üretim görevi bulunamadı.')
            job=PRODUCTION[key];current=view(row);now=time.time()
            if now-row['started']>3600:raise ValueError('Görev süresi doldu. İptal edip yeniden başla.')
            if not work_valid(p,state,current['target']):raise ValueError('Çalışmak için işarete yaya yaklaş ve dur.')
            work=db.execute('SELECT * FROM pn_work69 WHERE run=? AND step=?',(row['id'],row['step'])).fetchone()
            if verb=='begin-work':
                if not work:db.execute('INSERT OR REPLACE INTO pn_work69 VALUES(?,?,?)',(row['id'],row['step'],now))
                return dict(active=view(row),notice='Çalışma başladı. Hareket edersen süre sıfırlanır.')
            if not work or now-work['started']<job['seconds']:
                raise ValueError('Önce çalışmayı başlat ve işaretin içinde sürenin dolmasını bekle.')
            end=row['step']==len(job['points'])
            if key=='winery':
                changes={'wine':-2} if end else {'grape':2} if row['step']<2 else {'grape':-4,'wine':2}
            else:changes={job['item']:-(job['quantity']*len(job['points'])) if end else job['quantity']}
            stock(db,p,changes)
            if end:
                db.execute('UPDATE pn_job_runs SET completed=?,paid=? WHERE id=? AND completed IS NULL',(now,job['reward'],row['id']))
                db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?',(job['reward'],uid))
                db.execute('INSERT INTO pn_job_xp69 VALUES(?,100) ON CONFLICT(char_id) DO UPDATE SET xp=xp+100',(cid,))
                rp.ledger(db,uid,cid,'job-reward',job['reward'],dict(job=key,run=row['id']))
            else:db.execute('UPDATE pn_job_runs SET step=step+1,step_at=? WHERE id=?',(now,row['id']))
            db.execute('DELETE FROM pn_work69 WHERE run=?',(row['id'],))
            current=db.execute('SELECT * FROM pn_job_runs WHERE id=? AND completed IS NULL',(row['id'],)).fetchone()
            return dict(active=view(current),money=rp.bank_view(db,uid)['cash'],progression=progression(db,cid),
                notice=('Teslimat tamamlandı · $'+str(job['reward'])+' · +100 deneyim') if end else 'Üretim adımı tamamlandı. Sıradaki noktaya git.')
        result=old_action(db,verb,uid,cid,v,state,p)
        if verb=='complete-step' and row and result.get('active') is None:
            db.execute('INSERT INTO pn_job_xp69 VALUES(?,100) ON CONFLICT(char_id) DO UPDATE SET xp=xp+100',(cid,))
        if verb=='cancel' and row:db.execute('DELETE FROM pn_work69 WHERE run=?',(row['id'],))
        result['progression']=progression(db,cid)
        return result

    def borrow(db,key,cid):
        if db.execute('SELECT 1 FROM pn_job_vehicles WHERE borrower=?',(cid,)).fetchone():
            raise ValueError('Önce önceki meslek aracını iade et.')
        return old_borrow(db,key,cid)

    def return_car(db,cid):
        ids=[r[0] for r in db.execute('SELECT vehicle_id FROM pn_job_vehicles WHERE borrower=?',(cid,))]
        old_return(db,cid)
        for vid in ids:db.execute('UPDATE pn_vehicles SET locked=1 WHERE id=?',(vid,))

    def tick_fleet():
        import online_engine
        now=time.time();key=online_engine.DB_PATH
        if now-city.FLEET_CHECK.get(key,0)<3:return
        city.FLEET_CHECK[key]=now
        with api.database() as db:
            rows=db.execute('SELECT j.*,v.state FROM pn_job_vehicles j JOIN pn_vehicles v ON v.id=j.vehicle_id').fetchall()
            for row in rows:
                vid=row['vehicle_id'];cid=row['borrower']
                if cid:
                    run=db.execute('SELECT started FROM pn_job_runs WHERE char_id=? AND completed IS NULL',(cid,)).fetchone()
                    online=any(p['char_id']==cid and now-p['last_seen']<30 for p in api.PRESENCE.values())
                    absent=(key,vid)
                    if online:city.FLEET_ABSENT.pop(absent,None)
                    else:city.FLEET_ABSENT.setdefault(absent,now)
                    if not run or now-run['started']>3600 or now-city.FLEET_ABSENT.get(absent,now)>120:
                        db.execute('UPDATE pn_job_runs SET completed=? WHERE char_id=? AND completed IS NULL',(now,cid))
                        return_car(db,cid)
                    continue
                if not row['return_at'] or row['return_at']>now or any(v==vid for v,s in w.SEATS):continue
                target=city.parked(row['job'],row['slot'])
                if any(now-s.get('last_seen',0)<15 and not s.get('dimension',0) and w.near(s,target,8) for s in api.GTA_STATE.values()):continue
                occupied=False
                for other in w.rows(target):
                    if other['id']!=vid and w.near(w.VEHICLE_CACHE.get(other['id'],json.loads(other['state'])),target,4.8):occupied=True;break
                if occupied:continue
                old=w.VEHICLE_CACHE.get(vid,json.loads(row['state']))
                fields=dict(old,**target);fields['pose_epoch']=old.get('pose_epoch',0)+1;fields['repair_epoch']=old.get('repair_epoch',0)+1
                db.execute('UPDATE pn_vehicles SET active=1,locked=1,state=?,updated=? WHERE id=?',(json.dumps(fields),now,vid))
                db.execute('UPDATE pn_job_vehicles SET return_at=0 WHERE vehicle_id=?',(vid,))
                w.VEHICLE_CACHE[vid]=fields;w.SAVED_AT[vid]=now
                break # At most one vehicle per tick; never pile up a returning fleet.

    def dispatch(path,payload,token):
        with api.LOCK:
            before=api.PRESENCE.get(token,{}).get('char_id')
            result=old_api(path,payload,token)
            if path in ('/api/gta/join','/api/lobby/leave') and result[0].get('success'):
                cid=before or api.PRESENCE.get(token,{}).get('char_id')
                if cid:
                    with api.database() as db:db.execute('DELETE FROM pn_work69 WHERE run IN (SELECT id FROM pn_job_runs WHERE char_id=?)',(cid,))
            if path=='/api/gta/sync' and result[0].get('success'):
                p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
                if p and s:
                    with api.database() as db:
                        row=db.execute('SELECT r.* FROM pn_job_runs r JOIN pn_work69 w ON w.run=r.id WHERE r.char_id=? AND r.completed IS NULL',(p['char_id'],)).fetchone()
                        if row and row['job'] in PRODUCTION:
                            job=PRODUCTION[row['job']];target=job['points'][row['step']] if row['step']<len(job['points']) else job['finish']
                            if not work_valid(p,s,target):db.execute('DELETE FROM pn_work69 WHERE run=?',(row['id'],))
            return result
    rp.job_action=action;rp.job_view=view
    city.borrow_job_car=borrow;city.return_job_car=return_car;city.tick_fleet=tick_fleet
    api.dispatch=dispatch;api.jobs69_installed=True
    return api
