"""Bounded, numeric-only anonymous performance hints, never game authority."""
from collections import OrderedDict
import math,re,time,threading

LIMITS = {
 'seq':(0,2**31-1),'visible':(0,1),'ui_interval_age_ms':(0,3600000),
 'ui_raf_age_ms':(0,3600000),'native_tick_age_ms':(0,3600000),
 'native_done_age_ms':(0,3600000),'native_phase':(0,99),'native_phase_age_ms':(0,3600000),
 'native_ms':(0,60000),'max_native_ms':(0,3600000),'slow_native_count':(0,2**31-1),
 'engine_status':(-2,5),'entry_locked':(0,1),'sync_age_ms':(0,3600000),
 'sync_ms':(0,120000),'fps_age_ms':(0,3600000),'fps':(0,1000),
 'heap_mib':(0,32768),'buffer_width':(0,16384),'buffer_height':(0,16384),
 'monitor_gap_ms':(0,3600000),'max_phase_ms':(0,3600000),'slow_phase_id':(0,99),'fps_available':(0,1),
}

class Diagnostics51:
 def __init__(self,clock=time.monotonic):
  self.clock=clock;self.lock=threading.RLock();self.streams=OrderedDict();self.reports=0
 def accept(self,payload):
  if not isinstance(payload,dict)or set(payload)-{'version','stream',*LIMITS}:raise ValueError('Unknown diagnostic field')
  if payload.get('version')!=51 or not isinstance(payload.get('stream'),str)or not re.fullmatch('[a-f0-9]{24}',payload['stream']):raise ValueError('Invalid diagnostic version/stream')
  if 'seq'not in payload:raise ValueError('Diagnostic sequence required')
  sample={k:v for k,v in payload.items()if k in LIMITS}
  for k,v in sample.items():
   lo,hi=LIMITS[k]
   if type(v)not in(int,float)or not math.isfinite(v)or not lo<=v<=hi:raise ValueError('Invalid numeric diagnostic')
  if type(sample['seq'])is not int:raise ValueError('Integer diagnostic sequence required')
  with self.lock:
   now=self.clock();key=payload['stream'];old=self.streams.get(key)
   if old and(sample['seq']<=old['sample']['seq']or now-old['at']<.9):return dict(success=True,accepted=False)
   peaks=dict(old.get('peaks',{}))if old else{}
   if sample.get('visible')==1:
    keys=['ui_interval_age_ms','ui_raf_age_ms','monitor_gap_ms']
    if sample.get('engine_status')==1 and sample.get('entry_locked')==0:
     keys+=['native_tick_age_ms','native_done_age_ms','sync_age_ms']
     if sample.get('fps_available')==1:keys.append('fps_age_ms')
    for k in keys:
     if k in sample:peaks[k]=max(peaks.get(k,0),sample[k])
   self.streams[key]=dict(at=now,sample=sample,peaks=peaks);self.streams.move_to_end(key)
   while len(self.streams)>32:self.streams.popitem(last=False)
   self.reports+=1
   return dict(success=True,accepted=True)
 def status(self):
  with self.lock:
   now=self.clock();fresh=[r for r in self.streams.values()if 0<=now-r['at']<120]
   latest=max(fresh,key=lambda r:r['at'])if fresh else None
   return dict(version=51,reports=self.reports,recent_streams=len(fresh),
               latest_age_ms=round((now-latest['at'])*1000)if latest else None,
               latest=dict(latest['sample'])if latest else None,
               peaks=dict(latest['peaks'])if latest else None,
               diagnostic_hints_only=True,freeze_root_cause_verified=False)
