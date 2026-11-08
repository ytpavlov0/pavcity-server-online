/* 200: what the engine had just read when it crashed. On the first two engine crashes that carry WASM frames, the io
 * worker (io-worker200, channel game-io200:<runtime id>) is asked for its last engine reads: path, range and the
 * SHA-256 of the stored bytes. For a broken resource (rage::datResource::GetFixup, fn 2092) or compressed data that
 * does not inflate (pgStreamerDeviceHandler::ProcessDecompression, fn 2060) those blocks are also dropped from the
 * store, so the next visit downloads them again. One "[PAV200_IO]" line goes to /log with the crash code (the C98 id
 * diagnostic.js stored), the wasm heap size and the reads; tools/verify compare the hashes with the server's bytes. */
(()=>{'use strict';
const BAD=new Set([2092,2060]);
window.PAVCrash200={bind(nonce){
 if(!/^[a-f0-9]{32}$/.test(nonce||''))return;
 const crash=new BroadcastChannel('game-crash56:'+nonce),io=new BroadcastChannel('game-io200:'+nonce);let sent=0,waiting=null;
 io.onmessage=({data})=>{if(data?.recent200&&waiting){const w=waiting;waiting=null;w(data);}};
 const ask=drop=>new Promise(res=>{waiting=res;io.postMessage({ask200:'recent',drop});setTimeout(()=>{if(waiting===res){waiting=null;res(null);}},4000);});
 crash.onmessage=async({data})=>{
  const d=data?.pnCrash56,top=Array.isArray(d?.frames)?d.frames.slice(0,4).map(f=>f?.fn).filter(Number.isInteger):[];
  if(!top.length||sent>=2)return;sent++;
  const drop=top.slice(0,3).some(fn=>BAD.has(fn)),r=await ask(drop);
  let id='';try{id=String(JSON.parse(sessionStorage.getItem('pav-crash98')||'{}').id||'');}catch{}
  let heap=null;try{heap=Math.round(window.__wasmInput.memory.buffer.byteLength/1048576);}catch{}
  const row={v:200,id:/^C98-[A-F0-9]{12}$/.test(id)?id:'',trap:String(d.trap||''),role:d.role==='pthread'?'pthread':'main',top,heap_mb:heap,store:r?!!r.store:null,dropped:r?r.dropped|0:null,reads:[]};
  for(const e of r?.recent||[]){if(typeof e?.p!=='string'||!Number.isSafeInteger(e.o)||!Number.isSafeInteger(e.l))continue;row.reads.push({p:e.p.slice(0,160),o:e.o,l:e.l,h:typeof e.h==='string'?e.h.slice(0,16):undefined});if(JSON.stringify(row).length>48000)break;}
  fetch('/log',{method:'POST',credentials:'same-origin',keepalive:true,headers:{'Content-Type':'text/plain;charset=UTF-8'},body:'[PAV200_IO] '+JSON.stringify(row)}).catch(()=>{});
 };
 addEventListener('pagehide',()=>{crash.close();io.close();},{once:true});
}};
})();
