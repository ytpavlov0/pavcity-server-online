"""Candidate native-population shadow collector; never spawns or grants entities.

All state is ephemeral and caller holds session_api.LOCK. One PC lease per
128m cell; local engine handles stay private. Render activation needs a separate
duplicate-culling/ownership handoff acceptance, not merely a valid observation.
"""
import math
import secrets
import time

VERSION = 200
CELL = 128
LEASE_TTL = 3.0
ROW_TTL = 1.5
MAX_LEASES = 64
MAX_PEDS = 16
MAX_CARS = 8
ID_START = 1520000000
ID_END = 1530000000


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def cell_of(row):
    return tuple(math.floor(row[k] / CELL) for k in ('x', 'y'))


class Population200:
    def __init__(self, ped_models, vehicle_models, monotonic=time.monotonic, wall=time.time):
        self.models = {'ped': dict(ped_models), 'vehicle': dict(vehicle_models)}
        self.mono, self.wall = monotonic, wall
        self.leases = {}
        self.next_id = ID_START

    def eligible(self, presence, state):
        return bool(presence and state and presence.get('world') == 'gta'
                    and presence.get('client_platform') == 'desktop'
                    and presence.get('health', 0) > 100
                    and not presence.get('dimension', 0)
                    and not presence.get('property_id', 0)
                    and all(finite(state.get(k)) for k in ('x', 'y', 'z'))
                    and self.wall() - state.get('last_seen', 0) < 5)

    def clean(self, people, states):
        now = self.mono()
        for cell, lease in list(self.leases.items()):
            p, s = people.get(lease['owner']), states.get(lease['owner'])
            if (lease['expires'] <= now or not self.eligible(p, s)
                    or cell_of(s) != cell or p.get('life_id', 0) != lease['life']
                    or p.get('char_id') != lease['character']):
                del self.leases[cell]
                continue
            lease['rows'] = {key: r for key, r in lease['rows'].items()
                             if now - r['_accepted_mono'] < ROW_TTL}

    def lease(self, token, p, s, capable, people, states):
        self.clean(people, states)
        if capable is not True or not self.eligible(p, s):
            return None
        cell = cell_of(s)
        lease = self.leases.get(cell)
        if lease and lease['owner'] != token:
            return None
        if lease is None:
            if len(self.leases) >= MAX_LEASES:
                return None
            lease = dict(owner=token, cell=cell, character=p['char_id'],
                         life=p.get('life_id', 0), id=secrets.token_hex(16),
                         seq=-1, at=-math.inf, expires=0, rows={})
            self.leases[cell] = lease
        lease['expires'] = self.mono() + LEASE_TTL
        return lease

    def row(self, source, kind, lease, state, sequence, now, wall):
        if not isinstance(source, dict):
            raise ValueError('row')
        key, model_hash = source.get('key'), source.get('model_hash')
        if type(key) is not int or not 0 < key < 2**31:
            raise ValueError('key')
        if type(model_hash) is not int or model_hash not in self.models[kind]:
            raise ValueError('model')
        if (type(source.get('population_type')) is not int
                or not 1 <= source['population_type'] <= 6
                or source.get('mission') is not False
                or source.get('is_player') is not False):
            raise ValueError('population')
        fields = ('x', 'y', 'z', 'heading', 'vx', 'vy', 'vz')
        if not all(finite(source.get(k)) for k in fields):
            raise ValueError('pose')
        if (abs(source['x']) > 16000 or abs(source['y']) > 16000
                or not -1700 < source['z'] < 2700 or cell_of(source) != lease['cell']
                or math.dist([source[k] for k in ('x', 'y', 'z')],
                             [state[k] for k in ('x', 'y', 'z')]) > 180):
            raise ValueError('region')
        speed = math.sqrt(sum(source[k] ** 2 for k in ('vx', 'vy', 'vz')))
        if speed > (15 if kind == 'ped' else 90):
            raise ValueError('speed')
        identity = (kind, key)
        old = lease['rows'].get(identity)
        # Handles can be recycled for a new model: never reuse the prior actor ID.
        if old and old['model_hash'] != model_hash:
            old = None
        if old:
            dt = now - old['_accepted_mono']
            distance = math.dist([source[k] for k in ('x', 'y', 'z')],
                                 [old[k] for k in ('x', 'y', 'z')])
            if distance > (15 if kind == 'ped' else 90) * dt + 4:
                raise ValueError('jump')
        row = {k: source[k] for k in fields}
        row.update(id=old['id'] if old else None, model_hash=model_hash,
                   model=self.models[kind][model_hash], kind=kind,
                   source='ambient200', source_seq=sequence, accepted_at=wall,
                   heading=source['heading'] % 360, speed=speed,
                   population_type=source['population_type'], vehicle_id=0, seat=-2,
                   appearance_profile='default000', native_variations_verified=False,
                   _accepted_mono=now)
        if kind == 'vehicle' and source.get('paint43') is not None:
            paint = source['paint43']
            if (not isinstance(paint, list) or len(paint) != 9
                    or any(type(v) is not int for v in paint)
                    or not all(0 <= v <= 160 for v in paint[:2])
                    or not 0 <= paint[2] <= 3):
                raise ValueError('paint')
            mods = dict(primary=paint[0], secondary=paint[1])
            for i, side in enumerate(('primary', 'secondary')):
                if paint[2] & (1 << i):
                    rgb = paint[3+i*3:6+i*3]
                    if not all(0 <= v <= 255 for v in rgb):
                        raise ValueError('paint')
                    mods[side + '_rgb'] = rgb
            row['mods'] = mods
        return identity, row

    def accept(self, token, p, s, data):
        if not self.eligible(p, s) or not isinstance(data, dict):
            return 'ineligible'
        lease = self.leases.get(cell_of(s))
        if not lease or lease['owner'] != token or lease['expires'] <= self.mono():
            return 'no_lease'
        if p.get('life_id', 0) != lease['life'] or p.get('char_id') != lease['character']:
            return 'invalid_frame'
        sequence = data.get('source_seq')
        if (data.get('version') != VERSION or data.get('lease_id') != lease['id']
                or type(data.get('life_id')) is not int or data['life_id'] != lease['life']
                or type(sequence) is not int or not 0 <= sequence < 2**53):
            return 'invalid_frame'
        if sequence <= lease['seq']:
            return 'stale'
        now = self.mono()
        if now - lease['at'] < .45:
            return 'rate_limited'
        peds, cars = data.get('peds'), data.get('vehicles')
        if (not isinstance(peds, list) or len(peds) > MAX_PEDS
                or not isinstance(cars, list) or len(cars) > MAX_CARS):
            return 'capacity'
        rows = {}
        try:
            for kind, sources in (('ped', peds), ('vehicle', cars)):
                for source in sources:
                    identity, row = self.row(source, kind, lease, s, sequence, now, self.wall())
                    if identity in rows:
                        raise ValueError('duplicate')
                    rows[identity] = row
        except (ValueError, OverflowError):
            return 'invalid_row'
        if self.next_id + sum(r['id'] is None for r in rows.values()) >= ID_END:
            return 'capacity'
        # Commit the complete validated frame atomically. No partial acceptance.
        for row in rows.values():
            if row['id'] is None:
                self.next_id += 1
                row['id'] = self.next_id
        lease.update(seq=sequence, at=now, rows=rows)
        return 'accepted'

    def envelope(self, token, lease, status=None):
        source = dict(can_observe=False)
        if lease and lease['owner'] == token:
            source.update(can_observe=True, cell=list(lease['cell']), lease_id=lease['id'],
                          life_id=lease['life'], lease_remaining_ms=round(max(0, lease['expires'] - self.mono()) * 1000),
                          max_peds=MAX_PEDS, max_vehicles=MAX_CARS, accepted_seq=lease['seq'])
        return dict(version=VERSION, mode='shadow', visual_enabled=False,
                    server_time=self.wall(), observation_hz=2, source=source,
                    peds=[], vehicles=[], ingest_status=status)


def install(api, ped_models, vehicle_models):
    if getattr(api, 'population200_installed', False):
        return api
    collector = Population200(ped_models, vehicle_models)
    original = api.dispatch

    def dispatch(path, payload, token):
        with api.LOCK:
            result, cookie = original(path, payload, token)
            if path == '/api/gta/sync' and result.get('success'):
                p, s = api.PRESENCE.get(token), api.GTA_STATE.get(token)
                lease = collector.lease(token, p, s, payload.get('population200_capable'), api.PRESENCE, api.GTA_STATE)
                status = collector.accept(token, p, s, payload['population200']) if 'population200' in payload else None
                result = dict(result, ambient200=collector.envelope(token, lease, status))
            return result, cookie

    api.dispatch = dispatch
    api.population200_installed = True
    api.population200_collector = collector
    return api
