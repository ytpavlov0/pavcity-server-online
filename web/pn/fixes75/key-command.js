/* The PC chat dispatcher is private; route its public information callback. */
(()=>{'use strict';addEventListener('pav-game-created',({detail:g})=>queueMicrotask(()=>queueMicrotask(()=>{
 const info=g.showInfo?.bind(g);if(!info)return;
 g.showInfo=value=>{if(value?.title==='Araç ve mülk anahtarları'){g.keyShop().catch(e=>g.notice(e.message,true));return;}return info(value);};
})));})();
