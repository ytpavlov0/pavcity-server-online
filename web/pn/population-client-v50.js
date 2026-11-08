/* Shadow uplink only. Rendering is separately disabled by the server. */
(()=>{'use strict';
class PopulationClient200{
 constructor(bridge,active,life,events=window,now=()=>performance.now()){
  this.bridge=bridge;this.active=active;this.life=life;this.events=events;this.now=now;this.lease=null;this.binding=0;this.at=-Infinity;this.frame=null;
  this.listener=e=>this.receive(e.detail);events.addEventListener('pn-native-population200',this.listener);
 }
 flag(on){const b=this.bridge();if(!b)return;const a=new Int32Array(b.memory.buffer,b.block,16384);Atomics.store(a,14101,this.binding);Atomics.store(a,14100,on?1:0);}
 observe(data){
  const s=data?.version===200&&data.source;
  const valid=s?.can_observe===true&&/^[a-f0-9]{32}$/.test(s.lease_id)&&Array.isArray(s.cell)&&s.cell.length===2&&s.cell.every(Number.isInteger)&&Number.isInteger(s.life_id)&&s.life_id===this.life()&&Number.isFinite(s.lease_remaining_ms)&&s.lease_remaining_ms>0;
  const id=valid?s.lease_id:null;
  if(id!==this.lease?.lease_id){this.binding++;this.frame=null;}
  this.lease=valid?s:null;this.at=this.now();this.flag(valid&&this.active());
 }
 receive(data){
  if(!this.lease||!this.active()||!data||data.binding_epoch!==this.binding||data.version!==200||!Number.isSafeInteger(data.source_seq)||data.source_seq<1||!Array.isArray(data.peds)||data.peds.length>16||!Array.isArray(data.vehicles)||data.vehicles.length>8)return;
  if(this.frame&&data.source_seq<=this.frame.source_seq)return;
  this.frame={...data,received:this.now()};
 }
 packet(){
  const valid=this.lease&&this.active()&&this.lease.life_id===this.life()&&this.now()-this.at<Math.min(3000,this.lease.lease_remaining_ms);
  this.flag(valid);
  if(!valid||!this.frame||this.now()-this.frame.received>1000)return {population200_capable:true};
  const cell=this.lease.cell,inside=r=>r&&Number.isFinite(r.x)&&Number.isFinite(r.y)&&Math.floor(r.x/128)===cell[0]&&Math.floor(r.y/128)===cell[1];
  return {population200_capable:true,population200:{version:200,lease_id:this.lease.lease_id,life_id:this.life(),source_seq:this.frame.source_seq,peds:this.frame.peds.filter(inside),vehicles:this.frame.vehicles.filter(inside)}};
 }
 dispose(){this.flag(false);this.events.removeEventListener('pn-native-population200',this.listener);this.lease=this.frame=null;}
}
window.PAVPopulationClient200=PopulationClient200;
})();
