/* PAVCITY HUD 106: marks #pn-game for the Vice layer, swaps raster icons for the crisp
 * PAVIcons105 set, animates cash changes and illustrates job cards. Runs after every
 * older pav-game-created patcher (they finish within five microtasks). */
(()=>{'use strict';
const icon=name=>window.PAVIcons105?.svg(name)||'';
const tiles={'Envanter':'inventory','Araçlarım':'car','Meslekler':'jobs','Birlik':'faction','Mülkler':'home','Telefon':'phone','Destek':'support','Hesabım':'user','Polis bilgisayarı':'police'};
const jobs=new Set(['courier','recycling','contraband','assassin','harvest','watermelon','tomato','winery']);
function swapIcon(holder,name){if(!holder||holder.dataset.icon106===name)return;holder.querySelectorAll('img,svg').forEach(n=>n.remove());holder.insertAdjacentHTML('afterbegin',icon(name));holder.dataset.icon106=name;}
function launchers(hud){hud.querySelectorAll('.pav-city-launchers>button').forEach(b=>{const name=tiles[b.querySelector('strong')?.textContent.trim()];if(name)swapIcon(b.querySelector('span'),name);});}
function jobCards(root){root.querySelectorAll('.rp-job-cards>article:not([data-job106])').forEach(card=>{const key=card.querySelector('[data-start],[data-route]')?.dataset.start||card.querySelector('[data-route]')?.dataset.route;card.dataset.job106=key||'';if(jobs.has(key))card.style.setProperty('--job106','url("/pn/fixes106/jobs/'+key+'.webp")');if(/İLLEGAL/.test(card.querySelector('small')?.textContent||''))card.classList.add('illegal106');});}
function decorate(){const hud=document.getElementById('pn-game');if(!hud)return;hud.classList.add('pav106');
 const wallet=hud.querySelector('.pn-wallet'),money=hud.querySelector('.pn-money');
 if(wallet&&money&&!wallet.querySelector('.pav106-cash')){const i=document.createElement('span');i.className='pav106-cash';i.innerHTML=icon('cash');money.before(i);i.firstElementChild?.setAttribute('style','width:24px;height:24px;color:var(--v6-cash);filter:drop-shadow(0 1px 1px rgba(0,0,0,.6))');
  let last=money.textContent;new MutationObserver(()=>{if(money.textContent===last)return;last=money.textContent;money.classList.remove('pav106-tick');void money.offsetWidth;money.classList.add('pav106-tick');}).observe(money,{childList:true,characterData:true,subtree:true});}
 swapIcon(hud.querySelector('.pav-map-location'),'pin');
 launchers(hud);const list=hud.querySelector('.pav-city-launchers');if(list&&!list.dataset.watch106){list.dataset.watch106='1';new MutationObserver(()=>launchers(hud)).observe(list,{childList:true});}
 if(!hud.dataset.watch106){hud.dataset.watch106='1';new MutationObserver(records=>{for(const r of records)for(const n of r.addedNodes)if(n.nodeType===1&&(n.matches?.('.rp-jobs')||n.querySelector?.('.rp-job-cards')))jobCards(n);}).observe(hud,{childList:true});}
}
addEventListener('pav-game-created',()=>{setTimeout(decorate,0);setTimeout(decorate,1500);});
if(document.getElementById('pn-game'))decorate();
window.PAVHud106={decorate,jobCards};
})();
