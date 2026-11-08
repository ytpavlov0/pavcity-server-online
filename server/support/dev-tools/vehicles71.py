"""Keep accessory responses consistent with live seats; verified stock traffic."""
from pathlib import Path
import json,time
R=Path(__file__).resolve().parents[2]
def install(api):
    if getattr(api,'vehicles71_installed',False):return api
    import gameplay_v29.pn_traffic as traffic
    import gameplay_v29.pn_commands as commands
    import gameplay_v29.pn_phone as phone
    import gameplay_v29.pn_economy as economy
    w=api.world;original=w.public;command=commands.command
    shops=[dict(id=2120,kind='tuning',name='LS Customs · La Mesa',sprite=72,color=2,radius=10,x=731.1,y=-1088.8,z=22.2),dict(id=2121,kind='tuning',name='LS Customs · Havalimanı',sprite=72,color=2,radius=10,x=-1145.0,y=-1992.0,z=13.2)]
    for shop in shops:
        if not any(x['id']==shop['id'] for x in economy.STORES):economy.STORES.append(shop)
        if not any(x['id']==shop['id'] for x in w.SERVICES):w.SERVICES.append(shop)
    with api.database() as db:
        for shop in shops:db.execute('INSERT OR IGNORE INTO pn_places70(code,name,pose,created_by) VALUES(?,?,?,0)',('service:'+str(shop['id']),shop['name'],json.dumps({k:shop.get(k,0) for k in ('x','y','z','heading')})))
    models=json.loads((R/'backups/tofas71-checks/road-models.json').read_text())['models']
    traffic.ROAD_MODELS.update(models)
    traffic.HASHES.update({traffic.joaat(model):model for model in models})
    def public(row):
        data=original(row)
        data['driver']=w.SEATS.get((row['id'],-1),{}).get('char_id',0)
        return data
    def custom(cmd,args,uid,p,s,peers):
        if cmd in ('/mekanikler','/mkenaikler'):
            if args:raise ValueError('Kullanım: /mekanikler')
            rows=[];seen=set();now=time.time()
            with api.database() as db:
                ids={r[0] for r in db.execute('SELECT char_id FROM pn_mechanic70')}
                for other in peers.values() if isinstance(peers,dict) else peers:
                    cid=other.get('char_id')
                    if cid not in ids or cid in seen or now-other.get('last_seen',0)>30 or other.get('world')!='gta':continue
                    seen.add(cid)
                    number=db.execute('SELECT number FROM pn_phone_numbers WHERE char_id=?',(cid,)).fetchone()
                    contact=str(number[0]) if number and phone.has_phone(cid) else 'Telefon yok'
                    rows.append([other['name']+' · ID '+str(other['server_id']),contact])
            return dict(success=True,info=dict(title='Şehirdeki mekanikler',rows=rows or [['Mekanik','Şu anda çevrimiçi mekanik yok.']]))
        if cmd in ('/atolyeler','/atölyeler'):
            rows=[[x['name'],f"{x['x']:.0f}, {x['y']:.0f} · F1 > Mekanikler > Atölye GPS"] for x in economy.STORES if x['kind']=='tuning']
            return dict(success=True,info=dict(title='Mekanik atölyeleri · Harita > Modifiye',rows=rows))
        return command(cmd,args,uid,p,s,peers)
    previous=api.dispatch
    def dispatch(path,payload,token):
        if path=='/api/mechanic70/start' and payload.get('part')=='wheels':
            with api.LOCK:
                api.authenticated61(token);api.require_client61(token,payload)
                import gameplay_v29.pn_roleplay as rp
                row=w.vehicle(rp.integer(payload.get('vehicle_id'),1,2147483647))
                if row['model']=='pavtofas':raise ValueError('Doğan özel jant takımını kullanır; bu modelde stok jant modifiyesi desteklenmiyor. Ücret kesilmedi.')
        return previous(path,payload,token)
    w.public=public;commands.command=custom;api.dispatch=dispatch;api.vehicles71_installed=True
    return api
