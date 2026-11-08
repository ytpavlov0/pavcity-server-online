"""Opt-in mobile hitscan intents. Legacy desktop native combat stays unchanged.

The server owns debit, cadence, target selection and receipts. Pose is the existing
accepted multiplayer observation, not authoritative server physics. Unknown cover
never authorizes damage. Installation does not migrate or grant account state.
"""
import copy
import hashlib
import json
import math
import re
import time
from collections import OrderedDict, deque
from contextlib import contextmanager

LIMITS = {'AMMO_PISTOL': (120, 250), 'AMMO_SMG': (140, 100),
          'AMMO_RIFLE': (180, 120), 'AMMO_MG': (180, 120), 'AMMO_SNIPER': (200, 900)}
INTENT_KEYS = {'request_id', 'shot_seq', 'server_instance51', 'life_id',
               'seat_epoch', 'loadout_version', 'weapon', 'direction', 'aimed'}
UNVERIFIED = {'outcome': 'unverified', 'distance': None}


def ray_capsule(origin, direction, center, maximum):
    """Vertical standing capsule: radius .30, native-origin z[-.8,+.75]."""
    ox, oy, oz = (origin[i] - center[i] for i in range(3))
    dx, dy, dz = direction
    radius, bottom, top = .30, -.50, .45
    results = []
    a = dx * dx + dy * dy
    b = ox * dx + oy * dy
    c = ox * ox + oy * oy - radius * radius
    if a > 1e-12 and b * b - a * c >= 0:
        root = math.sqrt(max(0, b * b - a * c))
        for distance in ((-b - root) / a, (-b + root) / a):
            if .02 <= distance <= maximum and bottom <= oz + distance * dz <= top:
                results.append(distance)
    for z in (bottom, top):
        qz = oz - z
        b = ox * dx + oy * dy + qz * dz
        c = ox * ox + oy * oy + qz * qz - radius * radius
        if b * b - c >= 0:
            root = math.sqrt(max(0, b * b - c))
            for distance in (-b - root, -b + root):
                if .02 <= distance <= maximum:
                    results.append(distance)
    return min(results) if results else None


def install(api, cover=None, clock=time.time):
    if getattr(api, 'combat53_installed', False):
        return api
    from gameplay_v29 import pn_inventory as inv, pn_admin as admin, pn_roleplay as roleplay
    from gameplay_v29 import pn_interactions as interactions
    world = api.world
    original, vehicle_dispatch, inventory_sample = api.dispatch, world.dispatch, inv.sample
    events, event_seq = deque(maxlen=256), [0]
    specs = {str(v['hash']): dict(key=k, range=LIMITS[v['category']][0],
             cooldown_ms=LIMITS[v['category']][1], damage=25, clip_capacity=inv.clip_capacity(k))
             for k, v in inv.WEAPONS.items() if v.get('category') in LIMITS}

    def context(p):
        identity = (api.pc51_instance, p.get('life_id', 0), p.get('seat_epoch', 0))
        book = p.get('combat53')
        if not book or book['identity'] != identity:
            book = dict(identity=identity, last_seq=0, ammo_revision53=0,
                        receipts=OrderedDict(), last_fire=-math.inf)
            p['combat53'] = book
        return book

    def origin(s):
        return [s['x'], s['y'], s['z'] + .45]

    def envelope(p, s, **extra):
        book, loadout = context(p), inv.view(p, False)
        return dict(success=True, server_instance51=api.pc51_instance,
                    life_id=p.get('life_id', 0), seat_epoch=p.get('seat_epoch', 0),
                    loadout_version=loadout['version'], loadout=loadout,
                    ammo_revision53=book['ammo_revision53'],
                    combat53=dict(last_seq=book['last_seq'], ammo_revision53=book['ammo_revision53'],
                                  origin=origin(s), specs=specs, coverage=getattr(cover, 'label', 'unverified')),
                    **extra)

    def schema(data):
        if set(data) != INTENT_KEYS:
            return False
        if not isinstance(data['request_id'], str) or not re.fullmatch('[a-f0-9]{32}', data['request_id']):
            return False
        for key in ('shot_seq', 'life_id', 'seat_epoch', 'loadout_version', 'weapon'):
            if type(data[key]) is not int or not 0 <= data[key] <= 2**53 - 1:
                return False
        if not 1 <= data['shot_seq'] or not 0 < data['weapon'] <= 0xffffffff or type(data['aimed']) is not bool:
            return False
        v = data['direction']
        return (isinstance(v, list) and len(v) == 3
                and all(type(n) in (int, float) and math.isfinite(n) for n in v)
                and .98 <= math.hypot(*v) <= 1.02)

    def denial(p, s, data, reason, **extra):
        identifier = data.get('request_id')
        if not isinstance(identifier, str) or len(identifier) > 32: identifier = None
        return envelope(p, s, request_id=identifier, accepted=False,
                        reason=reason, replayed=False, cooldown_ms=0, **extra)

    def restriction(p, db, now):
        r = db.execute('SELECT life,dimension,cuffed,prone,until FROM pn_restrictions178 WHERE char_id=?', (p['char_id'],)).fetchone()
        custody = db.execute('SELECT phase FROM pn_custody178 WHERE char_id=?', (p['char_id'],)).fetchone()
        held = r and r['life'] == p.get('life_id', 0) and r['dimension'] == p.get('dimension', 0) and r['until'] > now and (r['cuffed'] or r['prone'])
        return held or custody and custody['phase'] != 'pending' or interactions.CARRY.get(p['char_id'])

    def validate(p, s, data, now, db):
        if p.get('client_platform') != 'mobile': return 'Bu atış protokolü mobil istemci içindir.'
        if p.get('health', 0) <= 100 or s.get('health', 0) <= 100: return 'Hayatta olmalısın.'
        if p.get('dimension', 0) != 0: return 'Bu alanda atış henüz desteklenmiyor.'
        if world.occupation(p['char_id'])[0] or s.get('vehicle_id'): return 'Atış için araçtan in.'
        if p.get('fly') or p.get('godmode'): return 'Uçuş / koruma açıkken bu atış kullanılamaz.'
        if now - s.get('last_seen', 0) > 2.5: return 'Konum bağlantısını yenile.'
        if restriction(p, db, now): return 'Kısıtlı durumdayken ateş edemezsin.'
        if p.get('inventory_action') or p.get('activity', {}).get('until', 0) > now: return 'Önce mevcut işlemi tamamla.'
        if now < p.get('weapon_ready_at', 0): return 'Silah henüz hazır değil.'
        info = inv.view(p, False)
        if data['loadout_version'] != info['version']: return 'Envanter değişti; silah durumunu yenile.'
        if data['weapon'] != info['weapon'] or str(info['weapon']) not in specs: return 'Kuşandığın desteklenen silahı kullan.'
        key = specs[str(info['weapon'])]['key']
        if key not in p['loadout']['owned']: return 'Bu silaha sahip değilsin.'
        if info['ammo'] < 1 or info['clip'] < 1: return 'Şarjör boş; doldur.'
        return None

    def target(p, s, muzzle, direction, maximum, now):
        nearest = None
        for token, q in api.PRESENCE.items():
            t = api.GTA_STATE.get(token)
            if not t or q['char_id'] == p['char_id'] or q.get('world') != 'gta' or q.get('dimension', 0) != p.get('dimension', 0): continue
            if q.get('health', 0) <= 100 or now - t.get('last_seen', 0) > 2.5: continue
            distance = ray_capsule(muzzle, direction, [t[k] for k in ('x', 'y', 'z')], maximum)
            if distance is not None and (nearest is None or distance < nearest[0]): nearest = distance, q, t
        return nearest

    def remember(book, data, digest, result):
        book['last_seq'] = data['shot_seq']
        book['receipts'][data['request_id']] = (digest, result)
        while len(book['receipts']) > 128:
            book['receipts'].popitem(last=False)

    @contextmanager
    def atomic(journal):
        try:
            with api.database() as db:
                # Python's connection context does not BEGIN on a SELECT. Without
                # this, the first nested persist's SAVEPOINT RELEASE commits it.
                if not db.in_transaction: db.execute('BEGIN IMMEDIATE')
                yield db
        except BaseException:
            for obj, saved in reversed(journal):
                obj.clear(); obj.update(saved)
            raise

    def fire(p, s, data):
        book = context(p)
        if not schema(data): return denial(p, s, data, 'Geçersiz atış paketi.')
        if data['server_instance51'] != api.pc51_instance or data['life_id'] != p.get('life_id', 0) or data['seat_epoch'] != p.get('seat_epoch', 0):
            return denial(p, s, data, 'Karakter / sunucu / koltuk değişti; atış durumunu yenile.')
        digest = hashlib.sha256(json.dumps(data, sort_keys=True, allow_nan=False, separators=(',', ':')).encode()).hexdigest()
        old = book['receipts'].get(data['request_id'])
        if old:
            if old[0] != digest: return denial(p, s, data, 'Atış kimliği başka işlemde kullanılmış.')
            # Shot history is immutable; inventory in every ACK is CURRENT.
            return envelope(p, s, **copy.deepcopy(old[1]), replayed=True)
        if data['shot_seq'] != book['last_seq'] + 1:
            return denial(p, s, data, 'Atış sırası değişti; durumu yenile.')
        now = clock()
        journal = []
        with atomic(journal) as db:
            reason = validate(p, s, data, now, db)
            spec = specs.get(str(data['weapon']), {})
            remaining = max(0, book['last_fire'] + spec.get('cooldown_ms', 0) / 1000 - now)
            if not reason and remaining > 0: reason = 'Silah atış aralığını bekle.'
            if reason:
                result = dict(request_id=data['request_id'], accepted=False, reason=reason, cooldown_ms=math.ceil(remaining * 1000))
                remember(book, data, digest, result)
                return envelope(p, s, **result, replayed=False)
            muzzle = origin(s)
            length = math.hypot(*data['direction'])
            direction = [n / length for n in data['direction']]
            hit = target(p, s, muzzle, direction, spec['range'], now)
            maximum = hit[0] if hit else spec['range']
            cover_result = cover.trace(muzzle, direction, maximum, api, p) if cover else UNVERIFIED
            outcome = cover_result.get('outcome', 'unverified')
            distance = cover_result.get('distance')
            if outcome not in ('clear', 'blocked', 'unverified'): outcome = 'unverified'
            victim = None
            if outcome == 'clear':
                outcome = 'miss'
                if hit:
                    _, q, t = hit
                    # Standing hitbox is not proof of a seated/crouched target.
                    immune = (q.get('fly') or q.get('godmode')) and admin.rank(q['user_id']) >= 2
                    if world.occupation(q['char_id'])[0] or t.get('vehicle_id') or t.get('crouched') or t.get('flags', 0) & 16:
                        outcome = 'unverified'
                    elif immune: outcome = 'blocked'
                    else: outcome, victim, distance = 'hit', (q, t), hit[0]
            if distance is None: distance = maximum
            shot = dict(seq=data['shot_seq'], origin=muzzle, direction=direction,
                        range=spec['range'], distance=min(spec['range'], max(0, distance)), outcome=outcome)
            prior_loadout = copy.deepcopy(p['loadout'])
            journal.append((p['loadout'], prior_loadout))
            q = t = None
            prior_p = prior_s = None
            if victim:
                q, t = victim
                prior_p, prior_s = copy.deepcopy(q), copy.deepcopy(t)
                journal.extend(((q, prior_p), (t, prior_s)))
            try:
                # Nested persist/save share this request's SQLite transaction.
                key, info = spec['key'], inv.view(p, False)
                p['loadout']['owned'][key] = info['ammo'] - 1
                p['loadout'].setdefault('clips', {})[key] = info['clip'] - 1
                inv.persist(p, False)
                alert_due = now - p.get('shot_alert178', 0) > 8
                if alert_due:
                    db.execute('INSERT INTO pn_dispatch178(kind,x,y,z,dimension,created) VALUES(?,?,?,?,?,?)',
                               ('Silah sesi', s['x'], s['y'], s['z'], p.get('dimension', 0), now))
                    db.execute('DELETE FROM pn_dispatch178 WHERE created<?', (now-600,))
                if victim:
                    absorbed = min(spec['damage'], q.get('armor', 0))
                    q['armor'] = max(0, q.get('armor', 0) - absorbed)
                    before_health = q.get('health', 200)
                    q['health'] = max(0, before_health - (spec['damage'] - absorbed))
                    q['damage_sequence'] = q.get('damage_sequence', 0) + 1
                    q['damage_kind'] = 2
                    q['armor_ready_at'] = now + .5
                    t.update(armor=q['armor'], health=q['health'], damage_sequence=q['damage_sequence'], damage_kind=2)
                    if q['health'] <= 100 < before_health:
                        q.setdefault('dead_at', now)
                        roleplay.combat_event(q['char_id'], q.get('life_id', 0), p['char_id'])
                    api.multiplayer.save(q, t, True, db)
                    shot.update(target=q['char_id'], damage=spec['damage'])
            except BaseException:
                p['loadout'] = prior_loadout
                if victim:
                    q.clear(); q.update(prior_p); t.clear(); t.update(prior_s)
                raise
        # Do not cache or publish a shot before durable debit/damage commits.
        book['last_fire'] = now
        if alert_due: p['shot_alert178'] = now
        book['ammo_revision53'] += 1
        result = dict(request_id=data['request_id'], accepted=True, reason='',
                      cooldown_ms=spec['cooldown_ms'], shot53=shot)
        remember(book, data, digest, result)
        event_seq[0] += 1
        p['shot_sequence53'] = event_seq[0]
        s['shot_sequence53'] = event_seq[0]
        events.append(dict(event=event_seq[0], at=now, dimension=p.get('dimension', 0),
                           char_id=p['char_id'], server_id=p['server_id'],
                           life_id=p.get('life_id', 0), weapon=data['weapon'], aimed=data['aimed'], **shot))
        return envelope(p, s, **result, replayed=False)

    def vehicle(path, uid, token, data, p, s, presences):
        if path not in ('/api/vehicles/combat53-state', '/api/vehicles/combat53-fire'):
            return vehicle_dispatch(path, uid, token, data, p, s, presences)
        if not p or not s or p.get('world') != 'gta': raise ValueError('Önce karakterinle şehre gir.')
        if p.get('client_platform') != 'mobile': raise ValueError('Bu atış protokolü mobil istemci içindir.')
        if path.endswith('-state'):
            if data: raise ValueError('Atış durum isteği boş olmalı.')
            # Sticky until rejoin: older sync requests cannot double-spend ammo.
            p['combat53_enabled'] = True
            return envelope(p, s)
        if not p.get('combat53_enabled'): return denial(p, s, data, 'Önce atış durumunu hazırla.')
        return fire(p, s, data)

    def sample(p, data):
        if p.get('combat53_enabled') and p.get('client_platform') == 'mobile': return
        return inventory_sample(p, data)

    def dispatch(path, data, token):
        with api.LOCK:
            p = api.PRESENCE.get(token)
            if path in ('/api/combat53/state', '/api/combat53/fire'):
                route = '/api/vehicles/combat53-' + path.rsplit('/', 1)[-1]
                return original(route, data, token)
            modern = p and p.get('combat53_enabled') and p.get('client_platform') == 'mobile'
            if modern and path == '/api/gta/sync':
                data = dict(data)
                if isinstance(data.get('hits'), list):
                    data['hits'] = [h for h in data['hits'] if isinstance(h, dict) and h.get('kind') == 'melee']
                # Only accepted server shots can produce a shooting animation.
                data['flags'] = int(data.get('flags', 0)) & ~1
                latest = next((e for e in reversed(events) if e['char_id'] == p['char_id'] and e['life_id'] == p.get('life_id', 0) and clock() - e['at'] < .20), None)
                if latest:
                    data['flags'] |= 1
                    data.update({f'aim_{axis}': latest['origin'][i] + latest['direction'][i] * latest['distance'] for i, axis in enumerate(('x', 'y', 'z'))})
            result, cookie = original(path, data, token)
            p, s = api.PRESENCE.get(token), api.GTA_STATE.get(token)
            if path == '/api/gta/sync' and result.get('success') and p and s:
                # Replayed syncs cannot re-broadcast a shot. Recipients get a cursor.
                cursor = p.get('combat53_event_cursor', 0)
                rows = [{k: v for k, v in e.items() if k not in ('at', 'dimension')}
                        for e in events if e['event'] > cursor and clock() - e['at'] <= 1.5
                        and e['dimension'] == p.get('dimension', 0)
                        and math.dist(origin(s), e['origin']) < 350]
                p['combat53_event_cursor'] = event_seq[0]
                byid = {q['char_id']: q.get('shot_sequence53', 0) for q in api.PRESENCE.values()}
                result = dict(result, shots53=rows[-32:], players=[dict(q, shot_sequence53=byid.get(q.get('char_id'), 0)) for q in result.get('players', [])])
                if p.get('combat53_enabled'):
                    result = dict(result, **{k: v for k, v in envelope(p, s).items() if k not in ('success', 'loadout')})
            return result, cookie

    world.dispatch, inv.sample, api.dispatch = vehicle, sample, dispatch
    api.combat53_specs, api.combat53_installed = specs, True
    return api
