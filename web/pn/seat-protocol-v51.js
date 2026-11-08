/* Atomic receipts across process restarts; never retire a valid server on bad data. */
(()=>{'use strict';class Seat200{
 constructor(data={}){this.instance=null;this.retiredInstances=new Set();this.capable=false;this.epoch=null;this.life=0;this.vehicle=0;this.seat=-2;this.observe(data);}
 observe(data,rejoined=false){
  if(data.seat_protocol!==200)return !this.capable;
  const instance=data.server_instance51,hasInstance=instance!==undefined;
  if(this.instance&&!hasInstance)return false;
  if(hasInstance&&(typeof instance!=='string'||!/^[a-f0-9]{32}$/.test(instance)||this.retiredInstances.has(instance)))return false;
  if(!Number.isSafeInteger(data.seat_epoch)||data.seat_epoch<0)throw Error('Sunucunun koltuk sürümü okunamadı.');
  const changed=hasInstance&&instance!==this.instance,epoch=changed?null:this.epoch;
  if(epoch!==null&&data.seat_epoch<epoch)return false;
  const life=changed||rejoined?0:this.life;
  if(data.life_id!==undefined&&(!Number.isInteger(data.life_id)||data.life_id<life))return false;
  if(hasInstance&&(!Number.isInteger(data.life_id)||data.life_id<0||!Number.isInteger(data.vehicle_id)||data.vehicle_id<0||!Number.isInteger(data.seat)||data.seat<-2||data.seat>7||(data.vehicle_id===0&&data.seat!==-2)))return false;
  if(changed){if(this.instance)this.retiredInstances.add(this.instance);if(this.retiredInstances.size>8)this.retiredInstances.delete(this.retiredInstances.values().next().value);this.instance=instance;}
  this.capable=true;this.epoch=data.seat_epoch;this.life=Number.isInteger(data.life_id)?data.life_id:life;
  if(Number.isInteger(data.vehicle_id)){this.vehicle=data.vehicle_id;this.seat=Number.isInteger(data.seat)?data.seat:-2;}
  return true;
 }
 request(action,body,life=this.life){if(!this.capable)return body;if(!Number.isSafeInteger(this.epoch))throw Error('Araç durumu yenileniyor.');const result={...body,epoch_protocol:200,life_id:life,seat_epoch:this.epoch,...(this.instance?{server_instance51:this.instance}:{})};if(action==='exit'){if(!this.vehicle)throw Error('Sunucuya göre araçta değilsin.');result.id=this.vehicle;result.seat=this.seat;}return result;}
 current(){return {success:true,observation_only:true,seat_protocol:200,seat_epoch:this.epoch,life_id:this.life,vehicle_id:this.vehicle,seat:this.seat,...(this.instance?{server_instance51:this.instance}:{})};}
 packet(data){if(!this.capable)return data;return {...data,seat_protocol:200,seat_epoch:this.epoch,...(this.instance?{server_instance51:this.instance}:{}),vehicle_sample:data.vehicle_sample?{...data.vehicle_sample,seat_epoch:this.epoch,...(this.instance?{server_instance51:this.instance}:{})}:null};}
}window.PAVSeat200=Seat200;})();
