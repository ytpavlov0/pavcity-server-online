/* 207: why is one entry 60 FPS and the next 20-30? Each session sends a short performance summary to the game server's
 * log 2 minutes after the first frame and then every 10 minutes ("[PAV207_PERF]", no personal data: a random session
 * id, numbers and settings): FPS (median / 10th percentile over the last minute), draws per frame and how busy the
 * graphics translation worker is (worker v60), back-buffer size and render scale, graphics profile and NPC density,
 * shared-population mode, players near, MB downloaded this session (a cold cache streams while playing), CPU threads.
 * /perf shows the same in the game with the likely reason. support/dev-tools/perf207.py compares slow and fast sessions. */
(()=>{'use strict';
const SID=(()=>{try{return crypto.randomUUID().slice(0,8);}catch{return String(Math.random()).slice(2,10);}})();
let g=null,first=0,last=0,sent=0,dl=0,dlAt=[];const S=[];
addEventListener('pav-game-created',({detail})=>{g=detail;});
const med=(v,q=.5)=>{if(!v.length)return 0;const s=v.slice().sort((a,b)=>a-b);return s[Math.min(s.length-1,Math.floor(s.length*q))];};
function summary(now=performance.now()){
 const recent=S.filter(x=>now-x.t<=60000),fps=recent.map(x=>x.fps),draws=recent.map(x=>x.draws).filter(Boolean),busy=recent.map(x=>x.busy);
 let a=null;try{const b=g?.bridge;if(b)a=new Int32Array(b.memory.buffer,b.block,16384);}catch{}
 let ext=null;try{ext=window.__wasmInput?.ext;}catch{}
 const get=k=>{try{return localStorage.getItem(k);}catch{return null;}};
 let profile=null;try{const p=window.PAVGraphics79?.read();profile=p?[p.quality,p.distance,p.texture]:null;}catch{}
 let npc=null;try{const s=window.__npc201?.state();npc=s?s.mode:null;}catch{}
 const recentDl=dlAt.filter(x=>now-x.t<=60000).reduce((s,x)=>s+x.n,0);
 return{v:207,sid:SID,min:Math.round((now-first)/60000*10)/10,fps:Math.round(med(fps)),fps10:Math.round(med(fps,.1)),draws:Math.round(med(draws)),busy:Math.round(med(busy)),
  buf:ext?[ext[2],ext[3]]:null,win:[innerWidth,innerHeight],dpr:Math.round(devicePixelRatio*100)/100,scale:Number(get('pav-render-scale')||1),profile,density:Number(get('pav-npc206')||0)||null,
  npc,peers:a?Math.min(32,Math.max(0,a[5]|0)):null,dl_mb:Math.round(dl/1048576),dl_min_mb:Math.round(recentDl/1048576),threads:navigator.hardwareConcurrency||0,mem:navigator.deviceMemory||0,
  chrome:Number((/Chrome\/(\d+)/.exec(navigator.userAgent)||[])[1]||0),hidden:!!document.hidden};}
function reason(s){
 if(!s.fps)return'Henüz ölçüm yok (oyuna gir ve bir dakika bekle).';
 if(s.fps>=50)return'Akıcı.';
 if(s.dl_min_mb>=20)return'Oyun dosyaları hâlâ indiriliyor (son dakikada '+s.dl_min_mb+' MB). İlk girişte normaldir; birkaç dakika sonra düzelir.';
 if(s.busy>=80)return'Grafik çevirisi tam dolu (karede '+s.draws+' çizim). Esc › Ayarlar: NPC yoğunluğunu “Az”, çevre mesafesini düşür.';
 if(s.buf&&s.buf[0]*s.buf[1]>2.2e6)return'Çizim çözünürlüğü yüksek ('+s.buf[0]+'×'+s.buf[1]+'). Esc › Görüntü ölçeğini düşür ya da pencereyi küçültüp sayfayı yenile.';
 return'Motor bekliyor (işlemci, ekran kartı ya da başka sekmeler). Diğer sekmeleri kapatıp Chrome’u yeniden başlatmayı dene.';}
function send(now){const s=summary(now);if(!s.fps)return;sent++;last=now;
 try{fetch('/log',{method:'POST',credentials:'same-origin',keepalive:true,headers:{'Content-Type':'text/plain;charset=UTF-8'},body:'[PAV207_PERF] '+JSON.stringify(s)});}catch{}}
function sample(d,now=performance.now()){
 if(!d||!Number.isFinite(d.fps))return;if(!first)first=now;
 S.push({t:now,fps:d.fps,draws:Number(d.draws)||0,busy:Number(d.busy)||0});while(S.length&&now-S[0].t>120000)S.shift();
 if((!sent&&now-first>=120000)||(sent&&now-last>=600000))send(now);}
try{new BroadcastChannel('game-fps').onmessage=e=>sample(e.data);}catch{}
try{new BroadcastChannel('game-progress').onmessage=e=>{const n=Number(e.data?.dl);if(n>0){dl+=n;dlAt.push({t:performance.now(),n});if(dlAt.length>400)dlAt.splice(0,200);}};}catch{}
const wrap=()=>{const d=window.PAVDiag192;if(!d||d.perf207)return!!d;const cmd=d.command.bind(d);
 d.command=m=>{if(String(m||'').trim().toLowerCase()==='/perf'){const s=summary();return'FPS '+s.fps+' (en düşük %10: '+s.fps10+') · karede '+s.draws+' çizim · çeviri işçisi %'+s.busy+' · çözünürlük '+(s.buf?s.buf.join('×'):'?')+' · yakında '+(s.peers??'?')+' oyuncu · bu oturumda '+s.dl_mb+' MB indirildi. → '+reason(s);}return cmd(m);};d.perf207=true;return true;};
if(!wrap()){const t=setInterval(()=>{if(wrap())clearInterval(t);},1000);setTimeout(()=>clearInterval(t),60000);}
window.PAVPerf207={summary,reason,sample,_set:x=>{g=x;}};
})();
