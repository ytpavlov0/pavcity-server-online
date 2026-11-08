"""Property-scoped retail, layered after the frozen67 backend.

Products/prices/inventory limits stay in the existing economy implementation.
An interior never impersonates an outdoor shop by rewriting player coordinates.
"""
import copy
import importlib
import json
import re
import time


def install(api):
    if getattr(api, 'retail68_installed', False):
        return api
    economy = importlib.import_module(api.__package__ + '.pn_economy')
    city = importlib.import_module(api.__package__ + '.pn_city')
    inv = importlib.import_module(api.__package__ + '.pn_inventory')
    world = api.world
    old_at, old_dispatch = economy.at, economy.dispatch
    with api.database() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS pn_shop_receipts68(
          user_id INTEGER NOT NULL, request_id TEXT NOT NULL, digest TEXT NOT NULL,
          notice TEXT NOT NULL, created REAL NOT NULL,
          PRIMARY KEY(user_id,request_id))''')

    def location(kind, p, state):
        world.live(p, state)
        dimension = p.get('dimension', 0)
        if not dimension:
            old_at(kind, p, state)
            return None
        if kind != 'market':
            raise ValueError('Bu mağaza bu iç mekânda bulunmuyor.')
        with api.database() as db:
            row = db.execute('SELECT id,name,kind,version FROM pn_properties WHERE id=?', (dimension,)).fetchone()
        if not row or row['kind'] != 'market':
            raise ValueError('Alışveriş için bir marketin içine gir.')
        transition = p.get('property45_used') or {}
        if transition.get('phase') == 'pending':
            raise ValueError('İç mekânın yüklenmesini ve girişin tamamlanmasını bekle.')
        if state.get('vehicle_id') or world.occupation(p['char_id'])[0]:
            raise ValueError('Alışverişi yaya olarak yap.')
        anchor = city.INTERIOR_TYPES['market']
        if not world.near(state, anchor, 12) or abs(state['z'] - anchor['z']) > 2:
            raise ValueError('Marketin alışveriş alanına yaklaş.')
        return dict(id=row['id'], name=row['name'], version=row['version'])

    def at(kind, p, state):
        return location(kind, p, state)

    def dispatch(path, uid, token, values, p, state, presences):
        if path not in ('/api/shops/list', '/api/shops/buy') or values.get('kind', 'market') not in ('market', 'electronics'):
            return old_dispatch(path, uid, token, values, p, state, presences)
        kind = values.get('kind', 'market')
        shop = location(kind, p, state)
        if path.endswith('/list'):
            result = old_dispatch(path, uid, token, values, p, state, presences)
            result['property_shop68'] = shop
            result['buyer68'] = p['char_id']
            return result
        # A stale open panel must not buy from a different dimension/shop.
        supplied = values.get('property_id', 0)
        if type(supplied) is not int or supplied != (shop['id'] if shop else 0):
            raise ValueError('Market değişti. Alışveriş ekranını yeniden aç.')
        if shop and (type(values.get('property_version')) is not int or values['property_version'] != shop['version']):
            raise ValueError('Mülk bilgisi değişti. Alışveriş ekranını yeniden aç.')
        request_id = values.get('request_id')
        if request_id is None and not shop:
            # Compatibility for pre68 outdoor clients; their old guards remain.
            return old_dispatch(path, uid, token, values, p, state, presences)
        if not isinstance(request_id, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{16,80}', request_id):
            raise ValueError('Alışveriş işlem kodu eksik. Güncel istemciyle ekranı yeniden aç.')
        item, qty = values.get('item'), values.get('qty', 1)
        if not isinstance(item, str) or type(qty) is not int or not 1 <= qty <= 10:
            raise ValueError('Geçerli ürün ve adet seç.')
        digest = json.dumps([p['char_id'], kind, supplied, values.get('property_version', 0), item, qty], separators=(',', ':'))
        before = copy.deepcopy(p)
        try:
            with api.database() as db:
                # sqlite's connection context does not BEGIN for SELECT. Without
                # an explicit transaction a nested SAVEPOINT could commit goods
                # before the outer receipt/audit is written.
                if not db.in_transaction:
                    db.execute('BEGIN IMMEDIATE')
                receipt = db.execute('SELECT * FROM pn_shop_receipts68 WHERE user_id=? AND request_id=?', (uid, request_id)).fetchone()
                if receipt:
                    if receipt['digest'] != digest:
                        raise ValueError('Aynı işlem kodu farklı alışverişte kullanılamaz.')
                    inv.load(p)
                    return dict(success=True, replayed=True, notice=receipt['notice'], loadout=inv.view(p), money=world.wallet(uid))
                # Nested economy savepoints share this transaction: money, goods,
                # audit and the retry receipt either all commit or all roll back.
                result = old_dispatch(path, uid, token, values, p, state, presences)
                if not result.get('success'):
                    raise ValueError(result.get('error', 'Alışveriş tamamlanamadı.'))
                db.execute('INSERT INTO pn_shop_receipts68 VALUES(?,?,?,?,?)', (uid, request_id, digest, result.get('notice', ''), time.time()))
                world.audit(db, uid, 'property-shop68' if shop else 'shop-receipt68', dict(property_id=supplied, item=item, qty=qty))
            return result
        except Exception:
            p.clear()
            p.update(before)
            raise

    economy.at, economy.dispatch = at, dispatch
    api.retail68_installed = True
    return api
