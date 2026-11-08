/* Probe separate memory capabilities and select the genuine wasm32 mobile build.
 * 144: the adapter request falls back to the other power preference and to no preference before giving up (a
 * dual-GPU laptop can refuse one of them), and the message says how to get the GPU back: after a GPU hang Chrome
 * blocks WebGPU for the site until the browser is fully restarted. */
(()=>{'use strict';
window.pnHeadlessTest=['127.0.0.1','localhost'].includes(location.hostname)&&new URLSearchParams(location.search).get('nogpu')==='1';
function probeMemory(bits){try{const bytes=bits===64?[0,97,115,109,1,0,0,0,5,4,1,7,1,2]:[0,97,115,109,1,0,0,0,5,4,1,3,1,2];if(!WebAssembly.validate(new Uint8Array(bytes)))return false;const memory=new WebAssembly.Memory(bits===64?{initial:1n,maximum:2n,shared:true,address:'i64'}:{initial:1,maximum:2,shared:true});return memory.buffer instanceof SharedArrayBuffer;}catch{return false;}}
window.checkPNGTAEnvironment=async()=>{
 if(!crossOriginIsolated)throw Error('Paylaşımlı oyun belleği için PAVCITY’nin HTTPS bağlantısını kullan.');
 const mobile=!!window.PAVMobile?.active,ios=/iPhone|iPad|iPod/.test(navigator.userAgent||'')||navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1;if(window.pnHeadlessTest){window.PAVCapabilities={mobile,ios,engine:mobile?(ios||new URLSearchParams(location.search).get('headlessengine')==='ios32'?'ios32':'mobile32'):'online64',headless:true};return;}
 if(typeof WebAssembly==='undefined'||typeof SharedArrayBuffer==='undefined'||typeof Worker==='undefined'||!HTMLCanvasElement.prototype.transferControlToOffscreen)throw Error('Tarayıcı oyun işçileri veya paylaşımlı belleği sunmuyor. Uygulama içi tarayıcı yerine doğrudan Safari / Chrome kullan.');
 if(mobile&&window.PAVCapabilities?.preflightReady)return;
 const memory32=probeMemory(32),memory64=probeMemory(64);
 if(!memory32&&!memory64)throw Error('Tarayıcı paylaşımlı WebAssembly belleğini sunmuyor. Bu oturumda oyun motoru başlatılamıyor.');
 const engine=mobile||!memory64?(ios?'ios32':'mobile32'):'online64';
 if(engine!=='online64'&&!memory32)throw Error('Mobil motor için 32 bit paylaşımlı WebAssembly belleği gerekli.');
 window.PAVCapabilities={mobile,ios,memory32,memory64,engine,initialHeapMiB:engine!=='online64'?256:3072};
 if(mobile&&+new URLSearchParams(location.search).get('startupProbe')>0){window.PAVCapabilities.probe=true;return;}
 if(!navigator.gpu)throw Error('Bu tarayıcı oturumunda WebGPU kullanılamıyor. Donanım hızlandırması açık bir tarayıcı gerekli.');
 const ask=async options=>{try{return await navigator.gpu.requestAdapter(options);}catch{return null;}};
 const adapter=await ask({powerPreference:mobile?'low-power':'high-performance'})||await ask({powerPreference:mobile?'high-performance':'low-power'})||await ask();
 if(!adapter)throw Error('Kullanılabilir WebGPU grafik aygıtı bulunamadı. Chrome’u tamamen kapatıp yeniden aç: ekran kartı bir kez takılırsa Chrome bu siteyi tarayıcı kapanana kadar engeller.');
 if(!adapter.features.has('texture-compression-bc'))throw Error('Grafik aygıtı GTA’nın BC sıkıştırmalı dokularını desteklemiyor.');
 if(!adapter.features.has('float32-filterable'))throw Error('Grafik aygıtı filtrelenebilir 32 bit karakter dokularını desteklemiyor.');
 // The real GPU worker creates the mobile device. Avoid creating/destroying
 // extra devices during login while the native engine is also loading.
 if(!mobile){const probe=await adapter.requestDevice({requiredFeatures:['texture-compression-bc','float32-filterable']});probe.destroy();}
 Object.assign(window.PAVCapabilities,{bc:true,features:[...adapter.features],preflightReady:true});
};})();
