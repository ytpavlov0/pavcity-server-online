/* Mobile lifecycle only. No engine replacement, timers pretending to be progress, or auto reloads. */
(()=>{'use strict';
if(!window.PAVMobile?.active)return;
const key='pav-mobile-session-v23-2',now=()=>performance.now();
let record={state:'idle',pct:0,bytes:0,stage:'Motor henüz başlatılmadı'},previous=null;
try{previous=JSON.parse(sessionStorage.getItem(key)||'null');}catch{}
let visibleAt=document.hidden?null:now(),activeMs=0,lastActivity=0,started=false,wanted=false,wake=null,pending=null,wakeStatus='idle',traceSequence=-1,signature='';
const activeTime=()=>activeMs+(visibleAt===null?0:now()-visibleAt);
function persist(){try{sessionStorage.setItem(key,JSON.stringify({...record,updated:Date.now(),activeSeconds:Math.floor(activeTime()/1000)}));}catch{}}
function signal(){dispatchEvent(new Event('pav-mobile-session-change'));}
function release(){const current=wake;wake=null;if(current)Promise.resolve(current.release()).catch(()=>{});}
async function acquire(){
 if(!wanted||document.hidden||wake||pending)return;
 if(!navigator.wakeLock?.request){wakeStatus='unsupported';signal();return;}
 wakeStatus='requesting';
 pending=Promise.resolve().then(async()=>{try{
  const lock=await navigator.wakeLock.request('screen');
  if(!wanted||document.hidden){await lock.release();return;}
  wake=lock;wakeStatus='held';
  lock.addEventListener('release',()=>{if(wake===lock){wake=null;wakeStatus=wanted?'released':'idle';signal();}});
 }catch{wakeStatus='denied';}finally{pending=null;signal();}});
 return pending;
}
function arm(){wanted=true;void acquire();}
function begin(){
 if(started)return;started=true;activeMs=0;visibleAt=document.hidden?null:now();lastActivity=0;
 record={state:'loading',pct:0,bytes:0,stage:'Motor kodu hazırlanıyor',started:Date.now()};signature='';traceSequence=-1;persist();arm();signal();
}
function progress(data){
 if(!started||record.state!=='loading')return;
 let changed=false;
 const pct=Number(data.pct);if(Number.isFinite(pct)&&pct>record.pct){record.pct=Math.min(99,pct);changed=true;}
 if(Number(data.dl)>0){record.bytes+=Number(data.dl);changed=true;}
 const startup=data.mobileStartup,io=data.mobileIO;
 const next=[data.label||'',startup?.phase||'',startup?.instances??'',startup?.heapMiB??'',io?.path||'',data.compiling??''].join('|');
 if(next!=='|||||'&&next!==signature){signature=next;changed=true;}
 if(data.label)record.stage=String(data.label).slice(0,180);
 if(io?.path)record.file=String(io.path).split('/').pop().slice(0,80);
 if(data.compiling!==undefined)record.shaders=data.compiling;
 if(changed){lastActivity=activeTime();persist();}
}
function trace(){
 const buffer=window.PAVMobileCheckpoint?.traceBuffer;if(!buffer||!started||record.state!=='loading')return;
 const words=new Int32Array(buffer),seq=Atomics.load(words,1);
 if(seq!==traceSequence){traceSequence=seq;lastActivity=activeTime();persist();}
}
function visibility(){
 if(document.hidden){if(visibleAt!==null)activeMs+=now()-visibleAt;visibleAt=null;release();wakeStatus='suspended';}
 else{visibleAt??=now();lastActivity=activeTime();if(wanted)void acquire();}
 persist();signal();
}
function finish(){if(!started)return;record.state='playing';record.pct=100;persist();signal();}
function cancel(){wanted=false;release();wakeStatus='idle';signal();}
function fail(message){record.state='error';record.error=String(message).slice(0,180);persist();cancel();}
window.PAVMobileSession={arm,begin,progress,trace,finish,cancel,fail,previous,
 snapshot(){trace();return {...record,hidden:document.hidden,activeSeconds:Math.floor(activeTime()/1000),quietSeconds:Math.max(0,Math.floor((activeTime()-lastActivity)/1000)),wake:wakeStatus,started};}};
const channel=new BroadcastChannel('game-progress');channel.onmessage=({data})=>progress(data);
document.addEventListener('visibilitychange',visibility);
addEventListener('pagehide',()=>{visibility();release();});
addEventListener('pageshow',()=>{if(!document.hidden)visibility();});
// A gesture can retry a denied/released lock; one pending request at a time.
document.addEventListener('pointerdown',()=>{if(wanted&&!wake&&!pending)void acquire();},{passive:true});
})();
