/* PAVCITY 133: running city event chip ("2x MESLEK KAZANCI · 45:12") from the sync's event133. */
(()=>{'use strict';
function install(g){if(!g?.hud||g.ui133)return;g.ui133=true;let ev=null,skew=0;
 const chip=document.createElement('aside');chip.className='ev133';chip.hidden=true;chip.innerHTML='<i>★</i><b></b><span></span>';g.hud.append(chip);
 const set=e=>{ev=e||null;if(ev)skew=(ev.now||Date.now()/1000)-Date.now()/1000;};
 addEventListener('pav-game-data',e=>set(e.detail?.event133));
 const api=g.api;g.api=async(path,data)=>{const r=await api(path,data);if(path==='/api/chat/send'&&r&&'event133'in r)set(r.event133);return r;};
 const t=setInterval(()=>{if(!g.hud.isConnected){clearInterval(t);return;}const left=ev?ev.ends-(Date.now()/1000+skew):0,show=left>0;if(chip.hidden===show)chip.hidden=!show;if(!show)return;
  chip.querySelector('b').textContent=(+ev.mult).toLocaleString('tr-TR')+'x MESLEK KAZANCI';chip.querySelector('span').textContent=Math.floor(left/60)+':'+String(Math.floor(left%60)).padStart(2,'0')+(ev.note?' · '+ev.note:'');},1000);}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
