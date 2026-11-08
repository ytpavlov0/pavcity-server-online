/* 206: graphics that fit the computer, and an NPC/traffic density setting.
 * - Automatic profile: unless the player picked a profile in Esc › Ayarlar (remembered: pav-gfx206-manual), the frame
 *   rate (game-fps channel, 2 a second) is sampled for 4 minutes after the first minute in the city (tab visible only).
 *   Median >= 50 and 10th percentile >= 38 on "Akıcı" -> "Dengeli" from the next entry (the engine reads the profile at
 *   start); median < 24 -> one step down. Never up to "Yüksek" on its own (768 MB textures), never up within 7 days
 *   of a graphics-card hang (pav-gpu-lost198). One decision per session, with a notice.
 * - NPC/trafik yoğunluğu (Esc › Ayarlar): Normal / Az / Çok az = the engine's persistent ped and vehicle population
 *   budgets 3 / 2 / 1 (bridge v206 reads cell 1000 of its 201 buffer). Default: "Az" on Akıcı, "Normal" otherwise. */
(()=>{'use strict';
const get=k=>{try{return localStorage.getItem(k);}catch{return null;}},set=(k,v)=>{try{localStorage.setItem(k,v);}catch{}};
const WARM=60000,SPAN=240000,DAY=86400000;
const G=()=>window.PAVGraphics79;
const level=()=>{try{return G()?.read().quality??0;}catch{return 0;}};
const density=()=>{const v=Number(get('pav-npc206'));return v>=1&&v<=3?v:2;};/* 210: "Az" by default for everybody */
let g=null,first=0,samples=[],decided=false;
const auto=()=>get('pav-gfx206-manual')!=='1'&&(get('pav-gfx195')==='1'||get('pav-pc-graphics79')===null)&&!window.PAVMobile?.active;
function decide(now){
 if(decided||!auto()||samples.length<SPAN/600)return null;decided=true;
 const v=samples.slice().sort((a,b)=>a-b),med=v[v.length>>1],p10=v[Math.floor(v.length*.1)],q=level(),P=G()?.presets;if(!P)return null;
 let to=null;
 if(med>=50&&p10>=38&&q<1&&!(Date.now()-Number(get('pav-gpu-lost198')||0)<7*DAY))to='balanced';
 else if(med<24&&q>0)to=q===2?'balanced':'low';
 if(!to)return{med,p10,to:null};
 set('pav-pc-graphics79',JSON.stringify(P[to]));set('pav-gfx206',JSON.stringify({at:Date.now(),from:q,to,med,p10}));
 const name={low:'Akıcı',balanced:'Dengeli'}[to],msg=to==='balanced'?'Bilgisayarın şehri rahat kaldırıyor (ortalama '+Math.round(med)+' FPS). Bir sonraki girişte grafikler “'+name+'” profiline yükseltilecek; Esc › Ayarlar’dan değiştirebilirsin.':'Oyun bu bilgisayarda zorlanıyor (ortalama '+Math.round(med)+' FPS). Bir sonraki girişte daha hafif “'+name+'” profili açılacak; Esc › Ayarlar’dan değiştirebilirsin.';
 try{if(g?.toast113)g.toast113(msg,'info','Grafik ayarı');else g?.notice?.(msg);}catch{}
 return{med,p10,to};}
function sample(v,now=performance.now()){
 if(!Number.isFinite(v)||v<=0||(typeof document!=='undefined'&&document.hidden))return;
 if(!first)first=now;if(now-first<WARM)return;samples.push(v);if(samples.length>=SPAN/500)decide(now);}
try{new BroadcastChannel('game-fps').onmessage=e=>sample(Number(e.data?.fps));}catch{}
// the player's own choice in the settings stops the automatic profile
addEventListener('submit',e=>{if(e.target?.closest?.('.pav-graphics79'))set('pav-gfx206-manual','1');},true);
addEventListener('click',e=>{if(e.target?.closest?.('.pav-graphics79 [data-profile]'))set('pav-gfx206-manual','1');},true);
// density: written for the bridge every 2 s, and a setting next to the graphics profile
function push(){const b=g?.bridge;if(!b)return;try{const a=new Int32Array(b.memory.buffer,b.block,16384),addr=(a[16332]>>>0)+a[16333]*4294967296;if(addr)new Int32Array(b.memory.buffer,addr,1024)[1000]=density();}catch{}}
setInterval(push,2000);
function ui(){const view=g?.hud?.querySelector?.('.pav-menu-view[data-view=settings]');if(!view||view.querySelector('.pav-npc206'))return;
 const box=document.createElement('div');box.className='pav-npc206';box.style.cssText='margin:12px 0;padding:12px 14px;border-radius:12px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.03)';
 box.innerHTML='<label style="display:flex;align-items:center;justify-content:space-between;gap:12px;font-weight:700">NPC ve trafik yoğunluğu<select><option value="3">Normal</option><option value="2">Az</option><option value="1">Çok az</option></select></label><p style="margin:6px 0 0;font-size:12px;opacity:.75">Daha az NPC ve araç = daha az çizim, daha akıcı oyun. Hemen uygulanır.</p>';
 const sel=box.querySelector('select');sel.value=String(density());sel.onchange=()=>{set('pav-npc206',sel.value);push();};
 const gfx=view.querySelector('.pav-graphics79');gfx?gfx.after(box):view.prepend(box);}
addEventListener('pav-game-created',({detail})=>{g=detail;setTimeout(ui,0);setTimeout(ui,500);});
window.PAVGfx206={sample,decide,density,state:()=>({first,samples:samples.length,decided}),_set:x=>{g=x;}};
})();
