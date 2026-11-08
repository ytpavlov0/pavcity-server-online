/* 196: the ping line shows the realtime connection (positions, cars, voice) and the HTTP sync separately.
 * 194: memory line without the shared-heap double count; a network probe (plain GET through Cloudflare, its colo
 * from cf-ray) separates the path delay from the sync's own time; the GPU worker verdict points at the Akıcı profile.
 * 193: diag192 + memory tracking + one game tab per browser.
 * Memory (/cpu): the page's total memory incl. workers and the engine's WebAssembly heap
 * (performance.measureUserAgentSpecificMemory, every 30 s), the engine heap size, and the growth over the last 10 and
 * 30 minutes; a steady climb is a leak, a flat line is not. GPU memory is not visible to the page (Chrome: Shift+Esc).
 * One game tab: the io worker opens the game store with exclusive handles, so a second game tab in the same browser
 * profile waited, then stalled (~22 %, "Compiling the engine"). A Web Lock now tells the second tab at once to use an
 * incognito window or another Chrome profile, and starting the game there is refused until the first tab closes.
 * 192: /showfps and /cpu (client commands, nothing is sent to the server).
 * /showfps: FPS and ping in the top-right corner (remembered, pn-showfps192).
 * /cpu: a live diagnostic panel (1 s) built from what the page already has:
 *  - FPS now / lowest / average over 10 s (game-fps channel, 2 per second), page main-thread long tasks,
 *    (the GPU worker and bridge reports go straight to the server log, where they can be read during a test),
 *  - ping split with Resource Timing of /api/gta/sync: connection, waiting for the server, download, and the delay
 *    before the page handled the answer; the server's own sync time from /pn/server-capabilities-v164.json,
 *  - JS heap, CPU cores, device memory; a one-line verdict of the most likely bottleneck and a "Kopyala" button. */
(()=>{'use strict';
const S={fps:null,fpsAt:0,hist:[],long:[],sync:[],server:null,serverAt:0};
try{new BroadcastChannel('game-fps').onmessage=e=>{const v=Number(e.data?.fps);if(Number.isFinite(v)){S.fps=v;S.fpsAt=performance.now();S.hist.push({at:S.fpsAt,v});if(S.hist.length>60)S.hist.shift();}};}catch{}
try{new PerformanceObserver(l=>{for(const e of l.getEntries())S.long.push({at:e.startTime,ms:e.duration});}).observe({type:'longtask',buffered:false});}catch{}
try{new PerformanceObserver(l=>{for(const e of l.getEntries())if(e.name.includes('/api/gta/sync')&&e.responseEnd>0){S.sync.push({conn:Math.max(0,e.requestStart-e.startTime),wait:Math.max(0,e.responseStart-e.requestStart),down:Math.max(0,e.responseEnd-e.responseStart),size:e.transferSize||e.encodedBodySize||0,end:e.responseEnd,proto:e.nextHopProtocol});if(S.sync.length>20)S.sync.shift();}}).observe({type:'resource',buffered:false});}catch{}
// memory: total (page + workers + wasm heaps) every 30 s, engine heap from the bridge, kept for 40 minutes
const MEM=[];let engineMem=null;S.mem=MEM;
(function hook(){if(typeof window.attachPNBridge!=='function'||window.attachPNBridge.d193){setTimeout(hook,250);return;}
 const orig=window.attachPNBridge;window.attachPNBridge=Object.assign(data=>{engineMem=data?.memory||null;return orig(data);},{d193:true});})();
async function sample(){
 const total=null;  // measureUserAgentSpecificMemory counts the shared engine heap once per thread (27 GB for 3 GB)
 const wasm=engineMem?.buffer?.byteLength??null,js=performance.memory?.usedJSHeapSize??null;
 MEM.push({at:performance.now(),total,wasm,js});while(MEM.length&&performance.now()-MEM[0].at>40*60000)MEM.shift();}
setInterval(sample,30000);setTimeout(sample,3000);
const mb=b=>b==null?'?':Math.round(b/1048576)+' MB';
function growth(min,key){const now=performance.now(),last=MEM[MEM.length-1];if(!last||last[key]==null)return null;const old=MEM.find(m=>now-m.at<=min*60000+15000&&m[key]!=null);if(!old||last.at-old.at<min*60000*.8)return null;return last[key]-old[key];}
// one game tab per browser profile
let tabBusy=false;
function tabLock(){if(!navigator.locks)return;navigator.locks.request('pavcity-oyun-193',{ifAvailable:true},lock=>{
 if(!lock){tabBusy=true;banner(true);setTimeout(tabLock,3000);return;}
 tabBusy=false;banner(false);return new Promise(()=>{});});}
function banner(show){let b=document.getElementById('pav-tab193');
 if(!show){b?.remove();return;}
 if(!b){b=document.createElement('div');b.id='pav-tab193';b.setAttribute('role','alert');
  b.style.cssText='position:fixed;left:50%;top:14px;transform:translateX(-50%);z-index:2147483001;max-width:min(620px,94vw);padding:12px 16px;border-radius:12px;background:rgba(40,12,24,.96);border:1px solid rgba(255,95,168,.6);color:#fff;font:600 14px/1.45 "Segoe UI",system-ui,sans-serif;box-shadow:0 12px 40px rgba(0,0,0,.5);text-align:center';
  b.textContent='Oyun bu tarayıcıda başka bir sekmede açık. Aynı tarayıcıda iki oyun birlikte çalışamaz (oyun dosyaları tek sekmeye açılır). İkinci hesap için gizli pencere (Ctrl+Shift+N) veya başka bir Chrome profili kullan; ya da diğer sekmeyi kapat, bu sekme kendiliğinden devam eder.';
  (document.body||document.documentElement).append(b);}}
const guard=name=>{(function wrap(){const f=window[name];if(typeof f!=='function'||f.d193){setTimeout(wrap,250);return;}
 window[name]=Object.assign(async(...a)=>{if(tabBusy){banner(true);throw Error('Oyun başka bir sekmede açık. İkinci hesap için gizli pencere veya başka bir Chrome profili kullan.');}return f(...a);},{d193:true});})();};
if(!/[?&]multitab=1/.test(location.search)){tabLock();guard('startPNGTA');guard('startPAVPreview');}
const on={fps:(()=>{try{return localStorage.getItem('pn-showfps192')==='1';}catch{return false;}})(),cpu:false};
const css='position:fixed;right:10px;z-index:2147482000;font:600 12px/1.35 Consolas,monospace;color:#eafff0;background:rgba(8,10,16,.72);border:1px solid rgba(255,255,255,.12);border-radius:10px;padding:6px 10px;text-shadow:0 1px 2px #000;';
let fpsEl=null,cpuEl=null;
const avg=a=>a.length?a.reduce((x,y)=>x+y,0)/a.length:null;const r=v=>v==null||!Number.isFinite(v)?'?':Math.round(v);
function pingParts(){const s=S.sync.slice(-10);if(!s.length)return null;return{conn:avg(s.map(x=>x.conn)),wait:avg(s.map(x=>x.wait)),down:avg(s.map(x=>x.down)),kb:avg(s.map(x=>x.size))/1024,proto:s[s.length-1].proto||'?'};}
async function server(){if(performance.now()-S.serverAt<5000)return;S.serverAt=performance.now();try{const t0=performance.now(),res=await fetch('/pn/server-capabilities-v164.json?p='+Date.now(),{cache:'no-store'}),t1=performance.now();const c=await res.json();S.net=S.net||[];S.net.push(t1-t0);if(S.net.length>6)S.net.shift();S.colo=((res.headers.get('cf-ray')||'').split('-')[1]||'')||S.colo;const row=(c.last_minute||[]).find(x=>x.cat==='/api/gta/sync');S.server=row?{ms:row.wall_ms_avg,n:row.n}:null;}catch{}}
function fpsWin(){const h=S.hist.filter(x=>performance.now()-x.at<10000).map(x=>x.v);return h.length?{min:Math.min(...h),avg:avg(h),drops:h.filter(v=>v<25).length,n:h.length}:null;}
function verdict(p){
 const fw=fpsWin(),lt=S.long.filter(x=>performance.now()-x.at<10000),ltMax=lt.length?Math.max(...lt.map(x=>x.ms)):0;
 const g30=growth(30,'wasm');if(g30!=null&&g30>300*1048576)return'Oyun motoru belleği sürekli artıyor (son 30 dk +'+mb(g30)+'): sızıntı şüphesi. Bu metni kopyalayıp gönder.';
 if(ltMax>150)return'Takılma: sayfada '+r(ltMax)+' ms süren bir iş (arayüz/sohbet/ses) oyunu bekletti.';
 if(fw&&fw.avg<30)return'FPS düşük (ortalama '+r(fw.avg)+'): sınır ekran kartı değil, karedeki çizim sayısı (tarayıcının grafik çeviri iş parçacığı). Esc › Ayarlar › PC görüntü profili › Akıcı › Profili kaydet, sonra F5.';
 if(fw&&fw.min<fw.avg*.5)return'Ani FPS düşüşleri var (en düşük '+r(fw.min)+'): genelde yeni bölge/doku yüklenirken olur.';
 if(p&&p.wait>120)return'Ping yüksek: sunucu cevabını bekleme '+r(p.wait)+' ms; ağ yolu '+(S.net&&S.net.length?r(Math.min(...S.net))+' ms':'?')+', sunucu '+(S.server?r(S.server.ms):'?')+' ms.';
 if(p&&self.__httpPing196&&self.__httpPing196-p.conn-p.wait-p.down>60)return'Ping’in bir kısmı tarayıcıdan: sayfa cevabı geç işliyor (meşgul ana iş parçacığı).';
 return'Belirgin bir sorun görünmüyor.';}
function text(){
 const p=pingParts(),ping=self.__ping158,fw=fpsWin(),lt=S.long.filter(x=>performance.now()-x.at<10000),mem=performance.memory;
 const L=['PAVCITY /cpu  ·  '+new Date().toLocaleTimeString('tr-TR',{hour12:false}),
  'FPS: '+r(S.fps)+(fw?'   (son 10 sn: en düşük '+r(fw.min)+', ortalama '+r(fw.avg)+', 25 altı '+fw.drops+'/'+fw.n+' ölçüm)':''),
  'Sayfa uzun görevleri (10 sn): '+lt.length+(lt.length?' adet, en uzun '+r(Math.max(...lt.map(x=>x.ms)))+' ms':''),
  'Ping (hızlı bağlantı: hareket, araç, ses): '+(self.__rtq196&&self.__rtq196.rtt!=null?r(self.__rtq196.rtt)+' ms':'bağlı değil'),
  'HTTP senkron (can, sohbet, vuruş): '+r(self.__httpPing196??ping)+' ms'+(p?'  = bağlantı '+r(p.conn)+' + sunucu cevabı '+r(p.wait)+' + indirme '+r(p.down)+' + sayfa '+r(Math.max(0,(self.__httpPing196??ping??0)-p.conn-p.wait-p.down))+'  ('+r(p.kb)+' KB, '+p.proto+')':''),
  'Sunucu senkron süresi: '+(S.server?r(S.server.ms)+' ms (son dakika '+S.server.n+' senkron)':'?'),
  'Ağ yolu (basit istek): '+(S.net&&S.net.length?r(Math.min(...S.net))+' ms en iyi, '+r(avg(S.net))+' ms ortalama':'ölçülüyor')+(S.colo?' · Cloudflare noktası '+S.colo:''),
  (()=>{const l=MEM[MEM.length-1]||{},g10=growth(10,'wasm'),g30=growth(30,'wasm'),w10=growth(10,'wasm');
   return'Bellek: oyun motoru '+mb(l.wasm??engineMem?.buffer?.byteLength)+' (sınır 4096 MB) · JS '+(mem?mb(mem.usedJSHeapSize):'?')+
    '\n  motor artışı: son 10 dk '+(w10==null?'(ölçülüyor)':'+'+mb(w10))+' · son 30 dk '+(g30==null?'(ölçülüyor)':'+'+mb(g30))+' · sekme/GPU belleği: Chrome › Shift+Esc'+
    '\n  CPU çekirdeği '+(navigator.hardwareConcurrency||'?')+' · RAM '+(navigator.deviceMemory?navigator.deviceMemory+' GB+':'?');})(),
  '➜ '+verdict(p)];
 return L.join('\n');}
function draw(){
 if(on.fps){if(!fpsEl){fpsEl=document.createElement('div');fpsEl.id='pav-fps192';fpsEl.style.cssText=css+'top:10px;pointer-events:none;font-size:14px';document.body.append(fpsEl);}
  const f=S.fps,col=f==null?'#ccc':f>=45?'#7CFFA0':f>=25?'#FFD36B':'#FF7B7B';fpsEl.innerHTML='<b style="color:'+col+'">'+r(f)+' FPS</b> · '+r(self.__ping158)+' ms';}
 else if(fpsEl){fpsEl.remove();fpsEl=null;}
 if(on.cpu){server();if(!cpuEl){cpuEl=document.createElement('div');cpuEl.id='pav-cpu192';cpuEl.style.cssText=css+'top:'+(on.fps?46:10)+'px;max-width:min(640px,92vw);white-space:pre-wrap;pointer-events:auto';
   cpuEl.innerHTML='<div class="t"></div><div style="margin-top:6px;display:flex;gap:6px"><button type="button" data-c>Kopyala</button><button type="button" data-x>Kapat (/cpu)</button></div>';
   cpuEl.querySelector('[data-c]').onclick=()=>{try{navigator.clipboard.writeText(text());cpuEl.querySelector('[data-c]').textContent='Kopyalandı';}catch{}};
   cpuEl.querySelector('[data-x]').onclick=()=>{on.cpu=false;draw();};document.body.append(cpuEl);}
  cpuEl.style.top=(on.fps?46:10)+'px';cpuEl.querySelector('.t').textContent=text();}
 else if(cpuEl){cpuEl.remove();cpuEl=null;}
 S.long=S.long.filter(x=>performance.now()-x.at<60000);}
setInterval(draw,1000);
window.PAVDiag192={command(message){const c=String(message||'').trim().toLowerCase();
 if(c==='/showfps'){on.fps=!on.fps;try{localStorage.setItem('pn-showfps192',on.fps?'1':'0');}catch{}draw();return on.fps?'FPS göstergesi açık (sağ üst). Kapatmak için tekrar /showfps':'FPS göstergesi kapalı.';}
 if(c==='/cpu'){on.cpu=!on.cpu;draw();return on.cpu?'Tanılama paneli açık. “Kopyala” ile metni alıp paylaşabilirsin; kapatmak için tekrar /cpu':'Tanılama paneli kapalı.';}
 return'';},state:S,text};
})();
