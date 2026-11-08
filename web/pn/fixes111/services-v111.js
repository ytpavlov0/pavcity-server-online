/* Additive city services. No polling loop or native physics writes. */
(()=>{'use strict';const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
addEventListener('pav-game-created',({detail:g})=>queueMicrotask(()=>{
 let sound=null,seen=0,initial=true;const chime111=volume=>{try{const ctx=chime111.ctx??=new (window.AudioContext||window.webkitAudioContext)(),t=ctx.currentTime+.02,out=ctx.createGain();out.gain.value=volume;out.connect(ctx.destination);for(const [freq,delay] of [[659.25,0],[783.99,.1],[1046.5,.2]]){const osc=ctx.createOscillator(),env=ctx.createGain();osc.type='sine';osc.frequency.value=freq;env.gain.setValueAtTime(0,t+delay);env.gain.linearRampToValueAtTime(.32,t+delay+.02);env.gain.exponentialRampToValueAtTime(.0001,t+delay+.85);osc.connect(env).connect(out);osc.start(t+delay);osc.stop(t+delay+.9);}}catch{}};
 g.garage=async()=>{
  const r=await g.api('/api/garage61/list');g.garages61=r.garages;
  const p=g.openRP('Garaj · Araçlarım','<p>'+esc(r.nearby?.name||'Bir garaja yaklaşarak aracını bırakabilir veya çıkarabilirsin.')+'</p><div class="pav-garage-routes61">'+r.garages.map(v=>'<button data-garage-gps="'+v.id+'">P · '+esc(v.name)+'</button>').join('')+'</div><div class="rp-job-cards">'+r.vehicles.map(v=>'<article><small>#'+v.id+' · '+esc(v.plate)+'</small><h3>'+esc(v.model.toUpperCase())+'</h3><p>'+ (v.active?'Dışarıda':'Garajda')+'</p><button data-car="'+v.id+'" data-do="'+(v.active?'store':'retrieve')+'" '+(!r.nearby?'disabled':'')+'>'+(v.active?'Garaja koy':'Garajdan çıkar')+'</button>'+(v.active?'<button data-car="'+v.id+'" data-do="park">Park noktası kaydet · $250</button>':'')+'</article>').join('')+'</div><p>Park kaydı aracın dönüş noktasını belirler. Boş araçlar yaklaşık 35 dakikada kademeli döner; dolu araçlara dokunulmaz.</p>','pav-garage61');
  p.querySelectorAll('[data-garage-gps]').forEach(b=>b.onclick=()=>{const v=r.garages.find(v=>v.id===Number(b.dataset.garageGps));g.setWaypoint(v.x,v.y);g.notice(v.name+' GPS’e işlendi.');});
  p.querySelectorAll('[data-car]').forEach(b=>b.onclick=async()=>{b.disabled=true;try{const result=await g.api('/api/garage61/'+b.dataset.do,{id:Number(b.dataset.car)});if(result.vehicle){g.failedModels33?.delete(result.vehicle.id);g.addVehicle?.(result.vehicle);}g.notice(result.notice);await g.garage();}catch(e){p.querySelector('.rp-error').textContent=e.message;}finally{b.disabled=false;}});
 };
 // Coordinates are presentation only; every action checks the server position.
 g.garages61=[{id:1,name:'Legion Garajı',x:215.8,y:-810.1,z:30.7},{id:2,name:'Vespucci Garajı',x:-1184.8,y:-1510.1,z:4.4},{id:3,name:'Sandy Garajı',x:1737.6,y:3710.2,z:34.1}];
 const receive=e=>{
  if(!g.hud.isConnected){removeEventListener('pav-game-data',receive);sound?.pause();return;}
  const s=e.detail.payroll61;if(!s)return;
  if(initial){initial=false;seen=s.paid?s.period:0;}
  if(s.period<=seen||(!s.code&&!s.paid))return;seen=s.period;
  g.notice(s.code?'Saatlik $'+s.amount+' hazır. Sohbete /onayla '+s.code+' yaz.':'Saatlik $'+s.amount+' banka hesabına yatırıldı.');
  // Playback failure never blocks or retries the financial transaction.
  if(!document.hidden&&g.voice?.listening&&localStorage.getItem('pav-payday-sound61')!=='off'){
   /* 111: a short soft chime replaces the payday music track. */chime111(.22*Math.max(0,Math.min(1,g.voice.volume??1)));
  }
 };
 addEventListener('pav-game-data',receive);
}));})();
