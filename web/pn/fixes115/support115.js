/* PAVCITY destek 115 (F2 · /rapor). Players see only their open tickets (closed ones stay in
 * SQL, nothing piles up on screen); staff get the open queue, "üzerimde" and search, plus the
 * reporter's situation recorded at creation (ID, position, vehicle, vitals, nearby players).
 * One panel, fixed two-column grid with its own scroll areas, so nothing overlaps. */
(()=>{'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date=t=>new Date(Number(t)*1000).toLocaleString('tr-TR',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
const CATEGORIES=['Genel soru','Kural ihlali','İç mekan / Bug','Eşya problemi','Araç sorunu','Diğer'];
const EVENTS={created:'Talep oluşturuldu',claimed:'Yetkili üstlendi',released:'Sıraya bırakıldı',resolved:'Sonuçlandırıldı',cancelled:'İptal edildi',reopened:'Yeniden açıldı',rated:'Değerlendirildi'};
addEventListener('pav-game-created',({detail})=>setTimeout(()=>{try{install(detail||window.PAVGame);}catch(e){window.PAVSupport115Error=String(e?.stack||e);}},0));
function install(g){window.PAVSupport115=(window.PAVSupport115||0)+1;
 let panel=null,selected=0,view='open',query='',timer=0,busy=false,staff=false;const draft={category:CATEGORIES[0],subject:'',body:'',reply:''};
 const api=(action,data={})=>g.api('/api/reports/'+action,data);
 const alive=()=>panel?.isConnected;
 const fail=e=>{if(alive())panel.querySelector('.rp-error').textContent=e?.message||String(e);else g.notice?.(e?.message||String(e),true);};
 const state=r=>r.status==='closed'?'Sonuçlandı':r.claimed_by?'Yetkili ilgileniyor':'Sırada';
 async function mutate(action,data){if(busy)return;busy=true;try{const r=await api(action,data);g.notice?.(r.notice||'Kaydedildi.');if(action==='create'){selected=r.id;draft.subject=draft.body='';}if(action==='message'||action==='resolve')draft.reply='';if(['cancel','resolve'].includes(action)&&!staff)selected=0;await render();}catch(e){fail(e);}finally{busy=false;}}
 function form(){return '<div class="s115-new"><small>OYUNCU DESTEK</small><h3>Yeni destek talebi</h3><p>Olayı, karıştığı oyuncuların ID’sini ve zamanını yaz. Konumun ve yanındaki oyuncular talebe otomatik eklenir. Şifre veya kişisel bilgi paylaşma.</p>'+
  '<form class="s115-form"><label>Kategori<select name="category">'+CATEGORIES.map(c=>'<option'+(c===draft.category?' selected':'')+'>'+esc(c)+'</option>').join('')+'</select></label><label>Konu<input name="subject" minlength="3" maxlength="80" required placeholder="Kısa başlık" value="'+esc(draft.subject)+'"></label>'+
  '<label class="wide">Açıklama<textarea name="body" minlength="5" maxlength="1000" required placeholder="Ne oldu, nerede, ne zaman?">'+esc(draft.body)+'</textarea></label><footer><small>En fazla 3 açık talep · 60 sn’de bir</small><button>Talebi gönder</button></footer></form></div>';}
 async function detail(){
  const r=await api('thread',{id:selected});if(!alive())return '';const v=r.report;staff=!!r.staff;let ctx=null;
  if(staff){try{ctx=(await g.api('/api/reports115/context',{id:selected})).context;}catch{}}
  const actions=[];if(staff&&v.status==='open'){actions.push('<button data-do="claim">'+(r.mine?'Üzerimde ✓':'Üzerime al')+'</button>');if(r.mine)actions.push('<button data-do="release">Sıraya bırak</button>');}
  if(v.status==='closed')actions.push('<button data-do="reopen">Yeniden aç</button>');else if(!staff)actions.push('<button data-do="cancel" class="ghost">Talebi iptal et</button>');
  const where=ctx?'<div class="s115-context"><b>Talep anındaki durum</b><span>ID '+esc(ctx.server_id)+' · Kayıt #'+esc(ctx.char_id)+'</span><span>Konum '+[ctx.x,ctx.y,ctx.z].map(n=>Number(n).toFixed(1)).join(', ')+(ctx.dimension?' · Boyut '+esc(ctx.dimension):'')+'</span><span>Can '+esc(ctx.health)+' · Zırh '+esc(ctx.armor)+(ctx.vehicle_id?' · Araç #'+esc(ctx.vehicle_id):' · Yaya')+'</span><span>Yakındakiler: '+(ctx.nearby.length?ctx.nearby.map(n=>esc(n.name)+' ['+esc(n.server_id)+'] '+esc(n.meters)+' m').join(' · '):'kimse yok')+'</span></div>':'';
  const msgs=r.messages.map(m=>'<article class="'+(m.staff?'staff':'')+'"><header><strong>'+esc(m.name)+(m.staff?' · Destek':'')+'</strong><time>'+date(m.created)+'</time></header><p>'+esc(m.body)+'</p></article>').join('');
  const reply=v.status==='open'?'<form class="s115-reply"><textarea name="body" minlength="2" maxlength="1000" required placeholder="Mesajını yaz…">'+esc(draft.reply)+'</textarea><footer><button name="send">Gönder</button>'+(staff?'<button name="resolve" class="ok">Yanıtla ve kapat</button>':'')+'</footer></form>':
   (!staff&&v.actor&&!v.rating?'<div class="s115-rate"><span>Desteği değerlendir</span>'+[1,2,3,4,5].map(n=>'<button data-rate="'+n+'">'+n+' ★</button>').join('')+'</div>':v.rating?'<p class="s115-muted">Değerlendirme · '+v.rating+'/5</p>':'');
  return '<div class="s115-detail"><header><div><small>TALEP #'+v.id+' · '+esc(v.category)+'</small><h3>'+esc(v.subject||String(v.body).slice(0,64))+'</h3><p>'+esc(v.name)+' · '+date(v.created)+'</p></div><span class="s115-state '+(v.status==='closed'?'closed':v.claimed_by?'claimed':'')+'">'+state(v)+'</span></header>'+
   (actions.length?'<div class="s115-actions">'+actions.join('')+'</div>':'')+where+'<div class="s115-thread">'+msgs+'</div><div class="s115-events">'+r.events.slice(0,4).reverse().map(e=>'<span>'+esc(EVENTS[e.kind]||e.kind)+' · '+date(e.created)+'</span>').join('')+'</div>'+reply+'</div>';}
 async function render(){
  if(!alive())return;const status=view==='search'?'all':view;const r=await api('list',{status,query:view==='search'?query:'',offset:0});if(!alive())return;staff=!!r.staff;
  const tabs=staff?[['open','Sıradakiler'],['mine','Üzerimde'],['search','Ara / geçmiş']]:[];
  const rows=r.reports.filter(v=>staff?view!=='open'||v.status==='open':v.status==='open');
  if(!staff&&selected&&!rows.some(v=>v.id===selected))selected=0;
  const list='<aside class="s115-list"><button class="s115-compose">+ Yeni talep</button>'+(tabs.length?'<nav>'+tabs.map(([k,n])=>'<button data-view="'+k+'" class="'+(k===view?'on':'')+'">'+n+(k==='open'?' <i>'+(r.summary.open||0)+'</i>':'')+'</button>').join('')+'</nav>':'<p class="s115-muted">Açık taleplerin ('+rows.length+'/3). Sonuçlananlar kayıtta saklanır.</p>')+
   (view==='search'&&staff?'<input class="s115-search" placeholder="Konu, isim, açıklama…" value="'+esc(query)+'">':'')+
   '<div class="s115-tickets">'+(rows.length?rows.map(v=>'<button data-ticket="'+v.id+'" class="'+(v.id===selected?'on':'')+'"><small>#'+v.id+' · '+esc(v.category)+(v.unread?' <b>'+v.unread+'</b>':'')+'</small><strong>'+esc(v.subject)+'</strong><span>'+esc(v.name)+' · '+state(v)+'</span></button>').join(''):'<p class="s115-muted">Bu görünümde talep yok.</p>')+'</div></aside>';
  const main='<section class="s115-main">'+(selected?await detail():form())+'</section>';if(!alive())return;
  const body=panel.querySelector('.s115-layout');const focus=document.activeElement?.closest?.('.s115-search')?'search':null;body.innerHTML=list+main;wire();if(focus){const s=body.querySelector('.s115-search');s?.focus();s?.setSelectionRange(s.value.length,s.value.length);}
  const thread=body.querySelector('.s115-thread');if(thread)thread.scrollTop=thread.scrollHeight;}
 function wire(){const body=panel.querySelector('.s115-layout');
  body.querySelector('.s115-compose').onclick=()=>{selected=0;render().catch(fail);};
  body.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view;selected=0;render().catch(fail);});
  body.querySelectorAll('[data-ticket]').forEach(b=>b.onclick=()=>{selected=Number(b.dataset.ticket);render().catch(fail);});
  let t;const s=body.querySelector('.s115-search');if(s)s.oninput=()=>{clearTimeout(t);t=setTimeout(()=>{query=s.value;render().catch(fail);},300);};
  body.querySelectorAll('[data-do]').forEach(b=>b.onclick=()=>mutate(b.dataset.do,{id:selected}));
  body.querySelectorAll('[data-rate]').forEach(b=>b.onclick=()=>mutate('rate',{id:selected,rating:Number(b.dataset.rate)}));
  const create=body.querySelector('.s115-form');if(create){create.oninput=()=>{const d=new FormData(create);draft.category=d.get('category');draft.subject=d.get('subject');draft.body=d.get('body');};create.onsubmit=e=>{e.preventDefault();mutate('create',Object.fromEntries(new FormData(create)));};}
  const reply=body.querySelector('.s115-reply');if(reply){reply.oninput=()=>{draft.reply=new FormData(reply).get('body');};reply.onsubmit=e=>{e.preventDefault();const text=new FormData(reply).get('body');mutate(e.submitter?.name==='resolve'?'resolve':'message',{id:selected,body:text,reply:text});};}}
 const open=async()=>{clearTimeout(timer);panel=g.openRP('F2 · Destek merkezi','<div class="s115-layout"></div>','pav-support115');
  try{await render();}catch(e){fail(e);}
  const poll=async()=>{if(!alive())return;try{if(!document.hidden&&!panel.querySelector('input:focus,textarea:focus,select:focus'))await render();}catch{}timer=setTimeout(poll,10000);};timer=setTimeout(poll,10000);};
 // fixes90/community.js re-wraps g.reports after other layers; keep this desk as the only one.
 Object.defineProperty(g,'reports',{configurable:true,get:()=>open,set:()=>{}});
 // Panels from different modules each track only their own overlay, so a second one used to
 // open on top of the first. Exactly one RP panel stays: a new one replaces the older ones.
 if(g.hud instanceof Node)new MutationObserver(records=>{for(const r of records)for(const n of r.addedNodes)if(n.nodeType===1&&n.classList.contains('rp-overlay'))for(const old of g.hud.querySelectorAll(':scope > .rp-overlay'))if(old!==n)old.remove();}).observe(g.hud,{childList:true});
}
})();
