/* PAVCITY UI 116:
 * - every failed action (not enough money, can't buy, engine running, sale refused, ...) also
 *   raises a typed error notification, not only the small red line inside a panel;
 * - /stats, /admins and other info results become a right-side glass card with a countdown bar
 *   (hover pauses it, it leaves when the time is up) instead of a modal;
 * - the fuel panel says why "Yakıt al" is locked (engine running) and offers to stop it;
 * - the always-on HUD canvas FX drop to the light mode once (players can turn them back on). */
(()=>{'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const QUIET=/^\/api\/(gta\/|lobby\/|admin114\/players|phone\/status|reports115\/context|combat53\/|anticheat108\/)/;
function install(g){
 if(!g?.hud||g.ui116)return;g.ui116=true;
 // 1 · failed actions become error notifications (deduplicated, polling endpoints stay quiet)
 const seen=new Map();const shout=(path,message)=>{if(QUIET.test(path)||!message)return;const now=Date.now();if(now-(seen.get(message)||0)<3000)return;seen.set(message,now);if(seen.size>40)seen.clear();(g.toast113?g.toast113(message,'error'):g.toast?.(message,true));};
 // phone status also tells the bridge whether a call is live (cell 13930: phone to the ear)
 const cell=(i,v)=>{if(g.bridge)new Int32Array(g.bridge.memory.buffer,g.bridge.block,16384)[i]=v;};
 const api=g.api;g.api=async(path,data)=>{try{const r=await api(path,data);if(path==='/api/phone/status'){const c=r?.call;cell(13930,c&&(c.state==='active'||c.state==='ringing'&&c.caller===g.character?.id)?1:0);}if(path==='/api/phone/hangup')cell(13930,0);return r;}catch(e){shout(String(path),String(e?.message||e));throw e;}};
 // 2 · info results as a timed side card
 const layer=document.createElement('aside');layer.className='i116-stack';g.hud.append(layer);
 const card=value=>{const rows=Array.isArray(value?.rows)?value.rows:[];const ms=Math.min(20000,6000+rows.length*700);
  const n=document.createElement('section');n.className='i116';n.setAttribute('role','status');n.style.setProperty('--life',ms+'ms');
  n.innerHTML='<header><small>PAVCITY · BİLGİ</small><button aria-label="Kapat">×</button></header><h3>'+esc(value?.title||'Bilgi')+'</h3><dl>'+rows.map(([k,v])=>'<div><dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd></div>').join('')+'</dl><i></i>';
  while(layer.children.length>=2)layer.firstElementChild.remove();layer.append(n);
  let left=ms,started=Date.now(),timer=0;const go=()=>{started=Date.now();n.classList.remove('paused');timer=setTimeout(leave,left);},leave=()=>{n.classList.add('leaving');setTimeout(()=>n.remove(),350);};
  n.onmouseenter=()=>{clearTimeout(timer);left-=Date.now()-started;n.classList.add('paused');};n.onmouseleave=go;n.querySelector('button').onclick=leave;go();};
 Object.defineProperty(g,'showInfo',{configurable:true,get:()=>card,set:()=>{}});
 // 3 · fuel: explain the locked purchase
 // Only the HUD's direct children are watched (cheap); a new RP panel is watched until it shows fuel.
 const fuel=panel=>{if(panel.dataset.f116||!panel.textContent.includes('Yakıtını seç'))return false;
  const buy=[...panel.querySelectorAll('button')].find(b=>/Yakıt al/.test(b.textContent)),stop=[...panel.querySelectorAll('button')].find(b=>/Motoru durdur/.test(b.textContent));
  if(!buy||!stop)return false;panel.dataset.f116='1';if(!buy.disabled)return true;const warn=document.createElement('p');warn.className='f116-warn';warn.textContent='Motor çalışıyor: yakıt almak için önce motoru durdur (M).';buy.before(warn);
  g.toast113?.('Motor çalışıyor. Yakıt almak için önce motoru durdur (M).','warning','Yakıt istasyonu');return true;};
 new MutationObserver(records=>{for(const r of records)for(const n of r.addedNodes)if(n.nodeType===1&&n.classList.contains('rp-overlay')){const watch=new MutationObserver(()=>{if(!n.isConnected||fuel(n))watch.disconnect();});watch.observe(n,{childList:true,subtree:true});setTimeout(()=>watch.disconnect(),15000);}}).observe(g.hud,{childList:true});
 // 5 · armor: shield icon (the 5th vital and the nametag bar are recolored blue in glass116)
 const shield=()=>{const n=g.hud.querySelector('.pn-stat[data-stat=armor]>span');if(n&&!n.dataset.s116&&window.PAVIcons105){n.dataset.s116='1';n.innerHTML=PAVIcons105.svg('armor');}};shield();setTimeout(shield,1500);
 // 6 · render resolution: unless the player picked a scale in ESC › Görüntü, cap the back buffer at
 // ~1.6 MP (fullscreen 1080p renders ~12% fewer pixels; the window stays sharp). PAVSetRenderScale
 // calls from the menu mark the choice as the player's own.
 const setScale=window.PAVSetRenderScale;
 if(setScale&&!window.PAVSetRenderScale.p116){let applied=0;const user=()=>{try{return localStorage.getItem('pav-scale-user116')==='1';}catch{return false;}};
  // a scale saved before 116 was the player's choice
  try{if(localStorage.getItem('pav-render-scale')!==null&&localStorage.getItem('pav-scale-auto116')===null)localStorage.setItem('pav-scale-user116','1');localStorage.setItem('pav-scale-auto116','1');}catch{}
  window.PAVSetRenderScale=Object.assign(v=>{try{localStorage.setItem('pav-scale-user116','1');}catch{}return setScale(v);},{p116:true});
  const auto=()=>{if(user())return;const px=innerWidth*devicePixelRatio*innerHeight*devicePixelRatio,s=Math.max(.6,Math.min(1,Math.round(Math.sqrt(1.6e6/px)*20)/20));if(Math.abs(s-applied)<.01)return;applied=s;setScale(s);};
  let t=0;addEventListener('resize',()=>{clearTimeout(t);t=setTimeout(auto,400);});document.addEventListener('fullscreenchange',()=>setTimeout(auto,450));auto();}
 // 4 · lighter HUD FX by default (one-time migration; the ESC settings can switch it back)
 try{if(!localStorage.getItem('pav-fx116')){localStorage.setItem('pav-fx116','1');if((localStorage.getItem('pav-fx-mode')||'ember')==='ember')g.setVisualMode?.('low');}}catch{}
}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
