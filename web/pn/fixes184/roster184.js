/* 159: TAB player list, second pass after the owner's test (31 Oct):
 * - TAB / Esc closes it again: the key handler is registered when this file loads (it is placed early in the page,
 *   right after guard156), before the handler that swallowed TAB while a menu is open (158 registered too late);
 * - wider sheet (up to 780 px) and one line per player: ID, name, role, ping (glass116 forced 3 grid columns, so
 *   158's ping wrapped onto a second line);
 * - your own ping as a chip on the status line;
 * - clicking a player closes the list and opens the chat box with "/pm <ID> " ready to type (client159). */
(()=>{
 'use strict';
 const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const cls=ms=>ms==null?'na':ms<90?'good':ms<200?'ok':'bad';
 const label=ms=>ms==null?'—':Math.round(ms)+' ms';
 const S='html body #pn-game.pav106.pav106 .p85-scoreboard.p85-scoreboard.r159';
 const css=document.createElement('style');css.id='pav-roster159';
 css.textContent=[
  S+'{pointer-events:auto!important;display:flex!important;flex-direction:column!important;overflow:hidden!important;width:min(780px,94vw)!important;max-height:min(80vh,760px)!important}',
  S+' .r159-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:2px 22px 10px;min-height:28px}',
  S+' .r159-bar [role=status]{margin:0!important;padding:0!important}',
  S+' .r159-me{display:inline-flex;align-items:center;gap:8px;padding:5px 12px;border-radius:999px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.1);font-size:12px;font-weight:700;color:#e9def7;white-space:nowrap}',
  S+' .r159-me b{font-variant-numeric:tabular-nums}',
  S+' .p85-roster.r159-list{display:flex!important;flex-direction:column!important;gap:6px!important;flex:1 1 auto!important;min-height:0!important;max-height:none!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain;scrollbar-width:none!important;padding:0 18px 14px!important}',
  S+' .p85-roster.r159-list::-webkit-scrollbar{display:none!important;width:0!important;height:0!important}',
  S+' .p85-roster.r159-list article.r159-row{display:grid!important;grid-template-columns:62px minmax(0,1fr) auto 72px!important;align-items:center!important;gap:14px!important;padding:10px 16px!important;cursor:pointer;flex:0 0 auto}',
  S+' .p85-roster.r159-list article.r159-row.me{cursor:default;opacity:.9}',
  S+' .p85-roster.r159-list article.r159-row>b{justify-self:start}',
  S+' .p85-roster.r159-list article.r159-row>span{overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important}',
  S+' .p85-roster.r159-list article.r159-row>small{justify-self:end}',
  S+' .ms{font-variant-numeric:tabular-nums;font-size:12.5px;font-weight:800;text-align:right;font-style:normal;justify-self:end;white-space:nowrap}',
  S+' .ms.good{color:#7ee2a8!important}'+S+' .ms.ok{color:#ffd27a!important}'+S+' .ms.bad{color:#ff7b8a!important}'+S+' .ms.na{color:#8f86a0!important}',
  S+' footer{margin-top:auto}'
 ].join('\n');
 (document.head||document.documentElement).append(css);
 let current=null;   // {close}
 addEventListener('keydown',e=>{
  if(!current)return;
  if(e.code==='Tab'||e.code==='Escape'){e.preventDefault();e.stopImmediatePropagation();if(!e.repeat)current.close();}
 },true);
 function install(g){
  if(!g||g.__roster159)return;g.__roster159=true;
  let board=null,timer=0,epoch=0,last=null;
  const ownId=()=>Number((g.hud?.querySelector('.pn-own-id')?.textContent||'').replace(/\D+/g,''))||0;
  const close=()=>{epoch++;clearTimeout(timer);board?.remove();board=null;current=null;if(g.__ui159){g.uiOpen=false;g.__ui159=false;}};
  const render=()=>{if(!board||!last)return;const me=ownId(),mine=self.__ping158;
   board.querySelector('[role=status]').textContent=last.count+' oyuncu şehirde';
   board.querySelector('.r159-me').innerHTML='Pingin <b class="ms '+cls(mine)+'">'+label(mine)+'</b>';
   const list=board.querySelector('.r159-list'),keep=list.scrollTop;
   list.innerHTML=(last.players||[]).slice(0,200).map(p=>{const sid=Number(p.server_id)||0,isMe=sid===me;
    return'<article class="r159-row'+(isMe?' me':'')+'" data-sid="'+sid+'" title="'+(isMe?'Sen':'Tıkla: özel mesaj')+'"><b>#'+sid+'</b><span>'+esc(p.name)+(p.username?' <small style="opacity:.7;font-weight:500">('+esc(p.username)+')</small>':'')+(isMe?' (sen)':'')+'</span><small>'+(p.admin_duty?'Yönetici':p.police_badge?'Polis':'Şehirli')+'</small><em class="ms '+cls(p.ping)+'">'+label(p.ping)+'</em></article>';}).join('');
   list.scrollTop=keep;};
  const poll=async life=>{try{last=await g.api('/api/gta/roster');if(life!==epoch||!board)return;render();}catch(e){if(board&&life===epoch)board.querySelector('[role=status]').textContent=e.message;}finally{if(board&&life===epoch)timer=setTimeout(()=>poll(life),2500);}};
  g.scoreboard=()=>{
   if(board){close();return;}
   const life=++epoch;board=document.createElement('section');board.className='p85-scoreboard r159';
   board.innerHTML='<header><div><small>LOS SANTOS ROLEPLAY</small><h2>PAVCITY</h2></div><span>TAB · Kapat</span></header><div class="r159-bar"><p role="status">Oyuncular yükleniyor…</p><span class="r159-me"></span></div><div class="p85-roster r159-list" role="list"></div><footer>Bir oyuncuya tıkla → sohbette özel mesaj · TAB veya Esc ile kapat</footer>';
   g.hud.append(board);g.__ui159=true;g.uiOpen=true;current={close};try{g.release?.();}catch{}try{document.exitPointerLock?.();}catch{}
   board.addEventListener('click',e=>{const row=e.target.closest('.r159-row');if(!row||row.classList.contains('me'))return;const sid=Number(row.dataset.sid);if(!sid)return;close();
    if(typeof self.__openChat159==='function')self.__openChat159('/pm '+sid+' ');else g.notice?.('Özel mesaj için sohbete /pm '+sid+' mesaj yaz.');});
   void poll(life);
  };
  window.PAVRoster159={open:()=>!!board,close,render};
 }
 addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),80));
 if(window.PAVGame)setTimeout(()=>install(window.PAVGame),80);
})();
