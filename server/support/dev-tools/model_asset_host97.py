"""Exact online and stock Story manifests, with a restored playlist alias."""
from pathlib import Path
from urllib.parse import urlsplit,unquote,parse_qs
import json,io,gzip,re
import model_asset_host94 as old
import character_asset94 as characters
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'mirror/playgta5.com/data';OVERLAY=ROOT/'backups/models97/runtime'
PREFIX='/pn/model-data-v97/';STORY='/pn/story-data-v97/';ALIAS='common/data/ugc/ytpavlovPlaylists_00.ugc'
ONLINE=json.loads((OVERLAY/'manifest.json').read_text());STOCK=json.loads((OVERLAY/'story-manifest.json').read_text())
ALLOWED=[{r[0]for r in m['files']}|{'manifest.json','bootset.json','bootset_low.json','bootset_mobile_shaders_v16_9.json'}for m in[ONLINE,STOCK]]
def resolve(name,story=False):
 if not isinstance(name,str) or not name or '\\'in name or '\x00'in name or ':'in name or name.startswith('/') or any(p in('','..','.')for p in name.split('/')):raise ValueError('Invalid model path')
 if name not in ALLOWED[int(story)]:raise ValueError('Unknown model file')
 path=OVERLAY/('story-manifest.json'if story else'manifest.json')if name=='manifest.json'else OVERLAY/name if name==ALIAS or(not story and name=='x64/dlcPacks/pavcity36/dlc.rpf')else BASE/name if story else old.resolve(name)
 if not path.is_file():raise ValueError('Unavailable model file')
 return path
class ModelDataMixin:
 def data97(self):
  path=unquote(urlsplit(self.path).path)
  for prefix,story in[(PREFIX,False),(STORY,True)]:
   if path.startswith(prefix):return path[len(prefix):],story
  return None
 def translate_path(self,path):
  selected=self.data97()
  if selected:
   try:return str(resolve(*selected))
   except ValueError:return str(OVERLAY/'__unavailable__')
  return super().translate_path(path)
 def special97(self,head=False):
  selected=self.data97()
  if not selected or selected!=(characters.RELATIVE,False):return False
  size=characters.RECIPE['size'];start,end=0,size-1;partial=False
  if self.headers.get('Range'):
   m=re.fullmatch(r'bytes=(\d+)-(\d*)',self.headers['Range'])
   if not m:self.send_error(416);return True
   start=int(m[1]);end=min(size-1,int(m[2])if m[2]else size-1);partial=True
   if start>end:self.send_error(416);return True
  self.send_response(206 if partial else 200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes')
  if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
  self.end_headers()
  if not head:
   while start<=end:
    b=characters.read(start,min(1024*1024,end-start+1))
    if not b:raise OSError('Incomplete character archive')
    self.wfile.write(b);start+=len(b)
  return True
 def do_HEAD(self):
  if not self.special97(True):return super().do_HEAD()
 def do_GET(self):
  if not self.special97():return super().do_GET()
 def do_POST(self):
  selected=self.data97()
  if not selected or selected[0]!='batch':return super().do_POST()
  story=selected[1]
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=1024*1024:self.send_error(413);return
   runs=json.loads(self.rfile.read(size))
   if not isinstance(runs,list)or len(runs)>1000:raise ValueError('Invalid batch')
   chosen=[];total=0
   for row in runs:
    if not isinstance(row,list)or len(row)!=3:raise ValueError('Invalid row')
    name,start,end=row
    if type(start)is not int or type(end)is not int or start<0 or end<start:raise ValueError('Invalid range')
    path=resolve(name,story);length=characters.RECIPE['size']if not story and name==characters.RELATIVE else path.stat().st_size
    count=max(0,min(end+1,length)-start);total+=count
    if total>64*1024*1024:raise ValueError('Batch too large')
    chosen.append((name,path,start,count))
   out=io.BytesIO()
   for name,path,start,count in chosen:
    if not story and name==characters.RELATIVE:data=characters.read(start,count)
    else:
     with path.open('rb')as f:f.seek(start);data=f.read(count)
    if len(data)!=count:raise OSError('Incomplete model data')
    out.write(data)
   body=out.getvalue();compressed=parse_qs(urlsplit(self.path).query).get('gz')==['1']
   if compressed:body=gzip.compress(body,compresslevel=1)
   self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(len(body)));self.send_header('X-Run-Lengths',','.join(str(x[3])for x in chosen))
   if compressed:self.send_header('Content-Encoding','gzip')
   self.end_headers();self.wfile.write(body)
  except(ValueError,TypeError,OSError):self.send_error(400,'Invalid model batch')
