from pathlib import Path
import sys
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v93 as previous
host=previous.host
def install():
 from offline94 import install as trade
 return trade(previous.install())
from model_asset_host94 import ModelDataMixin
class Handler(ModelDataMixin,previous.Handler):
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v94.json':return self.json51(200,dict(backend_release='v94',frontend_components=94,model_data=94,mobile=217,physical_acceptance=False,magazines=True))
  return super().do_GET()
 def do_POST(self):
  url=urlsplit(self.path)
  if not url.path.startswith('/api/offline94/'):return super().do_POST()
  import json
  from http.cookies import SimpleCookie
  try:
   size=int(self.headers.get('Content-Length','0'));origin=self.headers.get('Origin')
   if origin and urlsplit(origin).netloc!=self.headers.get('Host'):self.close_connection=True;return self.json51(403,dict(success=False,error='Geçersiz istek kaynağı.'))
   if self.headers.get('Content-Type','').split(';')[0]!='application/json':self.close_connection=True;return self.json51(415,dict(success=False,error='JSON gerekli.'))
   cookies=SimpleCookie(self.headers.get('Cookie',''));token=cookies['gta_session'].value if 'gta_session'in cookies else ''
   api=host.serve_local.session_api
   if not api.authenticated61(token):self.close_connection=True;return self.json51(401,dict(success=False,error='Önce hesabına giriş yap.'))
   if not 0<size<=34*1024*1024:self.close_connection=True;return self.json51(413,dict(success=False,error='Kayıt sınırı aşıldı.'))
   data=json.loads(self.rfile.read(size))
   if not isinstance(data,dict):raise ValueError('Geçersiz kayıt isteği.')
   result,_=api.dispatch(url.path,data,token)
   return self.json51(200,result)
  except (ValueError,TypeError,UnicodeDecodeError)as e:return self.json51(400,dict(success=False,error=str(e)))
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups' not in f.parents or not f.name.endswith('-v94.db'):p.error('Disposable -v94.db under backups required')
  host.online_engine.DB_PATH=str(f)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();host.StableWorkerHTTPServer(('0.0.0.0' if args.live and args.port==8000 else '127.0.0.1',args.port),Handler).serve_forever()
