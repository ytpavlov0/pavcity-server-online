/* Screen-projected targeting and compact RP information; paint capped at10Hz. */
(()=>{'use strict';
const hull=points=>{points.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);let lo=[],hi=[];for(const p of points){while(lo.length>1&&cross(lo.at(-2),lo.at(-1),p)<=0)lo.pop();lo.push(p);}for(const p of [...points].reverse()){while(hi.length>1&&cross(hi.at(-2),hi.at(-1),p)<=0)hi.pop();hi.push(p);}lo.pop();hi.pop();return lo.concat(hi);};
addEventListener('pav-game-created',({detail:game})=>queueMicrotask(()=>{
 const hud=game.hud;let targeting=false,selected=null,last=0,lastClock=-1,world=null;
 const header=document.createElement('div');header.className='pav-city-meta';header.innerHTML='<span class="pav-date"></span><span class="pav-clock"></span>';const topHud=hud.querySelector('.pn-top-hud');topHud.prepend(header);
 const dateNode=header.querySelector('.pav-date'),clockNode=header.querySelector('.pav-clock');
 const population=topHud.querySelector('.pn-player-count');header.prepend(population);
 const layout=()=>hud.style.setProperty('--pav-info-top',Math.ceil(topHud.offsetTop+topHud.offsetHeight+10)+'px');
 const topObserver=new ResizeObserver(layout);topObserver.observe(topHud);addEventListener('resize',layout,{passive:true});layout();
 const location=document.createElement('div');location.className='pav-map-location';location.innerHTML=PAVIcons.get('location')+'<span>LOS SANTOS</span>';hud.querySelector('.pn-radar-frame').append(location);
 const layer=document.createElement('div');layer.className='pav-car-target';layer.hidden=true;layer.innerHTML='<svg aria-hidden="true"><polygon/></svg><button class="pav-car-target-button" aria-label="Seçili araçla etkileşim"><span></span><small></small></button>';hud.append(layer);
 const button=layer.querySelector('button'),name=button.querySelector('span'),meta=button.querySelector('small'),polygon=layer.querySelector('polygon');
 const write=(n,t)=>{if(n.textContent!==t)n.textContent=t;};
 const heap=()=>game.bridge?{a:new Int32Array(game.bridge.memory.buffer,game.bridge.block,16384),f:new Float32Array(game.bridge.memory.buffer,game.bridge.block,16384)}:null;
 Object.defineProperty(game,'interactionActive',{get:()=>targeting});
 const disable=()=>{targeting=false;game.isTargeting=false;if(game.bridge)new Int32Array(game.bridge.memory.buffer,game.bridge.block,16384)[6380]=0;hud.classList.remove('pav-targeting');layer.hidden=true;const h=heap();if(h)h.a[6254]=0;};
 addEventListener('blur',disable);
 game.eyeMode=()=>{if(game.isDead)return;targeting=!targeting;game.isTargeting=targeting;if(game.bridge)new Int32Array(game.bridge.memory.buffer,game.bridge.block,16384)[6380]=targeting?1:0;hud.classList.toggle('pav-targeting',targeting);game.closeFeatures?.();game.closeActions?.();game.release();const h=heap();if(h){h.a[6254]=targeting?1:0;h.f[6252]=.5;h.f[6253]=.5;}if(!targeting)layer.hidden=true;hud.querySelector('.pav-target-eye').setAttribute('aria-pressed',String(targeting));};
 hud.querySelector('.pav-target-eye').onclick=game.eyeMode;
 const move=e=>{if(!targeting)return;const h=heap(),canvas=document.getElementById('canvas'),r=canvas?.getBoundingClientRect();if(h&&r){h.f[6252]=Math.max(0,Math.min(1,(e.clientX-r.left)/r.width));h.f[6253]=Math.max(0,Math.min(1,(e.clientY-r.top)/r.height));game.targetPointer={x:h.f[6252],y:h.f[6253]};}};
 addEventListener('pointermove',move,{passive:true});const cancelMouse=e=>{if(targeting&&e.target===document.getElementById('canvas')){e.preventDefault();e.stopImmediatePropagation();}};addEventListener('mousedown',cancelMouse,true);addEventListener('keydown',e=>{if(targeting&&e.code==='Escape'){e.preventDefault();e.stopImmediatePropagation();disable();}},true);
 button.onclick=e=>{e.preventDefault();e.stopPropagation();const v=selected;if(!v)return;disable();if(v.id){game.vehicleControls(v.id);const panel=hud.querySelector('.pav-vehicle-controls .pav-vehicle-buttons');if(panel){const enter=document.createElement('button');enter.textContent=v.locked?'Maymuncukla aç':'Bin / sürücüyü indir';enter.onclick=()=>{game.closeActions?.();game.enterNearby(v.id).catch(x=>game.quietVehicleError(x.message));};panel.prepend(enter);}}else game.enterNearby().catch(x=>game.quietVehicleError(x.message));};
 hud.querySelector('.pn-tags').addEventListener('click',e=>{if(!targeting)return;const tag=e.target.closest('.pn-tag'),id=Number(tag?.dataset.character),p=world?.players?.find(p=>p.char_id===id);if(id===game.character.id&&tag?.dataset.own==='true'){e.stopImmediatePropagation();disable();game.targets();return;}if(p&&id!==game.character.id&&tag.dataset.nearTarget==='true'){e.stopImmediatePropagation();disable();game.playerActions(p);}},true);
 addEventListener('pav-game-data',e=>{world=e.detail;if(world.health<=100)disable();});
 const render=now=>{if(!hud.isConnected){removeEventListener('blur',disable);removeEventListener('mousedown',cancelMouse,true);removeEventListener('pointermove',move);removeEventListener('resize',layout);topObserver.disconnect();game.closeInfo?.();return;}requestAnimationFrame(render);if(document.hidden||now-last<100)return;last=now;
  const minute=Math.floor(Date.now()/60000);if(minute!==lastClock){lastClock=minute;const date=new Date();write(dateNode,date.toLocaleDateString('tr-TR',{day:'2-digit',month:'short'}));write(clockNode,date.toLocaleTimeString('tr-TR',{hour:'2-digit',minute:'2-digit'}));}
  if(targeting&&(game.menuOpen||game.chatOpen||game.uiOpen||game.isDead))disable();const h=heap();if(!h)return;h.a[6254]=targeting&&!game.menuOpen&&!game.chatOpen&&!game.uiOpen?1:0;
  layer.hidden=!h.a[6254]||!h.a[6250];if(layer.hidden){selected=null;return;}
  const seq=Atomics.load(h.a,6255);if(seq&1)return;const selectedId=h.a[6251],selectedHandle=h.a[6250],points=[];for(let i=0;i<8;i++)if(h.f[6262+i*3])points.push([h.f[6260+i*3],h.f[6261+i*3]]);if(seq!==Atomics.load(h.a,6255)||points.length<3){layer.hidden=true;return;}
  const r=document.getElementById('canvas').getBoundingClientRect(),boundary=hull(points).map(p=>[r.left+p[0]*r.width,r.top+p[1]*r.height]);
  const path=boundary.map(p=>p.map(v=>Math.round(v)).join(',')).join(' ');if(polygon.getAttribute('points')!==path)polygon.setAttribute('points',path);
  const v=game.vehicles.find(v=>v.id===selectedId),traffic=game.trafficCandidate?.();selected=v||(traffic?.handle===selectedHandle?traffic:null);if(!selected){layer.hidden=true;return;}
  const xs=boundary.map(p=>p[0]),ys=boundary.map(p=>p[1]),x=Math.max(110,Math.min(innerWidth-110,(Math.min(...xs)+Math.max(...xs))/2)),y=Math.max(40,Math.min(innerHeight-65,Math.min(...ys)-18));button.style.transform=`translate(${Math.round(x)}px,${Math.round(y)}px) translate(-50%,-100%)`;
  write(name,'ARAÇ BİLGİLERİ · '+(v?'#'+v.id:'NPC'));write(meta,(v?.owner_label||'NPC')+' · '+(selected.locked?'KİLİTLİ · MAYMUNCUK':'AÇIK · ETKİLEŞİM'));
 };requestAnimationFrame(render);
}));})();
