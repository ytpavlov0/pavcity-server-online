"""51 candidate: counts and opt-in mobile read-only views of actual observations.

No fabricated rows, SQL vehicles, keys, physics ownership or native replicas.
Caller holds api.LOCK. Reading status never refreshes lease or observation TTL.
"""
import math
from collections import Counter


def install(api):
    if getattr(api, 'population201_installed', False):
        return api
    collector = api.population200_collector
    accept, envelope, row, original = collector.accept, collector.envelope, collector.row, api.dispatch
    ingests = Counter()

    def accept201(*args):
        status = accept(*args)
        ingests[status] += 1
        return status

    def row201(source, kind, *args):
        identity, result = row(source, kind, *args)
        if kind == 'vehicle' and any(k in source for k in ('rx', 'ry', 'rz')):
            if not all(type(source.get(k)) in (int, float) and math.isfinite(source[k]) and abs(source[k]) <= 360 for k in ('rx', 'ry', 'rz')):
                raise ValueError('rotation')
            result.update({k: source[k] for k in ('rx', 'ry', 'rz')})
        return identity, result

    def leases():
        now = collector.mono()
        for lease in collector.leases.values():
            p, s = api.PRESENCE.get(lease['owner']), api.GTA_STATE.get(lease['owner'])
            if (lease['expires'] > now and collector.eligible(p, s)
                    and p.get('life_id', 0) == lease['life'] and p.get('char_id') == lease['character']
                    and tuple(math.floor(s[k] / 128) for k in ('x', 'y')) == lease['cell']):
                yield lease

    def fresh_rows(lease):
        now = collector.mono()
        return (r for r in lease['rows'].values() if 0 <= now-r['_accepted_mono'] < 1.5)

    def status():
        with api.LOCK:
            active = list(leases())
            counts = Counter(r['kind'] for lease in active for r in fresh_rows(lease))
            return dict(version=201, native_observation_protocol=200, active_leases=len(active),
                        fresh_peds=counts['ped'], fresh_vehicles=counts['vehicle'],
                        accepted_frames=ingests['accepted'], rejected_frames=sum(v for k, v in ingests.items() if k != 'accepted'),
                        pc_visual_enabled=False, mobile_opt_in_available=True,
                        native_runtime_or_variation_parity_verified=False)

    def envelope201(token, lease, status=None):
        result = envelope(token, lease, status)
        p, s = api.PRESENCE.get(token), api.GTA_STATE.get(token)
        allowed = bool(p and s and p.get('world') == 'gta' and p.get('client_platform') == 'mobile'
                       and p.get('population201_visual_capable') is True and p.get('health', 0) > 100
                       and not p.get('dimension', 0) and not p.get('property_id', 0)
                       and collector.wall()-s.get('last_seen', 0) < 5
                       and all(type(s.get(k)) in (int, float) and math.isfinite(s[k]) for k in ('x', 'y', 'z')))
        if not allowed:
            return result
        rows = []
        for source in leases():
            for r in fresh_rows(source):
                distance = math.dist([r[k] for k in ('x', 'y', 'z')], [s[k] for k in ('x', 'y', 'z')])
                if distance < 150:
                    rows.append((distance, r))
        rows.sort(key=lambda pair: (pair[0], pair[1]['id']))
        public = [dict({k: v for k, v in r.items() if not k.startswith('_')},readonly=True,interaction_allowed=False) for _, r in rows]
        return dict(result, mode='observed', visual_enabled=True, readonly=True, ttl_ms=1500,
                    peds=[r for r in public if r['kind'] == 'ped'][:6],
                    vehicles=[r for r in public if r['kind'] == 'vehicle'][:4])

    def dispatch(path, payload, token):
        with api.LOCK:
            p = api.PRESENCE.get(token)
            if path == '/api/gta/sync' and p:
                # Each sync explicitly opts in; an older page cannot inherit it.
                p['population201_visual_capable'] = payload.get('population201_visual_capable') is True
            return original(path, payload, token)

    collector.accept, collector.row, collector.envelope = accept201, row201, envelope201
    api.dispatch = dispatch
    api.population201_status = status
    api.population201_installed = True
    return api
