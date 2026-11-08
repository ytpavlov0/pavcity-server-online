/* PAVCITY 129: hotwiring. Starting an engine without a key (M) opens the hotwire panel: connect the
 * five shown wires in order (1–4 or click) before the bar runs out. The server validates every step
 * (/api/hotwire129/*) and grants the vehicle key on success. */
(()=>{'use strict';
const WIRES={red:['Kırmızı','#ff4d6a'],blue:['Mavi','#4da3ff'],yellow:['Sarı','#ffd23f'],green:['Yeşil','#3ddc84']},ORDER=['red','blue','yellow','green'];
function install(g){
 if(!g?.hud||g.hotwire129)return;let active=null;
 const heap=()=>g.bridge?new Float32Array(g.bridge.memory.buffer,g.bridge.block,16384):null;
 const keys=e=>{if(!active||e.ctrlKey||e.metaKey||['F5','F11','F12'].includes(e.code))return;e.preventDefault();e.stopImmediatePropagation();if(e.type!=='keydown'||e.repeat)return;if(e.code==='Escape')active.close();const n=['Digit1','Digit2','Digit3','Digit4','Numpad1','Numpad2','Numpad3','Numpad4'].indexOf(e.code);if(n>=0)active.press(ORDER[n%4]);};
 addEventListener('keydown',keys,true);addEventListener('keyup',keys,true);
 async function hotwire(id){
  if(active)return;const v=g.vehicles.find(x=>x.id===Number(id));if(!v)throw Error('Araç bulunamadı.');
  const first=await g.api('/api/hotwire129/start',{id:v.id});g.closeFeatures?.();g.closeActions?.();g.release?.();g.uiOpen=true;
  const panel=document.createElement('section');panel.className='pav-lockpick hw129';
  panel.innerHTML='<div class="pav-lockpick-card"><header><small>PAVCITY / DÜZ KONTAK</small><button aria-label="Kapat">×</button></header><h2>Kabloları bağla.</h2><p class="pav-lockpick-car"></p><div class="pav-lockpick-steps"></div><div class="hw129-target" aria-live="polite"><i></i><b></b></div><div class="pav-lockpick-time"><i></i></div><p class="pav-lockpick-message" role="status"></p><div class="hw129-wires">'+ORDER.map((w,i)=>'<button data-wire="'+w+'" style="--w:'+WIRES[w][1]+'"><span></span><kbd>'+(i+1)+'</kbd>'+WIRES[w][0]+'</button>').join('')+'</div><footer>Gösterilen kabloyu sırayla bağla · 1–4 ya da tıkla · ESC ile vazgeç</footer></div>';
  g.hud.append(panel);panel.querySelector('.pav-lockpick-car').textContent=v.model.toUpperCase()+' · '+v.plate;
  let state=first,busy=false,ended=false,ready=0,deadline=0,timer;const target=panel.querySelector('.hw129-target'),message=panel.querySelector('[role=status]'),bar=panel.querySelector('.pav-lockpick-time i'),buttons=[...panel.querySelectorAll('[data-wire]')];
  const render=r=>{state=r;ready=performance.now()+r.ready_in_ms;deadline=performance.now()+r.timeout_ms;const w=r.completed?null:WIRES[r.wire];target.style.setProperty('--w',w?w[1]:'#fff');target.querySelector('b').textContent=w?w[0]+' kablo':'✓';panel.querySelector('.pav-lockpick-steps').replaceChildren(...Array.from({length:r.total},(_,i)=>{const n=document.createElement('i');n.className=i<r.step?'done':i===r.step?'current':'';return n;}));message.textContent='Kıvılcım gelince doğru kabloyu bağla.';};
  const cancel=()=>g.api('/api/hotwire129/cancel',{id:v.id,challenge:state.challenge}).catch(()=>{});
  const close=()=>{clearInterval(timer);if(!ended)cancel();ended=true;panel.remove();active=null;g.uiOpen=false;document.getElementById('canvas')?.focus();};
  const fail=text=>{if(ended)return;ended=true;clearInterval(timer);cancel();panel.classList.add('failed');target.querySelector('b').textContent='×';message.textContent=text;buttons.forEach(b=>b.disabled=true);panel.querySelector('footer').textContent='Tekrar denemek için pencereyi kapat ve M’ye bas.';};
  async function press(wire){if(busy||ended||performance.now()<ready)return;busy=true;buttons.forEach(b=>b.disabled=true);
   try{const r=await g.api('/api/hotwire129/step',{id:v.id,challenge:state.challenge,step:state.step,wire});if(ended||!panel.isConnected)return;render(r);
    if(r.completed){const done=await g.api('/api/hotwire129/finish',{id:v.id,challenge:r.challenge});g.addVehicle?.(done.vehicle);ended=true;close();(g.toast113?g.toast113(done.notice,'success','Düz kontak'):g.toast?.(done.notice));}}
   catch(e){fail(e.message);}finally{busy=false;}}
  active={close,press};panel.querySelector('header button').onclick=close;buttons.forEach(b=>b.onclick=()=>press(b.dataset.wire));render(first);
  timer=setInterval(()=>{if(ended)return;const f=heap(),now=performance.now();if(!f||g.isDead||g.vehicle!==v.id){fail('Sürücü koltuğundan ayrıldın. Deneme iptal edildi.');return;}if(!busy&&now>deadline){fail('Süre doldu, kablolar ayrıldı.');return;}const usable=!busy&&now>=ready;target.classList.toggle('ready',usable);buttons.forEach(b=>b.disabled=!usable);bar.style.transform='scaleX('+Math.max(0,Math.min(1,(deadline-now)/2400))+')';},50);
 }
 g.hotwire129=id=>hotwire(id??g.vehicle).catch(e=>(g.toast113?g.toast113(e.message,'error','Düz kontak'):g.toast?.(e.message,true)));
 const original=g.vehicleAction;
 if(typeof original==='function')g.vehicleAction=async(action,id,...rest)=>{try{return await original(action,id,...rest);}catch(e){if(action==='engine'&&/düz kontak gerekiyor/i.test(e.message||'')){g.hotwire129(id);return{success:false,hotwire:true};}throw e;}};
 addEventListener('blur',()=>active?.close());addEventListener('pav-game-stop',()=>active?.close(),{once:true});
}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
