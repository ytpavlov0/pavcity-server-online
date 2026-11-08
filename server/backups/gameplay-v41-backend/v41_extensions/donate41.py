"""Explicitly requested addon activation. No startup grants or wallet changes."""
from pathlib import Path
import json,hashlib
MODELS={
 'pavtofas':dict(name='Tofaş · Özel sedan',category='Özel araç',accent='#d6e8ea',custom=True),
 'pavbus':dict(name='Denizli · Şehir otobüsü',category='Şehir aracı',accent='#a9da8a',custom=True),
 'g65':dict(name='Mercedes-Benz G65 AMG · 2013',category='İndirilen model',accent='#dec386',custom=True,author='smokey8808',source='https://www.gta5-mods.com/vehicles/2013-mercedes-benz-g65-amg-add-on'),
 'audquattros':dict(name='Audi Quattro Sport · 1983',category='İndirilen model',accent='#ff776e',custom=True,author='Wanted188, METALman',source='https://www.gta5-mods.com/vehicles/audi-quattro-sport-83-lods-template-add-on-tuning'),
}
ALIASES={'tofas':'pavtofas','tofaş':'pavtofas','otobus':'pavbus','otobüs':'pavbus','denizli':'pavbus','audi':'audquattros','quattro':'audquattros','mercedes':'g65','bmw':'i8','r34':'skyline'}
def install(api,receipt):
 if getattr(api,'donate41_installed',False):return api
 proof=json.loads(Path(receipt).read_text());pack=Path(receipt).parent/'runtime'/proof['dlc_path']
 assert proof['models']==list(MODELS)and hashlib.sha256(pack.read_bytes()).hexdigest()==proof['dlc_sha256'],'Addon archive changed; validate before activation'
 world=api.world;world.SPAWN_MODELS.update(MODELS);world.DONATE_MODELS.update(MODELS)
 old_vehicle_dispatch=world.dispatch
 def vehicle_dispatch(path,uid,token,payload,p,state,presences):
  if path=='/api/vehicles/enter':
   with world.database()as db:row=db.execute('SELECT model FROM pn_vehicles WHERE id=?',(payload.get('id'),)).fetchone()
   if row and row['model']=='audquattros':
    # This exact fragment has only two physical seat anchors. Keep all the
    # original lock/key/proximity/life checks in the existing dispatcher.
    requested=payload.get('seat');current=world.occupation(p['char_id'])
    if requested is None:requested=current[1]if current[0]==payload.get('id')else next((s for s in(-1,0)if(payload.get('id'),s)not in world.SEATS),-2)
    if type(requested)is not int or requested not in(-1,0):raise ValueError('Audi Quattro iki koltuklu; uygun boş koltuk seç.')
    payload={**payload,'seat':requested}
  return old_vehicle_dispatch(path,uid,token,payload,p,state,presences)
 world.dispatch=vehicle_dispatch
 original=api.dispatch;old_location=world.spawn_location
 def spawn_location(state,model='sultan',excluding=0):
  # A full-size custom bus needs the same clearance as the stock bus.
  with world.database()as db:
   bus=db.execute("SELECT 1 FROM pn_vehicles WHERE active=1 AND model='pavbus' AND id<>? AND abs(json_extract(state,'$.x')-?)<50 AND abs(json_extract(state,'$.y')-?)<50 LIMIT 1",(excluding,state['x'],state['y'])).fetchone()
  return old_location(state,'bus'if model=='pavbus'or bus else model,excluding)
 def dispatch(path,payload,token):
  if path.startswith('/api/vehicles/')and isinstance(payload.get('model'),str):
   code=payload['model'].strip().lower();payload={**payload,'model':ALIASES.get(code,code)}
  if path=='/api/chat/send'and isinstance(payload.get('message'),str):
   parts=payload['message'].split()
   if len(parts)==3 and parts[0].lower()in('/donatearacver','/donatever'):
    parts[0]='/donatearacver';parts[2]=ALIASES.get(parts[2].lower(),parts[2].lower());payload={**payload,'message':' '.join(parts)}
  return original(path,payload,token)
 world.spawn_location=spawn_location;api.dispatch=dispatch;api.donate41_installed=True
 return api
