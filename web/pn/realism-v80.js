/* Native world color grading; one writer for the existing acknowledged FX ABI. */
(()=>{'use strict';
const key='pav-realism80',profiles=[1,2,3,4];
const normalize=v=>({enabled:typeof v?.enabled==='boolean'?v.enabled:profiles.includes(v?.profile),profile:profiles.includes(v?.profile)?v.profile:3,strength:Number.isFinite(v?.strength)?Math.max(0,Math.min(1,v.strength)):.4});
const read=()=>{try{return normalize(JSON.parse(localStorage.getItem(key)||localStorage.getItem('pav-native-fx33')||'null'));}catch{return normalize();}};
window.PAVRealism80={normalize,read};
addEventListener('pav-game-created',({detail:g})=>queueMicrotask(()=>queueMicrotask(()=>{
 const settings=g.hud.querySelector('.pav-menu-view[data-view=settings]');if(!settings)return;
 const box=document.createElement('div');box.className='pav-realism80';box.innerHTML='<header><div><span>CANLI GÖRÜNTÜ MODU</span><h3>PAV Realism</h3><p>Oyunun renk, ışık ve ton eşleme efektleri.</p></div><label class="pav-realism-switch80"><input type="checkbox" aria-label="Gerçekçi görüntü modunu aç"><span>Mod kapalı</span></label></header><div class="pav-realism-profiles80"><button data-realism="3" type="button"><i></i><strong>Gerçekçi</strong><small>Temiz renk, dengeli ışık</small></button><button data-realism="1" type="button"><i></i><strong>Doğal</strong><small>Yumuşak ton ve kontrast</small></button><button data-realism="2" type="button"><i></i><strong>Sinematik</strong><small>Film tonlaması, belirgin atmosfer</small></button><button data-realism="4" type="button"><i></i><strong>Sıcak film</strong><small>Sıcak ton, hafif film dokusu</small></button></div><div class="pav-realism-controls80"><label>Etki yoğunluğu <output></output><input type="range" min="0" max="100" step="5" aria-label="Görüntü modu yoğunluğu"></label><button type="button" data-compare80>Basılı tut · Orijinal</button><button type="button" data-reset80>Efekti kapat</button></div><p class="pav-realism-status80" role="status" aria-live="polite">Motor bekleniyor…</p><footer>Efekt anında uygulanır. Doku ve gölge kalitesi aşağıdaki PC profilinden ayarlanır. <button type="button" data-quality80>Kalite ayarlarına git ↓</button></footer>';
 settings.prepend(box);
 let state=read(),bound=null,sequence=0,last=0,timer=0,held=false,disposed=false,lastSent='';
 const limited=window.PAVMobile?.active||['mobile32','ios32'].includes(window.PAVCapabilities?.engine);
 if(limited){if(state.profile>2)state.profile=1;box.querySelectorAll('[data-realism="3"],[data-realism="4"]').forEach(b=>b.hidden=true);box.querySelector('.pav-realism-profiles80').style.gridTemplateColumns='repeat(2,minmax(0,1fr))';const quality=settings.querySelector('.pav-graphics79');if(quality)quality.hidden=true;box.querySelector('footer').textContent='Mobil motor Doğal ve Sinematik görünümleri destekler. Yoğunluğu azaltarak daha hafif bir görünüm seçebilirsin.';}
 const toggle=box.querySelector('input[type=checkbox]'),slider=box.querySelector('input[type=range]'),status=box.querySelector('[role=status]'),compare=box.querySelector('[data-compare80]');
 const paint=()=>{toggle.checked=state.enabled;toggle.nextElementSibling.textContent=state.enabled?'Mod açık':'Mod kapalı';slider.value=Math.round(state.strength*100);slider.previousElementSibling.value=slider.value+'%';box.querySelectorAll('[data-realism]').forEach(b=>b.setAttribute('aria-pressed',String(Number(b.dataset.realism)===state.profile)));compare.disabled=!state.enabled;};paint();
 const write=()=>{timer=0;if(disposed||!g.bridge){bound=null;sequence=0;lastSent='';status.textContent='Oyun motoru hazır olduğunda uygulanacak.';return;}const {memory,block}=g.bridge;if(!memory?.buffer||!Number.isInteger(block)||block<0||block+65536>memory.buffer.byteLength){bound=null;sequence=0;lastSent='';status.textContent='Motor bağlantısı bekleniyor…';return;}
  const profile=state.enabled&&!held?state.profile:0,sig=profile+'|'+state.strength;if(bound===g.bridge&&sig===lastSent)return;
  const a=new Int32Array(memory.buffer,block,16384),f=new Float32Array(memory.buffer,block,16384);a[7801]=profile;f[7802]=state.strength;sequence=Atomics.add(a,7800,1)+1;bound=g.bridge;lastSent=sig;status.textContent='Görüntü modu uygulanıyor…';
 };
 const queue=()=>{if(!timer)timer=setTimeout(write,90);};
 const save=()=>{try{localStorage.setItem(key,JSON.stringify(state));}catch{}paint();queue();};
 toggle.onchange=()=>{state.enabled=toggle.checked;held=false;save();};
 slider.oninput=()=>{state.strength=Number(slider.value)/100;slider.previousElementSibling.value=slider.value+'%';queue();};slider.onchange=save;
 box.querySelectorAll('[data-realism]').forEach(b=>b.onclick=()=>{state.profile=Number(b.dataset.realism);state.enabled=true;held=false;save();});
 const release=()=>{if(!held)return;held=false;compare.setAttribute('aria-pressed','false');write();};
 compare.onpointerdown=e=>{if(!state.enabled)return;e.preventDefault();held=true;compare.setPointerCapture?.(e.pointerId);compare.setAttribute('aria-pressed','true');write();};compare.onpointerup=compare.onpointercancel=release;compare.onlostpointercapture=release;
 compare.onkeydown=e=>{if((e.code==='Space'||e.code==='Enter')&&!e.repeat&&state.enabled){e.preventDefault();held=true;compare.setAttribute('aria-pressed','true');write();}};compare.onkeyup=e=>{if(e.code==='Space'||e.code==='Enter'){e.preventDefault();release();}};
 addEventListener('blur',release);compare.onblur=release;
 box.querySelector('[data-reset80]').onclick=()=>{state.enabled=false;held=false;save();};const qualityJump=box.querySelector('[data-quality80]');if(qualityJump)qualityJump.onclick=()=>settings.querySelector('.pav-graphics79')?.scrollIntoView({behavior:'smooth',block:'start'});
 // Keep the server-owned timed reload shortcut from the replaced v33 module.
 const reload=e=>{if(e.code!=='KeyR'||e.type!=='keydown'||e.repeat||e.ctrlKey||e.metaKey||g.chatOpen||g.menuOpen||g.uiOpen||g.isLoading||g.isDead||g.actionBusy||e.target?.closest?.('input,textarea,select,[contenteditable=true]'))return;const gun=g.loadout?.weapons?.find(w=>w.owned&&w.slot===g.loadout.selected);if(!gun||gun.category==='NULL')return;e.preventDefault();e.stopImmediatePropagation();g.usePackage('ammo_'+gun.key).catch(error=>g.notice(error.message,true));};addEventListener('keydown',reload,true);
 const render=now=>{if(!g.hud.isConnected){disposed=true;clearTimeout(timer);removeEventListener('blur',release);removeEventListener('keydown',reload,true);box.remove();return;}requestAnimationFrame(render);if(now-last<250||document.hidden)return;last=now;if(held&&!g.menuOpen)release();if(g.bridge!==bound)write();if(!bound||!sequence)return;
  const a=new Int32Array(bound.memory.buffer,bound.block,16384);if(a[7803]!==sequence)return;const active=state.enabled&&!held;
  status.textContent=active?(a[7804]>=0?'Motor tarafından uygulandı · '+Math.round(state.strength*100)+'%':'Bu efekt motor tarafından uygulanamadı. Farklı bir profil seç.'):(a[7804]===-1?(held?'Karşılaştırma · Orijinal görüntü':'Orijinal görüntü aktif · Mod kapalı'):'Kapatma motor tarafından henüz doğrulanmadı.');
 };requestAnimationFrame(render);
})));})();
