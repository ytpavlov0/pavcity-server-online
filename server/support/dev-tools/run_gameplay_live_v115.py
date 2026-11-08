"""115 backend: the live v114 chain plus features115 (/paragonder, PAV Puan, vehicle sale
offers, report context)."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v114 as previous
host=previous.host
def install():
 from features115 import install as features115
 return features115(previous.install())
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v115.json':return self.json51(200,dict(backend_release='v115',frontend_components=107,model_data=98,mobile=217,physical_acceptance=False,job_integrity=True,anticheat='log-only',staff_chat=True,admin_panel=True,weapon_damage=True,cash_give=True,pav_points=True,vehicle_sale=True,report_context=True))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v115.db'):p.error('Disposable -v115.db under backups required')
  host.online_engine.DB_PATH=str(f)
  previous.previous.previous.crash98.OUTPUT=f.parent/'fixture-crashes115.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else'127.0.0.1',args.port),Handler).serve_forever()
