/* Workshop view of the real car. Preview is local; payment is server-owned. */
(()=>{'use strict';const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
addEventListener('pav-game-created',({detail:g})=>queueMicrotask(()=>queueMicrotask(()=>{
 let active=null,opening=false,remote=null,audio=null;
 const heap=()=>g.bridge?{a:new Int32Array(g.bridge.memory.buffer,g.bridge.block,16384),f:new Float32Array(g.bridge.memory.buffer,g.bridge.block,16384)}:null;
 const requestId=()=>crypto.randomUUID().replaceAll('-','');
 const sound=air=>{try{audio??=new AudioContext();void audio.resume();const count=Math.floor(audio.sampleRate*.18),buffer=audio.createBuffer(1,count,audio.sampleRate),data=buffer.getChannelData(0);for(let i=0;i<count;i++)data[i]=(Math.random()*2-1)*(1-i/count)*(air?.06:.035);const source=audio.createBufferSource(),filter=audio.createBiquadFilter();source.buffer=buffer;filter.type=air?'highpass':'bandpass';filter.frequency.value=air?1600:950;source.connect(filter).connect(audio.destination);source.start();}catch{}};
 const stop=()=>{if(active){active.dead=true;active.panel.remove();active=null;}const h=heap();if(h){h.a[12800]=h.a[12810]=0;h.a[12811]=h.a[12812]=h.a[12813]=h.a[12814]=-2;}g.uiOpen=false;};
 const close=g.closeRP;g.closeRP=()=>{stop();return close();};
 const open=g.openRP;g.openRP=(...args)=>{stop();return open(...args);};
 const errors=(p,e)=>{const n=p.querySelector('.rp-error');if(n)n.textContent=e.message;};
 g.tuning=async()=>{
  if(opening)return;opening=true;let entry;
  try{
   entry=await g.api('/api/tuning/list');const v=entry.vehicle;
   if(v.engine)await g.vehicleAction('engine',v.id);
   const r=await g.api('/api/customs72/list',{vehicle_id:v.id});const horns=(await g.api('/api/horns84/catalog')).horns;
   const p=g.openRP('PAV CUSTOMS','<p class="p72-plate">'+esc(v.plate)+' <small>'+esc(v.model.toUpperCase())+' · #'+v.id+'</small></p><div class="p72-camera"><button data-camera="-30">↶ Döndür</button><button data-camera="30">Döndür ↷</button><label>Yakınlık<input data-zoom type="range" min="3" max="9" step=".2" value="5"></label></div><p class="p72-preview-note">Gerçek aracın üzerinde önizle. Satın almadığın önizleme kapatınca geri alınır.</p><nav class="p72-parts"></nav><div class="p72-selected"></div><section class="p72-air-kit"><h3>Air süspansiyon</h3><p data-air-state>Motor uyumluluğu kontrol ediliyor…</p><button data-air-buy disabled>Air kiti · $18.000</button></section>','p72-customs');
   const h=heap();if(!h)throw Error('Oyun motoru hazır değil.');const life={panel:p,id:v.id,dead:false,selection:null,read:r};active=life;h.a[12800]=1;h.a[12801]=v.id;h.a[12804]=0;h.f[12802]=45;h.f[12803]=5;h.a[12810]=1;h.a[12811]=h.a[12812]=h.a[12813]=h.a[12814]=-2;
   const closePanel=p.querySelector('.rp-close');closePanel.onclick=()=>g.closeRP();
   p.querySelectorAll('[data-camera]').forEach(b=>b.onclick=()=>{h.f[12802]+=Number(b.dataset.camera);});p.querySelector('[data-zoom]').oninput=e=>h.f[12803]=Number(e.target.value);
   const labels=p.querySelector('.p72-parts'),selected=p.querySelector('.p72-selected');
   const caps={wheels:12820,engine:12821,brakes:12822,suspension:12823,spoiler:12824};
   const select=(key,opt)=>{life.selection=key;labels.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.part===key)));const cap=caps[key],max=cap?Math.min(opt.max,h.a[cap]-1):opt.max,unavailable=key==='wheels'&&v.model==='pavtofas'||cap&&max<0;selected.innerHTML='<h3>'+esc(opt.name)+'</h3><p>$'+Number(opt.price).toLocaleString('tr-TR')+'</p>'+(unavailable?'<p>Bu modelde bu parça desteklenmiyor. Ücret kesilmez.</p>':'<label>Seviye / renk ID<input type="number" data-value min="'+opt.min+'" max="'+max+'" value="'+(r.vehicle.mods?.[key]??opt.min)+'"></label><div class="p72-colours"></div><button data-preview>Önizle</button><button data-buy>Tak ve öde</button>');if(unavailable)return;
    if(key==='custom_horn'){const old=selected.querySelector('[data-value]'),list=document.createElement('select');list.dataset.value='';list.setAttribute('aria-label','Havalı korna');list.innerHTML='<option value="0">Fabrika kornası</option>'+horns.map(v=>'<option value="'+v.id+'">'+esc(v.name)+'</option>').join('');list.value=String(r.vehicle.mods?.custom_horn||0);old.replaceWith(list);list.closest('label').firstChild.textContent='Korna sesi';}
    const field=selected.querySelector('[data-value]'),preview=()=>{const value=Number(field.value);if(!Number.isInteger(value)||value<opt.min||value>max)throw Error('Desteklenen değer '+opt.min+'–'+max+'.');const cell={primary:12811,secondary:12812,wheels:12813,tint:12814}[key];if(cell){h.a[cell]=value;h.a[12810]++;}return value;};
    if(['primary','secondary'].includes(key))for(const [id,colour]of [[0,'#090909'],[5,'#999ba3'],[27,'#8b1114'],[38,'#df6521'],[53,'#15502b'],[64,'#213862'],[70,'#2471da'],[88,'#f3b435'],[111,'#eee'],[134,'#fff'],[135,'#ba2469'],[145,'#70278b']]){const b=document.createElement('button');b.title='Renk #'+id;b.style.background=colour;b.textContent=id;b.onclick=()=>{field.value=id;preview();};selected.querySelector('.p72-colours').append(b);}
    selected.querySelector('[data-preview]').onclick=()=>{try{const value=preview();if(key==='custom_horn'){void g.previewHorn85?.(value).catch(e=>errors(p,e));return;}if(!['primary','secondary','wheels','tint'].includes(key))g.notice('Performans parçası satın alındığında uygulanır.');}catch(e){errors(p,e);}};
    selected.querySelector('[data-buy]').onclick=async e=>{const button=e.currentTarget;if(life.buying)return;life.buying=true;button.disabled=true;try{const value=preview(),result=await g.api('/api/customs72/buy',{vehicle_id:v.id,part:key,value,request_id:requestId()});if(life.dead)return;r.vehicle.mods=result.mods;h.a[12811]=h.a[12812]=h.a[12813]=h.a[12814]=-2;g.notice(result.notice);sound(false);}catch(e){errors(p,e);}finally{life.buying=false;button.disabled=false;}};
   };
   for(const [key,opt]of Object.entries(r.options)){const b=document.createElement('button');b.dataset.part=key;b.textContent=opt.name;b.onclick=()=>select(key,opt);labels.append(b);}
   await new Promise(resolve=>setTimeout(resolve,350));if(life.dead)return;select('primary',r.options.primary);
   const buy=p.querySelector('[data-air-buy]'),status=p.querySelector('[data-air-state]');
   if(r.air){buy.disabled=false;buy.textContent='Air kumandasını aç';status.textContent='Bu araca bağlı air kiti takılı.';buy.onclick=()=>{g.closeRP();g.air72(v.id).catch(e=>g.notice(e.message,true));};}
   else{
    h.a[13251]=v.id;h.a[13252]=0;Atomics.add(h.a,13250,1);const until=performance.now()+1800;while(!life.dead&&!h.a[13252]&&performance.now()<until)await new Promise(resolve=>setTimeout(resolve,50));if(life.dead)return;
    const supported=h.a[13252]===1;status.textContent=supported?'Air desteği motor tarafından doğrulandı.':'Bu araçta air hareketi doğrulanamadı; kit satışı kapalı ve ücret kesilmez.';buy.disabled=!supported;
    buy.onclick=async()=>{if(life.buying)return;life.buying=true;buy.disabled=true;try{const result=await g.api('/api/customs72/air-buy',{vehicle_id:v.id,native_verified:true,request_id:requestId()});if(life.dead)return;g.notice(result.notice);sound(true);g.closeRP();await g.air72(v.id);}catch(e){errors(p,e);buy.disabled=false;}finally{life.buying=false;}};
   }
  }catch(e){if(active)errors(active.panel,e);else g.notice(e.message,true);}finally{opening=false;}
 };
 g.air72=async(id)=>{
  id=Number(id||g.vehicle||g.nearestVehicle?.()?.id);if(!id)throw Error('Air kitli aracına yaklaş.');const r=await g.api('/api/customs72/air-status',{vehicle_id:id});if(!r.air)throw Error('Bu araçta air kiti yok. Atölyeden alabilirsin.');remote?.remove();
  const p=document.createElement('aside');p.className='p72-remote';p.innerHTML='<header><span>AIR / PAVCITY</span><button aria-label="Kumandayı kapat">×</button></header><h3></h3><small>ARACA BAĞLI KUMANDA</small><label>Ön<input data-axle="front" type="range" min="0" max="1" step=".1"></label><label>Arka<input data-axle="rear" type="range" min="0" max="1" step=".1"></label><div><button data-preset="0">Alçalt</button><button data-preset=".5">Orta</button><button data-preset="1">Yükselt</button></div><p role="status"></p>';g.hud.append(p);remote=p;p.querySelector('h3').textContent=r.vehicle.plate+' · #'+id;let setting=r.air,busy=false;
  const paint=()=>p.querySelectorAll('[data-axle]').forEach(n=>n.value=setting[n.dataset.axle]);paint();p.querySelector('header button').onclick=()=>{p.remove();if(remote===p)remote=null;};
  const set=async(front,rear)=>{if(busy)return;busy=true;p.querySelectorAll('input,button[data-preset]').forEach(n=>n.disabled=true);try{const done=await g.api('/api/customs72/air-set',{vehicle_id:id,front,rear,version:setting.version});setting=done.air;sound(true);p.querySelector('[role=status]').textContent='Ön '+Math.round(setting.front*100)+'% · Arka '+Math.round(setting.rear*100)+'%';}catch(e){p.querySelector('[role=status]').textContent=e.message;try{setting=(await g.api('/api/customs72/air-status',{vehicle_id:id})).air;}catch{}}finally{busy=false;paint();p.querySelectorAll('input,button[data-preset]').forEach(n=>n.disabled=false);}};
  p.querySelectorAll('[data-axle]').forEach(n=>n.onchange=()=>set(Number(p.querySelector('[data-axle=front]').value),Number(p.querySelector('[data-axle=rear]').value)));p.querySelectorAll('[data-preset]').forEach(n=>n.onclick=()=>set(Number(n.dataset.preset),Number(n.dataset.preset)));
 };
 addEventListener('pav-game-stop',()=>{stop();remote?.remove();void audio?.close();},{once:true});
 addEventListener('pav-game-data',({detail:d})=>{if(active&&(d.health<=100||d.vehicle_id!==undefined&&d.vehicle_id!==active.id))g.closeRP();});
})));})();
