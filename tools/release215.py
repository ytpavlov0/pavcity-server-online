"""215 release (frontend: loader215/bridge v215 NPC ambulance, crime215): preflight, publish (index215 + release.json frontend v215), verify."""
from pathlib import Path
import sys,json,hashlib,sqlite3,time,urllib.request,concurrent.futures
R=Path(__file__).resolve().parents[2];W=R/'mirror/playgta5.com';O=R/'backups/release215-checks';B=R/'backups/before-release215';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();mode=sys.argv[1]
proof=json.loads((O/'checks.json').read_text(encoding='utf-8-sig'));assert proof['passed']
for section,root in[('source_hashes',R),('model_hashes',R),('assets',W)]:
 for name,h in proof[section].items():assert sha(root/name)==h,name
def caps(origin):
 with urllib.request.urlopen(origin+'/pn/server-capabilities-v178.json',timeout=30)as r:return json.load(r)
if mode=='preflight':
 assert sha(W/'index.html')==proof['baseline_index_sha256'];B.mkdir(exist_ok=True)
 for name in['index.html','pn/release.json']:
  dest=B/name;assert not dest.exists();dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes((W/name).read_bytes())
 assert not(B/'online.db').exists()
 with sqlite3.connect((R/'online.db').as_uri()+'?mode=ro',uri=True)as src,sqlite3.connect(B/'online.db')as dst:src.backup(dst);assert dst.execute('PRAGMA quick_check').fetchone()[0]=='ok'
 state=(R/'backups/detached-server.json').read_bytes();(B/'detached-server.json').write_bytes(state)
 (O/'deployment.json').write_text(json.dumps(dict(prepared=True,db_backup_sha256=sha(B/'online.db'),server_state_sha256=hashlib.sha256(state).hexdigest(),frontend_only=True)));print('215 rollback prepared');raise SystemExit()
if mode=='publish':
 assert sha(W/'index.html')==proof['baseline_index_sha256']and sha(O/'index215.html')==proof['index_sha256']and not(R/'gameplay-validation-v215.json').exists()
 c=caps('http://127.0.0.1:8000');assert c['backend_release']=='v178',c
 meta=json.loads((W/'pn/release.json').read_text(encoding='utf-8-sig'));base=dict(meta.get('gameplay214')or{})
 meta.update(gameplay_release='v215',frontend_release='v215',cache_version=meta['cache_version']+1)
 meta['gameplay215']=dict(base,loader=215,bridge=215,crime=215)
 for path,data in[(W/'index.html',(O/'index215.html').read_bytes()),(W/'pn/release.json',(json.dumps(meta,indent=2)+'\n').encode())]:
  temp=path.with_suffix('.215.tmp');temp.write_bytes(data);temp.replace(path)
 proof.update(published=True,published_at=time.time());(R/'gameplay-validation-v215.json').write_text(json.dumps(proof,indent=2));print('215 frontend published');raise SystemExit()
assert mode=='verify'
def check(origin):
 local=origin.startswith('http://127.0.0.1')
 for name,h in{**{k:v for k,v in proof['assets'].items()if 'fixes215/'in k},**({'?gameplay=215':proof['index_sha256']}if local else{})}.items():
  with urllib.request.urlopen(urllib.request.Request(origin+'/'+name,headers={'User-Agent':'Mozilla/5.0 PAVCITY-verify'}),timeout=90)as r:assert hashlib.sha256(r.read()).hexdigest()==h,name
 return origin
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:origins=list(pool.map(check,['http://127.0.0.1:8000',*sys.argv[2:3]]))
receipt=json.loads((R/'gameplay-validation-v215.json').read_text(encoding='utf-8-sig'));receipt.update(verified_at=time.time(),verified_origins=origins);(R/'gameplay-validation-v215.json').write_text(json.dumps(receipt,indent=2));print('215 verified:',origins)
