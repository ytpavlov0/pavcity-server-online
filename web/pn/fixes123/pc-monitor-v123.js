/* Tiny independent observer: no engine instantiation, no input/world mutation. */
(()=>{'use strict';
let config=null,lastAt=0,sequence=0,pending=false,timer=null;const seen=new Map();
function age(key,value,now){let row=seen.get(key);if(!row||row.value!==value){row={value,at:now};seen.set(key,row);}return Math.max(0,Math.min(3600000,now-row.at));}
function sample(now=performance.timeOrigin+performance.now()){
 if(!config)return null;
 const a=new Int32Array(config.state),f=new Float64Array(config.state,64),out={version:51,stream:config.stream,seq:++sequence,
 visible:Atomics.load(a,2),ui_interval_age_ms:age('ui',Atomics.load(a,0),now),ui_raf_age_ms:age('raf',Atomics.load(a,1),now),
 sync_age_ms:Math.min(3600000,Math.max(0,now-f[0])),sync_ms:f[1],fps_age_ms:Math.min(3600000,Math.max(0,now-f[2])),fps:f[3],
 fps_available:Atomics.load(a,6)?1:0,buffer_width:Atomics.load(a,3),buffer_height:Atomics.load(a,4),monitor_gap_ms:lastAt?Math.min(3600000,Math.max(0,now-lastAt)):0};
 lastAt=now;
 if(config.memory)try{
  const n=new Int32Array(config.memory.buffer,config.block,16384),nf=new Float32Array(config.memory.buffer,config.block,16384);
  Object.assign(out,{native_tick_age_ms:age('native',Atomics.load(n,8),now),native_done_age_ms:age('done',Atomics.load(n,9),now),native_phase:Math.max(0,Math.min(99,Atomics.load(n,14102))),native_phase_age_ms:age('phase',Atomics.load(n,14104),now),native_ms:Math.max(0,Math.min(60000,nf[14105]||0)),max_native_ms:Math.max(0,Math.min(3600000,nf[14106]||0)),slow_native_count:Math.max(0,Atomics.load(n,14107)),max_phase_ms:Math.max(0,Math.min(3600000,nf[14108]||0)),slow_phase_id:Math.max(0,Math.min(99,Atomics.load(n,14109))),engine_status:Math.max(-2,Math.min(5,Atomics.load(n,2))),entry_locked:n[62]||n[7610]||n[71]||n[72]?1:0,heap_mib:config.memory.buffer.byteLength/1048576});
 }catch{out.engine_status=-2;}
 return out;
}
async function report(){
 if(!config||pending)return;
 const data=sample();if(!data)return;pending=true;
 try{await fetch('/api/pc51/diagnostics',{method:'POST',credentials:'omit',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),signal:AbortSignal.timeout(5000)});}catch{}finally{pending=false;}
}
self.onmessage=e=>{
 if(e.data?.stop){clearInterval(timer);timer=null;config=null;return;}
 if(e.data?.state){config={...e.data};seen.clear();lastAt=0;if(!timer)timer=setInterval(report,5000);}
 else if(e.data?.memory&&config){config.memory=e.data.memory;config.block=e.data.block;seen.clear();}
};
// CPU tests invoke the exact sampler without starting timers or a native world.
self.PAVPC51MonitorSample=sample;
})();
