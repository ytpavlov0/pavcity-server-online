/* 112: publish each HUD-editor group's real rendered size so the on-screen clamp lets a
 * group sit flush in any corner (the 110 clamp assumed a 360 px wide money stack). */
(()=>{'use strict';
const groups='.p84-status-stack,.p82-vitals,.pn-radar-frame,.pn-tools,.p83-drive,.pn-chat';
const sizes=new ResizeObserver(rows=>{for(const r of rows){const box=r.target.getBoundingClientRect();r.target.style.setProperty('--fit112w',Math.ceil(box.width)+'px');r.target.style.setProperty('--fit112h',Math.ceil(box.height)+'px');}});
const watch=()=>{const hud=document.getElementById('pn-game');if(!hud)return;hud.querySelectorAll(groups).forEach(n=>{if(!n.dataset.fit112){n.dataset.fit112='1';sizes.observe(n);}});};
addEventListener('pav-game-created',()=>{setTimeout(watch,0);setTimeout(watch,2000);});
addEventListener('resize',watch);
})();
