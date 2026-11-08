/* Native-side police sampling. Called only inside the engine's script TLS.
 * Shared cells 14500..14595 are reserved for this protocol, below native scratch.
 * Input: membership + server heartbeat. Output: seqlocked wanted + 16 positions.
 */
(()=>{'use strict';
class Police84 {
 constructor(){this.beat=0;this.beatAt=-Infinity;this.last=-Infinity;this.applied=null;this.actor=0;this.enforced=-Infinity;this.samples=0;this.cars=[];this.carsAt=-Infinity;}
 step(n,a,f,now,active=true){
  const beat=Atomics.load(a,14501);
  if(beat!==this.beat){this.beat=beat;this.beatAt=now;}
  const protectedMember=active&&a[14500]===1&&beat>0&&now-this.beatAt<2500;
  if(this.applied!==protectedMember||this.actor!==n.ped||now-this.enforced>=1000){
   n.ignore(protectedMember);this.applied=protectedMember;this.actor=n.ped;this.enforced=now;
  }
  if(!active){if(a[14505]||a[14504])this.publish(a,f,0,[]);this.last=-Infinity;this.carsAt=-Infinity;this.cars=[];return;}
  if(now-this.last<250)return;
  this.last=now;this.samples++;
  let wanted=Math.max(0,Math.min(5,n.wanted()|0));
  if(protectedMember&&wanted){n.clearWanted();wanted=0;}
  const rows=[],origin=n.position(n.ped),seen=new Set(),vehicles=new Set();
  if(!origin.every(Number.isFinite)){this.publish(a,f,wanted,[]);return;}
  const collect=h=>{
   if(!h||h===n.ped||seen.has(h)||!n.exists(h)||n.excluded(h)||n.player(h))return;
   seen.add(h);const type=n.type(h);if(type!==6&&type!==27||n.health(h)<=100)return;
   const car=n.vehicle(h);if(car&&vehicles.has(car))return;
   const pos=n.position(car&&n.exists(car)?car:h),distance=Math.hypot(...pos.map((v,i)=>v-origin[i]));
   if(!pos.every(Number.isFinite)||distance>220)return;
   if(car)vehicles.add(car);rows.push({h,pos,distance,kind:car?(pos[2]-origin[2]>12?2:1):0});
  };
  for(const h of n.nearby().slice(0,32))collect(h);
  // Seated cops can be omitted by GET_PED_NEARBY_PEDS. Sample a small local
  // vehicle list twice per second; empty/stolen police cars are never marked.
  if(now-this.carsAt>=500){this.carsAt=now;this.cars=(n.nearbyVehicles?.()||[]).slice(0,16);}
  for(const car of this.cars){
   if(!car||!n.exists(car)||vehicles.has(car))continue;
   const pos=n.position(car);if(!pos.every(Number.isFinite)||Math.hypot(...pos.map((v,i)=>v-origin[i]))>220)continue;
   for(const h of(n.occupants?.(car)||[]).slice(0,2))collect(h);
  }
  rows.sort((x,y)=>x.distance-y.distance);
  this.publish(a,f,wanted,rows.slice(0,16));
 }
 publish(a,f,wanted,rows){
  Atomics.add(a,14506,1);a[14504]=wanted;a[14505]=rows.length;
  for(let i=0;i<rows.length;i++){const o=14512+i*5,r=rows[i];a[o]=r.h;f.set(r.pos,o+1);a[o+4]=r.kind;}
  Atomics.add(a,14506,1);
 }
}
self.PAVPolice84=Police84;
})();
