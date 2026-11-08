"""Sparse read-through face replacement, avoiding a second 197 MiB base archive."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];DIRECTORY=ROOT/'backups/characters82';RECIPE=json.loads((DIRECTORY/'recipe.json').read_text());RELATIVE=RECIPE['relative']
BASE=ROOT/'mirror/playgta5.com/data'/RELATIVE
assert BASE.stat().st_size==RECIPE['baseBytes']
SEGMENTS=[]
for s in RECIPE['segments']:
 p=(DIRECTORY/s['file']).resolve();assert p.is_relative_to(DIRECTORY.resolve())
 b=p.read_bytes();assert len(b)==s['length'];SEGMENTS.append((s['offset'],b))
def read(start,count):
 if type(start)is not int or type(count)is not int or start<0 or count<0 or count>64*1024*1024:raise ValueError('Character range bound')
 count=max(0,min(count,RECIPE['size']-start));out=bytearray(count)
 if start<RECIPE['baseBytes']:
  with BASE.open('rb')as f:f.seek(start);b=f.read(min(count,RECIPE['baseBytes']-start));out[:len(b)]=b
 for offset,blob in SEGMENTS:
  a=max(start,offset);b=min(start+count,offset+len(blob))
  if a<b:out[a-start:b-start]=blob[a-offset:b-offset]
 return bytes(out)
def prepare():
 p=ROOT/'backups/material82-release/runtime/manifest.json';m=json.loads(p.read_text());found=0
 for row in m['files']:
  if row[0]==RELATIVE:row[1]=RECIPE['size'];row[2]+=1;found+=1
 assert found==1
 h=hashlib.sha256()
 for start in range(0,RECIPE['size'],1024*1024):h.update(read(start,1024*1024))
 m['version']+='-jason-lucia82-'+h.hexdigest()[:12];(DIRECTORY/'manifest.json').write_text(json.dumps(m,separators=(',',':')))
 result=dict(passed=True,virtualSHA256=h.hexdigest(),virtualBytes=RECIPE['size'],baseSHA256=hashlib.file_digest(BASE.open('rb'),'sha256').hexdigest(),patchBytes=sum(len(b)for _,b in SEGMENTS),manifestSHA256=hashlib.sha256((DIRECTORY/'manifest.json').read_bytes()).hexdigest(),recipe=RECIPE)
 (DIRECTORY/'asset-checks.json').write_text(json.dumps(result,indent=2));print('Sparse character archive and combined model82 manifest verified; only',result['patchBytes'],'patch bytes stored')
if __name__=='__main__':prepare()
