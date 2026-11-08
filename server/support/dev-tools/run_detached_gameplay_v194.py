from pathlib import Path
import os,sys,json,runpy
R=Path(__file__).resolve().parents[2];os.chdir(R)
sys.stdout=(R/'backups/detached-server.log').open('a',encoding='utf8',buffering=1);sys.stderr=sys.stdout
script=R/'support/dev-tools/run_gameplay_live_v194.py'
(R/'backups/detached-server.json').write_text(json.dumps(dict(kind='server',pid=os.getpid(),runner=str(script)),indent=2)+'\n')
print('Explicit194 service start',os.getpid(),flush=True)
sys.argv=[str(script),'--live','--port','8000'];sys.path.insert(0,str(script.parent));runpy.run_path(str(script),run_name='__main__')


