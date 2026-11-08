/* 210 (from 208): "Yapım süreci" video everywhere a player looks first. The link opens YouTube in a new tab (noopener); nothing is
 * loaded from YouTube before a click.
 * - Login / register / character screens: a glass pill in the header bar next to "Güncellemeler" / "Yardım".
 * - ESC menu: a new first tab "HAKKIMIZDA" (about PAVCITY + the video + Güncellemeler); ESC opens on it. The map (F11)
 *   and settings shortcuts still open their own tab.
 * - F1 (Şehir merkezi): the same video card at the top of the panel. */
(()=>{'use strict';
const URL208='https://youtube.com/@YOUR-CHANNEL';
const open=()=>{try{window.open(URL208,'_blank','noopener,noreferrer');}catch{}};
const CSS='.v208-glass{display:flex;align-items:center;gap:12px;padding:10px 16px 10px 10px;border-radius:16px;border:1px solid rgba(255,255,255,.22);background:linear-gradient(150deg,rgba(255,255,255,.16),rgba(255,255,255,.05));backdrop-filter:blur(14px) saturate(1.3);-webkit-backdrop-filter:blur(14px) saturate(1.3);color:#fff;font:600 13px/1.3 PAVSource,"Segoe UI",system-ui,sans-serif;text-align:left;cursor:pointer;box-shadow:0 10px 30px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.25);transition:transform .15s ease,border-color .15s ease}'+
'.v208-glass:hover{transform:translateY(-1px);border-color:rgba(255,179,107,.8)}.v208-glass:focus-visible{outline:2px solid #ffb36b;outline-offset:3px}'+
'.v208-glass .v208-play{flex:none;display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:linear-gradient(140deg,#ffb36b,#ff5fa8);box-shadow:0 4px 14px rgba(255,95,168,.45)}'+
'.v208-glass .v208-play::before{content:"";margin-left:3px;border-style:solid;border-width:7px 0 7px 12px;border-color:transparent transparent transparent #1a1024}'+
'.v208-glass small{display:block;color:#ffb3d6;font-size:10px;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.v208-glass b{display:block;font-size:14px;font-weight:800}.v208-glass em{display:block;font-style:normal;font-size:11.5px;color:rgba(255,255,255,.7)}'+
'#yt-auth-modal .pav-entry-header .v210-open{display:inline-flex;align-items:center;gap:8px;margin-left:12px;padding:8px 14px 8px 8px;border-radius:999px;border:1px solid rgba(255,255,255,.28);background:linear-gradient(150deg,rgba(255,255,255,.18),rgba(255,255,255,.06));backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);color:#fff;font:800 12.5px/1 PAVSource,"Segoe UI",sans-serif;letter-spacing:.04em;cursor:pointer;pointer-events:auto;box-shadow:0 6px 18px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.25)}'+
'#yt-auth-modal .pav-entry-header .v210-open i{display:grid;place-items:center;width:22px;height:22px;border-radius:50%;font-style:normal;font-size:10px;background:linear-gradient(140deg,#ffb36b,#ff5fa8);color:#1a1024}#yt-auth-modal .pav-entry-header .v210-open:hover{border-color:rgba(255,179,107,.9)}'+
'.pav-about208{display:grid;gap:14px;padding:4px 2px}.pav-about208 h3{margin:0;font-size:22px}.pav-about208 p{margin:0;line-height:1.55;color:rgba(246,241,255,.85)}.pav-about208 .v208-row{display:flex;flex-wrap:wrap;gap:10px}.pav-about208 .v208-glass{background:linear-gradient(150deg,rgba(255,179,107,.18),rgba(255,95,168,.08))}';
const style=()=>{if(!document.getElementById('v208-style')){const s=document.createElement('style');s.id='v208-style';s.textContent=CSS;document.head.append(s);}};
const card=(id)=>{const b=document.createElement('button');b.type='button';b.className='v208-glass';if(id)b.id=id;b.title='YouTube’da yeni sekmede açılır';
 b.innerHTML='<span class="v208-play" aria-hidden="true"></span><span><small>PAVCITY · Video</small><b>Yapım süreci videosu</b><em>Tıkla, YouTube’da izle</em></span>';b.onclick=open;return b;};
// ---- login / register / character screens
// 210: on the auth screens the button sits in the header bar next to "Güncellemeler" / "Yardım" (the 208 card at the
// top right went behind the character preview).
function syncAuth(){const header=document.querySelector('#yt-auth-modal .pav-entry-header');if(!header||header.querySelector('.v210-open'))return;style();
 const b=document.createElement('button');b.type='button';b.className='v210-open';b.title='Yapım süreci videosu · YouTube’da yeni sekmede açılır';b.innerHTML='<i>▶</i><span>Yapım süreci</span>';b.onclick=open;
 const news=header.querySelector('.n189-open')||header.querySelector('.h141-open');news?header.insertBefore(b,news):header.append(b);}
let queued=false;new MutationObserver(()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;syncAuth();});}).observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden','style','class']});
// ---- in the city: ESC "HAKKIMIZDA" tab (first, opened with ESC) and the F1 panel
function installMenu(g){
 const shell=g.hud?.querySelector('.pn-menu section'),nav=shell?.querySelector('.pav-menu-tabs');if(!shell||!nav||nav.querySelector('[data-tab=about]'))return!!nav?.querySelector('[data-tab=about]');
 style();const btn=document.createElement('button');btn.type='button';btn.textContent='HAKKIMIZDA';btn.dataset.tab='about';
 const view=document.createElement('div');view.className='pav-menu-view pav-about208';view.dataset.view='about';view.hidden=true;
 view.innerHTML='<h3>PAVCITY · Los Santos Roleplay</h3><p>Tarayıcıdan oynanan, Türkçe bir GTA V rol yapma şehri. Meslekler, mülkler, birlikler, sesli sohbet ve ortak şehir; hepsi yayınlarda birlikte geliştirildi.</p><div class="v208-row"></div><p style="font-size:12.5px;opacity:.7">ESC menüsünün diğer bölümleri yukarıdaki sekmelerde.</p>';
 const row=view.querySelector('.v208-row');row.append(card());
 const news=document.createElement('button');news.type='button';news.className='v208-glass';news.innerHTML='<span class="v208-play" aria-hidden="true" style="background:linear-gradient(140deg,#8ad7ff,#9d7bff)"></span><span><small>PAVCITY</small><b>Güncellemeler</b><em>Şehirde neler değişti?</em></span>';news.onclick=()=>window.PAVNews189?.();row.append(news);
 nav.prepend(btn);const first=shell.querySelector('.pav-menu-view');first?first.before(view):nav.after(view);
 const show=()=>{shell.querySelectorAll('.pav-menu-view').forEach(v=>v.hidden=v!==view);nav.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===btn)));};
 btn.onclick=show;
 // another tab: the menu's own select() shows its view; ours just steps aside
 nav.addEventListener('click',e=>{const b=e.target.closest('button');if(b&&b!==btn){view.hidden=true;btn.setAttribute('aria-pressed','false');}},true);
 // ESC opens on HAKKIMIZDA unless a shortcut (map, settings) asked for another tab in the same call
 let pending=false;const setMenu=g.setMenu;
 if(typeof setMenu==='function'&&!setMenu.about208){g.setMenu=Object.assign(function(on,...rest){const r=setMenu.call(this,on,...rest);if(on){pending=true;queueMicrotask(()=>{if(pending)show();pending=false;});}return r;},{about208:true});
  for(const k of['openMap','openSettings'])if(typeof g[k]==='function'){const f=g[k];g[k]=function(...x){const r=f.apply(this,x);pending=false;view.hidden=true;btn.setAttribute('aria-pressed','false');return r;};}}
 return true;}
function installF1(g){const d=g.dashboard;if(typeof d!=='function'||d.about208)return;
 g.dashboard=Object.assign(async function(...x){const r=await d.apply(this,x);try{const root=g.hud.querySelector('.p70-dashboard')||g.hud.querySelector('.pav-dashboard');const host=root?.querySelector('.rp-content')||root;
  if(host&&!host.querySelector('.v208-glass')){style();const c=card();c.style.margin='0 0 14px';const hero=host.querySelector('.p70-hero');hero?hero.after(c):host.prepend(c);}}catch{}return r;},{about208:true});
 g.accountPanel=g.dashboard;}
addEventListener('pav-game-created',({detail:g})=>{let n=0;const t=setInterval(()=>{n++;const ok=installMenu(g);installF1(g);if((ok&&g.dashboard?.about208)||n>20)clearInterval(t);},500);});
syncAuth();
window.PAVAbout210=window.PAVAbout208={url:URL208,open,syncAuth};
})();
