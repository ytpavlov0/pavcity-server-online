/* 215: the death panel calls the NPC ambulance (backend v194 /api/gta/ems194, 5 s after going down); the calls near
 * us from each sync (ems194) are written into the 201 buffer for bridge v215 (cells 970-995); our own call revives
 * us (/api/gta/npcrevive192) once it is 24 s old, when the paramedic has tended to us.
 * 211: + the unconscious flag for the bridge (cell 1001, written at once from each sync so a revive is never laid
 * down again) and clearly disabled death buttons while the medic window runs.
 * 210: crime and rescue on the page (backend v192 crime192, bridge v210 block 210).
 * - Sync crime192: wanted level (set once in the engine: NPC police chase, hiding works), chop spot (ring marker) and
 *   session, weapon attachments of the weapon in hand (fitted in the engine).
 * - NPC police arrest (bridge counter a[7107]) -> /api/police192/npc-arrest (fine + short jail on the server).
 * - Chop shop panel within 30 m of the spot: start, strip a door/wheel (6 s kneel animation), carry it to the counter
 *   and sell, press the hull, or quit. /hurdaci puts the spot on the GPS.
 * - Death panel: medics have 60 s; then "NPC sağlıkçı çağır" (paramedic scene, revive with 20 % health, $300). */
(()=>{'use strict';
let g=null,last=null,arrestSeen=null,busy=false,wantedSeq=null,compKey='',deadAt=0,medicWait=null;
const PART_NAMES={door0:'Sol ön kapı',door1:'Sağ ön kapı',door2:'Sol arka kapı',door3:'Sağ arka kapı',wheel0:'Sol ön teker',wheel1:'Sağ ön teker',wheel2:'Sol arka teker',wheel3:'Sağ arka teker'};
const PART_INDEX={door0:0,door1:1,door2:2,door3:3,wheel0:4,wheel1:5,wheel2:6,wheel3:7};
const cells=()=>{const b=g?.bridge;if(!b)return null;const a=new Int32Array(b.memory.buffer,b.block,16384),addr=(a[16332]>>>0)+a[16333]*4294967296;if(!addr)return null;
 return{a,f:new Float32Array(b.memory.buffer,b.block,16384),ci:new Int32Array(b.memory.buffer,addr,1024),cf:new Float32Array(b.memory.buffer,addr,1024)};};
const say=(m,bad)=>{if(!m)return;try{if(g?.toast113)g.toast113(m,bad?'warning':'info','PAVCITY');else g?.notice?.(m,bad);}catch{}};
async function call(path,body={}){const r=await g.api(path,body);if(r&&r.success===false)throw Error(r.error||'İşlem yapılamadı.');return r;}
function apply(d){const c=cells();if(!c||!d)return;const{ci,cf}=c;
 if(d.wanted&&d.wanted.seq!==wantedSeq){wantedSeq=d.wanted.seq;ci[1005]=d.wanted.level|0;ci[1004]=(ci[1004]+1)|0;}
 if(d.chop?.spot){ci[1020]=1;cf[1021]=d.chop.spot.x;cf[1022]=d.chop.spot.y;cf[1023]=d.chop.spot.z;}
 const k=JSON.stringify(d.comp||null);if(k!==compKey){compKey=k;const cp=d.comp;ci[1014]=cp?cp.weapon|0:0;const hs=(cp?.hashes||[]).slice(0,4);ci[1015]=hs.length;hs.forEach((h,i)=>ci[1016+i]=h|0);ci[1013]=(ci[1013]+1)|0;}
 const carrying=d.chop?.session?.carrying;ci[1011]=carrying?(carrying.startsWith('door')?1:2):0;}
// ---- chop panel
let panel=null;
{const st=document.createElement('style');st.textContent='.pav-death button:disabled{opacity:.45!important;filter:grayscale(.7)!important;cursor:not-allowed!important}';(document.head||document.documentElement).append(st);}
function pos(){const c=cells();return c?[c.f[16],c.f[17],c.f[18]]:null;}
function nearSpot(r){const p=pos(),sp=last?.chop?.spot;return!!(p&&sp&&Math.hypot(p[0]-sp.x,p[1]-sp.y)<r);}
function render(){const show=!!(last&&nearSpot(30)&&g&&!g.isDead);
 if(!show){panel?.remove();panel=null;return;}
 if(!panel){panel=document.createElement('aside');panel.className='pav-chop210';panel.style.cssText='position:fixed;right:18px;top:38%;z-index:40;width:270px;padding:14px;border-radius:16px;background:rgba(14,10,22,.88);border:1px solid rgba(255,140,60,.45);color:#fff;font:600 13px/1.35 "Segoe UI",system-ui,sans-serif;box-shadow:0 12px 34px rgba(0,0,0,.45)';document.body.append(panel);}
 const sess=last.chop.session,html=[];html.push('<b style="display:block;font-size:15px;margin-bottom:4px">HURDACI</b>');
 if(!sess){html.push('<p style="margin:0 0 10px;opacity:.85">Sana ait olmayan bir aracı alana getir, yanına in ve sökmeye başla. Polis haberdar olur!</p><button data-c="start">Aracı sökmeye başla</button>');}
 else{html.push('<p style="margin:0 0 8px;opacity:.85">'+String(sess.model||'').toUpperCase()+' · satılan '+sess.done.length+' parça'+(sess.carrying?' · elinde: '+PART_NAMES[sess.carrying]:'')+'</p>');
  if(sess.carrying)html.push('<button data-c="sell">Tezgâhta sat ($'+(sess.carrying.startsWith('door')?sess.prices.door:sess.prices.wheel)+')</button>');
  else html.push('<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">'+Object.keys(PART_NAMES).map(p=>'<button data-p="'+p+'"'+(sess.done.includes(p)?' disabled':'')+'>'+PART_NAMES[p]+'</button>').join('')+'</div>');
  html.push('<div style="display:flex;gap:6px;margin-top:8px"><button data-c="crush"'+(sess.done.length<sess.min_parts||sess.carrying?' disabled':'')+'>Presle</button><button data-c="cancel">Bırak</button></div>');}
 const markup=html.join('');if(panel.dataset.m===markup)return;panel.dataset.m=markup;panel.innerHTML=markup;
 panel.querySelectorAll('button').forEach(b=>{b.style.cssText='padding:7px 8px;border-radius:9px;border:1px solid rgba(255,255,255,.18);background:rgba(255,140,60,.18);color:#fff;font:700 12px/1.2 inherit;cursor:pointer;width:100%';if(b.disabled)b.style.opacity='.4';});
 panel.querySelectorAll('[data-c]').forEach(b=>b.onclick=()=>act(b.dataset.c));panel.querySelectorAll('[data-p]').forEach(b=>b.onclick=()=>strip(b.dataset.p));}
async function act(verb){if(busy)return;busy=true;try{const r=await call('/api/chop192/'+verb);if(last?.chop)last.chop.session=r.session??null;say(r.notice);render();}catch(e){say(e.message,true);}finally{busy=false;}}
async function strip(part){if(busy)return;busy=true;const c=cells();
 try{if(c){c.ci[1007]=1;c.ci[1006]=(c.ci[1006]+1)|0;}say(PART_NAMES[part]+' sökülüyor…');await new Promise(r=>setTimeout(r,6000));
  if(c){c.ci[1007]=0;c.ci[1006]=(c.ci[1006]+1)|0;}
  const r=await call('/api/chop192/strip',{part});if(last?.chop)last.chop.session=r.session;
  if(c&&r.session){c.ci[1009]=r.session.vehicle|0;c.ci[1010]=PART_INDEX[part];c.ci[1008]=(c.ci[1008]+1)|0;}apply(last);say(r.notice);render();}
 catch(e){if(c){c.ci[1007]=0;c.ci[1006]=(c.ci[1006]+1)|0;}say(e.message,true);}finally{busy=false;}}
// ---- arrest
setInterval(()=>{const c=cells();if(!c)return;const n=c.a[7107];if(arrestSeen===null){arrestSeen=n;return;}if(n!==arrestSeen){arrestSeen=n;call('/api/police192/npc-arrest').then(r=>say(r.notice,true)).catch(()=>{});}},500);
// ---- death panel (215): the NPC ambulance comes with sirens (~20 s), the paramedic tends to us, then we get up
let own=null;const REVIVE_AT=24000;
function emsWrite(list){const c=cells();if(!c)return;const{ci,cf}=c,q=(ci[970]|0)&~1,rows=(list||[]).slice(0,3);Atomics.store(ci,970,q+1);
 rows.forEach((r,i)=>{const o=972+8*i;ci[o]=r.id|0;cf[o+1]=r.x;cf[o+2]=r.y;cf[o+3]=r.z;ci[o+4]=r.age_ms|0;ci[o+5]=r.me?1:0;});ci[971]=rows.length;Atomics.store(ci,970,(q+2)|0);}
async function emsRevive(){if(busy||!own||own.reviving)return;own.reviving=true;busy=true;
 try{const r=await call('/api/gta/npcrevive192');say(r.notice);own=null;}
 catch(e){if(own){own.reviving=false;own.retryAt=performance.now()+2500;}if(!/Ambulans yolda/.test(e.message))say(e.message,true);}finally{busy=false;}}
function death(){const box=document.querySelector('.pav-death');if(!g?.isDead)own=null;if(!box)return;let ex=box.querySelector('.pav-medic210');
 if(!g?.isDead){ex?.remove();return;}
 if(!ex){ex=document.createElement('div');ex.className='pav-medic210';ex.style.cssText='margin-top:10px;display:grid;gap:6px';ex.innerHTML='<small></small><button type="button">Ambulans çağır · $300 · %20 can</button>';box.append(ex);
  ex.querySelector('button').onclick=async()=>{if(busy||own)return;busy=true;try{const r=await call('/api/gta/ems194');if(r.ems194)own={id:r.ems194.id,t0:performance.now()-(r.ems194.age_ms|0)};say(r.notice);}catch(e){say(e.message,true);}finally{busy=false;}};}
 const t=performance.now(),since=medicWait==null?99:60-(medicWait-(t-deadAt)/1000);let text;
 if(own){const age=t-own.t0;text=age<18000?'Ambulans sirenlerle geliyor: '+Math.max(1,Math.ceil((18000-age)/1000))+' sn':'Sağlıkçı sana müdahale ediyor…';if(age>=REVIVE_AT&&!own.reviving&&!(own.retryAt>t))emsRevive();}
 else text=since<5?'Ambulans '+Math.max(1,Math.ceil(5-since))+' sn sonra çağrılabilir. Bir sağlıkçı /canlandir ile seni kaldırabilir.':'Ambulans çağırabilirsin (yaklaşık 20 sn) ya da bir sağlıkçı /canlandir ile seni kaldırabilir.';
 ex.querySelector('small').textContent=text;ex.querySelector('button').disabled=busy||!!own||since<5;}
setInterval(()=>{try{render();death();}catch{}},500);
addEventListener('pav-game-created',({detail})=>{g=detail;});
addEventListener('pav-game-data',({detail:d})=>{{const c=cells();if(c&&Number.isFinite(d?.health))c.ci[1001]=d.health<=100?1:0;}if(!d?.crime192)return;last=d.crime192;apply(last);if(typeof last.medic_wait==='number'){medicWait=last.medic_wait;deadAt=performance.now();}else medicWait=null;
 const rows=Array.isArray(d.ems194)?d.ems194.filter(r=>r&&Number.isInteger(r.id)&&[r.x,r.y,r.z].every(Number.isFinite)):[];emsWrite(rows);const mine=rows.find(r=>r.me);
 if(mine){const t0=performance.now()-(mine.age_ms|0);if(!own||own.id!==mine.id)own={id:mine.id,t0};else if(Math.abs(own.t0-t0)>2000)own.t0=t0;}else if(own&&!own.reviving&&performance.now()-own.t0>4000)own=null;});
// /hurdaci: GPS to the chop spot (local command)
const wrap=()=>{const d=window.PAVDiag192;if(!d||d.c210)return!!d;const cmd=d.command.bind(d);
 d.command=m=>{const t=String(m||'').trim().toLowerCase();if(t==='/hurdaci'||t==='/hurdacı'){const sp=last?.chop?.spot;if(!sp)return'Hurdacı konumu henüz bilinmiyor; biraz bekle.';try{g?.setWaypoint?.(sp.x,sp.y);}catch{}return'Hurdacı GPS’e işlendi. Sana ait olmayan bir aracı oraya getir.';}return cmd(m);};d.c210=true;return true;};
if(!wrap()){const t=setInterval(()=>{if(wrap())clearInterval(t);},1000);setTimeout(()=>clearInterval(t),60000);}
window.PAVCrime215=window.PAVCrime211=window.PAVCrime210={apply,_set:(game,d)=>{g=game;last=d;},render,death,emsWrite,state:()=>({last,wantedSeq,compKey,own})};
})();
