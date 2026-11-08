/* PAVCITY 135: clubs. Near Vanilla Unicorn, Bahama Mamas or Tequi-la-la a chip lists who is there; meeting
 * someone adds their number to the phone (texts get Turkish replies from the server). */
(()=>{'use strict';
const CLUBS=[[128.0,-1298.0,29.2],[-1388.0,-586.0,30.2],[-565.0,276.0,83.0]];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function install(g){if(!g?.hud||g.ui135)return;g.ui135=true;let data=null,busy=false;
 const toast=(m,k='info')=>g.toast113?g.toast113(m,k,'Kulüp'):g.toast?.(m,k==='error');
 const chip=document.createElement('button');chip.className='club135';chip.hidden=true;chip.innerHTML='<i>♪</i><span></span><kbd>Tıkla</kbd>';g.hud.append(chip);
 const panel=()=>{if(!data?.club)return;const p=g.openRP(data.club.name,'<div class="club135-list">'+data.people.map(x=>'<article><i>'+esc(x.name.slice(0,1))+'</i><div><b>'+esc(x.name)+'</b><small>'+(x.met?'Tanışıyorsunuz · yakınlık %'+x.closeness+' · '+x.number:'Henüz tanışmadınız')+'</small>'+(x.met?'<span class="club135-bar"><em style="width:'+x.closeness+'%"></em></span>':'')+'</div>'+(x.met?'<button data-msg="'+x.number+'">Mesaj at</button>':'<button data-meet="'+x.id+'">Tanış</button>')+'</article>').join('')+'</div><p class="club135-hint">Tanıştığın kişilere telefondan (Mesajlar) yazabilirsin; konuştukça yakınlığınız artar.</p>','pav-club135');
  p.querySelectorAll('[data-meet]').forEach(b=>b.onclick=async()=>{try{const r=await g.api('/api/npc135/meet',{id:b.dataset.meet});toast(r.notice,'success');g.closeRP?.();data=null;}catch(e){toast(e.message,'error');}});
  p.querySelectorAll('[data-msg]').forEach(b=>b.onclick=()=>{g.closeRP?.();toast('Telefon › Mesajlar › '+b.dataset.msg+' ile yazışabilirsin.');});};
 chip.onclick=panel;
 const t=setInterval(async()=>{if(!g.hud.isConnected){clearInterval(t);return;}const b=g.bridge;if(!b)return;const f=new Float32Array(b.memory.buffer,b.block,16384);
  const near=!g.vehicle&&CLUBS.some(c=>Math.hypot(c[0]-f[16],c[1]-f[17])<9&&Math.abs(c[2]-f[18])<6);
  if(near&&!busy&&(!data||Date.now()-data.at>4000)){busy=true;try{const r=await g.api('/api/npc135/near');data=r.club?{...r,at:Date.now()}:null;}catch{data=null;}finally{busy=false;}}
  if(!near)data=null;const show=!!data?.club&&!g.menuOpen&&!g.uiOpen;if(chip.hidden===show)chip.hidden=!show;if(show)chip.querySelector('span').textContent=data.club.name+' · '+data.people.length+' kişi';},700);}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
