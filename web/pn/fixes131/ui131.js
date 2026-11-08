/* PAVCITY 131: capacity bars under the inventory headers ("2.4 / 30 kg", "0 / 6 hazır"). Only the open
 * inventory panel is observed; the HUD itself is watched for panels being added, not for its updates. */
(()=>{'use strict';
function bars(root){for(const span of root.querySelectorAll('.pav-storage-layout>section>header span,.p86-magazines header span')){const m=/([\d.,]+)\s*\/\s*([\d.,]+)/.exec(span.textContent);if(!m)continue;const head=span.parentElement;let bar=head.querySelector(':scope>.w131');if(!bar){bar=document.createElement('div');bar.className='w131';bar.innerHTML='<i></i>';head.append(bar);}
 const v=parseFloat(m[1].replace(',','.')),max=parseFloat(m[2].replace(',','.'))||1,pct=Math.max(0,Math.min(100,v/max*100)),w=pct.toFixed(1)+'%';if(bar.style.getPropertyValue('--w')!==w)bar.style.setProperty('--w',w);bar.classList.toggle('heavy',pct>=85);}}
function install(g){if(!g?.hud||g.ui131)return;g.ui131=true;let watched=null,inner=null,queued=false;
 const schedule=()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;if(watched?.isConnected)bars(watched);});};
 const look=()=>{const s=g.hud.querySelector('.pav-storage');if(s===watched)return;inner?.disconnect();watched=s;inner=null;if(s){inner=new MutationObserver(schedule);inner.observe(s,{childList:true,subtree:true,characterData:true});schedule();}};
 new MutationObserver(look).observe(g.hud,{childList:true});const poll=setInterval(()=>{if(!g.hud.isConnected){clearInterval(poll);return;}look();},1000);
 addEventListener('pav-game-stop',()=>inner?.disconnect(),{once:true});}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
