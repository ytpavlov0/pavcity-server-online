"""Character-owned weapons and server-priced purchases, with persistent ammo."""
import json
import pn_world as world
WEAPONS={'pistol':{'hash':0x1B06D571,'price':7500,'ammo':24,'slot':1,'name':'Tabanca'},'smg':{'hash':0x2BE6766B,'price':22000,'ammo':90,'slot':4,'name':'SMG'}}
UNARMED=0xA2719263

def load(p):
    if 'loadout' not in p:
        with world.database() as db:
            row=db.execute('SELECT state,version FROM pn_loadout WHERE char_id=?',(p['char_id'],)).fetchone()
        p['loadout']=json.loads(row['state']) if row else {'owned':{},'selected':0}
        p['loadout_version']=row['version'] if row else 1
    return p['loadout']

def persist(p,revision=True):
    if revision:p['loadout_version']=p.get('loadout_version',1)+1
    with world.database() as db:
        db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version',(p['char_id'],json.dumps(p['loadout']),p['loadout_version']))

def view(p):
    state=load(p);key=next((k for k,v in WEAPONS.items() if v['slot']==state['selected']),None)
    return {'version':p['loadout_version'],'selected':state['selected'],'weapon':WEAPONS[key]['hash'] if key else UNARMED,'ammo':state['owned'].get(key,0),
            'weapons':[dict(key=k,owned=k in state['owned'],remaining=state['owned'].get(k,0),**v) for k,v in WEAPONS.items()]}

def sample(p,payload):
    info=view(p)
    if payload.get('weapon')!=info['weapon'] or info['weapon']==UNARMED:return
    ammo=payload.get('ammo')
    if type(ammo) is not int or not 0<=ammo<=info['ammo']:return
    key=next(k for k,v in WEAPONS.items() if v['hash']==info['weapon'])
    if p['loadout']['owned'][key]!=ammo:p['loadout']['owned'][key]=ammo;persist(p,False)

def dispatch(path,uid,token,payload,p,state):
    world.live(p,state);load(p)
    action=path.rsplit('/',1)[-1]
    if action=='list':return {'success':True,'loadout':view(p),'money':world.wallet(uid)}
    if action=='restock':
        item=payload.get('item');price={'water':100,'food':150}.get(item)
        if price is None:raise ValueError('Geçersiz tüketim eşyası.')
        if p.get(item,0)>=20:raise ValueError('Bu eşya için çanta sınırı 20 adet.')
        from pn_multiplayer import rate,save,needs
        rate(token,'inventory-restock',.5)
        updated=dict(p);updated[item]=p.get(item,0)+1
        with world.database() as db:
            if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(price,uid,price)).rowcount:raise ValueError('Yeterli paran yok.')
            world.audit(db,uid,'restock',{'char_id':p['char_id'],'item':item,'price':price})
            save(updated,state,True,db)
        p[item]=updated[item];p['saved_at']=updated['saved_at']
        return {'success':True,'needs':needs(p),'money':world.wallet(uid)}
    if action=='equip':
        slot=payload.get('slot')
        if type(slot) is not int or slot not in (0,1,4):raise ValueError('Geçersiz silah slotu.')
        key=next((k for k,v in WEAPONS.items() if v['slot']==slot),None)
        if key and key not in p['loadout']['owned']:raise ValueError('Bu slotta silahın yok. Envanterden satın al.')
        p['loadout']['selected']=slot;persist(p)
        return {'success':True,'loadout':view(p)}
    if action=='buy':
        key=payload.get('weapon');item=WEAPONS.get(key)
        if not item:raise ValueError('Geçersiz silah.')
        from pn_multiplayer import rate
        rate(token,'inventory-buy',1)
        cost=500 if key in p['loadout']['owned'] else item['price']
        updated=json.loads(json.dumps(p['loadout']));updated['owned'][key]=min(999,updated['owned'].get(key,0)+item['ammo']);version=p['loadout_version']+1
        with world.database() as db:
            if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?',(cost,uid,cost)).rowcount:raise ValueError('Yeterli paran yok.')
            db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version',(p['char_id'],json.dumps(updated),version))
            world.audit(db,uid,'weapon-buy',{'char_id':p['char_id'],'weapon':key,'price':cost})
        p['loadout']=updated;p['loadout_version']=version
        return {'success':True,'loadout':view(p),'money':world.wallet(uid),'notice':item['name']+' envanterine kaydedildi.'}
    raise ValueError('Envanter işlemi bulunamadı.')
