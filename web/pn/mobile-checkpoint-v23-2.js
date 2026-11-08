function pnReadNativeTrace(trace){
 const rows=[];
 if(!trace || trace.length<358)return rows;
 for(let id=0;id<=32;id++){
  const at=160+id*6,phase=Atomics.load(trace,at);
  if(!phase)continue;
  rows.push([id,phase,...Array.from({length:5},(_,i)=>Atomics.load(trace,at+1+i))]);
 }
 return rows;
}

/* A bounded, local-only boot breadcrumb survives a tab process being killed. */
(()=>{'use strict';const key='pav-mobile-boot-v13';let startedHere=false,lastWrite=0,lastReport=0,lastReportKey='',samples=0,attempt='';const mobile=()=>!!window.PAVMobile?.active;
function read(){try{return JSON.parse(localStorage.getItem(key)||'null');}catch{return null;}}
function report(record,force=false){
 if(!mobile())return;if(typeof record.previous?.traceNote==='string')record={...record,previous:{...record.previous,workerStage:record.previous.traceNote.slice(0,180)}};const now=Date.now(),identity=[record.state,record.stage,record.phase,record.instances,record.gpu?.phase,record.workerStage,JSON.stringify(record.native||[])].join('|');
 if(!force&&(now-lastReport<1500||identity===lastReportKey))return;lastReport=now;lastReportKey=identity;
 try{fetch('/mobile-diagnostics',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(record),keepalive:true}).catch(()=>{});}catch{}
}
function save(record){if(attempt)record.attempt=attempt;record=sampleTrace(record);report(record,record.state==='error'||record.state==='ready'||record.state==='probe-ready');try{localStorage.setItem(key,JSON.stringify(record));}catch{}}
let trace=null,seenTrace=-1,traceSampling=false;
function sampleTrace(record){
 if(!trace)return record;record.native=pnReadNativeTrace(trace);
 const states=[];let ready=0,requested=0;
 for(let id=1;id<=32;id++){const phase=Atomics.load(trace,16+id*3);if(phase){requested++;if(phase>=4&&phase<9)ready++;states.push(id+':'+phase);}}
 const io=Atomics.load(trace,4),ioid=Atomics.load(trace,5),iophase=Atomics.load(trace,6),result=Atomics.load(trace,7),shaders=Atomics.load(trace,8);
 const bridge=window.getPAVEngineState?.()?.bridge;
 if(bridge){record.heapMiB=Math.round(bridge.memory.buffer.byteLength/1048576);record.frames=new Int32Array(bridge.memory.buffer,bridge.block,16)[8]||0;}
 const last=Atomics.load(trace,2),entry=last>0?Atomics.load(trace,17+last*3):0;
 record.traceNote=('L'+last+':'+Atomics.load(trace,3)+'@'+entry+' W '+states.join(' ')+'; IO'+io+'/'+ioid+':'+iophase+'='+result+'; S'+shaders+' F'+(record.frames||0)).slice(0,180);
 record.workerStage=record.traceNote;record.instances=Math.max(record.instances||0,requested);record.readyInstances=ready;
 window.PAVMobileWorkerTrace={requested:record.instances,ready};
 return record;
}
function traceTick(){
 if(startedHere&&trace){const old=read();if(old?.state==='loading'){
 const seq=Atomics.load(trace,1);if(seq!==seenTrace){seenTrace=seq;save({...sampleTrace(old),updated:Date.now()});}
 setTimeout(traceTick,250);return;
 }}traceSampling=false;
}
window.PAVMobileCheckpoint={previous:read(),get traceBuffer(){return trace?.buffer;},start(){if(!mobile())return;startedHere=true;attempt=Array.from(crypto.getRandomValues(new Uint8Array(6)),n=>n.toString(16).padStart(2,'0')).join('');if(typeof SharedArrayBuffer!=="undefined"){trace=new Int32Array(new SharedArrayBuffer(2048));seenTrace=-1;if(!traceSampling){traceSampling=true;setTimeout(traceTick,250);}}const previous=read();if(previous?.state==='loading'||previous?.state==='error')report({release:(typeof location!=='undefined'&&['127.0.0.1','localhost'].includes(location.hostname)?'v16.18-local':'v16.18'),state:'previous-interrupted',previous},true);save({release:(typeof location!=='undefined'&&['127.0.0.1','localhost'].includes(location.hostname)?'v16.18-local':'v16.18'),state:'loading',pct:0,stage:'Başlatılıyor',updated:Date.now()});},probeComplete(){if(!mobile()||!startedHere)return;save({...read(),state:'probe-ready',pct:100,stage:'Motor tanılaması tamamlandı; şehir başlatılmadı',updated:Date.now()});},complete(){if(!mobile())return;const old=read()||{};save({...old,state:'ready',pct:100,updated:Date.now()});},fail(message){if(!mobile())return;const old=read()||{};save({...old,state:'error',stage:String(message).slice(0,180),updated:Date.now()});}};
// Recover the persisted final sample as soon as Safari recreates the page.
// This is only an observation: another tab may also have an active session.
const observedPrevious=read();
if(mobile()&&observedPrevious&&['loading','error'].includes(observedPrevious.state))report({release:(typeof location!=='undefined'&&['127.0.0.1','localhost'].includes(location.hostname)?'v16.18-local':'v16.18'),state:'previous-observed',previous:observedPrevious},true);
const channel=new BroadcastChannel('game-progress');channel.onmessage=({data})=>{if(!mobile()||!startedHere)return;const old=read();if(!old||['ready','probe-ready','error'].includes(old.state))return;const now=Date.now(),heap=data.mobileHeap,phase=data.mobileStartup?.phase||(heap?'heap-growth':null);
 if(heap){old.heapNote=(heap.ok?'Heap ':'Heap reddedildi ')+Math.round(heap.beforeMiB)+'→'+Math.round(heap.afterMiB)+' MiB';old.heapMiB=heap.afterMiB;}
 const threadLine=(data.lines||[]).filter(s=>/engine thread \d+:/.test(String(s))).pop();
 if(threadLine)old.nativeThread=String(threadLine).slice(0,120);
 if(data.mobileIO?.path)old.lastFile=String(data.mobileIO.path).slice(0,70);
 if(!threadLine&&!data.mobileIO&&!phase&&!data.mobileGpu&&!data.error&&!data.gpuLost&&now-lastWrite<700&&(!Number.isFinite(Number(data.pct))||Number(data.pct)<=Number(old.pct||0)))return;lastWrite=now;
 save({...old,pct:Math.max(old.pct||0,Math.floor(Number(data.pct)||0)),stage:typeof data.label==='string'&&!phase?data.label.slice(0,180):old.stage,workerStage:heap?(old.heapNote+' · istenen '+Number(heap.requestedMiB).toFixed(2)+' MiB · '+heap.thread).slice(0,180):phase?String(data.label||phase).slice(0,180):old.workerStage,gpu:data.mobileGpu||old.gpu,engine:window.PAVCapabilities?.engine||old.engine,phase:phase||old.phase,heapMiB:data.mobileStartup?.heapMiB??old.heapMiB,instances:data.mobileStartup?.instances??old.instances,state:data.error||data.gpuLost?'error':'loading',updated:now});
};
const crash=new BroadcastChannel('game-crash');crash.onmessage=({data})=>{
 if(!mobile()||!startedHere)return;const message='Motor hatası ('+String(data.kind||'worker')+'): '+String(data.text||'Bilinmeyen hata').split('\n')[0].slice(0,160);
 window.PAVMobileCheckpoint.fail(message);dispatchEvent(new CustomEvent('pav-engine-failed',{detail:message}));
};
function heartbeat(){
 if(mobile()&&startedHere){const old=read();if(old?.state==='loading'&&samples++<60){
 const bridge=window.getPAVEngineState?.()?.bridge;
 if(bridge){const words=new Int32Array(bridge.memory.buffer,bridge.block,16384);old.heapMiB=Math.round(bridge.memory.buffer.byteLength/1048576);old.workerStage=('Kare: '+(words[8]||0)+' · '+(old.nativeThread||'')+' · '+(old.lastFile||'')).slice(0,180);}
 report({...sampleTrace(old),phase:'page-alive',updated:Date.now()});
 }}setTimeout(heartbeat,samples<10?1000:6000);
}setTimeout(heartbeat,1000);

// Export only the numeric startup schema, never arbitrary localStorage values.
window.PAVMobileCheckpoint.debugRecord=()=>{const v=read()||{};const result={};for(const key of ['release','attempt','state','stage','workerStage','phase','engine','pct','instances','heapMiB','updated','native','gpu'])if(v[key]!==undefined)result[key]=v[key];return result;};
window.PAVMobileCheckpoint.download=()=>{const blob=new Blob([JSON.stringify({...window.PAVMobileCheckpoint.debugRecord(),lifecycle:window.PAVMobileSession?.snapshot()},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='pavcity-mobile-debug.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
addEventListener('error',event=>{if(startedHere)window.PAVMobileCheckpoint.fail('Sayfa JS hatası: '+String(event.message||'Bilinmiyor').slice(0,140));});
addEventListener('unhandledrejection',event=>{if(startedHere)window.PAVMobileCheckpoint.fail('Promise hatası: '+String(event.reason?.message||event.reason||'Bilinmiyor').slice(0,140));});
addEventListener('pagehide',()=>{if(startedHere){const v=read();if(v?.state==='loading')save({...v,phase:'pagehide-observed',updated:Date.now()});}});

})();
