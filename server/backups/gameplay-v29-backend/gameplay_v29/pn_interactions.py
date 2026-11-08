"""Transient nearby RP actions. Dispatch is serialized by session_api.LOCK."""
import math
import time
import gameplay_v29.pn_world as world
CARRY = {}

def release(cid):
    for victim, carrier in list(CARRY.items()):
        if cid in (victim, carrier):
            CARRY.pop(victim, None)

def clean(presences):
    live = {p['char_id']: p for p in presences.values() if time.time() - p['last_seen'] < 20}
    for victim, carrier in list(CARRY.items()):
        if victim not in live or carrier not in live or live[carrier].get('health', 200) <= 100 or world.occupation(carrier)[0] or world.occupation(victim)[0]:
            CARRY.pop(victim, None)

def constrain(p, fields, states):
    carrier = CARRY.get(p['char_id'])
    source = next((s for s in states.values() if s['char_id'] == carrier), None)
    if source:
        fields.update({k: source[k] for k in ('x', 'y', 'z', 'heading')})
        fields['z'] += 0.6
        fields.update(speed=0, vx=0, vy=0, vz=0)
    fields['carried_by'] = carrier or 0

def dispatch(path, uid, token, payload, p, state, presences, states):
    world.live(p, state)
    clean(presences)
    action = path.rsplit('/', 1)[-1]
    if action == 'drop':
        release(p['char_id'])
        return {'success': True, 'notice': 'Taşıma sonlandırıldı.'}
    try:
        cid = int(payload.get('target', 0))
    except (ValueError, TypeError):
        raise ValueError('Geçersiz oyuncu.')
    pair = next(((k, v) for k, v in presences.items() if v['char_id'] == cid and time.time() - v['last_seen'] < 10 and (k in states)), None)
    if not pair or cid == p['char_id']:
        raise ValueError('Yakında başka oyuncu seç.')
    key, victim = pair
    other = states[key]
    if math.dist([state[k] for k in ('x', 'y', 'z')], [other[k] for k in ('x', 'y', 'z')]) > 3:
        raise ValueError('Oyuncuya yaklaş (3 m).')
    if action == 'info':
        return {'success': True, 'info': {'title': 'Yakındaki karakter', 'rows': [['İsim', victim['name']], ['ID', victim['server_id']], ['Can', max(0, int(victim.get('health', 200) - 100))], ['Zırh', int(victim.get('armor', 0))]]}}
    if world.occupation(cid)[0] or world.occupation(p['char_id'])[0]:
        raise ValueError('İkiniz de araçtan inmelisiniz.')
    if victim.get('health', 200) > 100 and (not other.get('flags', 0) & 128):
        raise ValueError('Oyuncu ellerini kaldırmalı (X) veya bilincini kaybetmiş olmalı.')
    from gameplay_v29.pn_multiplayer import rate
    if action == 'carry':
        if cid in CARRY or p['char_id'] in CARRY or p['char_id'] in CARRY.values() or (cid in CARRY.values()):
            raise ValueError('Taşıma zaten sürüyor.')
        CARRY[cid] = p['char_id']
        return {'success': True, 'notice': 'Oyuncuyu sırtına aldın. ALT → Taşımayı bırak.'}
    if action == 'rob':
        rate(str(uid), 'robbery', 10)
        rate('victim:' + str(cid), 'robbery', 60)
        with world.database() as db:
            amount = min(5000, world.wallet(victim['user_id']))
            if amount <= 0:
                raise ValueError('Oyuncunun üzerinde para yok.')
            db.execute('UPDATE pn_wallet SET balance=balance-? WHERE user_id=? AND balance>=?', (amount, victim['user_id'], amount))
            db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?', (amount, uid))
            world.audit(db, uid, 'robbery', {'char_id': cid, 'amount': amount})
        return {'success': True, 'money': world.wallet(uid), 'notice': f'Üzerinden ${amount:,} alındı.'}
    raise ValueError('Etkileşim bulunamadı.')
