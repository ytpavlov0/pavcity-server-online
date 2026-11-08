"""192 backend: 191 + crime and rescue systems (crime192.py: chop shop, wanted level and NPC arrests with fines,
impound release fee for stolen cars, 60 s medic window with /canlandir and NPC paramedic revive, weapon attachments).
Also fixes 190: the job point tolerance was installed on the root pn_roleplay module, but the live API uses
gameplay_v29.pn_roleplay, so the vine-row point still needed 5 m in 3D. Now that module is patched as well.
/pn/server-capabilities-v192.json: counts."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v191 as previous
import run_gameplay_live_v190 as v190
import crime192
host=previous.host;API=previous.API
def fix190():
 import gameplay_v29.pn_roleplay as rp
 if not hasattr(rp.near,'strict190'):rp.near=v190.tolerant(rp.near,v190.job_points(rp.JOBS))
 return rp
def install():
 api=previous.install()
 if getattr(api,'v192_installed',False):return api
 fix190();crime192.install(api);api.v192_installed=True;API[0]=api;return api
class Handler(previous.Handler):
 def get164(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v192.json':
   api=API[0];st=dict(getattr(api,'crime192',{}).get('stats',{}))if api else{}
   return self.json51(200,dict(backend_release='v192',base_release='v191',v192=st,v191=previous.STATS,v190=v190.STATS))
  return super().get164()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v192.db'):p.error('Disposable -v192.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes192.jsonl'
 elif not args.live:p.error('Fixture DB required')
 pp=previous.previous.previous.previous.previous.previous.previous
 for _ in range(25):pp=pp.previous
 host.online_engine.init_db();install();pp.Server(('127.0.0.1',args.port),Handler,max_workers=pp.WORKERS,pending_requests=pp.QUEUE).serve_forever()
