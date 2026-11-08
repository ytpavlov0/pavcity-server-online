"""Unpublished51: aggregate status, mobile201 opt-in, numeric PC diagnostics."""
from pathlib import Path
import sys,json,secrets
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'support/dev-tools'),str(R/'backups/gameplay-v51-backend')]
import run_gameplay_live_v50 as previous
from v51_extensions.population201 import install as population
from v51_extensions.pc_diagnostics51 import Diagnostics51
host=previous.host
def install():
 api=previous.install()
 if getattr(api,'pc51_installed',False):return api
 population(api);api.pc51_diagnostics=Diagnostics51();api.pc51_instance=secrets.token_hex(16);original=api.dispatch
 def dispatch(path,payload,token):
  with api.LOCK:
   p=api.PRESENCE.get(token);bound=path in('/api/gta/sync','/api/vehicles/enter','/api/vehicles/exit')
   if p and bound and('server_instance51'in payload or p.get('instance_protocol51')):
    if payload.get('server_instance51')!=api.pc51_instance:raise ValueError('Sunucu oturumu değişti; karakter durumunu yenile.')
    p['instance_protocol51']=True
    packet=payload.get('vehicle_sample')
    if isinstance(packet,dict)and packet.get('server_instance51')!=api.pc51_instance:payload={**payload,'vehicle_sample':None}
   result,cookie=original(path,payload,token)
   if result.get('success')and(path.startswith('/api/gta/')or path in('/api/vehicles/enter','/api/vehicles/exit','/api/vehicles/seat-state200')):result=dict(result,server_instance51=api.pc51_instance)
   return result,cookie
 api.dispatch=dispatch;api.pc51_installed=True;return api
class Handler(previous.Handler):
 def json51(self,code,value):
  body=json.dumps(value,allow_nan=False).encode();self.send_response(code)
  for k,v in [('Content-Type','application/json; charset=utf-8'),('Content-Length',str(len(body))),('Cache-Control','no-store'),('Cross-Origin-Opener-Policy','same-origin'),('Cross-Origin-Embedder-Policy','require-corp'),('Cross-Origin-Resource-Policy','same-origin')]:self.send_header(k,v)
  self.end_headers();self.wfile.write(body)
 def do_GET(self):
  path=urlsplit(self.path).path;api=host.serve_local.session_api
  if path=='/pn/population200-status.json':return self.json51(200,api.population201_status())
  if path=='/pn/pc51-status.json':return self.json51(200,api.pc51_diagnostics.status())
  if path=='/pn/server-capabilities-v51.json':return self.json51(200,dict(backend_release='v51',backend_implementation=51,native_sync=51,model_data_default=49,seat_protocol=200,repair_epoch_ack=181,ambient_car_traffic=False,population200_visual_enabled=False,population201_visual_opt_in=True,population201_mobile_only=True,population201_readonly=True,pc_visual_enabled=False,population200_status='/pn/population200-status.json',pc_diagnostics51='/pn/pc51-status.json',native_runtime_or_variation_parity_verified=False))
  return super().do_GET()
 def do_POST(self):
  if urlsplit(self.path).path!='/api/pc51/diagnostics':return super().do_POST()
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=4096:self.close_connection=True;return self.json51(413,dict(success=False,error='Diagnostic payload size'))
   origin=self.headers.get('Origin');target=urlsplit(origin)if origin else None
   if target and target.netloc!=self.headers.get('Host'):self.close_connection=True;return self.json51(403,dict(success=False,error='Diagnostic origin'))
   data=json.loads(self.rfile.read(size));result=host.serve_local.session_api.pc51_diagnostics.accept(data)
  except (ValueError,TypeError,UnicodeDecodeError):return self.json51(400,dict(success=False,error='Invalid numeric diagnostic'))
  return self.json51(200,result)

if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8010);p.add_argument('--fixture-db');p.add_argument('--live',action='store_true');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  fixture=Path(args.fixture_db).resolve()
  if R/'backups'not in fixture.parents or not fixture.name.endswith('-v51.db'):p.error('Use a disposable -v51.db below backups')
  host.online_engine.DB_PATH=str(fixture)
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();print('V51 PC diagnostics, nonce fences and mobile opt-in observation; port'+str(args.port),flush=True)
 host.StableWorkerHTTPServer(('0.0.0.0'if args.live and args.port==8000 else'127.0.0.1',args.port),Handler).serve_forever()
