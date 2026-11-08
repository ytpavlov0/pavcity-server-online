/* The service role is supplied by authenticated sync, never by local settings.
 * No extra requests, entity scans, global key handlers or gameplay pause flags.
 */
(()=>{'use strict';
addEventListener('pav-game-created',({detail:g})=>{queueMicrotask(()=>queueMicrotask(()=>queueMicrotask(()=>queueMicrotask(()=>{
 if(!g?.hud?.isConnected||g.hud.querySelector('.p84-status-stack'))return;
 const live=g.hud.querySelector('.pn-live'),account=g.hud.querySelector('.pn-top-hud');if(!live||!account)return;
 const stack=document.createElement('div');stack.className='p84-status-stack';account.before(stack);stack.append(account);
 const wanted=document.createElement('section');wanted.className='p84-wanted';wanted.hidden=true;wanted.setAttribute('role','status');wanted.setAttribute('aria-live','polite');
 wanted.innerHTML='<span>ARANIYOR</span><div class="p84-stars" aria-hidden="true">'+Array.from({length:5},()=>'<svg viewBox="0 0 24 24"><path d="m12 2 3 6.1 6.7 1-4.8 4.7 1.1 6.7-6-3.2-6 3.2 1.1-6.7-4.8-4.7 6.7-1Z"/></svg>').join('')+'</div><b></b>';
 stack.append(wanted);const ammo=g.hud.querySelector('.p82-ammo');if(ammo)stack.append(ammo);
 const stars=[...wanted.querySelectorAll('svg')];let dataAt=-Infinity,role=null,sequence=-1,changedAt=-Infinity,lastWanted=-1,timer;
 const receive=event=>{const data=event.detail||{};role=data.services178?.role||null;dataAt=performance.now();
  const bridge=g.bridge;if(!bridge)return;const a=new Int32Array(bridge.memory.buffer,bridge.block,16384);
  // The requested exemption covers police faction members, including off duty.
  a[14500]=role?.kind==='police'&&Number.isSafeInteger(role.faction_id)&&role.faction_id>0?1:0;
  Atomics.add(a,14501,1);
 };
 const clear=()=>{if(!g.bridge)return;const a=new Int32Array(g.bridge.memory.buffer,g.bridge.block,16384);a[14500]=0;};
 const update=()=>{
  if(!g.hud.isConnected){removeEventListener('pav-game-data',receive);removeEventListener('pagehide',clear);clear();return;}
  const now=performance.now(),bridge=g.bridge;let level=0;
  if(bridge){const a=new Int32Array(bridge.memory.buffer,bridge.block,16384);
   if(now-dataAt>=2000)a[14500]=0;
   const seq=Atomics.load(a,14506);if(!(seq&1)){if(seq!==sequence){sequence=seq;changedAt=now;}if(seq&&now-changedAt<1500){const value=a[14504];if(seq===Atomics.load(a,14506))level=Math.max(0,Math.min(5,value));}}
  }
  const visible=!document.hidden&&!g.menuOpen&&!g.uiOpen&&!g.isDead&&g.hud.dataset.entering!=='true'&&level>0;
  wanted.hidden=!visible;
  if(level!==lastWanted){lastWanted=level;stars.forEach((star,i)=>star.classList.toggle('active',i<level));wanted.querySelector('b').textContent=level+'/5';wanted.setAttribute('aria-label','Aranma seviyesi '+level+' / 5');}
  timer=setTimeout(update,125);
 };
 addEventListener('pav-game-data',receive);addEventListener('pagehide',clear);update();
}))));});
})();
