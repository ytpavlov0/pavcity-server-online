/* Capture the original exception before Emscripten's thread-crash hook traps.
 * Only enum values and bounded numeric stack locations leave this runtime. */
(()=>{'use strict';
 const roles=new Set(['main','pthread']);
 const stages=new Set(['event','rejection','pthread-catch','main-catch','bridge-catch']);
 function parse(error){
  const text=typeof error?.stack==='string'?error.stack:typeof error==='string'?error:'';
  const s=text.slice(0,16384),frames=[],js=[];
  const trap=/unreachable/i.test(s)?'unreachable':/out of bounds/i.test(s)?'memory-bounds':/out of memory|\bOOM\b/i.test(s)?'oom':/RuntimeError/i.test(s)?'runtime':'other';
  const exception=['TypeError','RangeError','ReferenceError','SyntaxError','RuntimeError'].find(n=>error?.name===n||new RegExp('(?:^|\\b)'+n+':').test(s))||'Error';
  const category=/Cannot read properties/i.test(s)?'missing-property':/not a function/i.test(s)?'not-callable':/Invalid typed array length|Invalid array buffer length/i.test(s)?'invalid-buffer':/offset is out of bounds/i.test(s)?'buffer-bounds':/Maximum call stack/i.test(s)?'stack-overflow':'unspecified';
  for(const m of s.matchAll(/wasm-function\[(\d{1,7})\]:(0x[0-9a-f]{1,12})(?![0-9a-f])/gi)){
   const fn=Number(m[1]),offset=Number(m[2]);
   if(fn<=1000000&&Number.isSafeInteger(offset)&&offset<=0xffffffff)frames.push({fn,offset:'0x'+offset.toString(16)});
   if(frames.length===24)break;
  }
  for(const m of s.matchAll(/(game-pn-online-v15-gameplay-v(?:41|56(?:-candidate)?)|pn_native_bridge-v52|loader-pn-online-v16-gameplay-v(?:55|56(?:-candidate)?))\.js(?:\?[^\s):]*)?:(\d{1,7}):(\d{1,7})/g)){
   js.push({unit:m[1].startsWith('game-')?'core':m[1].startsWith('pn_native')?'bridge':'loader',line:Number(m[2]),column:Number(m[3])});if(js.length===8)break;
  }
  return{trap,exception,category,frames,js};
 }
 function clean(d){
  if(!d||!['unreachable','memory-bounds','oom','runtime','other'].includes(d.trap))return null;
  return{trap:d.trap,exception:['TypeError','RangeError','ReferenceError','SyntaxError','RuntimeError','Error'].includes(d.exception)?d.exception:'Error',category:['missing-property','not-callable','invalid-buffer','buffer-bounds','stack-overflow','unspecified'].includes(d.category)?d.category:'unspecified',
   frames:Array.isArray(d.frames)?d.frames.slice(0,24).filter(f=>Number.isInteger(f?.fn)&&f.fn>=0&&f.fn<=1000000&&typeof f.offset==='string'&&/^0x[0-9a-f]{1,8}$/i.test(f.offset)).map(f=>({fn:f.fn,offset:f.offset.toLowerCase()})):[],
   js:Array.isArray(d.js)?d.js.slice(0,8).filter(f=>['core','bridge','loader'].includes(f?.unit)&&Number.isInteger(f.line)&&f.line>=0&&f.line<=9999999&&Number.isInteger(f.column)&&f.column>=0&&f.column<=9999999).map(f=>({unit:f.unit,line:f.line,column:f.column})):[]};
 }
 function installWorker(nonce,env=globalThis){
  if(!/^[a-f0-9]{32}$/.test(nonce||''))return null;
  const channel=new env.BroadcastChannel('game-crash56:'+nonce);let count=0;const seen=new Set();
  const capture=(error,stage='event')=>{
   try{
    const data=parse(error),role=env.name==='em-pthread'?'pthread':'main';
    const key=JSON.stringify([data,stage]);if(count>=4||seen.has(key))return;seen.add(key);count++;
    channel.postMessage({pnCrash56:{...data,role,stage:stages.has(stage)?stage:'event'}});
   }catch{/* Reporting must never replace the original exception. */}
  };
  env.__pavCapture56=capture;
  env.addEventListener('error',e=>capture(e.error||e.message,'event'));
  env.addEventListener('unhandledrejection',e=>capture(e.reason,'rejection'));
  return capture;
 }
 function bind(nonce,deps){
  if(!/^[a-f0-9]{32}$/.test(nonce||''))throw Error('Invalid crash runtime');
  const channel=new deps.BroadcastChannel('game-crash56:'+nonce),seen=new Set();let count=0;
  const receive=({data})=>{
   const d=data?.pnCrash56,row=clean(d);if(!row||!roles.has(d.role)||!stages.has(d.stage)||count>=6)return;
   const key=JSON.stringify([row,d.role,d.stage]);if(seen.has(key))return;seen.add(key);count++;
   const report={version:57,id:deps.id(),source:'scoped-engine',variant:'pc64',role:d.role,stage:d.stage,...row};
   if(!/^C57-[A-F0-9]{12}$/.test(report.id))return;
   const body='[PAV57_CRASH] '+JSON.stringify(report)+'\n';if(body.length>6000)return;
   Promise.resolve(deps.send(body)).then(ok=>deps.note(report.id,ok),()=>deps.note(report.id,false));
  };
  channel.onmessage=receive;
  const pageError=event=>receive({data:{pnCrash56:{...parse(event.detail),role:'main',stage:'event'}}});
  deps.listen?.(pageError);
  return()=>{channel.close();deps.unlisten?.(pageError);};
 }
 if(typeof module==='object'&&module.exports){module.exports={parse,clean,installWorker,bind};return;}
 if(typeof document==='undefined'){
  globalThis.PAVCrash56={installWorker};
  installWorker(new URLSearchParams(self.location.search).get('runtime56'));return;
 }
 window.PAVCrash57={bind:nonce=>{
  const stop=bind(nonce,{BroadcastChannel,listen:f=>addEventListener('pn-native-error',f),unlisten:f=>removeEventListener('pn-native-error',f),id:()=>'C57-'+crypto.randomUUID().replaceAll('-','').slice(0,12).toUpperCase(),send:body=>fetch('/log',{method:'POST',credentials:'same-origin',keepalive:true,headers:{'Content-Type':'text/plain;charset=UTF-8'},body}).then(r=>r.ok),note:(code,ok)=>{
   const host=document.querySelector('.pav-arrival-error:not([hidden])')?.parentElement||document.getElementById('hud');if(!host)return;
   let el=document.getElementById('pav-crash57-note');if(!el){el=document.createElement('small');el.id='pav-crash57-note';host.append(el);}el.textContent='Tanılama kodu: '+code+(ok?' · Kaydedildi':' · Gönderilemedi');
  }});addEventListener('pagehide',stop,{once:true});return stop;
 }};
})();
