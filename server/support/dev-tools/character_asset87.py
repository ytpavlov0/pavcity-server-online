"""Bounded sparse wardrobe reads, retaining the published face archive underneath."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import character_asset82 as previous
ROOT=Path(__file__).resolve().parents[2];DIRECTORY=ROOT/'backups/characters87';RECIPE=json.loads((DIRECTORY/'recipe.json').read_text());RELATIVE=RECIPE['relative'];SEGMENTS=[]
assert RECIPE['baseBytes']==previous.RECIPE['size']
assert hashlib.sha256((previous.DIRECTORY/'recipe.json').read_bytes()).hexdigest()==RECIPE['priorRecipeSHA256']
for s in RECIPE['segments']:
 p=(DIRECTORY/s['file']).resolve();assert p.is_relative_to(DIRECTORY.resolve()) and p.stat().st_size==s['length']
 with p.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==s['sha256']
 SEGMENTS.append((s['offset'],s['length'],p))
def read(start,count):
 if type(start)is not int or type(count)is not int or start<0 or count<0 or count>64*1024*1024:raise ValueError('Character range bound')
 count=max(0,min(count,RECIPE['size']-start));out=bytearray(count)
 if start<RECIPE['baseBytes']:
  b=previous.read(start,min(count,RECIPE['baseBytes']-start));out[:len(b)]=b
 for offset,length,file in SEGMENTS:
  a=max(start,offset);b=min(start+count,offset+length)
  if a<b:
   with file.open('rb')as f:f.seek(a-offset);out[a-start:b-start]=f.read(b-a)
 return bytes(out)
def prepare():
 m=json.loads((previous.DIRECTORY/'manifest.json').read_text());model=json.loads((ROOT/'backups/models87/asset-checks.json').read_text());found=0
 for row in m['files']:
  if row[0]in(RELATIVE,model['dlcPath']):row[1]=RECIPE['size']if row[0]==RELATIVE else model['dlcBytes'];row[2]+=1;found+=1
 assert found==2
 h=hashlib.sha256()
 for start in range(0,RECIPE['size'],1024*1024):h.update(read(start,1024*1024))
 m['version']+='-wardrobe-wheel87-'+h.hexdigest()[:12];p=ROOT/'backups/models87/runtime/manifest.json';p.write_text(json.dumps(m,separators=(',',':')))
 (DIRECTORY/'asset-checks.json').write_text(json.dumps(dict(passed=True,virtualSHA256=h.hexdigest(),virtualBytes=RECIPE['size'],patchBytes=sum(n for _,n,_ in SEGMENTS),manifestSHA256=hashlib.sha256(p.read_bytes()).hexdigest(),nativeGPU=False),indent=2));print('87 combined sparse wardrobe/model manifest verified')
if __name__=='__main__':prepare()
