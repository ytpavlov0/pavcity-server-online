"""134 backend: the live v133 chain plus features134 (AFK zone)."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v133 as previous
host=previous.host
def install():
 from features134 import install as features134
 return features134(previous.install())
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v134.json':return self.json51(200,dict(backend_release='v134',frontend_components=107,model_data=98,mobile=217,physical_acceptance=False,job_integrity=True,anticheat='log-only',staff_chat=True,admin_panel=True,weapon_damage=True,cash_give=True,pav_points=True,vehicle_sale=True,report_context=True,fixveh_doors=True,admin_details=True,mic_playtime=True,sync_error_log=True,job_interior_life=True,chat_cursor=True,server_time=True,account_settings=True,weapon_stock=True,weapon_rights=True,confiscation=True,native_cash=True,downtime_fuel=True,lockpick_item=True,hotwire=True,theft_reports=True,body_integrity=True,life_log=True,character_page=True,rentals=True,group_chats=True,events=True,afk_zone=True))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v134.db'):p.error('Disposable -v134.db under backups required')
  host.online_engine.DB_PATH=str(f)
  previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.previous.crash98.OUTPUT=f.parent/'fixture-crashes134.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else'127.0.0.1',args.port),Handler).serve_forever()
