/* Shared mission copy and completion rules for the HUD and hold prompt. */
(()=>{'use strict';window.PAVJobFlow27=(job,position,speed=0,now=Date.now()/1000)=>{
 const distance=Math.hypot(job.target.x-position.x,job.target.y-position.y,job.target.z-position.z),wait=Math.max(0,Math.ceil(job.ready_at-now));
 const state=distance>5?'travel':wait?'wait':speed>1?'stop':'ready';
 return {distance,wait,state,ready:state==='ready',label:state==='travel'?Math.round(distance)+' m · GPS hedefine git':state==='wait'?'Hazırlık · '+wait+' sn bekle':state==='stop'?'Teslimat için tamamen dur':'E basılı tut · '+(job.phase==='return'?'Ücretini al':'Durağı tamamla')};
};})();
