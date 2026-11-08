"""Shared advancing clock and deterministic regional weather; explicit install."""
import importlib,time
CYCLE=('CLEARING','CLOUDS','CLEAR','EXTRASUNNY','CLEAR','CLOUDS','OVERCAST','RAIN','THUNDER','CLEARING')
STEP=600

def weather_at(weather,changed,now,x=0,y=0):
    elapsed=max(0,now-changed)
    if elapsed<STEP:return weather
    slot=int(elapsed//STEP)-1
    # Large named areas share one deterministic weather selection, across clients.
    offset=2 if y>4000 else 1 if y>1500 else 0
    return CYCLE[(slot+offset)%len(CYCLE)]

def install(api):
    if getattr(api,'environment183_installed',False):return api
    commands=importlib.import_module(api.__package__+'.pn_commands')
    original_environment=commands.environment
    original_dispatch=api.dispatch
    def environment(x=0,y=0):
        result=original_environment()
        with api.database()as db:row=db.execute('SELECT weather,changed FROM pn_environment WHERE singleton=1').fetchone()
        result.update(weather=weather_at(row['weather'],row['changed'],time.time(),x,y),rate=30,
                      weather_cycle_seconds=STEP,weather_region='Kuzey'if y>4000 else'Blaine County'if y>1500 else'Los Santos',protocol=183)
        return result
    def dispatch(path,payload,token):
        with api.LOCK:
            result,cookie=original_dispatch(path,payload,token)
            if result.get('success')and isinstance(result.get('environment'),dict):
                state=api.GTA_STATE.get(token)or result.get('spawn')or{}
                result=dict(result,environment=environment(state.get('x',0),state.get('y',0)))
            return result,cookie
    commands.environment=environment
    api.dispatch=dispatch;api.environment183_installed=True
    return api
