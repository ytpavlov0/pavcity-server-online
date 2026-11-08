"""Additive PC gameplay fixes. No schemas, credentials or server startup on import."""
import copy, importlib, math, secrets, time

# Verified mounted DLCList lacks mpLuxe2/mpHeist. Retain old records/entitlements.
MISSING_MODELS = {'t20': 'mpLuxe2', 'kuruma': 'mpHeist'}
def availability(model):
    pack = MISSING_MODELS.get(model)
    return dict(available=not pack, unavailable_reason=(f'{model.upper()} için {pack} model paketi yüklü değil. Araç kaydın korunuyor.' if pack else ''))

def install(api):
    if getattr(api, 'gameplay33_installed', False): return api
    world = api.world
    inv = importlib.import_module(api.__package__+'.pn_inventory')
    commands = importlib.import_module(api.__package__+'.pn_commands')
    city = importlib.import_module(api.__package__+'.pn_city')
    from pathlib import Path
    import json
    office=json.loads((Path(__file__).parent/'office208.json').read_text())
    city.INTERIOR_TYPES['office']=dict(name='Ofis',**office['target'])
    market=json.loads((Path(__file__).parent/'market210.json').read_text())
    city.INTERIOR_TYPES['market']=dict(name='Market',**market['target'])
    old_city = city.dispatch
    previous, old_world, old_rows, old_cmd, old_inv, old_sample = api.dispatch, world.dispatch, world.rows, commands.command, inv.dispatch, inv.sample
    def require_model(model):
        info = availability(model)
        if not info['available']: raise ValueError(info['unavailable_reason'])
    def city_dispatch(path,uid,token,v,p,s,presences):
        return old_city(path,uid,token,v,p,s,presences)
    def command(cmd, args, uid, p, state, presences):
        if cmd == '/donatearacver' and len(args) == 2:
            require_model(str(args[1]).lower())
        return old_cmd(cmd, args, uid, p, state, presences)
    def rows(state):
        return [r for r in old_rows(state) if availability(r['model'])['available']]
    def vehicles(path, uid, token, payload, p, state, presences):
        action = path.rsplit('/', 1)[-1]
        if action in ('spawn', 'buy'): require_model(str(payload.get('model','')).lower())
        if action == 'donate-claim':
            with world.database() as db:
                r = db.execute('SELECT model,vehicle_id FROM pn_donate_vehicles WHERE id=? AND user_id=?',(payload.get('id'),uid)).fetchone()
            if r and not r['vehicle_id']: require_model(r['model'])
        if action in ('retrieve', 'enter'):
            with world.database() as db:r=db.execute('SELECT model FROM pn_vehicles WHERE id=?',(payload.get('id'),)).fetchone()
            if r: require_model(r['model'])
        result = old_world(path, uid, token, payload, p, state, presences)
        if 'catalog' in result:
            result = dict(result, catalog=[dict(v, **availability(v['model'])) for v in result['catalog']])
        if action == 'garage' and 'vehicles' in result:
            result = dict(result, vehicles=[dict(v, **availability(v['model'])) for v in result['vehicles']])
        return result
    def cancel(p):
        p.pop('inventory_action',None); p.pop('activity',None)
    def invalid(p,s,task):
        elapsed=max(0,time.time()-task['started'])
        return (p.get('life_id',0)!=task['life'] or p.get('dimension',0)!=task['dimension'] or
                world.occupation(p['char_id'])[0] or s.get('vehicle_id') or p.get('health',200)<=100 or
                p.get('cuffed') or p.get('restrained') or task['item'][5:] not in p['loadout']['owned'] or p['loadout']['selected']!=task['slot'] or
                abs(s['z']-task['position']['z'])>2.5 or not world.near(s,task['position'],min(14,elapsed*3.1+1.5)))
    def receipt(p, identifier):
        r=p.get('reload33_receipts',{}).get(identifier)
        return r if r and time.time()-r['at']<60 else None
    def inventory(path,uid,token,payload,p,s):
        world.live(p,s)
        action=path.rsplit('/',1)[-1];inv.load(p)
        item=payload.get('item');task=p.get('inventory_action')
        if action=='slots' and isinstance(item,str) and item.startswith('ammo_'):
            gun=item[5:];idx=payload.get('index');load=p['loadout'];total=load['owned'].get(gun,0);clip=inv.view(p)['clip'] if load['selected']==inv.WEAPONS.get(gun,{}).get('slot') else load.get('clips',{}).get(gun,0)
            if type(idx)is not int or not 0<=idx<5 or gun not in inv.WEAPONS or gun not in load['owned'] or (not load.get('stock',{}).get(item,0) and total<=clip):raise ValueError('Bu silah için mermi paketi veya yedek mermin olmalı.')
            slots=list(load.get('quickslots',['pistol','water','food','smg',None]))
            if item in slots:slots[slots.index(item)]=slots[idx]
            slots[idx]=item;load['quickslots']=slots;inv.persist(p);return dict(success=True,loadout=inv.view(p))
        if action=='quick-use':
            idx=payload.get('index');slots=p['loadout'].get('quickslots',[])
            key=slots[idx-1] if type(idx)is int and 1<=idx<=5 and idx<=len(slots) else None
            if isinstance(key,str) and key.startswith('ammo_'):
                return dict(success=True,package=key,loadout=inv.view(p))
        if action=='use-start' and isinstance(item,str) and item.startswith('ammo_'):
            world.live(p,s);gun=item[5:];load=p['loadout'];info=inv.view(p)
            if gun not in inv.WEAPONS or gun not in load['owned'] or load['selected']!=inv.WEAPONS[gun]['slot']:raise ValueError('Bu merminin silahını eline al.')
            if task or p.get('elevator176_ready') or p.get('cuffed') or p.get('restrained') or world.occupation(p['char_id'])[0] or s.get('vehicle_id'):raise ValueError('Şarjör için yaya ve serbest olmalısın; devam eden işlemi bitir.')
            if info['clip']>=info['clip_capacity']:raise ValueError('Şarjörün zaten dolu.')
            if info['ammo']<=info['clip'] and not load.get('stock',{}).get(item,0):raise ValueError('Yedek mermin veya uyumlu mermi paketin yok.')
            now=time.time();identifier=secrets.token_urlsafe(18);p['inventory_action']=dict(id=identifier,item=item,until=now+3,duration=3,started=now,life=p.get('life_id',0),dimension=p.get('dimension',0),position={k:s[k]for k in ('x','y','z')},slot=load['selected'],reload33=True)
            p['activity']=dict(kind='reload',until=now+3)
            return dict(success=True,action_id=identifier,duration=3,kind='reload',walking=True)
        if action=='use-finish':
            identifier=payload.get('action_id');done=receipt(p,identifier)
            if done:return dict(success=True,already_finished=True,loadout=inv.view(p),notice='Şarjör daha önce yüklendi.')
            if task and task.get('reload33'):
                if identifier!=task['id']:raise ValueError('İşlem kimliği eşleşmedi.')
                now=time.time()
                if invalid(p,s,task) or now>task['until']+10:
                    cancel(p);raise ValueError('Şarjör işlemi iptal edildi; mermi harcanmadı.')
                if now<task['until']:raise ValueError('Şarjör henüz hazırlanmadı.')
                gun=task['item'][5:];load=copy.deepcopy(p['loadout']);capacity=inv.clip_capacity(gun);total=load['owned'][gun];clip=min(load.get('clips',{}).get(gun,capacity),total,capacity);reserve=max(0,total-clip);stock=load.setdefault('stock',{});used=0
                if reserve<capacity-clip and stock.get(task['item'],0)>0:
                    added=min(capacity,999-total)
                    if added:total+=added;reserve+=added;stock[task['item']]-=1;used=1
                    if not stock.get(task['item']):stock.pop(task['item'],None)
                if reserve<=0:
                    cancel(p);raise ValueError('Yedek mermi kalmadı; paket harcanmadı.')
                load['owned'][gun]=total;load.setdefault('clips',{})[gun]=min(capacity,total);version=p['loadout_version']+1
                with world.database() as db:
                    db.execute('UPDATE pn_loadout SET state=?,version=? WHERE char_id=?',(__import__('json').dumps(load),version,p['char_id']))
                    world.audit(db,uid,'reload33',dict(char_id=p['char_id'],gun=gun,clip=load['clips'][gun],total=total,package_used=used))
                p.update(loadout=load,loadout_version=version,weapon_ready_at=now+1);cancel(p)
                receipts={k:v for k,v in p.get('reload33_receipts',{}).items()if now-v['at']<60};receipts[identifier]={'at':now};p['reload33_receipts']=dict(list(receipts.items())[-8:])
                return dict(success=True,loadout=inv.view(p),notice='Şarjör yüklendi.',package_used=used)
        if action in ('equip','quick-use') and task and task.get('reload33'):cancel(p)
        return old_inv(path,uid,token,payload,p,s)
    def sample(p,payload):
        info=inv.view(p);packet=dict(payload)
        # Magazine increases belong only to the timed server commit, never native auto-reload.
        if type(packet.get('clip'))is int and packet['clip']>info['clip']:packet['clip']=info['clip']
        task=p.get('inventory_action')
        if task and task.get('reload33') and (packet.get('weapon',info['weapon'])!=info['weapon'] or type(packet.get('ammo'))is int and packet['ammo']<info['ammo']):cancel(p)
        return old_sample(p,packet)
    def dispatch(path,payload,token):
        with api.LOCK:
            result,cookie=previous(path,payload,token)
            p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
            if p and path=='/api/gta/join' and result.get('success'):
                p['client_platform']='mobile' if payload.get('client_platform')=='mobile' else 'desktop'
            if p and s and path=='/api/gta/sync' and result.get('success'):
                task=p.get('inventory_action')
                if task and task.get('reload33') and invalid(p,s,task):cancel(p);result=dict(result,reload_cancelled=True)
                byid={v['char_id']:v.get('client_platform','desktop')for v in api.PRESENCE.values()}
                result=dict(result,players=[dict(v,client_platform=byid.get(v.get('char_id'),'desktop'))for v in result.get('players',[])])
            return result,cookie
    commands.command=command;city.dispatch=city_dispatch;world.rows=rows;world.dispatch=vehicles;inv.dispatch=inventory;inv.sample=sample;api.dispatch=dispatch;api.gameplay33_installed=True
    return api
