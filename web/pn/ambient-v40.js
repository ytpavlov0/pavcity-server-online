/* Shared NPC observations consume only unused native replica slots. */
(()=>{'use strict';let game=null;
 const MODEL=(()=>{let h=0;for(const c of 'a_m_y_business_01'){h=(h+c.charCodeAt(0))|0;h=(h+(h<<10))|0;h^=h>>>6;}h=(h+(h<<3))|0;h^=h>>>11;return(h+(h<<15))|0;})();
 addEventListener('pav-game-created',event=>game=event.detail);
 addEventListener('pav-game-data',event=>{
  if(!game?.bridge)return;const data=event.detail,{memory,block}=game.bridge,a=new Int32Array(memory.buffer,block,16384),f=new Float32Array(memory.buffer,block,16384);
  // Main sync has just rewritten the real-player rows. Preserve their priority.
  const real=Math.max(0,Math.min(32,Atomics.load(a,5))),seen=new Set();
  const rows=data.ambient188?.version===188&&Array.isArray(data.ambient188.peds)?data.ambient188.peds.filter(p=>p&&Number.isInteger(p.id)&&p.id>=1500000000&&p.id<1510000000&&p.model==='a_m_y_business_01'&&['x','y','z','heading','speed'].every(k=>Number.isFinite(p[k]))&&!seen.has(p.id)&&seen.add(p.id)).slice(0,Math.min(10,32-real)):[];
  Atomics.add(a,6,1);
  try{rows.forEach((p,i)=>{const o=128+(real+i)*64;a.fill(0,o,o+64);a[o]=p.id;f.set([p.x,p.y,p.z,p.heading,p.speed,200,Number(p.vx)||0,Number(p.vy)||0,0],o+1);a[o+10]=0xA2719263|0;a[o+11]=256;f.set([p.x,p.y,p.z],o+12);a[o+15]=p.vehicle_id||0;a[o+16]=p.vehicle_id?-1:-2;a[o+17]=188;a[o+19]=MODEL;});Atomics.store(a,5,real+rows.length);}
  finally{Atomics.add(a,6,1);}
  game.hud.dataset.ambientActors=String(rows.length);
 });
 addEventListener('pav-game-stop',()=>game=null);
})();
