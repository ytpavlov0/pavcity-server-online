/* Two-stop lift UI. Every mutation, target and key is rechecked by the server. */
(()=>{'use strict';const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
addEventListener('pav-game-created',({detail:g})=>{
 if(window.PAVMobile?.active)return;
 let rows=[],world=null,nearest=null,last=0,opening=false,progress=null;
 const pose=()=>g.bridge&&new Float32Array(g.bridge.memory.buffer,g.bridge.block,16384);
 const distance=r=>{const f=pose();return f?Math.hypot(r.x-f[16],r.y-f[17],r.z-f[18]):Infinity;};
 const available=()=>!g.transitions32?.busy&&!g.vehicle&&!g.isDead&&!g.actionBusy&&!g.menuOpen&&!g.uiOpen&&!g.chatOpen;
 const key=e=>{
  if(e.code!=='KeyE'||e.ctrlKey||e.metaKey||!available()||!nearest||distance(nearest)>2.2||g.nearVehiclePart||g.jobInteraction||e.target?.matches?.('input,textarea,select,[contenteditable=true]'))return;
  e.preventDefault();e.stopImmediatePropagation();if(e.type==='keydown'&&!e.repeat)void open(nearest.id);
 };
 // Registered before the older generic E handlers; only a nearby lift consumes it.
 addEventListener('keydown',key,true);addEventListener('keyup',key,true);
 const hint=document.createElement('button');hint.className='pav-lift32-hint';hint.hidden=true;hint.innerHTML='<kbd>E</kbd><span><strong></strong><small>Asansör · İki yönlü geçiş</small></span>';hint.onclick=()=>nearest&&open(nearest.id);g.hud.append(hint);
 const receive=e=>{world=e.detail;rows=Array.isArray(world.elevators)?world.elevators.slice(0,64):[];};addEventListener('pav-game-data',receive);
 const status=e=>{if(e.detail.game!==g)return;const s=e.detail;if(!progress){progress=document.createElement('aside');progress.className='pav-transition32';progress.setAttribute('role','status');progress.setAttribute('aria-live','polite');g.hud.append(progress);}progress.hidden=!s.busy&&!s.retry;progress.dataset.recovery=s.retry?'yes':'no';progress.textContent=s.detail||({prepare:'Geçiş kontrol ediliyor…',geometry:'Hedefteki zemin hazırlanıyor…',commit:'Geçiş onaylanıyor…',arrival:'Varış noktası kontrol ediliyor…',rollback:'Güvenli konuma dönülüyor…'})[s.phase]||'Geri dönüş onaylanamadı. Karakterin güvenli şekilde bekletiliyor.';if(s.canCancel){const cancel=document.createElement('button');cancel.textContent='Hazırlığı iptal et';cancel.style.pointerEvents='auto';cancel.onclick=()=>{cancel.disabled=true;g.transitions32.cancelPreparation();};progress.append(cancel);}if(s.retry){const retry=document.createElement('button');retry.textContent='Geri dönüşü tekrar dene';retry.onclick=async()=>{retry.disabled=true;try{await g.transitions32.retryRollback();}catch(error){g.notice(error.message,true);}finally{if(retry.isConnected)retry.disabled=false;}};progress.append(retry);}};addEventListener('pav-transition-state',status);
 async function open(id){
  if(opening||g.transitions32?.busy)return;opening=true;
  try{
   const result=await g.api('/api/elevators/list'),lift=result.elevators.filter(v=>v.id===id).sort((a,b)=>distance(a)-distance(b))[0];
   if(!lift||distance(lift)>3)throw Error('Asansör kapısına yaklaş.');
   const p=g.openRP('Asansör · '+lift.name,'<div class="pav-lift32"><div class="pav-lift32-route"><article><small>BULUNDUĞUN DURAK</small><strong>'+ (lift.side+1)+'</strong></article><span aria-hidden="true">⇄</span><article><small>HEDEF DURAK</small><strong>'+ (2-lift.side)+'</strong></article></div><div class="pav-lift32-status"><span>'+(lift.locked?'Kilitli':'Açık')+'</span><span>'+(lift.has_key?'Anahtar sende':'Anahtarın yok')+'</span></div><button class="pav-primary" data-lift-travel '+(lift.locked&&!lift.has_key?'disabled':'')+'>Diğer durağa geç</button>'+(lift.has_key?'<button data-lift-lock>'+(lift.locked?'Kilidi aç':'Kilitle')+'</button>':'')+(lift.owner?'<form class="pav-lift32-keys"><label>Oyuncu ID<input name="server_id" type="number" min="1" step="1" required aria-label="Asansör anahtarı için oyuncu ID"></label><div><button type="submit">Anahtar ver</button><button type="button" data-lift-revoke>Anahtarı geri al</button></div><small>Anahtar verirken oyuncu yanında olmalı.</small></form>':'')+'</div>','pav-lift32-panel');
   const error=e=>{if(p.isConnected)p.querySelector('.rp-error').textContent=e.message;else g.notice(e.message,true);};
   p.querySelector('[data-lift-travel]').onclick=async e=>{e.currentTarget.disabled=true;try{await g.elevatorTravel32(lift.id);}catch(e){error(e);}finally{if(p.isConnected)p.querySelector('[data-lift-travel]').disabled=lift.locked&&!lift.has_key;}};
   const mutate=async(action,body={})=>{const r=await g.api('/api/elevators/'+action,{id:lift.id,...body});g.notice(r.notice);g.closeRP();await open(lift.id);};
   p.querySelector('[data-lift-lock]')?.addEventListener('click',async e=>{e.currentTarget.disabled=true;try{await mutate('lock');}catch(e){error(e);}finally{if(p.isConnected)p.querySelector('[data-lift-lock]').disabled=false;}});
   const form=p.querySelector('form');if(form){let pending=false;const change=async action=>{if(pending)return;const input=form.elements.server_id;if(!input.reportValidity())return;pending=true;try{await mutate(action,{server_id:Number(input.value)});}catch(e){error(e);}finally{pending=false;}};form.onsubmit=e=>{e.preventDefault();void change('give-key');};form.querySelector('[data-lift-revoke]').onclick=()=>change('revoke-key');}
  }catch(e){g.notice(e.message,true);}finally{opening=false;}
 }
 g.elevatorPanel32=open;
 queueMicrotask(()=>queueMicrotask(()=>{
  const oldTargets=g.targets;g.targets=(...args)=>{oldTargets(...args);const list=g.hud.querySelector('.pav-target-list');if(!list)return;const nearby=rows.filter(v=>distance(v)<=3).sort((a,b)=>distance(a)-distance(b));const seen=new Set();for(const row of nearby){if(seen.has(row.id))continue;seen.add(row.id);const article=document.createElement('article'),h=document.createElement('h3'),button=document.createElement('button');h.textContent=row.name+' · Asansör';button.textContent='Durak '+(row.side+1)+' · Etkileşime gir';button.onclick=()=>{g.closeFeatures?.();void open(row.id);};article.append(h,button);list.append(article);if(seen.size===4)break;}if(seen.size)list.querySelector(':scope > p')?.remove();};
 }));
 function frame(now){
  if(!g.hud.isConnected){hint.remove();progress?.remove();removeEventListener('keydown',key,true);removeEventListener('keyup',key,true);removeEventListener('pav-game-data',receive);removeEventListener('pav-transition-state',status);g.transitions32?.cancel();return;}
  requestAnimationFrame(frame);if(document.hidden||now-last<150)return;last=now;
  nearest=rows.filter(v=>distance(v)<=2.2).sort((a,b)=>distance(a)-distance(b))[0]||null;
  hint.hidden=!nearest||!available()||!!g.nearVehiclePart||!!g.jobInteraction;
  if(!hint.hidden)hint.querySelector('strong').textContent=nearest.name+' · Durak '+(nearest.side+1);
 }
 requestAnimationFrame(frame);
});})();
