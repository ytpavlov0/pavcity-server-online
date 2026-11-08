/* 201: shared street population (page side). The realtime server relays, to everyone within 400 m, what a "host"
 * reports of its own traffic and pedestrians ("n" blocks, about 4 a second). Each player decides here:
 *   - a host within 220 m (the one with the lowest character id if several) -> follower: the engine's own population
 *     is switched off and the bridge drives copies of the host's cars and pedestrians;
 *   - none -> after 2.5 s, host: we report our own population;
 *   - two hosts meet: the higher character id gives way after 3 s within 180 m.
 * Not outdoors, wanted, realtime down, ?npc=0, or the bridge turned it off -> neither (the engine's own population).
 * Cells: see the 201 block in the bridge (a[16331..16339], a[16382]). A follower that gets into a copied car asks its
 * host ("k,<host>,<handle>") to remove the original; a host receives such requests as {"y":[handle]}.
 * /npc shows the state. Row: handle, kind (0 ped, 1 car), model, x, y, z, rx, ry, rz, vx, vy, vz, a, b, c, d. */
(()=>{'use strict';
const HOST_R=220,KEEP_R=320,YIELD_R=180,FRESH=1500,WARMUP=2500,YIELD_AFTER=3000,MAX_CARS=20,MAX_PEDS=24,ROW=16,ROWS=48;
const NUM=/^-?(0|[1-9]\d{0,9})(\.\d{1,3})?$/;
const S={mode:0,host:0,hosts:new Map(),ableSince:null,yieldSince:null,sample:null,sentSeq:0,claimSeen:-1,claims:[],ticked:0,
 off:/[?&]npc=0\b/.test(self.location?.search||''),written:0,lastWrite:0,stats:{in:0,out:0,rows:0,bad:0}};
const fix=(x,d)=>{const v=Math.round(x*10**d)/10**d;return Object.is(v,-0)?0:v;};
function parse(entry,now){
 if(!Array.isArray(entry)||entry.length<7)return null;
 const [cid,age,seq,hx,hy,hz,count]=entry;
 if(!Number.isSafeInteger(cid)||cid<=0||!Number.isFinite(age)||age<0||!Number.isSafeInteger(seq)||![hx,hy,hz].every(Number.isFinite)||!Number.isInteger(count)||count<0||count>ROWS||entry.length!==7+count*ROW)return null;
 const rows=[];
 for(let i=0;i<count;i++){const r=entry.slice(7+i*ROW,7+(i+1)*ROW);if(!r.every(Number.isFinite)||(r[1]!==0&&r[1]!==1)||!Number.isInteger(r[0])||!Number.isInteger(r[2]))return null;rows.push(r);}
 return{cid,t:now-age,seq,pos:[hx,hy,hz],rows};
}
function format(sample){
 // n,<seq>,<x>,<y>,<z>,<count>,<rows...>: integers stay integers, coordinates 2 decimals, angles 1
 const rows=[];let len=0;
 for(const r of sample.rows||[]){if(!Array.isArray(r)||r.length!==ROW||!r.every(Number.isFinite))continue;
  const out=r.map((v,i)=>i<=2||i>=12?Math.trunc(v):fix(v,i>=6&&i<=8?1:2)).map(String);
  if(!out.every(x=>NUM.test(x)))continue;const part=out.join(',');if(len+part.length>6200||rows.length>=ROWS)break;rows.push(part);len+=part.length+1;}
 const head=['n',Math.trunc(sample.seq),...sample.pos.map(v=>fix(v,1)),rows.length].map(String).join(',');
 return rows.length?head+','+rows.join(','):head;
}
const view=b=>({a:new Int32Array(b.memory.buffer,b.block,16384),f:new Float32Array(b.memory.buffer,b.block,16384)});
function write(b,a,me,now){
 const addr=(a[16332]>>>0)+a[16333]*4294967296;if(!addr)return;
 const rows=[];
 for(const h of S.hosts.values()){if(now-h.t>FRESH)continue;for(const r of h.rows)rows.push({h,r,d:Math.hypot(r[3]-me[0],r[4]-me[1])});}
 const pick=k=>rows.filter(x=>x.r[1]===k&&x.d<400).sort((p,q)=>p.d-q.d).slice(0,k?MAX_CARS:MAX_PEDS);
 const chosen=[...pick(1),...pick(0)];
 const bi=new Int32Array(b.memory.buffer,addr,1024),bf=new Float32Array(b.memory.buffer,addr,1024);
 const w=Atomics.load(bi,0)|1;Atomics.store(bi,0,w);		// odd while writing: the bridge skips a half-written buffer
 chosen.forEach(({h,r},i)=>{const o=8+i*20;bi[o]=h.cid;bi[o+1]=r[0];bi[o+2]=r[1];bi[o+3]=r[2]|0;for(let k=3;k<12;k++)bf[o+1+k]=r[k];for(let k=12;k<16;k++)bi[o+1+k]=r[k]|0;bf[o+17]=Math.max(0,now-h.t);});
 bi[1]=chosen.length;Atomics.store(bi,0,(w+1)|0);S.written++;S.lastWrite=now;S.stats.rows=chosen.length;
}
window.__npc201={
 receive(list,now=performance.now()){
  if(!Array.isArray(list))return;
  for(const entry of list){const h=parse(entry,now);if(!h){S.stats.bad++;continue;}S.stats.in++;const old=S.hosts.get(h.cid);if(!old||h.seq!==old.seq)S.hosts.set(h.cid,h);}
  for(const[k,h]of S.hosts)if(now-h.t>5000)S.hosts.delete(k);
 },
 host(sample){if(sample&&Number.isSafeInteger(sample.seq)&&Array.isArray(sample.pos)&&sample.pos.length===3&&Array.isArray(sample.rows))S.sample={...sample,at:performance.now()};},
 claimed(list){if(Array.isArray(list))for(const h of list)if(Number.isSafeInteger(h)&&h>0&&S.claims.length<8)S.claims.push(h);},
 // called with every realtime send (~15/s); returns the text to append to the message ("" for nothing)
 tick({bridge,cid,dim=0,now=performance.now()}){
  S.ticked=now;S.bridge=bridge;if(!bridge)return'';const {a,f}=view(bridge),me=[f[16],f[17],f[18]];let out='';
  const able=!S.off&&!dim&&a[16382]===1&&me.every(Number.isFinite)&&Number.isSafeInteger(cid)&&cid>0;
  if(!able){S.mode=0;S.host=0;S.ableSince=null;S.yieldSince=null;}
  else{if(S.ableSince===null)S.ableSince=now;
   const near=[...S.hosts.values()].filter(h=>h.cid!==cid&&now-h.t<FRESH).map(h=>({h,d:Math.hypot(h.pos[0]-me[0],h.pos[1]-me[1])}));
   const keep=S.mode===2&&near.find(x=>x.h.cid===S.host&&x.d<KEEP_R);
   const cand=near.filter(x=>x.d<HOST_R).sort((p,q)=>p.h.cid-q.h.cid)[0];
   if(keep){}
   else if(S.mode===1){
    const lower=near.filter(x=>x.d<YIELD_R&&x.h.cid<cid).sort((p,q)=>p.h.cid-q.h.cid)[0];
    if(lower){if(S.yieldSince===null)S.yieldSince=now;if(now-S.yieldSince>=YIELD_AFTER){S.mode=2;S.host=lower.h.cid;S.yieldSince=null;}}else S.yieldSince=null;}
   else if(cand){S.mode=2;S.host=cand.h.cid;}
   else if(now-S.ableSince>=WARMUP){S.mode=1;S.host=0;}
   else{S.mode=0;S.host=0;}}
  a[16331]=S.mode;
  if(S.mode===2&&(now-S.lastWrite>=200||[...S.hosts.values()].some(h=>h.t>S.lastWrite-FRESH&&h.seq!==h.wrote))){for(const h of S.hosts.values())h.wrote=h.seq;write(bridge,a,me,now);}
  if(S.mode===1){
   if(a[16339]===0&&S.claims.length)a[16339]=S.claims.shift();
   const sm=S.sample;if(sm&&sm.seq!==S.sentSeq&&now-sm.at<400){S.sentSeq=sm.seq;out+=';'+format(sm);S.stats.out++;}}
  else S.claims.length=0;
  if(a[16336]!==S.claimSeen){if(S.claimSeen!==-1&&a[16337]>0&&a[16338]>0)out+=';k,'+a[16337]+','+a[16338];S.claimSeen=a[16336];}
  return out;
 },
 state(){return{mode:S.mode,host:S.host,hosts:S.hosts.size,...S.stats};},
 _test:{S,parse,format}
};
// realtime down: our own population again
setInterval(()=>{if(S.mode&&performance.now()-S.ticked>1000){S.mode=0;S.host=0;try{if(S.bridge)view(S.bridge).a[16331]=0;}catch{}}},500);
const wrap=()=>{const d=window.PAVDiag192;if(!d||d.npc201)return!!d;const cmd=d.command.bind(d);
 d.command=message=>{if(String(message||'').trim().toLowerCase()==='/npc'){const s=window.__npc201.state();
  return(s.mode===2?'NPC/trafik: ortak (ev sahibi oyuncu #'+s.host+'), kopya '+s.rows:s.mode===1?'NPC/trafik: sen ev sahibisin, '+s.out+' rapor gÃ¶nderildi':'NPC/trafik: kendi motorun (yakÄ±nda ev sahibi yok ya da kapalÄ±)')+' Â· duyulan ev sahibi '+s.hosts;}
  return cmd(message);};d.npc201=true;return true;};
if(!wrap()){const t=setInterval(()=>{if(wrap())clearInterval(t);},1000);setTimeout(()=>clearInterval(t),60000);}
})();
