"""Serve frozen V16 gameplay plus bounded pre-login mobile diagnostics.

V17 workspace modules stay staged. This entry point explicitly loads the
saved V16 backend and uses the original production DB and current mirror.
"""
from pathlib import Path
import sys,json,time,threading,argparse,math,re
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import online_engine
sys.path.insert(0,str(ROOT/'backups/v16-before-v17'))
import serve_local
sys.path.append(str(Path(__file__).resolve().parent))  # embedded Python omits script directory
from stable_http_pool import StableWorkerHTTPServer
serve_local.ROOT=ROOT/'mirror/playgta5.com';serve_local.SUPPORT=ROOT/'support';serve_local.ENGINE_LOG=ROOT/'engine-debug.log'
LOCK=threading.Lock();RATES={};GLOBAL=[]
ALLOWED_ORIGINS={'https://old-tunnel.example','https://old-tunnel.example','http://127.0.0.1:8000','http://127.0.0.1:8002','http://127.0.0.1:8003'}

def origin_allowed(origin):
 if not isinstance(origin,str):return False
 if origin in ALLOWED_ORIGINS:return True
 try:
  with (ROOT/'PN-public-url.txt').open(encoding='utf8') as source:configured=source.read(256).strip()
 except (OSError,UnicodeError):return False
 return bool(re.fullmatch(r'https://[a-z0-9-]+\.trycloudflare\.com',configured)) and origin==configured
def clean_report(value):
 if not isinstance(value,dict):raise ValueError('Object required')
 result={}
 for key in ('release','state','stage','workerStage','phase','engine'):
  if isinstance(value.get(key),str):result[key]=value[key][:180].replace('\r',' ').replace('\n',' ')
 if isinstance(value.get('attempt'),str) and re.fullmatch(r'[a-f0-9]{12}',value['attempt']):result['attempt']=value['attempt']
 if isinstance(value.get('native'),list):
  # Fixed numeric schema: worker, phase, part+1, bytes, completions, ms, gate.
  result['native']=[]
  for row in value['native'][:33]:
   if (isinstance(row,list) and len(row)==7 and
       all(type(n) is int and 0<=n<=2147483647 for n in row) and
       row[0]<=32 and row[1]<=11 and row[2]<=128 and row[6]<=1):result['native'].append(row)
 for key,maximum in [('pct',100),('instances',128),('heapMiB',65536),('updated',10**15)]:
  n=value.get(key)
  if isinstance(n,(int,float)) and not isinstance(n,bool) and math.isfinite(n):result[key]=max(0,min(maximum,n))
 if isinstance(value.get('gpu'),dict):
  gpu=value['gpu'];result['gpu']={}
  if isinstance(gpu.get('phase'),str):result['gpu']['phase']=gpu['phase'][:60]
  for key in ('texturesMiB','buffersMiB','shaderModules','pipelinePending','queued'):
   n=gpu.get(key)
   if isinstance(n,(int,float)) and not isinstance(n,bool) and math.isfinite(n):result['gpu'][key]=max(0,min(65536,n))
 if value.get('previous') and isinstance(value['previous'],dict):
  # One bounded level; neither credentials nor arbitrary nested JSON retained.
  previous=dict(value['previous']);previous.pop('previous',None);result['previous']=clean_report(previous)
 return result
class Handler(serve_local.Handler):
 def do_POST(self):
  if urlsplit(self.path).path!='/mobile-diagnostics':return super().do_POST()
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=4096:self.send_error(413);return
   if self.headers.get('Sec-Fetch-Site','same-origin') not in ('same-origin','none') or not origin_allowed(self.headers.get('Origin')):self.send_error(403);return
   report=clean_report(json.loads(self.rfile.read(size)))
   now=time.monotonic();ip=self.headers.get('CF-Connecting-IP',self.client_address[0])[:80]
   with LOCK:
    GLOBAL[:]=[n for n in GLOBAL if now-n<60]
    recent=[n for n in RATES.get(ip,[]) if now-n<60]
    if len(recent)>=60 or len(GLOBAL)>=240:self.send_error(429);return
    if len(RATES)>256:
     for key in list(RATES):
      if not RATES[key] or now-RATES[key][-1]>=60:RATES.pop(key,None)
     if len(RATES)>256:RATES.pop(next(iter(RATES)))
    RATES[ip]=recent+[now];GLOBAL.append(now)
   with serve_local.ENGINE_LOG_LOCK:
    log=serve_local.ENGINE_LOG
    if log.exists() and log.stat().st_size>8*1024*1024:log.replace(log.with_suffix('.previous.log'))
    with log.open('a',encoding='utf8') as output:output.write('[PAV MOBILE 16.3] '+json.dumps(report,ensure_ascii=False)+'\n')
   self.send_response(204);self.send_header('Content-Length','0');self.end_headers()
  except (ValueError,TypeError):self.send_error(400)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8000);parser.add_argument('--host',default='0.0.0.0');parser.add_argument('--open',action='store_true');parser.add_argument('--fixture-db');args=parser.parse_args()
 if args.fixture_db:online_engine.DB_PATH=str(Path(args.fixture_db).resolve())
 online_engine.init_db()
 server=StableWorkerHTTPServer((args.host if args.port==8000 else '127.0.0.1',args.port),Handler)
 if args.open:
  import webbrowser;webbrowser.open('http://127.0.0.1:'+str(args.port))
 print('FrozenV16 backend with bounded pre-login mobile diagnostics; port'+str(args.port),flush=True);server.serve_forever()
if __name__=='__main__':main()
