/* Pointer ownership is separate from gameplay buttons. A capture click never fires. */
(()=>{'use strict';
 const P=window.PAVPointer26={manual:false};
 P.blocked=()=>{const g=window.PAVGame;return !!(g&&(g.isLoading||g.uiOpen||g.menuOpen||g.chatOpen||g.isDead||g.interactionActive));};
 P.paint=()=>{const h=window.PAVGame?.hud;if(h)h.dataset.cursorMode=document.pointerLockElement?'captured':P.manual?'manual':'free';};
 P.capture=async canvas=>{try{try{await canvas.requestPointerLock({unadjustedMovement:true});}catch(e){if(e.name!=='NotSupportedError')throw e;await canvas.requestPointerLock();}}catch(e){window.PAVGame?.notice('İmleç yakalanamadı. F3 ile yeniden dene.',true);}};
 P.install=({canvas,w,BTN,LOCKED,release,trace})=>{
  const suppressed=new Set();let swallowClick=false;
  const locked=()=>document.pointerLockElement===canvas;
  canvas.addEventListener('mousedown',e=>{
   if(window.PAVMobile?.active)return;
   if(!locked()||P.blocked()){
    release();suppressed.add(e.button);swallowClick=true;e.preventDefault();e.stopImmediatePropagation();
    if(!P.manual&&!P.blocked())P.capture(canvas);return;
   }
   if(suppressed.size)return;
   Atomics.or(w,BTN,1<<[0,2,1,3,4][e.button]);e.preventDefault();
  });
  addEventListener('mouseup',e=>{Atomics.and(w,BTN,~(1<<[0,2,1,3,4][e.button]));if(suppressed.delete(e.button)){e.preventDefault();e.stopImmediatePropagation();}},true);
  addEventListener('click',e=>{if(e.target===canvas&&swallowClick){swallowClick=false;e.preventDefault();e.stopImmediatePropagation();}},true);
  document.addEventListener('pointerlockchange',()=>{release();trace('pointer lock '+(locked()?'on':'off'));Atomics.store(w,LOCKED,locked()?1:0);if(locked())P.manual=false;P.paint();});
  addEventListener('blur',()=>{suppressed.clear();swallowClick=false;release();});
 };
 addEventListener('pav-game-created',({detail:g})=>{const hint=g.hud.querySelector('.pn-tools>span');if(hint)hint.insertAdjacentHTML('beforeend',' · <kbd>F3</kbd> İmleç');});
 addEventListener('keydown',e=>{
  if(e.code!=='F3'||window.PAVMobile?.active||!window.PAVGame)return;
  e.preventDefault();e.stopImmediatePropagation();if(e.repeat)return;
  const g=window.PAVGame;if(P.blocked()||e.target?.matches?.('input,textarea,select'))return;
  if(document.pointerLockElement){P.manual=true;g.release();g.notice('İmleç açık · F3 ile oyuna dön.');P.paint();}
  else{P.manual=false;window.pnReleaseGameInput?.();P.capture(document.getElementById('canvas'));}
 },true);
})();
