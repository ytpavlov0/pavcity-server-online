/* PAVCITY 134: AFK zone counter (time today, money and PAV Points earned, next payment, immortal) from the
 * sync's afk134; /afk puts the zone on the GPS. */
(()=>{'use strict';
const money=v=>'$'+Number(v||0).toLocaleString('tr-TR');
function install(g){if(!g?.hud||g.ui134)return;g.ui134=true;let info=null,at=0;
 const box=document.createElement('aside');box.className='afk134';box.hidden=true;box.innerHTML='<header><i>☾</i><div><small>AFK BÖLGESİ</small><b></b></div><em>ÖLÜMSÜZ</em></header><div class="afk134-row"><span><small>Bugün</small><strong data-t></strong></span><span><small>Kazanç</small><strong data-m></strong></span><span><small>PP</small><strong data-p></strong></span></div><div class="afk134-bar"><i></i></div><p data-n></p>';g.hud.append(box);
 addEventListener('pav-game-data',e=>{const a=e.detail?.afk134;info=a&&a.active?a:null;at=performance.now();});
 const api=g.api;g.api=async(path,data)=>{const r=await api(path,data);if(path==='/api/chat/send'&&r?.afk134&&r.waypoint)g.setWaypoint?.(r.waypoint.x,r.waypoint.y);return r;};
 const t=setInterval(()=>{if(!g.hud.isConnected){clearInterval(t);return;}const show=!!info&&performance.now()-at<4000&&!g.menuOpen;if(box.hidden===show)box.hidden=!show;if(!show)return;
  const s=info.seconds||0,h=Math.floor(s/3600),m=Math.floor(s%3600/60);box.querySelector('b').textContent=info.zone||'AFK';box.querySelector('[data-t]').textContent=(h?h+' sa ':'')+m+' dk';box.querySelector('[data-m]').textContent=money(info.earned);box.querySelector('[data-p]').textContent=String(info.pp||0);
  box.querySelector('.afk134-bar i').style.width=Math.min(100,s/(info.cap||14400)*100).toFixed(1)+'%';
  box.querySelector('[data-n]').textContent=info.capped?'Günlük 4 saatlik sınıra ulaştın; yarın yeniden kazanırsın.':!info.on_foot?'Kazanç için araçtan in.':!info.alive?'Kazanç için hayatta olmalısın.':'Sonraki ödeme '+(info.next_pay??60)+' sn · dakikada $150, 10 dakikada 1 PP';},1000);}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
