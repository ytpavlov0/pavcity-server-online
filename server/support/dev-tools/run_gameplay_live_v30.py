"""Use current mobile HTTP host with the independently pinned V29 API."""
from pathlib import Path
import sys,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_mobile_diagnostics_v16_3 as host
def install():
 sys.path.insert(0,str(ROOT/'backups/gameplay-v29-backend'));from gameplay_v29 import session_api
 from gameplay_mobile170 import install as extend_mobile
 extend_mobile(session_api)
 host.serve_local.session_api=session_api;return session_api
from donate_asset_host_v30 import ModelDataMixin
class Handler(ModelDataMixin,host.Handler):pass
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8000);parser.add_argument('--fixture-db');args=parser.parse_args()
 if args.fixture_db:host.online_engine.DB_PATH=str(Path(args.fixture_db).resolve())
 host.online_engine.init_db();install();print('V30 model/lighting host with pinned V29 gameplay; current mobile host; port'+str(args.port),flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0' if args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
