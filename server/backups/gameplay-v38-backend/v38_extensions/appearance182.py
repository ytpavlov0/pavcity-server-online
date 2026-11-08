"""Explicit appearance validation extension; no saved outfit migration or grants."""
from copy import deepcopy

TORSO_MAX = {'male': 18, 'female': 19}  # Original drawable files in avatar177 catalog.
TEXTURE_MAX = 15  # Original a..p texture variants; native clamps each component.

def install(api):
    world = api.world
    if getattr(world, '_appearance182', False):
        return api
    previous = world.appearance

    def appearance(raw=None):
        if raw is None:
            return previous(None)
        if not isinstance(raw, dict):
            return previous(raw)
        source = deepcopy(raw)
        gender = source.get('gender', 'male')
        if gender not in TORSO_MAX:
            return previous(source)
        for key, default, maximum in [('torso', 0, TORSO_MAX[gender]), ('texture', 0, TEXTURE_MAX)]:
            value = source.get(key, default)
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
                raise ValueError('Geçersiz görünüm: ' + key)
        source['torso'] = min(source.get('torso', 0), 15)
        source['texture'] = min(source.get('texture', 0), 10)
        result = previous(source)
        result['torso'] = raw.get('torso', 0)
        result['texture'] = raw.get('texture', 0)
        return result

    world.appearance = appearance
    world._appearance182 = True
    return api
