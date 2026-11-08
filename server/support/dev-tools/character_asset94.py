"""Sparse identity-only model repair layered over the preserved face/wardrobe data."""
from pathlib import Path
import json,hashlib
import character_asset87 as previous
ROOT=Path(__file__).resolve().parents[2];DIRECTORY=ROOT/'backups/characters94';RECIPE=json.loads((DIRECTORY/'recipe.json').read_text());RELATIVE=RECIPE['relative'];SEGMENTS=[]
assert hashlib.sha256((previous.DIRECTORY/'recipe.json').read_bytes()).hexdigest()==RECIPE['priorRecipeSHA256']
for s in RECIPE['segments']:
 p=(DIRECTORY/s['file']).resolve();assert p.is_relative_to(DIRECTORY.resolve()) and p.stat().st_size==s['length'];assert hashlib.sha256(p.read_bytes()).hexdigest()==s['sha256'];SEGMENTS.append((s['offset'],s['length'],p))
def read(start,count):
 if type(start)is not int or type(count)is not int or start<0 or count<0 or count>64*1024*1024:raise ValueError('Character range bound')
 count=max(0,min(count,RECIPE['size']-start));out=bytearray(count)
 if start<RECIPE['baseBytes']:out[:min(count,RECIPE['baseBytes']-start)]=previous.read(start,min(count,RECIPE['baseBytes']-start))
 for offset,length,file in SEGMENTS:
  a=max(start,offset);b=min(start+count,offset+length)
  if a<b:
   with file.open('rb')as f:f.seek(a-offset);out[a-start:b-start]=f.read(b-a)
 return bytes(out)
