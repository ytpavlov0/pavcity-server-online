"""Immutable additive model view; stock /data files are never overwritten."""
from pathlib import Path
from urllib.parse import urlsplit,unquote,parse_qs
import json,io,gzip
import character_asset82 as characters
from model_asset_host81 import ModelDataMixin as LegacyModelDataMixin

ROOT=Path(__file__).resolve().parents[2]
BASE=(ROOT/'mirror/playgta5.com/data').resolve()
OVERLAY=(ROOT/'backups/material82-release/runtime').resolve()
PREFIX='/pn/model-data-v82/'
OVERRIDES=set(json.loads((OVERLAY.parent/'overrides.json').read_text()))
ALLOWED={r[0] for r in json.loads((OVERLAY/'manifest.json').read_text())['files']}|{'manifest.json','bootset_mobile_shaders_v16_9.json','bootset_low.json','bootset.json'}

def resolve(name):
    if not isinstance(name,str) or not name or '\\' in name or '\x00' in name or ':' in name or any(p in ('','..','.') for p in name.split('/')) or name.startswith('/'):
        raise ValueError('Invalid model data path')
    if name not in ALLOWED:raise ValueError('Unknown model data file')
    if name=='manifest.json':return characters.DIRECTORY/'manifest.json'
    root=OVERLAY if name in OVERRIDES else BASE
    target=(root/name).resolve()
    if not target.is_relative_to(root) or not target.is_file():raise ValueError('Unavailable model data file')
    return target

class ModelDataMixin(LegacyModelDataMixin):
    def do_GET(self):
        if unquote(urlsplit(self.path).path)!=PREFIX+characters.RELATIVE:return super().do_GET()
        import re
        size=characters.RECIPE['size'];start,end=0,size-1;partial=False
        if self.headers.get('Range'):
            m=re.fullmatch(r'bytes=(\d+)-(\d*)',self.headers['Range'])
            if not m:self.send_error(416);return
            start=int(m[1]);end=min(size-1,int(m[2])if m[2]else size-1);partial=True
            if start>end:self.send_error(416);return
        self.send_response(206 if partial else 200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(end-start+1));self.send_header('Accept-Ranges','bytes')
        if partial:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        while start<=end:
            b=characters.read(start,min(1024*1024,end-start+1));self.wfile.write(b);start+=len(b)
    def translate_path(self,path):
        url=urlsplit(path).path
        if url.startswith(PREFIX):
            try:return str(resolve(unquote(url[len(PREFIX):])))
            except ValueError:return str(OVERLAY/'__unavailable__')
        return super().translate_path(path)

    def do_POST(self):
        url=urlsplit(self.path)
        if url.path!=PREFIX+'batch':return super().do_POST()
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=1024*1024:self.send_error(413);return
            runs=json.loads(self.rfile.read(size))
            if not isinstance(runs,list) or len(runs)>1000:raise ValueError('Invalid batch')
            selected=[];total=0
            for row in runs:
                if not isinstance(row,list) or len(row)!=3:raise ValueError('Invalid range')
                name,start,end=row
                if type(start) is not int or type(end) is not int or start<0 or end<start:raise ValueError('Invalid range')
                file=resolve(name);length=characters.RECIPE['size']if name==characters.RELATIVE else file.stat().st_size;count=max(0,min(end+1,length)-start);total+=count
                if total>64*1024*1024:raise ValueError('Batch exceeds 64MiB')
                selected.append((name,file,start,count))
            output=io.BytesIO()
            for name,file,start,count in selected:
                if name==characters.RELATIVE:output.write(characters.read(start,count))
                else:
                    with file.open('rb') as source:source.seek(start);output.write(source.read(count))
            body=output.getvalue();compressed=parse_qs(url.query).get('gz')==['1']
            if compressed:body=gzip.compress(body,compresslevel=1)
            self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(len(body)));self.send_header('X-Run-Lengths',','.join(str(n) for _,_,_,n in selected))
            if compressed:self.send_header('Content-Encoding','gzip')
            self.end_headers();self.wfile.write(body)
        except (ValueError,TypeError,OSError):self.send_error(400,'Invalid model batch')
