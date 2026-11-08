/* PAVCITY perf 123: the game canvas only moves on resize/fullscreen, but several HUD loops (eye mode,
 * targeting, nametags) asked for its rectangle every frame after other loops had written styles,
 * forcing a synchronous layout each time. The rectangle is cached and refreshed on resize. */
(()=>{'use strict';
const wrap=c=>{if(!c||c.__rect123)return;const real=c.getBoundingClientRect.bind(c);let rect=null;const clear=()=>{rect=null;};
 c.__rect123=true;c.getBoundingClientRect=()=>rect??=real();
 new ResizeObserver(clear).observe(c);addEventListener('resize',clear);addEventListener('scroll',clear,true);document.addEventListener('fullscreenchange',clear);};
const find=()=>wrap(document.getElementById('canvas'));
find();addEventListener('pav-game-created',()=>setTimeout(find,0));
})();
