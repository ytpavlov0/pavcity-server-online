/* Native acknowledgement separates an old body sample from a new server life. */
(()=>{'use strict';
class PAVLife {
 constructor(bridge,id=0){this.bridge=bridge;this.id=id;this.sampleId=id;this.pending=null;this.healthOnly=false;}
 apply(data,force=false){
  if(!force&&data.life_id<=this.id&&this.pending===null)return;
  const {memory,block}=this.bridge,a=new Int32Array(memory.buffer,block,16384),f=new Float32Array(memory.buffer,block,16384),spawn=data.spawn||data.teleport;
  if(!spawn)return;
  if(spawn.health_only&&!force){
   this.id=data.life_id;this.healthOnly=true;a[44]=spawn.health??200;this.pendingHealth=a[44];
   this.pending=Atomics.add(a,45,1)+1;return;
  }
  this.healthOnly=false;a[112]=spawn.safe_ground?1:0;this.id=data.life_id;f.set([spawn.x,spawn.y,spawn.z,spawn.heading],40);a[44]=spawn.health??200;this.pendingHealth=a[44];a[65]=spawn.armor||0;
  a[48]=0;a[49]=-2;Atomics.add(a,50,1);Atomics.add(a,66,1);Atomics.add(a,45,1);
  this.pending=Atomics.add(a,46,1)+1;
 }
 sample(){
  if(this.pending!==null){const {memory,block}=this.bridge,a=new Int32Array(memory.buffer,block,16384),f=new Float32Array(memory.buffer,block,16384);
   if((this.healthOnly?a[125]:a[96])===this.pending&&(this.pendingHealth>100?f[21]>100:f[21]<=100)){this.sampleId=this.id;this.pending=null;this.healthOnly=false;}
  }return this.sampleId;
 }
}
window.PAVLife=PAVLife;
})();
