/* 188: long info results (/adminkomutları, /stats, /hesapbilgi, /supheliler ...) were squeezed into the 116 side card
 * (narrow, two cramped columns, auto-closing after max 20 s). Results with more than 8 rows now open a wide, scrollable
 * panel that stays until closed (×, Esc or a click outside); "— Başlık —" rows become full-width section headers and a
 * search box filters the rows. Short results keep the timed side card. */
(()=>{'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const CSS='.i188-back{position:fixed;inset:0;z-index:60;display:grid;place-items:center;background:rgba(5,6,12,.45);backdrop-filter:blur(3px)}'+
'.i188{width:min(820px,94vw);max-height:84vh;display:flex;flex-direction:column;border-radius:18px;background:linear-gradient(180deg,rgba(32,22,44,.97),rgba(18,14,28,.97));color:#f4eefc;box-shadow:0 18px 60px rgba(0,0,0,.55);border:1px solid rgba(255,255,255,.08);font:500 14px/1.4 system-ui,"Segoe UI",sans-serif}'+
'.i188 header{display:flex;align-items:center;gap:12px;padding:16px 20px 10px}.i188 header small{color:#ff8fc7;font-weight:700;letter-spacing:.12em;font-size:11px}.i188 h3{margin:2px 0 0;font-size:19px}'+
'.i188 header div{flex:1}.i188 header button{width:32px;height:32px;border-radius:10px;border:0;background:rgba(255,255,255,.08);color:#fff;font-size:18px;cursor:pointer}'+
'.i188 input{margin:0 20px 10px;padding:9px 12px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);color:#fff;font:inherit}'+
'.i188 .rows{overflow:auto;padding:0 20px 18px;display:grid;grid-template-columns:minmax(150px,240px) 1fr;gap:6px 14px}'+
'.i188 .k{color:#ffffff;font-weight:700;font-family:Consolas,monospace;font-size:13px;word-break:break-word;padding:8px 10px;border-radius:9px;background:rgba(255,255,255,.05)}'+
'.i188 .v{color:rgba(240,232,252,.86);padding:8px 2px;word-break:break-word}'+
'.i188 .sec{grid-column:1/-1;margin-top:10px;color:#ff8fc7;font-weight:800;letter-spacing:.06em;text-transform:uppercase;font-size:12px;border-bottom:1px solid rgba(255,143,199,.25);padding-bottom:4px}'+
'@media (max-width:620px){.i188 .rows{grid-template-columns:1fr}.i188 .v{padding-top:0}}';
function panel(value){
 if(!document.getElementById('i188-style')){const s=document.createElement('style');s.id='i188-style';s.textContent=CSS;document.head.append(s);}
 document.querySelector('.i188-back')?.remove();
 const rows=value.rows,back=document.createElement('div');back.className='i188-back';
 back.innerHTML='<section class="i188" role="dialog" aria-modal="true"><header><div><small>PAVCITY · BİLGİ</small><h3>'+esc(value.title||'Bilgi')+'</h3></div><button aria-label="Kapat">×</button></header><input type="search" placeholder="Ara…" aria-label="Ara"><div class="rows"></div></section>';
 const box=back.querySelector('.rows'),input=back.querySelector('input');
 const draw=q=>{q=(q||'').toLocaleLowerCase('tr');box.innerHTML=rows.filter(([k,v])=>!q||String(k).toLocaleLowerCase('tr').includes(q)||String(v).toLocaleLowerCase('tr').includes(q)||/^—/.test(String(k))).map(([k,v])=>/^—/.test(String(k))&&!String(v||'').trim()?'<div class="sec">'+esc(String(k).replace(/^—\s*|\s*—$/g,''))+'</div>':'<div class="k">'+esc(k)+'</div><div class="v">'+esc(v)+'</div>').join('');};
 draw('');input.oninput=()=>draw(input.value);
 const close=()=>{back.remove();removeEventListener('keydown',key,true);};
 const key=e=>{if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();close();}else if(document.activeElement===input)e.stopPropagation();};
 addEventListener('keydown',key,true);back.querySelector('button').onclick=close;back.onclick=e=>{if(e.target===back)close();};
 document.body.append(back);try{document.exitPointerLock?.();}catch{}
}
addEventListener('pav-game-created',({detail:g})=>setTimeout(()=>{
 const card=g.showInfo;if(typeof card!=='function'||card.i188)return;
 const show=value=>{const rows=Array.isArray(value?.rows)?value.rows:[];return rows.length>8?panel({title:value.title,rows}):card(value);};show.i188=true;
 Object.defineProperty(g,'showInfo',{configurable:true,get:()=>show,set:()=>{}});
},0));
window.__info188=panel;
})();
