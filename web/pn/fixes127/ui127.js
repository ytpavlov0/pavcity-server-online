/* PAVCITY 127: floating icons over entry markers. bridge127 projects every drawn entry (cells
 * 13960 + slot*5: visible, x, y, distance, kind; 13959 frame stamp); this layer places a glass icon
 * above each ground ring and, up close, a label with the place name and the key to use. */
(()=>{'use strict';
const ICON={
 house:'<path d="M4 11.5 12 5l8 6.5V19a1 1 0 0 1-1 1h-4.5v-5h-5v5H5a1 1 0 0 1-1-1Z" fill="currentColor"/>',
 door:'<path d="M6 3.5h9.5a1 1 0 0 1 1 1V20H6Z" fill="currentColor"/><circle cx="13.6" cy="12.2" r="1.1" fill="#1a1024"/><path d="M4 20.5h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
 exit:'<path d="M13 4H6v16h7" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/><path d="M11 12h9m-3-3.5L20.5 12 17 15.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
 job:'<rect x="3.5" y="7.5" width="17" height="12" rx="2.5" fill="currentColor"/><path d="M9 7.5V5.8A1.8 1.8 0 0 1 10.8 4h2.4A1.8 1.8 0 0 1 15 5.8v1.7" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 12.5h17" stroke="#1a1024" stroke-width="1.4"/>',
 garage:'<path d="M3 10 12 4.5 21 10v10h-3v-7H6v7H3Z" fill="currentColor"/><path d="M7.5 15h9M7.5 18h9" stroke="currentColor" stroke-width="1.6"/>',
 lift:'<rect x="5" y="3.5" width="14" height="17" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="m9 9.5 3-3 3 3M9 14.5l3 3 3-3" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>',
 police:'<path d="M12 3 19 5.6v5.8c0 4.3-2.9 7.7-7 9.6-4.1-1.9-7-5.3-7-9.6V5.6Z" fill="currentColor"/><path d="m12 8 1.2 2.5 2.7.4-2 1.9.5 2.7L12 14.2l-2.4 1.3.5-2.7-2-1.9 2.7-.4Z" fill="#1a1024"/>',
 medical:'<path d="M10 4h4v6h6v4h-6v6h-4v-6H4v-4h6Z" fill="currentColor"/>',
 cafe:'<path d="M5 9h11v5a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5Z" fill="currentColor"/><path d="M16 10.5h1.5a2.5 2.5 0 0 1 0 5H16" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8 4.5c0 1.2 1 1.2 1 2.4M11.5 4.5c0 1.2 1 1.2 1 2.4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>',
 boat:'<path d="M3 15h18l-2.5 4.5h-13Z" fill="currentColor"/><path d="M12 4v10M12 5l6 8h-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>'
};
const KIND={1:['job','Meslek / Garaj'],2:['house','Mülk'],3:['lift','Asansör'],4:['police','Hizmet masası'],5:['door','Giriş'],6:['house','Giriş'],7:['exit','Çıkış']};
const SERVICE={police:['police','LSPD'],medical:['medical','Hastane'],uwu:['cafe','UwU Café'],marina:['boat','Marina']};
const svg=n=>'<svg viewBox="0 0 24 24" aria-hidden="true">'+(ICON[n]||ICON.door)+'</svg>';
function install(g){
 if(!g?.hud||g.entry127)return;g.entry127=true;
 const layer=document.createElement('div');layer.className='e127-layer';layer.setAttribute('aria-hidden','true');g.hud.append(layer);
 const nodes=[];for(let n=0;n<6;n++){const d=document.createElement('div');d.className='e127';d.innerHTML='<i class="e127-ic"></i><span class="e127-tag"><b></b><small></small></span>';d.hidden=true;layer.append(d);nodes.push({el:d,ic:d.firstChild,b:d.querySelector('b'),small:d.querySelector('small'),key:'',x:-1,y:-1,o:-1});}
 let world=null,lastStamp=-1,stampAt=0,last=0;addEventListener('pav-game-data',e=>{world=e.detail;});
 const near=(list,x,y,z,r=2.2)=>(list||[]).find(p=>Number.isFinite(p.x)&&Math.hypot(p.x-x,p.y-y,(p.z??z)-z)<r);
 const describe=(kind,slot,f,a)=>{let icon=KIND[kind]?.[0]||'door',title=KIND[kind]?.[1]||'Giriş',sub='';
  if(slot===0&&(kind===6||kind===7)){const p=(world?.properties||[]).find(p=>p.id===a[12840]);if(p){title=kind===7?'Çıkış':(p.name||p.label||'Mülk');sub=kind===7?'E · Dışarı çık':(p.owner_name?p.owner_name:p.price?'$'+Number(p.price).toLocaleString('tr-TR'):'')+' · E · Gir';if(kind===6)icon=p.kind==='garage'?'garage':'house';}else sub=kind===7?'E · Dışarı çık':'E · Gir';return[icon,title,sub];}
  const o=7204+(slot-1)*8,x=f[o+1],y=f[o+2],z=f[o+3];
  if(kind===2){const p=near(world?.properties,x,y,z);if(p){title=p.name||p.label||'Mülk';sub=(p.owner_name?p.owner_name+' · ':p.price?'$'+Number(p.price).toLocaleString('tr-TR')+' · ':'')+'E';icon=p.kind==='garage'?'garage':'house';}}
  else if(kind===4){const s=near(world?.services,x,y,z,3);const m=s&&SERVICE[s.kind];if(m){icon=m[0];title=s.name||m[1];}sub='E · Etkileşim';}
  else if(kind===3){const v=near(world?.elevators,x,y,z);if(v?.name)title=v.name;sub='E · Kat seç';}
  else if(kind===1){const job=g.activeJob;if(job){icon='job';title=job.name||job.title||'Meslek noktası';sub='Görev hedefi';}else{icon='garage';title='Garaj';sub='E · Araçlarım';}}
  else sub='E · Gir';
  return[icon,title,sub];};
 const frame=now=>{if(!layer.isConnected)return;requestAnimationFrame(frame);if(now-last<33)return;last=now;
  const b=g.bridge;if(!b||g.menuOpen||g.isDead||document.hidden){if(!layer.hidden)layer.hidden=true;return;}
  const a=new Int32Array(b.memory.buffer,b.block,16384),f=new Float32Array(b.memory.buffer,b.block,16384),stamp=a[13959];if(stamp!==lastStamp){lastStamp=stamp;stampAt=now;}
  const stale=now-stampAt>400;if(layer.hidden!==stale)layer.hidden=stale;if(stale)return;
  const c=document.getElementById('canvas'),r=c?.getBoundingClientRect();if(!r?.width)return;
  for(let n=0;n<6;n++){const node=nodes[n],o=13960+n*5,vis=a[o]===1,d=f[o+3],sx=f[o+1],sy=f[o+2],kind=a[o+4];
   const show=vis&&Number.isFinite(sx)&&Number.isFinite(sy)&&sx>-.05&&sx<1.05&&sy>-.05&&sy<1.08&&d<45;if(node.el.hidden===show)node.el.hidden=!show;if(!show)continue;
   const key=kind+':'+n+':'+(n===0?a[12840]:Math.round(f[7205+(n-1)*8]*2)+','+Math.round(f[7206+(n-1)*8]*2));
   if(node.key!==key){node.key=key;const [icon,title,sub]=describe(kind,n,f,a);node.ic.innerHTML=svg(icon);node.b.textContent=title;node.small.textContent=sub;node.small.hidden=!sub;node.el.dataset.kind=kind;}
   const x=Math.round(r.left+sx*r.width),y=Math.round(r.top+sy*r.height),scale=Math.max(.62,Math.min(1.08,1.2-d/40)),op=Math.max(0,Math.min(1,(45-d)/12)),close=d<7;
   if(node.x!==x||node.y!==y||node.s!==scale){node.x=x;node.y=y;node.s=scale;node.el.style.transform='translate3d('+x+'px,'+y+'px,0) translate(-50%,-100%) scale('+scale.toFixed(3)+')';}
   const oq=Math.round(op*20)/20;if(node.o!==oq){node.o=oq;node.el.style.opacity=String(oq);}
   if(node.el.classList.contains('close')!==close)node.el.classList.toggle('close',close);}
 };requestAnimationFrame(frame);
 addEventListener('pav-game-stop',()=>layer.remove(),{once:true});
}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
