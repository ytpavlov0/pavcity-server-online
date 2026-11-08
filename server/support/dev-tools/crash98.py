"""Anonymous pre-login crash intake: enums and numeric WASM locations only."""
import json,re,time,threading
from pathlib import Path
R=Path(__file__).resolve().parents[2];OUTPUT=R/'backups/engine-crashes98.jsonl';LOCK=threading.Lock();WINDOW=[]
def clean(value):
 if not isinstance(value,dict)or set(value)-{'version','id','role','stage','trap','frames','reason','read','archive'}:raise ValueError('Unknown crash field')
 if value.get('version')!=98 or not re.fullmatch('C98-[A-F0-9]{12}',str(value.get('id',''))):raise ValueError('Crash identity')
 enums={'role':['main','pthread'],'stage':['event','rejection','pthread-catch','main-catch','bridge-catch'],'trap':['unreachable','memory-bounds','oom','runtime','other'],'reason':['short-read','stream-queue','allocation','pool','unspecified']}
 for key,allowed in enums.items():
  if value.get(key)not in allowed:raise ValueError('Crash enum')
 frames=value.get('frames')
 if not isinstance(frames,list)or len(frames)>24:raise ValueError('Frames')
 for f in frames:
  if not isinstance(f,dict)or set(f)!={'fn','offset'}or type(f['fn'])is not int or not 0<=f['fn']<=1000000 or not re.fullmatch('0x[0-9a-f]{1,8}',str(f['offset'])):raise ValueError('Frame')
 reads=value.get('read',[])
 if not isinstance(reads,list)or len(reads)not in(0,4)or any(type(n)is not int or not -1<=n<=2**48 for n in reads):raise ValueError('Read counts')
 archive=value.get('archive',[])
 if not isinstance(archive,list)or len(archive)not in(0,5)or any(type(n)is not int or not 0<=n<=1000000 for n in archive):raise ValueError('Archive counters')
 return value
def accept(data):
 row=clean(data)
 with LOCK:
  now=time.monotonic();WINDOW[:]=[t for t in WINDOW if now-t<60]
  if len(WINDOW)>=120:return False
  WINDOW.append(now);path=OUTPUT
  if path.exists()and path.stat().st_size>1024*1024:path.replace(path.with_suffix('.previous.jsonl'))
  with path.open('a',encoding='utf8')as f:f.write(json.dumps(dict(received_at=time.time(),**row),separators=(',',':'))+'\n')
 return True
