"""Faction-owned fleet: treasury purchase, fixed depot, member/duty access."""
import importlib,json,secrets,time

CATALOG={'police': [('police','Devriye',65000)],'medical':[('ambulance','Ambulans',70000)],
 'legal':[('burrito3','İşletme minibüsü',40000),('blista','Hizmet aracı',25000)],
 'illegal':[('sultan','Birlik aracı',60000),('burrito3','Birlik minibüsü',40000)]}

def install(api):
    if getattr(api,'fleet69_installed',False):return api
    rp=importlib.import_module(api.__package__+'.pn_roleplay');w=api.world
    old_action,old_view,old_world=rp.faction_action,rp.faction_view,w.dispatch
    with api.database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pn_faction_depot69(faction_id INTEGER PRIMARY KEY,anchor TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS pn_faction_fleet69(vehicle_id INTEGER PRIMARY KEY,faction_id INTEGER NOT NULL)')
        db.execute('CREATE TRIGGER IF NOT EXISTS pn_fleet69_removed AFTER DELETE ON pn_vehicles BEGIN DELETE FROM pn_faction_fleet69 WHERE vehicle_id=OLD.id; END')

    def allowed(db,cid,p,fid):
        m=rp.membership(db,cid)
        if not m or m['faction_id']!=fid:raise ValueError('Bu araç başka birliğe ait.')
        if m['kind'] in ('police','medical'):
            duty=db.execute('SELECT faction_id,min_rank FROM pn_faction_duty WHERE id=?',(p.get('faction_duty',0),)).fetchone()
            if not duty or duty['faction_id']!=fid or m['rank']>duty['min_rank']:raise ValueError('Resmî birlik aracını kullanmak için yetkili görevde olmalısın.')
        return m

    def view(db,cid):
        result=old_view(db,cid);m=result['member']
        if m:
            row=db.execute('SELECT anchor FROM pn_faction_depot69 WHERE faction_id=?',(m['faction_id'],)).fetchone()
            result['depot']=json.loads(row[0]) if row else None
            result['fleet_catalog']=[dict(model=model,name=name,price=price) for model,name,price in CATALOG[m['kind']] if model in w.SPAWN_MODELS]
            fleet={r[0] for r in db.execute('SELECT vehicle_id FROM pn_faction_fleet69 WHERE faction_id=?',(m['faction_id'],))}
            for car in result['vehicles']:car['fleet']=car['id'] in fleet
        return result

    def action(db,verb,uid,cid,v,p,s,presences,releases):
        if verb=='duty' and p.get('faction_duty') and db.execute('SELECT 1 FROM pn_faction_fleet69 WHERE vehicle_id=?',(w.occupation(cid)[0],)).fetchone():
            raise ValueError('Görevden çıkmadan önce filo aracından in.')
        if verb in ('rank','duty-delete'):
            targets=[v.get('char_id')] if verb=='rank' else [x['char_id'] for x in presences.values() if x.get('faction_duty')==v.get('point')]
            if any(db.execute('SELECT 1 FROM pn_faction_fleet69 WHERE vehicle_id=?',(w.occupation(target)[0],)).fetchone() for target in targets):
                raise ValueError('Görev yetkisini değiştirmeden önce ilgili üye filo aracından inmeli.')
        if verb=='vehicle-unshare' and db.execute('SELECT 1 FROM pn_faction_fleet69 WHERE vehicle_id=?',(v.get('vehicle_id'),)).fetchone():
            raise ValueError('Birlik kasasından alınan araç kişisel paylaşımdan çıkarılamaz.')
        if verb not in ('depot-set','fleet-buy','fleet-retrieve','fleet-store'):
            return old_action(db,verb,uid,cid,v,p,s,presences,releases)
        m=rp.membership(db,cid)
        if not m:raise ValueError('Birlik üyesi değilsin.')
        fid=m['faction_id']
        if p.get('dimension',0) or s.get('vehicle_id') or w.occupation(cid)[0]:raise ValueError('Birlik garajını dışarıda ve yaya kullan.')
        depot=db.execute('SELECT anchor FROM pn_faction_depot69 WHERE faction_id=?',(fid,)).fetchone()
        if verb=='depot-set':
            rp.lead(db,cid)
            if db.execute('SELECT 1 FROM pn_faction_fleet69 WHERE faction_id=?',(fid,)).fetchone():raise ValueError('Araç satın alındıktan sonra filo parkı taşınamaz.')
            anchor={k:s[k] for k in ('x','y','z','heading')}
            db.execute('INSERT OR REPLACE INTO pn_faction_depot69 VALUES(?,?)',(fid,json.dumps(anchor)))
        else:
            if not depot:raise ValueError('Önce lider dışarıda bir filo parkı belirlemeli.')
            anchor=json.loads(depot[0])
            if not w.near(s,anchor,20):raise ValueError('Birlik filo parkına yaklaş (20 m).')
            if verb=='fleet-buy':
                rp.lead(db,cid)
                entry=next((x for x in CATALOG[m['kind']] if x[0]==v.get('model') and x[0] in w.SPAWN_MODELS),None)
                if not entry:raise ValueError('Bu birlik türü için desteklenen aracı seç.')
                if db.execute('SELECT count(*) FROM pn_faction_fleet69 WHERE faction_id=?',(fid,)).fetchone()[0]>=3:raise ValueError('Birlik filosu en fazla 3 araç olabilir.')
                model,name,price=entry
                if not db.execute('UPDATE pn_factions SET bank=bank-? WHERE id=? AND bank>=?',(price,fid,price)).rowcount:raise ValueError('Birlik kasası yetersiz.')
                fields=dict(anchor,rx=0,ry=0,rz=anchor['heading'],vx=0,vy=0,vz=0,body=1000,fuel=100,km=0,engine=False)
                vid=db.execute('INSERT INTO pn_vehicles(owner,model,plate,locked,active,state,updated) VALUES(0,?,?,1,0,?,?)',(model,'FAC'+secrets.token_hex(2).upper(),json.dumps(fields),time.time())).lastrowid
                db.execute('INSERT INTO pn_faction_vehicles VALUES(?,?,0)',(vid,fid));db.execute('INSERT INTO pn_faction_fleet69 VALUES(?,?)',(vid,fid))
                db.execute('INSERT INTO pn_vehicle_home61(vehicle_id,anchor,due) VALUES(?,?,?)',(vid,json.dumps(anchor),time.time()+2100))
                rp.ledger(db,uid,cid,'faction-fleet-buy',price,dict(faction=fid,vehicle_id=vid))
            else:
                allowed(db,cid,p,fid);vid=rp.integer(v.get('vehicle_id'))
                if not db.execute('SELECT 1 FROM pn_faction_fleet69 WHERE vehicle_id=? AND faction_id=?',(vid,fid)).fetchone():raise ValueError('Filo aracı bulunamadı.')
                row=w.vehicle(vid);old=w.VEHICLE_CACHE.get(vid,json.loads(row['state']))
                if any(car==vid for car,seat in w.SEATS):raise ValueError('Önce herkes araçtan insin.')
                if verb=='fleet-retrieve':
                    if row['active']:raise ValueError('Araç zaten dışarıda. Yeniden çıkarılamaz.')
                    at=w.spawn_location(anchor,row['model'],vid)
                    if any(time.time()-x.get('last_seen',0)<15 and w.near(x,at,3) for x in api.GTA_STATE.values()):raise ValueError('Çıkış noktası dolu. Biraz uzaklaşıp tekrar dene.')
                    fields=dict(old,**at,heading=anchor['heading'],rx=0,ry=0,rz=anchor['heading'],vx=0,vy=0,vz=0,engine=False,pose_epoch=old.get('pose_epoch',0)+1)
                    # Exact safe spawn becomes this vehicle's distinct return anchor.
                    db.execute('UPDATE pn_vehicle_home61 SET anchor=?,due=? WHERE vehicle_id=?',(json.dumps({k:fields[k] for k in ('x','y','z','heading')}),time.time()+2100,vid))
                else:
                    if not row['active'] or not w.near(s,old,7):raise ValueError('İade edilecek aracın yanına yaklaş.')
                    if sum(float(old.get(k,0))**2 for k in ('vx','vy','vz'))>1:raise ValueError('Önce aracı durdur.')
                    fields=dict(old,engine=False,vx=0,vy=0,vz=0)
                db.execute('UPDATE pn_vehicles SET active=?,locked=1,state=?,updated=? WHERE id=?',(int(verb=='fleet-retrieve'),json.dumps(fields),time.time(),vid))
                w.VEHICLE_CACHE[vid]=fields;w.SAVED_AT[vid]=time.time()
        w.audit(db,uid,'faction-'+verb,dict(char_id=cid,faction=fid))
        return dict(faction=view(db,cid),on_duty=bool(p.get('faction_duty')),notice={'depot-set':'Birlik filo parkı kaydedildi.','fleet-buy':'Araç birlik kasasından alındı ve garaja kondu.','fleet-retrieve':'Filo aracı garajdan çıkarıldı.','fleet-store':'Filo aracı garaja iade edildi.'}[verb])

    def world_dispatch(path,uid,token,v,p,s,presences):
        if path.startswith('/api/vehicles/') and v.get('id'):
            with api.database() as db:
                fleet=db.execute('SELECT faction_id FROM pn_faction_fleet69 WHERE vehicle_id=?',(v['id'],)).fetchone()
                if fleet:
                    allowed(db,p['char_id'],p,fleet['faction_id'])
                    if path.rsplit('/',1)[-1] in ('retrieve','park','break-start','break-step','break-finish'):
                        raise ValueError('Filo aracını birlik panelindeki garajdan kullan.')
        return old_world(path,uid,token,v,p,s,presences)
    rp.faction_action=action;rp.faction_view=view;w.dispatch=world_dispatch
    api.fleet69_installed=True
    return api
