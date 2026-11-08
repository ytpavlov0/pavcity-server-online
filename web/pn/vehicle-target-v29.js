(()=>{'use strict';const key=v=>v.id+':'+v.index;
 window.PAVVehicleTarget26={key,
  choose(points,previous,held,pointer,eye){
   const score=v=>eye?Math.hypot(v.x-pointer.x,v.y-pointer.y):v.d;
   const best=points.reduce((a,b)=>!a||score(b)<score(a)?b:a,null),old=points.find(v=>key(v)===(held||previous));
   if(!old)return best;if(held)return old;
   return best&&score(best)+(eye?.035:.3)<score(old)?best:old;
  },
  blend(previous,x,y,now){if(!previous||Math.hypot(previous.x-x,previous.y-y)>80)return {x,y,t:now};const k=1-Math.exp(-Math.max(0,now-previous.t)/38);return {x:previous.x+(x-previous.x)*k,y:previous.y+(y-previous.y)*k,t:now};}
 };
})();
