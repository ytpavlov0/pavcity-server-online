"""Base-game office208 with unchanged vehicle64/account/property ownership rules."""
from pathlib import Path
import sys
from urllib.parse import urlsplit,unquote
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v64 as previous
from office65 import configure
host=previous.host
def install():
 pins=configure();api=previous.install();api.office208=pins;host.serve_local.session_api=api;return api
class Handler(previous.Handler):
 def translate_path(self,path):
  decoded=unquote(urlsplit(path).path)
  if decoded.startswith('/mlo208/'):
   root=(R/'backups/mobile-office208/public').resolve();name=decoded[len('/mlo208/'):]
   if not name or '\\'in name or '\x00'in name or ':'in name or any(p in('','..','.')for p in name.split('/')):return str(root/'__unavailable__')
   file=(root/name).resolve()
   if file.is_relative_to(root)and (name=='index.json'or name in('office/scene.json','office/ground.bin')or name.startswith('models/')and file.suffix=='.glb'):return str(file)
   return str(root/'__unavailable__')
  return super().translate_path(path)
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v65.json':return self.json51(200,dict(backend_release='v65',seat_protocol=200,office_interior_available=True,office_package='mobile-office208',office_native_acceptance=False,full_mobile_parity=False))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups'not in fixture.parents or not fixture.name.endswith('-v65.db'):p.error('Disposable -v65.db under backups required')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('Backend65: verified base-game office208, vehicle64 retained',flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
