/* PAVCITY UI 117:
 * - microphone lock for new players: the server counts play time (voice117 in every sync); a
 *   bottom pill shows the countdown, Z while locked explains it once, unlock is announced;
 * - TAB list opens in the middle as small blurred glass with an animated top/bottom vignette that
 *   slides back out when it closes. */
(()=>{'use strict';
const icon=n=>window.PAVIcons105?.svg(n)||'';
function install(g){
 if(!g?.hud||g.ui117)return;g.ui117=true;
 // 1 · microphone lock
 const pill=document.createElement('aside');pill.className='m117';pill.hidden=true;pill.innerHTML='<span class="m117-i">'+icon('mic')+'</span><div><b></b><small>Yeni oyuncular ilk 15 dakika yazılı RP yapar (T). Süre sunucuda sayılır.</small></div><i><em></em></i>';g.hud.append(pill);
 let state=null,warned=0,wasLocked=false;
 const fmt=s=>Math.floor(s/60)+':'+String(s%60).padStart(2,'0');
 addEventListener('pav-game-data',({detail})=>{const v=detail?.voice117;if(!v)return;state=v;pill.hidden=!v.locked;
  if(v.locked){pill.querySelector('b').textContent='Mikrofon '+fmt(v.remaining)+' sonra açılacak';pill.querySelector('em').style.width=Math.max(0,Math.min(100,100-v.remaining/v.required*100))+'%';}
  else if(wasLocked)g.toast113?.('Mikrofon açıldı. Z basılı tutarak konuşabilirsin.','success','Sesli sohbet');
  wasLocked=!!v.locked;});
 const voice=g.voice;if(voice&&typeof voice.push==='function'&&!voice.push.p117){const push=voice.push.bind(voice);voice.push=Object.assign(down=>{if(down&&state?.locked){if(Date.now()-warned>20000){warned=Date.now();g.toast113?.('Mikrofon '+fmt(state.remaining)+' sonra açılacak. Şimdilik T ile yazarak RP yap.','warning','Sesli sohbet');}return push(false);}return push(down);},{p117:true});}
 // 2 · TAB vignette (top and bottom bars slide in with the list and back out after it)
 let vignette=null,hideTimer=0;
 const show=()=>{clearTimeout(hideTimer);if(!vignette){vignette=document.createElement('div');vignette.className='v117';g.hud.append(vignette);}requestAnimationFrame(()=>vignette?.classList.add('in'));};
 const hide=()=>{if(!vignette)return;const v=vignette;v.classList.remove('in');hideTimer=setTimeout(()=>{v.remove();if(vignette===v)vignette=null;},420);};
 new MutationObserver(records=>{for(const r of records){for(const n of r.addedNodes)if(n.nodeType===1&&n.classList.contains('p85-scoreboard'))show();for(const n of r.removedNodes)if(n.nodeType===1&&n.classList.contains('p85-scoreboard'))hide();}}).observe(g.hud,{childList:true});
}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
