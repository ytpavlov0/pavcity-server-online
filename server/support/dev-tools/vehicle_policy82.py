"""One registered-model rule for the frozen world's entry and garage paths."""
import inspect,sys
from pathlib import Path


def configure():
    from vehicle_policy79 import configure as prior
    prior()
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/'backups/gameplay-v29-backend'))
    import gameplay_v29.pn_world as world
    import gameplay_v29.pn_traffic as traffic
    if getattr(world, 'model_gate82', False):
        return
    # Install before extensions capture dispatch. Only the model predicates change;
    # key, seat, proximity, job, life and duty checks stay in the original function.
    source = inspect.getsource(world.dispatch)
    entry = "row['model'] not in __import__('gameplay_v29.pn_traffic', fromlist=['*']).ROAD_MODELS"
    garage = "available=r['model'] in SPAWN_MODELS"
    assert source.count(entry) == 1 and source.count(garage) == 1
    world.model_available82 = lambda model: model in world.SPAWN_MODELS or model in traffic.ROAD_MODELS
    world.legacy_dispatch82 = world.dispatch
    source = source.replace(entry, "not model_available82(row['model'])").replace(garage, "available=model_available82(r['model'])")
    exec(compile(source, __file__ + ':world-dispatch', 'exec'), world.__dict__)
    world.model_gate82 = True
