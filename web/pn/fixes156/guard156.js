/* 156: (1) the key under Esc (code Backquote; '"' on a Turkish keyboard) opened GTA's cheat-code box (CCheat::DoCheats);
 * it never reaches the engine any more unless a text field has focus (chat, forms keep typing '"').
 * (2) Tab player list: glass116.css forces overflow:hidden on every overlay panel, so with 11+ players the lower rows
 * could not be reached. The scoreboard panel scrolls again (hidden scrollbar) with the wheel anywhere on screen and with
 * the arrow / Page / Home / End keys. Loaded before game-v29.js so its window capture listeners run first. */
(()=>{
 'use strict';
 const editable=t=>!!t&&(t.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName||''));
 const board=()=>document.querySelector('.pav-overlay.pav-scoreboard .pav-overlay-panel');
 let blocked=0;
 const key=e=>{
  if(e.code==='Backquote'&&!editable(e.target)&&!editable(document.activeElement)){e.preventDefault();e.stopImmediatePropagation();if(e.type==='keydown')blocked++;return;}
  if(e.type!=='keydown')return;
  const p=board();if(!p)return;
  const page=Math.max(60,p.clientHeight*.85),step={ArrowDown:48,ArrowUp:-48,PageDown:page,PageUp:-page}[e.code];
  if(step!==undefined)p.scrollTop+=step;else if(e.code==='Home')p.scrollTop=0;else if(e.code==='End')p.scrollTop=p.scrollHeight;else return;
  e.preventDefault();e.stopImmediatePropagation();
 };
 addEventListener('keydown',key,true);addEventListener('keyup',key,true);
 addEventListener('wheel',e=>{const p=board();if(!p)return;p.scrollTop+=e.deltaMode===1?e.deltaY*32:e.deltaMode===2?e.deltaY*p.clientHeight:e.deltaY;e.preventDefault();e.stopImmediatePropagation();},{capture:true,passive:false});
 const css=document.createElement('style');css.id='pav-guard156';
 css.textContent='html body #pn-game .pav-overlay.pav-scoreboard .pav-overlay-panel,html body #pn-game.pav106.pav106 .pav-overlay.pav-scoreboard:not(.rp-overlay) .pav-overlay-panel{max-height:86vh!important;overflow-x:hidden!important;overflow-y:auto!important;overscroll-behavior:contain;scrollbar-width:none!important;-ms-overflow-style:none!important}'+
  'html body #pn-game .pav-overlay.pav-scoreboard .pav-overlay-panel::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}'+
  'html body #pn-game .pav-overlay.pav-scoreboard .pav-overlay-panel>header{position:sticky!important;top:0;z-index:2;background:rgba(13,8,21,.97)!important}';
 (document.head||document.documentElement).append(css);
 window.PAVGuard156={cheatKeysBlocked:()=>blocked,board};
})();
