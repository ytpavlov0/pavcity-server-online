"""Character-owned weapons and server-priced purchases, with persistent ammo."""
import json, time, secrets
import gameplay_v29.pn_world as world
WEAPONS = {'pistol': {'hash': 453432689, 'price': 7500, 'ammo': 24, 'slot': 1, 'name': 'Tabanca'}, 'smg': {'hash': 736523883, 'price': 22000, 'ammo': 90, 'slot': 4, 'name': 'SMG'}}
ITEM_IDS = {'pistol': 101, 'smg': 102, 'water': 201, 'food': 202}
ITEM_WEIGHTS = {'pistol': 1.2, 'smg': 2.4, 'water': 0.5, 'food': 0.3}
UNARMED = 2725352035

def clip_capacity(key):
    if key not in WEAPONS:
        return 0
    v = WEAPONS.get(key, {})
    if v.get('category') == 'NULL':
        return 0
    k = str(key)
    return 1 if k in ('rpg', 'grenadelauncher', 'stungun') else 6 if 'revolver' in k else 12 if 'pistol' in k else 8 if 'shotgun' in k else 10 if 'sniper' in k else 30
from pathlib import Path
import online_engine
_catalog = Path(__file__).parent / 'weapons-v19.json'
if _catalog.exists():
    WEAPONS = json.loads(_catalog.read_text(encoding='utf8'))
    ITEM_IDS.update({k: v['id'] for k, v in WEAPONS.items()})
    ITEM_WEIGHTS.update({k: v.get('kg', 2) for k, v in WEAPONS.items()})
ITEM_IDS.update(armor=301)
ITEM_WEIGHTS.update(armor=4)

def at_shop(state, p):
    import gameplay_v29.pn_roleplay as pn_roleplay
    return not state.get('vehicle_id') and (not p.get('dimension', 0)) and any((world.near(state, shop, 5) for shop in pn_roleplay.WEAPON_SHOPS))

def load(p):
    if 'loadout' not in p:
        with world.database() as db:
            row = db.execute('SELECT state,version FROM pn_loadout WHERE char_id=?', (p['char_id'],)).fetchone()
        p['loadout'] = json.loads(row['state']) if row else {'owned': {}, 'selected': 0}
        p['loadout_version'] = row['version'] if row else 1
        repaired = False
        for key, amount in list(p['loadout'].get('owned', {}).items()):
            if key in WEAPONS and amount > 999:
                p['loadout']['owned'][key] = min(999, clip_capacity(key) * 3)
                repaired = True
        if repaired:
            persist(p)
    return p['loadout']

def persist(p, revision=True):
    if revision:
        p['loadout_version'] = p.get('loadout_version', 1) + 1
    with world.database() as db:
        db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version', (p['char_id'], json.dumps(p['loadout']), p['loadout_version']))

def view(p, full=True):
    state = load(p)
    key = next((k for k, v in WEAPONS.items() if v['slot'] == state['selected']), None)
    ammo = state['owned'].get(key, 0)
    capacity = clip_capacity(key)
    clip = max(0, min(state.get('clips', {}).get(key, capacity), capacity, ammo)) if key else 0
    return {'version': p['loadout_version'], 'selected': state['selected'], 'weapon': WEAPONS[key]['hash'] if key else UNARMED, 'ammo': ammo, 'clip_capacity': capacity, 'clip': clip, 'quickslots': state.get('quickslots', ['pistol', 'water', 'food', 'smg', None]), 'counts': {'water': p.get('water', 3), 'food': p.get('food', 3)}, 'item_ids': ITEM_IDS, 'weights': ITEM_WEIGHTS, 'stock': state.get('stock', {}), 'tints': state.get('tints', {}), 'weapons': [{**v, 'key': k, 'id': ITEM_IDS[k], 'owned': k in state['owned'], 'remaining': state['owned'].get(k, 0)} for k, v in WEAPONS.items() if full or k in state['owned']]}

def sample(p, payload):
    acknowledged = payload.get('loadout_version') == p.get('loadout_version') and payload.get('loadout_applied') == p.get('loadout_version')
    if time.time() < p.get('weapon_ready_at', 0) and (not acknowledged):
        return
    if payload.get('loadout_version', p.get('loadout_version')) != p.get('loadout_version'):
        return
    if payload.get('loadout_applied', p.get('loadout_version')) != p.get('loadout_version'):
        return
    info = view(p)
    if payload.get('weapon') != info['weapon'] or info['weapon'] == UNARMED:
        return
    ammo = payload.get('ammo')
    if type(ammo) is not int or not 0 <= ammo <= info['ammo']:
        return
    key = next((k for k, v in WEAPONS.items() if v['hash'] == info['weapon']))
    clip = payload.get('clip')
    clips = p['loadout'].setdefault('clips', {})
    changed = p['loadout']['owned'][key] != ammo
    if type(clip) is int and 0 <= clip <= min(clip_capacity(key), ammo):
        changed = changed or clips.get(key) != clip
        clips[key] = clip
        p['weapon_clip'] = clip
    p['loadout']['owned'][key] = ammo
    if changed:
        persist(p, False)

def dispatch(path, uid, token, payload, p, state):
    world.live(p, state)
    load(p)
    action = path.rsplit('/', 1)[-1]
    if action == 'use-cancel':
        task = p.get('inventory_action')
        if task and task['id'] != payload.get('action_id'):
            raise ValueError('İşlem kimliği eşleşmedi.')
        p.pop('inventory_action', None)
        p.pop('activity', None)
        return dict(success=True, notice='İşlem iptal edildi; eşyan harcanmadı.')
    if action == 'quick-use':
        index = payload.get('index')
        if type(index) is not int or not 0 <= index <= 5:
            raise ValueError('Geçersiz hızlı slot.')
        slots = p['loadout'].get('quickslots', ['pistol', 'water', 'food', 'smg', None])
        item = slots[index - 1] if index and len(slots) >= index else None
        if item in ('water', 'food') and p.get(item, 3) > 0:
            from gameplay_v29.pn_multiplayer import consume
            result = consume(token, {'item': item}, p, state)
            result.update(loadout=view(p), notice='Su içtin.' if item == 'water' else 'Sandviç yedin.')
            return result
        if item == 'armor' and p['loadout'].get('stock', {}).get('armor', 0) > 0:
            return dict(success=True, package='armor', loadout=view(p))
        key = item if item in WEAPONS and item in p['loadout']['owned'] else None
        p['loadout']['selected'] = WEAPONS[key]['slot'] if key else 0
        persist(p)
        return dict(success=True, loadout=view(p))
    if action == 'list':
        return {'success': True, 'loadout': view(p), 'money': world.wallet(uid)}
    if action == 'slots':
        index = payload.get('index')
        item = payload.get('item')
        if type(index) is not int or not 0 <= index < 5 or item not in tuple(WEAPONS) + ('water', 'food', 'armor', None):
            raise ValueError('Geçersiz hızlı slot.')
        if item in WEAPONS and item not in p['loadout']['owned']:
            raise ValueError('Bu eşyaya sahip değilsin.')
        from gameplay_v29.pn_multiplayer import rate
        rate(token, 'inventory-slots', 0.2)
        slots = list(p['loadout'].get('quickslots', ['pistol', 'water', 'food', 'smg', None]))
        if item and item in slots:
            other = slots.index(item)
            slots[other] = slots[index]
        slots[index] = item
        p['loadout']['quickslots'] = slots
        persist(p)
        return {'success': True, 'loadout': view(p)}
    if action == 'restock':
        import gameplay_v29.pn_roleplay as pn_roleplay
        if state.get('vehicle_id') or p.get('dimension', 0) or (not any((world.near(state, shop, 5) for shop in pn_roleplay.MARKETS))):
            raise ValueError('Alışveriş için market NPC yanına yaya yaklaş.')
        item = payload.get('item')
        price = {'water': 100, 'food': 150}.get(item)
        if price is None:
            raise ValueError('Geçersiz tüketim eşyası.')
        if p.get(item, 0) >= 20:
            raise ValueError('Bu eşya için çanta sınırı 20 adet.')
        from gameplay_v29.pn_multiplayer import rate, save, needs
        rate(token, 'inventory-restock', 0.5)
        updated = dict(p)
        updated[item] = p.get(item, 0) + 1
        with world.database() as db:
            if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?', (price, uid, price)).rowcount:
                raise ValueError('Yeterli paran yok.')
            world.audit(db, uid, 'restock', {'char_id': p['char_id'], 'item': item, 'price': price})
            save(updated, state, True, db)
        p[item] = updated[item]
        p['saved_at'] = updated['saved_at']
        return {'success': True, 'needs': needs(p), 'money': world.wallet(uid)}
    if action == 'equip':
        slot = payload.get('slot')
        if type(slot) is not int or slot not in (0,) + tuple((v['slot'] for v in WEAPONS.values())):
            raise ValueError('Geçersiz silah slotu.')
        key = next((k for k, v in WEAPONS.items() if v['slot'] == slot), None)
        if key and key not in p['loadout']['owned']:
            raise ValueError('Bu slotta silahın yok. Ammu-Nation mağazasından satın al.')
        p['loadout']['selected'] = slot
        persist(p)
        p['weapon_ready_at'] = time.time() + 1
        return {'success': True, 'loadout': view(p)}
    if action == 'buy':
        import gameplay_v29.pn_roleplay as pn_roleplay, gameplay_v29.pn_admin as pn_admin
        if not at_shop(state, p):
            raise ValueError('Silah satın almak için Ammu-Nation NPC yanına yaya yaklaş.')
        key = payload.get('weapon')
        item = WEAPONS.get(key)
        if not item:
            raise ValueError('Geçersiz silah.')
        from gameplay_v29.pn_multiplayer import rate
        rate(token, 'inventory-buy', 1)
        if key in p['loadout']['owned']:
            raise ValueError('Bu silaha sahipsin. Mermi paketi alıp envanterden yükle.')
        cost = item['price']
        updated = json.loads(json.dumps(p['loadout']))
        updated['owned'][key] = 0
        updated['selected'] = item['slot']
        version = p['loadout_version'] + 1
        with world.database() as db:
            if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?', (cost, uid, cost)).rowcount:
                raise ValueError('Yeterli paran yok.')
            db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version', (p['char_id'], json.dumps(updated), version))
            world.audit(db, uid, 'weapon-buy', {'char_id': p['char_id'], 'weapon': key, 'price': cost})
        p['loadout'] = updated
        p['loadout_version'] = version
        p['weapon_ready_at'] = time.time() + 1
        return {'success': True, 'loadout': view(p), 'money': world.wallet(uid), 'notice': item['name'] + ' envanterine kaydedildi.'}
    if action == 'supply':
        if not at_shop(state, p):
            raise ValueError('Malzeme için silahçı NPC yanına yaya yaklaş.')
        key = payload.get('item')
        gun = WEAPONS.get(str(key)[5:]) if str(key).startswith('ammo_') else None
        if key != 'armor' and (not gun):
            raise ValueError('Geçersiz malzeme.')
        cost = 12000 if key == 'armor' else max(1500, gun['price'] // 30)
        stock = p['loadout'].setdefault('stock', {})
        if stock.get(key, 0) >= 20:
            raise ValueError('Paket sınırı 20.')
        updated = json.loads(json.dumps(p['loadout']))
        updated['stock'][key] = stock.get(key, 0) + 1
        version = p['loadout_version'] + 1
        with world.database() as db:
            if not db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?', (cost, uid, cost)).rowcount:
                raise ValueError('Yeterli paran yok.')
            db.execute('INSERT INTO pn_loadout VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,version=excluded.version', (p['char_id'], json.dumps(updated), version))
            world.audit(db, uid, 'supply-buy', dict(item=key, cost=cost))
        p['loadout'] = updated
        p['loadout_version'] = version
        return dict(success=True, loadout=view(p), money=world.wallet(uid), notice='Paket envantere eklendi.')
    if action == 'use-start':
        key = payload.get('item')
        stock = p['loadout'].get('stock', {})
        gun = WEAPONS.get(str(key)[5:]) if str(key).startswith('ammo_') else None
        from gameplay_v29.pn_economy import PRODUCTS
        consumable = PRODUCTS.get(key, {})
        if key != 'armor' and (not gun) and (consumable.get('kind') not in ('food', 'drink', 'heal')) or not stock.get(key, 0):
            raise ValueError('Çantanda kullanılabilir bu paket yok.')
        if state.get('vehicle_id') or p.get('health', 0) <= 100:
            raise ValueError('Yaya ve hayatta olmalısın.')
        if p.get('inventory_action') and p['inventory_action']['until'] > time.time():
            raise ValueError('İşlemin tamamlanmasını bekle.')
        if gun and (str(key)[5:] not in p['loadout']['owned'] or p['loadout']['selected'] != gun['slot']):
            raise ValueError('Önce bu paketin silahını kuşan.')
        if key == 'armor' and p.get('armor', 0) >= 100:
            raise ValueError('Zırhın zaten dolu.')
        if gun and p['loadout']['owned'][str(key)[5:]] >= 999:
            raise ValueError('Bu silahın mermisi dolu (999).')
        duration = 5 if key == 'armor' else 3
        identifier = secrets.token_urlsafe(18)
        p['inventory_action'] = dict(id=identifier, item=key, until=time.time() + duration, duration=duration, life=p.get('life_id', 0), position={k: state[k] for k in ('x', 'y', 'z')}, slot=p['loadout']['selected'])
        p['activity'] = dict(kind='armor' if key == 'armor' else 'food' if consumable.get('kind') == 'food' else 'water' if consumable.get('kind') == 'drink' else 'reload', until=time.time() + duration)
        return dict(success=True, action_id=identifier, duration=duration, kind=p['activity']['kind'])
    if action == 'use-finish':
        task = p.get('inventory_action')
        now = time.time()
        if not task or task['id'] != payload.get('action_id'):
            raise ValueError('İşlem bulunamadı.')
        if now < task['until']:
            raise ValueError('İşlem henüz tamamlanmadı.')
        if now > task['until'] + 15 or p.get('life_id', 0) != task['life'] or state.get('vehicle_id') or (p.get('health', 0) <= 100) or (not world.near(state, task['position'], 2)) or (p['loadout']['selected'] != task['slot']):
            p.pop('inventory_action', None)
            p.pop('activity', None)
            raise ValueError('İşlem iptal edildi; paket harcanmadı.')
        key = task['item']
        stock = p['loadout'].get('stock', {})
        if not stock.get(key, 0):
            raise ValueError('Paket kalmadı.')
        if key == 'armor':
            p['armor'] = 100
            state['armor'] = 100
            p['armor_ready_at'] = now + 1
        elif key.startswith('ammo_'):
            gun = key[5:]
            p['loadout']['owned'][gun] = min(999, p['loadout']['owned'][gun] + clip_capacity(gun))
            p['loadout'].setdefault('clips', {})[gun] = min(clip_capacity(gun), p['loadout']['owned'][gun])
            p['weapon_ready_at'] = now + 1
        else:
            from gameplay_v29.pn_economy import PRODUCTS
            item = PRODUCTS[key]
            kind = item['kind']
            field = 'hunger' if kind == 'food' else 'thirst' if kind == 'drink' else 'health'
            p[field] = min(200 if kind == 'heal' else 100, p.get(field, 200 if kind == 'heal' else 100) + item['value'])
            state[field] = p[field]
            from gameplay_v29.pn_multiplayer import save, emote
            save(p, state, True)
            emote(p, state, item['name'] + ' kullandı.')
        stock[key] -= 1
        if stock[key] <= 0:
            stock.pop(key, None)
        from gameplay_v29.pn_multiplayer import save
        with world.database() as db:
            persist(p)
            save(p, state, True, db)
        p.pop('inventory_action', None)
        p.pop('activity', None)
        return dict(success=True, loadout=view(p), armor=p.get('armor', 0), notice='Yelek takıldı.' if key == 'armor' else 'Şarjör yüklendi.' if key.startswith('ammo_') else 'Eşya kullanıldı.')
    raise ValueError('Envanter işlemi bulunamadı.')
