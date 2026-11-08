/* PAVCITY admin panel 114 (staff only; F9 or the YETKİLİ button): online players with
 * vitals/duty/rank, rank-checked actions (goto, bring, revive, heal, armor, jail, kick,
 * ban, money, rank grant), staff chat (/a), open reports, staff roster and anticheat.
 * Every action goes through /api/admin114/action, which maps onto pn_admin commands. */
(()=>{'use strict';
const icon=n=>window.PAVIcons105?.svg(n)||'';
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=text;return n;};
const ago=t=>{const s=Math.max(0,Math.round(Date.now()/1000-Number(t||0)));return s<60?s+' sn':s<3600?Math.round(s/60)+' dk':Math.round(s/3600)+' sa';};
const LABELS={goto:'Yanına git',gethere:'Yanıma getir',revive:'Canlandır',heal:'Can doldur',armor:'Zırh ver',unjail:'Hapisten çıkar',jail:'Hapse at',kick:'Sunucudan at (5 dk)',ban:'Yasakla',money:'Para ver',rank:'Yetki ver'};
const DANGER=new Set(['kick','ban','rank','jail']);
function install(g){
 let staff=null,open=false,tab='players',selected=0,timer=0,probe=0,query='';const drafts={},armed={};
 const fab=el('button','a114-fab');fab.type='button';fab.innerHTML=icon('star')+'<span>YETKİLİ</span>';fab.hidden=true;g.hud.append(fab);
 const root=el('section','a114');root.hidden=true;root.setAttribute('role','dialog');root.setAttribute('aria-label','Yetkili paneli');
 root.innerHTML='<div class="a114-window"><header><div class="a114-title"><b>PAVCITY</b><strong>Yetkili Paneli</strong></div><span class="a114-rank"></span><button type="button" class="a114-duty"></button><button type="button" class="a114-close" aria-label="Kapat">'+icon('close')+'</button></header>'+
  '<nav class="a114-tabs"></nav><div class="a114-body"></div></div>';
 g.hud.append(root);
 const body=root.querySelector('.a114-body'),tabs=root.querySelector('.a114-tabs'),rankChip=root.querySelector('.a114-rank'),duty=root.querySelector('.a114-duty');
 const run=async(fn)=>{try{await fn();}catch(e){g.toast?.(String(e?.message||e),true);}};
 const act=(action,extra={})=>run(async()=>{const r=await g.api('/api/admin114/action',{action,...extra});if(r?.notice)g.toast?.(r.notice);await refresh();});
 async function refresh(){try{staff=await g.api('/api/admin114/players');fab.hidden=false;}catch{staff=null;fab.hidden=true;if(open)close();return;}if(open)render();}
 function show(){if(!staff)return;open=true;root.hidden=false;g.uiOpen=true;g.release?.();render();clearInterval(timer);timer=setInterval(refresh,3000);refresh();}
 function close(){open=false;root.hidden=true;g.uiOpen=false;clearInterval(timer);}
 fab.onclick=()=>open?close():show();root.querySelector('.a114-close').onclick=close;
 duty.onclick=()=>act('duty');
 const TABS=[['players','Oyuncular'],['chat','Yetkili sohbeti'],['reports','Raporlar'],['staff','Ekip'],['anticheat','Anticheat']];
 function render(){
  if(!staff)return;rankChip.textContent=staff.rank_name+' · '+staff.rank;duty.textContent=staff.duty?'GÖREVDE · Çık':'GÖREV DIŞI · Gir';duty.classList.toggle('on',!!staff.duty);
  tabs.replaceChildren(...TABS.map(([key,label])=>{const b=el('button',key===tab?'on':'',label);b.type='button';const n=key==='reports'?staff.reports.length:key==='anticheat'?staff.anticheat.length:key==='players'?staff.players.length:0;if(n){const c=el('i','',String(n));b.append(c);}b.onclick=()=>{tab=key;render();};return b;}));
  const keep=document.activeElement&&root.contains(document.activeElement)&&document.activeElement.matches('input,select,textarea')?document.activeElement.dataset.keep:null;
  body.replaceChildren(({players,chat,reports,staff:team,anticheat})[tab]());
  if(keep){const again=body.querySelector('[data-keep="'+keep+'"]');if(again){again.focus();if(again.setSelectionRange&&again.value!=null)try{again.setSelectionRange(again.value.length,again.value.length);}catch{}}}
 }
 const players=()=>{
  const wrap=el('div','a114-players'),list=el('div','a114-list'),side=el('div','a114-detail');
  const search=el('input','a114-search');search.placeholder='İsim veya ID ara…';search.value=query;search.dataset.keep='search';search.oninput=()=>{query=search.value;fill();};
  const fill=()=>{const q=query.trim().toLowerCase();list.replaceChildren(...staff.players.filter(p=>!q||String(p.server_id)===q||p.name.toLowerCase().includes(q)).map(p=>{
   const row=el('button','a114-row'+(p.server_id===selected?' on':''));row.type='button';row.onclick=()=>{selected=p.server_id;render();};
   const id=el('span','a114-id',String(p.server_id)),name=el('span','a114-name',p.name),meta=el('span','a114-meta');
   if(p.rank)meta.append(el('em','r'+p.rank,p.rank_name));if(p.duty)meta.append(el('em','duty','GÖREVDE'));if(p.jailed)meta.append(el('em','jail','HAPİS'));if(p.afk>=120)meta.append(el('em','afk','AFK'));if(p.me)meta.append(el('em','me','SEN'));
   const bars=el('span','a114-bars');bars.style.setProperty('--hp',p.health+'%');bars.style.setProperty('--ar',p.armor+'%');bars.title='Can '+p.health+' · Zırh '+p.armor;
   row.append(id,name,meta,bars);return row;}));if(!list.children.length)list.append(el('p','a114-empty','Oyuncu bulunamadı.'));};
  fill();const target=staff.players.find(p=>p.server_id===selected);
  if(!target){side.append(el('p','a114-empty','Bir oyuncu seç: eylemler burada açılır.'));}
  else{
   const head=el('div','a114-who');head.append(el('b','',target.name),el('span','','ID '+target.server_id+' · Kayıt #'+target.char_id+(target.dimension?' · Boyut '+target.dimension:'')+(target.vehicle?' · Araçta':'')));
   const vit=el('div','a114-vitals');vit.innerHTML='<label>Can<i style="--v:'+target.health+'%"></i><b>'+target.health+'</b></label><label class="ar">Zırh<i style="--v:'+target.armor+'%"></i><b>'+target.armor+'</b></label>';
   side.append(head,vit);
   const allowed=k=>staff.rank>=(staff.actions[k]??99);
   const quick=el('div','a114-quick');for(const k of['goto','gethere','revive','heal','armor','unjail']){const b=el('button','',LABELS[k]);b.type='button';b.disabled=!allowed(k);b.onclick=()=>act(k,{target:target.server_id});quick.append(b);}side.append(quick);
   const form=(k,fields)=>{const box=el('form','a114-form'+(DANGER.has(k)?' danger':''));box.append(el('b','',LABELS[k]));const inputs={};
    for(const [name,ph,type,extra] of fields){let i;if(type==='select'){i=el('select');for(const [v,t] of extra){const o=el('option','',t);o.value=v;i.append(o);}}else{i=el('input');i.type=type;i.placeholder=ph;if(extra)Object.assign(i,extra);}
     const id=i.dataset.keep=target.server_id+'-'+k+'-'+name;if(drafts[id]!=null)i.value=drafts[id];i.addEventListener('input',()=>{drafts[id]=i.value;});i.addEventListener('change',()=>{drafts[id]=i.value;});inputs[name]=i;box.append(i);}
    const arm=target.server_id+'-'+k,sure=()=>armed[arm]>Date.now();
    const go=el('button',sure()?'sure':'',DANGER.has(k)?(sure()?'Emin misin? Tekrar bas':'Uygula'):'Gönder');go.type='submit';go.disabled=!allowed(k);box.append(go);
    box.onsubmit=ev=>{ev.preventDefault();if(DANGER.has(k)&&!sure()){armed[arm]=Date.now()+4000;go.classList.add('sure');go.textContent='Emin misin? Tekrar bas';return;}delete armed[arm];
     const data={target:target.server_id};for(const [n,i] of Object.entries(inputs)){data[n]=i.type==='number'||n==='rank'?Number(i.value):i.value;delete drafts[i.dataset.keep];}act(k,data);};
    return box;};
   const forms=el('div','a114-forms');
   forms.append(form('jail',[['minutes','Dakika','number',{min:1,max:1440,value:15}],['reason','Sebep','text',{maxLength:120}]]),form('kick',[['reason','Sebep','text',{maxLength:120}]]),
    form('ban',[['minutes','Dakika (0 = süresiz)','number',{min:0,max:525600,value:1440}],['reason','Sebep','text',{maxLength:120}]]),form('money',[['amount','Miktar $','number',{min:1,max:10000000}]]));
   if(staff.rank>=4)forms.append(form('rank',[['rank','','select',[[0,'0 · Oyuncu'],[1,'1 · Moderatör'],[2,'2 · Yönetici'],[3,'3 · Baş yönetici']]]]));
   side.append(forms);
  }
  const left=el('div','a114-left');left.append(search,list);wrap.append(left,side);return wrap;};
 const chat=()=>{const wrap=el('div','a114-chat'),log=el('div','a114-log');
  for(const m of staff.lines||[]){const row=el('p',Number(m.char_id)?'':'sys');row.append(el('time','',new Date(Number(m.created)*1000).toLocaleTimeString('tr-TR',{hour12:false,hour:'2-digit',minute:'2-digit'})));if(Number(m.char_id))row.append(el('b','',m.name));row.append(el('span','',m.body));log.append(row);}
  if(!log.children.length)log.append(el('p','a114-empty','Henüz yetkili mesajı yok. Oyunda /a mesaj da kullanılabilir.'));
  const form=el('form','a114-say'),input=el('input');input.placeholder='Yetkililere yaz…';input.maxLength=200;input.dataset.keep='say';input.value=drafts.say||'';input.oninput=()=>{drafts.say=input.value;};const send=el('button','','Gönder');send.type='submit';form.append(input,send);
  form.onsubmit=ev=>{ev.preventDefault();const text=input.value.trim();if(!text)return;input.value='';drafts.say='';run(async()=>{await g.api('/api/chat/send',{message:'/a '+text,scope:'local'});await refresh();});};
  wrap.append(log,form);requestAnimationFrame(()=>{log.scrollTop=log.scrollHeight;});return wrap;};
 const table=(rows,cols,empty)=>{const t=el('div','a114-table');if(!rows.length){t.append(el('p','a114-empty',empty));return t;}for(const r of rows){const row=el('div','a114-trow');for(const c of cols)row.append(el('span','',c(r)));t.append(row);}return t;};
 const reports=()=>table(staff.reports,[r=>'#'+r.id,r=>r.name,r=>r.category,r=>r.body,r=>ago(r.created)],'Açık rapor yok.');
 const team=()=>table(staff.staff,[r=>r.username||('Kullanıcı #'+r.user_id),r=>r.rank_name,r=>'Seviye '+r.rank],'Kayıtlı yetkili yok.');
 const anticheat=()=>table(staff.anticheat,[r=>'#'+r.id,r=>r.name||('Kayıt #'+r.char_id),r=>({teleport:'Işınlanma',speed:'Hız',climb:'Tırmanma'})[r.kind]||r.kind,r=>ago(r.at)],'Kayıt yok. (Yalnızca gözlem; oyuncu otomatik cezalandırılmaz.)');
 // While open, g.uiOpen makes the client swallow game keys (inputs still type). The client
 // offers Escape to hudEditorClose85 first, so the panel chains itself into that hook.
 let inner=g.hudEditorClose85;Object.defineProperty(g,'hudEditorClose85',{configurable:true,get:()=>()=>{if(open){close();return true;}return inner?.();},set:v=>{inner=v;}});
 const key=e=>{if(e.code==='F9'&&e.type==='keydown'&&staff){e.preventDefault();e.stopImmediatePropagation();if(!e.repeat)open?close():show();}};
 addEventListener('keydown',key,true);
 refresh();probe=setInterval(()=>{if(!open)refresh();},30000);
 addEventListener('pav-game-stop',()=>{clearInterval(probe);clearInterval(timer);removeEventListener('keydown',key,true);root.remove();fab.remove();},{once:true});
 g.adminPanel114={show,close,refresh};
}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
