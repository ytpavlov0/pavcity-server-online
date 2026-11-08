/* Native bone projections, two nearby cars at most; server rechecks every action. */
(()=>{'use strict';addEventListener('pav-game-created',({detail:g})=>queueMicrotask(()=>{
 const names=['Sol ön kapı','Sağ ön kapı','Sol arka kapı','Sağ arka kapı','Kaput','Bagaj'],layer=document.createElement('div');layer.className='pav-car-points22';g.hud.append(layer);const nodes=new Map();let target=null,last=0,busy=false,held=0,heldKey='',rect=null;const stable=PAVVehicleTarget26;const canvas=document.getElementById('canvas'),size=new ResizeObserver(()=>rect=null);size.observe(canvas);const reset=()=>{held=0;heldKey='';};addEventListener('blur',reset);
 async function open(v){if(busy)return;const car=g.vehicles.find(c=>c.id===v.id);if(!car)return;if(g.interactionActive)g.eyeMode();const p=g.openRP(names[v.index]+' · '+car.model.toUpperCase(),'<div class="pav-part-actions"><p>'+car.plate+' · '+(car.locked?'Kilitli':'Açık')+'</p><button data-part-door>'+((car.doors||0)&(1<<v.index)?'Kapat':'Aç')+'</button>'+(v.index<4?'<button data-part-enter>Bu koltuğa bin</button><button data-part-window>Camı '+((car.windows||0)&(1<<v.index)?'kapat':'aç')+'</button>':v.index===5?'<button data-part-inventory>Bagaj envanteri</button>':'<p>Motor · '+(car.engine?'Çalışıyor':'Kapalı')+' · Yakıt '+Math.round(car.fuel??100)+'%</p>')+'<button data-part-lock>Kilit aç / kapat · K</button></div>','pav-part22');const run=async fn=>{if(busy)return;busy=true;try{await fn();g.closeRP();}catch(e){p.querySelector('.rp-error').textContent=e.message;}finally{busy=false;}};p.querySelector('[data-part-door]').onclick=()=>run(async()=>{const r=await g.api('/api/vehicles/door',{id:v.id,index:v.index,open:!((car.doors||0)&(1<<v.index))});g.notice(r.notice);});p.querySelector('[data-part-lock]').onclick=()=>run(()=>g.vehicleAction('lock',v.id));p.querySelector('[data-part-enter]')?.addEventListener('click',()=>run(()=>g.vehicleAction('enter',v.id,v.index-1)));p.querySelector('[data-part-window]')?.addEventListener('click',()=>run(async()=>{const r=await g.api('/api/vehicles/window',{id:v.id,index:v.index,open:!((car.windows||0)&(1<<v.index))});g.notice(r.notice);}));p.querySelector('[data-part-inventory]')?.addEventListener('click',()=>g.inventory('trunk:'+v.id).catch(e=>p.querySelector('.rp-error').textContent=e.message));}
 const key=e=>{
  if(e.code!=='KeyE')return;if(e.type==='keyup'){reset();return;}
  if(e.repeat||!target||g.uiOpen||g.menuOpen||g.chatOpen||g.isDead||g.actionBusy||e.target.matches('input,textarea,select'))return;
  e.preventDefault();e.stopImmediatePropagation();held=performance.now();heldKey=target.id+':'+target.index;
 };addEventListener('keydown',key,true);addEventListener('keyup',key,true);
 function frame(now){
  if(!g.hud.isConnected){layer.remove();size.disconnect();removeEventListener('keydown',key,true);removeEventListener('keyup',key,true);removeEventListener('blur',reset);g.nearVehiclePart=null;return;}
  requestAnimationFrame(frame);if(document.hidden||now-last<33)return;last=now;
  layer.hidden=!g.bridge||!!g.vehicle||g.uiOpen||g.menuOpen||g.chatOpen||g.isDead||g.actionBusy||g.jobInteraction;g.nearVehiclePart=null;
  if(layer.hidden){target=null;reset();return;}
  const a=new Int32Array(g.bridge.memory.buffer,g.bridge.block,16384),f=new Float32Array(g.bridge.memory.buffer,g.bridge.block,16384),seq=Atomics.load(a,7500);if(seq&1)return;
  const points=[];for(let i=0;i<Math.min(12,a[7501]);i++){const o=7510+i*8;if(a[o+5]&&f[o+2]>0&&f[o+2]<1&&f[o+3]>0&&f[o+3]<1&&f[o+4]<3)points.push({id:a[o],index:a[o+1],x:f[o+2],y:f[o+3],d:f[o+4]});}if(seq!==Atomics.load(a,7500))return;
  const pointer=g.targetPointer||{x:.5,y:.5};const prior=heldKey&&nodes.get(heldKey);target=stable.choose(points,target?stable.key(target):'',heldKey,pointer,g.interactionActive);if(prior&&now-prior._seen<120&&!points.some(v=>stable.key(v)===heldKey))target=prior._point;g.nearVehiclePart=target;
  if(heldKey&&heldKey!==(target?target.id+':'+target.index:''))reset();
  rect??=canvas.getBoundingClientRect();const seen=new Set();
  /* 112: only the targeted part carries a label (eye mode keeps all); fewer nodes, no wall of prompts. */for(const v of (g.interactionActive?points:target?[target]:[])){const k=v.id+':'+v.index;seen.add(k);let n=nodes.get(k);if(!n){n=document.createElement('button');n.className='pav-car-point22';n.innerHTML='<kbd>E</kbd><span>'+names[v.index]+'</span>';n.setAttribute('aria-label',names[v.index]+' · Araç '+v.id);layer.append(n);nodes.set(k,n);n.onclick=()=>{if(performance.now()-n._seen<120&&!layer.hidden)open(n._point).catch(e=>g.notice(e.message,true));};}
   n._point=v;n._seen=now;n.hidden=false;n.disabled=false;n.classList.toggle('focused',v===target);
   n._pos=stable.blend(n._pos,rect.left+v.x*rect.width,rect.top+v.y*rect.height,now);const transform='translate3d('+n._pos.x.toFixed(1)+'px,'+n._pos.y.toFixed(1)+'px,0) translate(-50%,-50%)';if(n.style.transform!==transform)n.style.transform=transform;
   const progress=held&&v===target?Math.min(1,(now-held)/650):0;n.style.setProperty('--hold',Math.round(progress*100)+'%');
  }
  for(const [k,n] of nodes)if(!seen.has(k)){n.disabled=true;if(now-n._seen>120)n.hidden=true;if(now-n._seen>500){n.remove();nodes.delete(k);}}
  if(held&&now-held>=650&&target&&points.some(v=>stable.key(v)===heldKey)){const v=target;reset();open(v).catch(e=>g.notice(e.message,true));}
 }
 requestAnimationFrame(frame);
}));})();
