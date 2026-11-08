/* PAVCITY 130: character history (ESC › Karakter) and vehicle rentals.
 * History: /api/character130/profile — playtime, money, faction, properties, vehicles, jobs, jail,
 * deaths/kills and recent account activity in one panel.
 * Rentals: near a rental point (from /api/rental130/list) a chip offers "Araç kirala"; the panel rents a
 * scooter, bike or small car for 30/60 min; while it runs a countdown chip with "Teslim et" stays on the
 * HUD. /kirala puts the nearest point on the GPS. */
(()=>{'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=v=>'$'+Number(v||0).toLocaleString('tr-TR');
const dur=s=>{s=Math.max(0,Math.floor(s||0));const h=Math.floor(s/3600),m=Math.floor(s%3600/60);return h?h+' sa '+m+' dk':m+' dk';};
const when=t=>t?new Date(t*1000).toLocaleString('tr-TR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'—';
const ACT={'shop-buy':'Market alışverişi','weapon-buy':'Silah satın alma','supply-buy':'Mühimmat alımı','property-buy':'Mülk satın alma','tuning-buy':'Modifiye','buy':'Araç satın alma','bank-deposit':'Bankaya yatırma','bank-withdraw':'Bankadan çekme','give-money':'Para gönderme','rental130':'Araç kiralama','rental-return130':'Kiralık araç iadesi','lockpick':'Maymuncuk','hotwire129':'Düz kontak','native-cash128':'Oyun içi nakit','job-reward':'Meslek ödemesi','faction-deposit':'Birlik kasası','item-transfer':'Eşya aktarımı','weapon-right122':'Silah hakkı','password121':'Şifre değişikliği','traffic-register':'Sokak aracı'};
const JOB={trucker:'Tır şoförü',taxi:'Taksi',garbage:'Çöpçü',delivery:'Kurye',bus:'Otobüs',mechanic:'Tamirci',fisher:'Balıkçı',miner:'Madenci'};
function install(g){
 if(!g?.hud||g.ui130)return;g.ui130=true;
 const toast=(m,k='info',t='PAVCITY')=>g.toast113?g.toast113(m,k,t):g.toast?.(m,k==='error');
 /* ---------- character history ---------- */
 const history=async()=>{let r;try{r=await g.api('/api/character130/profile');}catch(e){toast(e.message,'error');return;}
  const tiles=[['Oynama süresi',dur(r.playtime)],['Nakit',money(r.cash)],['Banka',money(r.bank)],['Ölüm / Leş',r.deaths+' / '+r.kills],['Tamamlanan iş',r.jobs_done+' · '+money(r.jobs_paid)],['Durum','Can '+Math.max(0,r.health-100)+' · Zırh '+r.armor]];
  const list=(title,rows,empty)=>'<section class="c130-sec"><h4>'+title+'</h4>'+(rows.length?'<ul>'+rows.join('')+'</ul>':'<p class="c130-empty">'+empty+'</p>')+'</section>';
  const body='<div class="c130"><header class="c130-head"><div class="c130-av">'+esc(r.name.slice(0,1))+'</div><div><h3>'+esc(r.name)+'</h3><small>Karakter #'+r.char_id+' · kayıt '+when(r.created)+'</small></div>'+(r.jail?'<b class="c130-jail">HAPİSTE · '+when(r.jail.until)+'</b>':'')+'</header>'+
   '<div class="c130-tiles">'+tiles.map(([k,v])=>'<article><small>'+k+'</small><strong>'+esc(v)+'</strong></article>').join('')+'</div>'+
   '<div class="c130-grid">'+
   list('Birlik',r.faction?['<li><b>'+esc(r.faction.name)+'</b><span>'+esc(r.faction.rank)+' · '+esc(r.faction.kind)+'</span></li>']:[],'Bir birliğe üye değilsin.')+
   list('Mülkler',r.properties.map(p=>'<li><b>'+esc(p.name)+'</b><span>'+esc(p.kind)+' · '+money(p.price)+'</span></li>'),'Mülkün yok.')+
   list('Araçlar ('+r.vehicles.length+')',r.vehicles.slice(0,8).map(v=>'<li><b>'+esc(v.model.toUpperCase())+'</b><span>'+esc(v.plate)+' · #'+v.id+'</span></li>'),'Kayıtlı aracın yok.')+
   list('Son meslekler',r.jobs.slice(0,8).map(j=>'<li><b>'+esc(JOB[j.job]||j.job)+'</b><span>'+(j.completed?'Tamamlandı · '+money(j.paid):'Yarım kaldı')+' · '+when(j.started)+'</span></li>'),'Henüz meslek kaydın yok.')+
   list('Ölüm ve çatışma',r.life.slice(0,10).map(e=>'<li class="'+e.kind+'"><b>'+(e.kind==='kill'?'Etkisiz bıraktın':'Öldün')+'</b><span>'+(e.other_name?(e.kind==='kill'?esc(e.other_name):'· '+esc(e.other_name)+' tarafından'):'çevre / kaza')+' · '+when(e.created)+'</span></li>'),'Kayıt yok.')+
   list('Son hesap hareketleri',r.activity.slice(0,10).map(a=>'<li><b>'+esc(ACT[a.action]||a.action)+'</b><span>'+when(a.created)+'</span></li>'),'Hareket yok.')+
   '</div></div>';
  g.openRP('Karakter geçmişi',body,'pav-c130');};
 g.characterHistory130=history;
 setInterval(()=>{const box=g.hud.querySelector('.pav-menu-identity-details');if(!box||box.querySelector('.c130-open'))return;const b=document.createElement('button');b.type='button';b.className='c130-open';b.textContent='Karakter geçmişi · ölüm, meslek, birlik, mülk';b.onclick=()=>history();box.prepend(b);},1000);
 /* ---------- rentals ---------- */
 let points=[],models=[],active=null,skew=0,near=null;
 const chip=document.createElement('button');chip.className='r130-chip';chip.hidden=true;chip.innerHTML='<i>🛵</i><span>Araç kirala</span><kbd>Tıkla</kbd>';g.hud.append(chip);
 const timer=document.createElement('aside');timer.className='r130-timer';timer.hidden=true;timer.innerHTML='<small>KİRALIK</small><b></b><span></span><button>Teslim et</button>';g.hud.append(timer);
 const load=async()=>{try{const r=await g.api('/api/rental130/list');points=r.points;models=r.models;active=r.active;skew=r.now-Date.now()/1000;}catch{}};setTimeout(load,2500);
 const panel=()=>{if(!near)return;const p=g.openRP(near.name,'<div class="r130"><p>Süreyi seç; araç yanında hazırlanır, anahtarı sana verilir. Süre bitince araç inince geri alınır.</p><div class="r130-list">'+models.map(m=>'<article><div><b>'+esc(m.name)+'</b><small>30 dk '+money(m.price30)+' · 60 dk '+money(m.price30*2)+'</small></div><button data-m="'+m.model+'" data-t="30">30 dk</button><button data-m="'+m.model+'" data-t="60">60 dk</button></article>').join('')+'</div></div>','pav-r130');
  p.querySelectorAll('[data-m]').forEach(b=>b.onclick=async()=>{try{const r=await g.api('/api/rental130/rent',{model:b.dataset.m,minutes:Number(b.dataset.t)});g.addVehicle?.(r.vehicle);active={vehicle_id:r.vehicle.id,model:b.dataset.m,until:r.until};skew=r.now-Date.now()/1000;g.closeRP?.();toast(r.notice,'success','Kiralama');}catch(e){toast(e.message,'error','Kiralama');}});};
 chip.onclick=panel;
 timer.querySelector('button').onclick=async()=>{try{const r=await g.api('/api/rental130/return');active=null;toast(r.notice,'success','Kiralama');}catch(e){toast(e.message,'error','Kiralama');}};
 setInterval(async()=>{if(!g.hud.isConnected)return;const b=g.bridge;if(!b)return;const f=new Float32Array(b.memory.buffer,b.block,16384);
  near=!g.vehicle&&points.find(q=>Math.hypot(q.x-f[16],q.y-f[17])<8&&Math.abs(q.z-f[18])<6)||null;const show=!!near&&!active&&!g.menuOpen&&!g.uiOpen;if(chip.hidden===show)chip.hidden=!show;
  if(active){const left=active.until-(Date.now()/1000+skew);timer.hidden=false;timer.querySelector('b').textContent=(models.find(m=>m.model===active.model)?.name||active.model);timer.querySelector('span').textContent=left>0?Math.floor(left/60)+':'+String(Math.floor(left%60)).padStart(2,'0'):'Süre doldu · araçtan inince alınır';timer.classList.toggle('late',left<300);}else if(!timer.hidden)timer.hidden=true;},500);
 setInterval(async()=>{if(!active)return;try{const r=await g.api('/api/rental130/status');active=r.active;skew=r.now-Date.now()/1000;}catch{}},30000);
 const api=g.api;g.api=async(path,data)=>{const r=await api(path,data);if(path==='/api/chat/send'&&r?.rental130&&r.waypoint){g.setWaypoint?.(r.waypoint.x,r.waypoint.y);if(!points.length)load();}return r;};
}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
