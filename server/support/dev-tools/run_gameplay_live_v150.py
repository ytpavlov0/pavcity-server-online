"""150 backend: the live v135 chain plus features140 (staff /interiors, /delint) and features148 (one SQLite connection
per periodic request: sync, voice, presence, phone/jobs status; ~2.5x sync throughput)."""
from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v135 as previous
host=previous.host
def install():
 from features140 import install as features140
 from features148 import install as features148
 return features148(features140(previous.install()))
class Handler(previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v150.json':return self.json51(200,dict(backend_release='v150',frontend_components=107,model_data=98,mobile=217,physical_acceptance=False,job_integrity=True,anticheat='log-only',staff_chat=True,admin_panel=True,weapon_damage=True,cash_give=True,pav_points=True,vehicle_sale=True,report_context=True,fixveh_doors=True,admin_details=True,mic_playtime=True,sync_error_log=True,job_interior_life=True,chat_cursor=True,server_time=True,account_settings=True,weapon_stock=True,weapon_rights=True,confiscation=True,native_cash=True,downtime_fuel=True,lockpick_item=True,hotwire=True,theft_reports=True,body_integrity=True,life_log=True,character_page=True,rentals=True,group_chats=True,events=True,afk_zone=True,club_npcs=True,staff_interiors=True,sync_one_connection=True))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v150.db'):p.error('Disposable -v150.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes150.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else'127.0.0.1',args.port),Handler).serve_forever()
