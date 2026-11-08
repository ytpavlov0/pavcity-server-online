/* Observe UI/RAF/native/network separately; no forced memory GC or auto reload. */
(()=>{'use strict';
let worker=null,state=null,a=null,f=null,interval=null,raf=null,fps=null;const now=()=>performance.timeOrigin+performance.now();
function bridge(){const b=window.getPAVEngineState?.().bridge;if(b&&worker)worker.postMessage({memory:b.memory,block:b.block});}
function stop(){clearInterval(interval);cancelAnimationFrame(raf);fps?.close();worker?.postMessage({stop:true});worker?.terminate();worker=null;state=a=f=null;}
function start(){
 if(worker||window.PAVMobile?.active||typeof SharedArrayBuffer==='undefined'||typeof Worker==='undefined')return;
 try{
  state=new SharedArrayBuffer(256);a=new Int32Array(state);f=new Float64Array(state,64);a[2]=document.hidden?0:1;f[0]=f[2]=now();
  const bytes=crypto.getRandomValues(new Uint8Array(12)),stream=Array.from(bytes,v=>v.toString(16).padStart(2,'0')).join('');
  worker=new Worker('/pn/fixes123/pc-monitor-v123.js');worker.postMessage({state,stream});bridge();
  const beat=()=>{if(!worker)return;Atomics.add(a,0,1);a[2]=document.hidden?0:1;const c=document.getElementById('canvas');a[3]=c?.width||0;a[4]=c?.height||0;};
  interval=setInterval(beat,250);beat();const frame=()=>{if(!worker)return;Atomics.add(a,1,1);raf=requestAnimationFrame(frame);};raf=requestAnimationFrame(frame);
  fps=new BroadcastChannel('game-fps');fps.onmessage=e=>{if(Number.isFinite(e.data?.fps)){f[2]=now();f[3]=Math.max(0,Math.min(1000,e.data.fps));Atomics.add(a,6,1);}};
 }catch{stop();}
}
addEventListener('gta-story-start',start);
addEventListener('pav-game-created',()=>{start();bridge();});
addEventListener('pav-native-bridge51',bridge);
addEventListener('pav-game-data',()=>{if(f)f[0]=now();});
addEventListener('pagehide',stop);
addEventListener('pageshow',e=>{if(e.persisted){start();bridge();}});
window.PAVPC51Diagnostics={bridge,stop,syncStarted(){return now();},syncEnded(started){if(f&&Number.isFinite(started))f[1]=Math.max(0,Math.min(120000,now()-started));}};
})();
