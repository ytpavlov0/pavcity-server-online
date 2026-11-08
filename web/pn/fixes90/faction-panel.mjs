const types={legal:'Legal kuruluş',illegal:'İllegal birlik',police:'Polis',medical:'Sağlık'};
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
export function mountFaction(host,{load,mutate,characterId,route,garage,notify=()=>{}}){
 let selected='overview',busy=false,epoch=0,current;
 const error=el('p','','f69-error');error.setAttribute('role','alert');
 async function refresh(){const n=++epoch;const d=await load();if(host.isConnected&&n===epoch){current=d;render();}}
 async function run(action,data){if(busy)return;busy=true;error.textContent='';host.querySelectorAll('button').forEach(b=>b.disabled=true);try{const r=await mutate(action,data);notify(r.notice||'İşlem tamamlandı.');await refresh();}catch(e){if(host.isConnected)error.textContent=e.message;}finally{busy=false;if(host.isConnected)render();}}
 function button(parent,text,fn){const b=el('button',text);b.type='button';b.onclick=fn;parent.append(b);return b;}
 function dangerous(parent,text,fn){const b=button(parent,text,()=>{if(b.dataset.confirm==='yes')fn();else{b.dataset.confirm='yes';b.textContent=text+' · Onayla';}});}
 function card(parent,title,detail){const n=el('article',undefined,'f69-card');n.append(el('h3',title));if(detail)n.append(el('p',detail));parent.append(n);return n;}
 function form(parent,title,fields,action,convert=x=>x){const f=el('form',undefined,'f69-form');f.append(el('h3',title));for(const [key,label,type,options] of fields){const l=el('label',label),i=el(type==='select'?'select':type==='textarea'?'textarea':'input');i.name=key;i.required=true;if(type==='select'){for(const [value,text] of options){const o=el('option',text);o.value=value;i.append(o);}}else if(type!=='textarea'){i.type=type||'text';if(type==='number'){i.min='0';i.step='1';}}i.maxLength=key==='text'?300:40;l.append(i);f.append(l);}const submit=el('button','Kaydet');submit.type='submit';f.append(submit);f.onsubmit=e=>{e.preventDefault();run(action,convert(Object.fromEntries(new FormData(f))));};parent.append(f);}
 function render(){
  const f=current.faction,m=f.member;
  host.replaceChildren();host.classList.add('f69');
  const hero=el('header',undefined,'f69-hero');hero.append(el('small',m?types[m.kind]:'BİRLİKLER'),el('h2',m?m.name:'Birlik merkezine hoş geldin'),el('p',m?`[${m.tag}] · Seviye ${m.level} · ${f.members.length}/${m.level*10} üye`:'Bir daveti kabul et veya kendi kuruluşunu oluştur.'));host.append(hero);
  const nav=el('nav',undefined,'f69-tabs');nav.setAttribute('aria-label','Birlik bölümleri');host.append(nav);
  const tabs=m?[['overview','Genel'],['members','Üyeler'],['invites','Davetler'],['vehicles','Araçlar'],['duty','Görev'],...(m.leader?[['manage','Yönetim']]:[])]:[['overview','Davetler'],['create','Birlik kur']];
  if(!tabs.some(([key])=>key===selected))selected='overview';
  for(const [key,title] of tabs){const b=button(nav,title,()=>{selected=key;render();});b.setAttribute('aria-current',String(selected===key));}
  const body=el('section',undefined,'f69-body');if(selected==='duty')body.classList.add('f90-duty');host.dataset.kind=m?.kind||'';host.append(body,error);
  if(selected==='overview'){
   if(m){card(body,'Birlik lideri',f.members.filter(p=>p.leader).map(p=>`${p.name} ${p.surname}`).join(', ')||'Lider atanmamış');card(body,'Birlik duyurusu',m.motd||'Henüz duyuru yok.');card(body,'Birlik kasası',`$${Number(m.bank).toLocaleString('tr-TR')}`);form(body,'Kasaya para yatır',[['amount','Tutar','number']],'deposit',v=>({amount:Number(v.amount)}));if(!m.leader)dangerous(body,'Birlikten ayrıl',()=>run('leave',{}));}
   else {body.append(el('p','Davet 5 dakika geçerlidir. Kabul sırasında davet edenin 5 metre yakınında ve yaya olmalısın.'));if(!f.invites.length)card(body,'Gelen davet yok','Birlik lideri yanına gelip davet gönderebilir.');for(const i of f.invites){const c=card(body,i.name,`${i.inviter_name} · ${i.nearby?'Yakında':'Yakınına git'} · ${Math.max(0,Math.ceil((i.expires-Date.now()/1000)/60))} dk`);button(c,'Daveti kabul et',()=>run('accept',{invite:i.id}));button(c,'Reddet',()=>run('decline',{invite:i.id}));}}
  }
  if(selected==='invites'){
   body.append(el('p','Yalnız aynı yerdeki, 5 metre içindeki yaya oyuncular listelenir.'));
   if(!m.leader)card(body,'Davet yetkisi','Birliğe yalnız lider davet gönderebilir.');
   else {button(body,'Yakındakileri yenile',()=>refresh().catch(e=>error.textContent=e.message));for(const p of f.nearby){const c=card(body,p.name,`Oyuncu #${p.server_id}`);button(c,'Davet gönder',()=>run('invite',{server_id:p.server_id}));}if(!f.nearby.length)card(body,'Uygun oyuncu yok','Oyuncunun yanına yaya gel ve listeyi yenile.');for(const i of f.outgoing){const c=card(body,'Bekleyen · '+i.name);button(c,'Daveti geri çek',()=>run('revoke',{invite:i.id}));}}
  }
  if(selected==='members')for(const p of f.members){const c=card(body,`${p.name} ${p.surname}`,`${f.ranks.find(r=>r.rank===p.rank)?.title||p.rank}${p.leader?' · Lider':''}`);if(m.leader&&m.kind==='police'){button(c,p.badge85?'Rozeti geri al':'Rütbe rozeti düzenle',()=>run(p.badge85?'badge-revoke':'badge-issue',{char_id:p.char_id}));if(p.badge85)c.append(el('small',p.badge85.serial+' · '+p.badge85.title));}if(m.leader&&p.char_id!==characterId&&!p.leader){const select=el('select');select.setAttribute('aria-label','Üye rütbesi');for(const r of f.ranks){const o=el('option',r.title);o.value=r.rank;o.selected=r.rank===p.rank;select.append(o);}c.append(select);button(c,'Rütbeyi kaydet',()=>run('rank',{char_id:p.char_id,rank:Number(select.value)}));dangerous(c,'Üyeyi çıkar',()=>run('kick',{char_id:p.char_id}));dangerous(c,'Liderliği devret',()=>run('transfer-leader',{char_id:p.char_id}));}}
  if(selected==='vehicles'){
   body.append(el('p','Araç paylaşımı anahtar yetkisi verir. Sahiplik değişmez; üyelik bitince birlik yetkisi kalkar.'));
   if(!f.vehicles.length)card(body,'Paylaşılan araç yok','Araçlarım üzerinden kendi aracını seçerek birliğe paylaş.');
   if(f.depot)button(body,'Birlik filo parkı · GPS',()=>route(f.depot));
   for(const v of f.vehicles){const c=card(body,v.model.toUpperCase(),`${v.plate} · ${v.fleet?'Birlik filosu · ':''}${v.active?'Dışarıda':'Garajda'}`);if(v.fleet)button(c,v.active?'Filo parkında iade et':'Filodan çıkar',()=>run(v.active?'fleet-store':'fleet-retrieve',{vehicle_id:v.id}));else{button(c,v.active?'Konum / araç menüsü':'Garajı aç',()=>garage(v));if(m.leader||v.owner===characterId)dangerous(c,'Paylaşımı kaldır',()=>run('vehicle-unshare',{vehicle_id:v.id}));}}
   button(body,'Araçlarımı aç',()=>garage());
   if(m.leader){dangerous(body,'Bulunduğum yeri filo parkı yap',()=>run('depot-set',{}));for(const v of f.fleet_catalog||[]){const c=card(body,v.name,`Birlik kasasından $${v.price.toLocaleString('tr-TR')} · Filo sınırı 3`);dangerous(c,'Filoya satın al',()=>run('fleet-buy',{model:v.model}));}}
   form(body,'Kendi aracını birliğe paylaş',[['vehicle_id','Araç ID · Araçlarım panelinde görünür','number']],'vehicle-share',v=>({vehicle_id:Number(v.vehicle_id)}));
  }
  if(selected==='duty'){
   const credential=f.duty90||{},badgeOK=!credential.badge_required||credential.has_badge;
   if(m.kind==='illegal')card(body,'İllegal birlik','Resmî görev ve devlet teçhizatı bu birlik türünde kullanılamaz.');
   if(credential.badge_required){const c=card(body,credential.has_badge?'Rozetin hazır':'Kişisel rozet gerekli',credential.has_badge?'Göreve girdiğinde rütben ve rozetin isim etiketinde görünür.':'Birlik lideri Üyeler sekmesinden adına rozet düzenlemeli.');if(m.leader&&!credential.has_badge)button(c,'Üyelere git · Rozet düzenle',()=>{selected='members';render();});}
   if(current.on_duty){const c=card(body,'Görevdesin','Görevden ayrılınca verilen görev zırhı geri alınır.');button(c,'Görevden çık',()=>run('duty',{}));}
   const toolbar=el('div',undefined,'f90-duty-tools');body.append(toolbar);button(toolbar,'Konum ve görev durumunu yenile',()=>refresh().catch(e=>error.textContent=e.message));
   if(!f.duty.length){card(body,'Görev noktası yok','Lider Yönetim sekmesinden dış dünyada bir görev noktası oluşturabilir.');if(m.leader&&m.kind==='police')button(body,'Mission Row görev noktasını oluştur',()=>run('duty-hq',{}));}
   for(const p of f.duty){const allowed=m.rank<=p.min_rank&&badgeOK&&p.near90;
    const c=card(body,p.name,`Rütbe 1–${p.min_rank} · ${p.near90?'Görev alanındasın':'GPS noktasına 3 metre içinde yaklaş'} · Yaya`);
    button(c,'GPS konumu',()=>route(p));
    if(!current.on_duty){const b=button(c,!badgeOK?'Önce rozet düzenlenmeli':m.rank>p.min_rank?'Rütben uygun değil':!p.near90?'Görev alanına yaklaş':'Göreve gir',()=>run('duty',{point:p.id}));b.disabled=!allowed;}
   }
  }
  if(selected==='manage'){
   if(f.members.length>1)form(body,'Liderliği devret ve ayrıl',[['char_id','Yeni lider','select',f.members.filter(p=>p.char_id!==characterId).map(p=>[p.char_id,p.name+' '+p.surname])]],'leave-transfer',v=>({char_id:Number(v.char_id)}));
   if(!['police','medical'].includes(m.kind)){card(body,'Birliği kapat','Üyelikler ve davetler sonlanır. Kasa, boş filo araçları ve boş mülkler sana devredilir. Kişisel araçlar sahiplerinde kalır.');form(body,'Kapatmayı onayla',[['confirm','Birlik etiketini yaz: '+m.tag,'text']],'disband');}

   form(body,'Duyuru',[['text','Birlik duyurusu','textarea']],'motd');
   form(body,'Kasadan çek',[['amount','Tutar','number']],'withdraw',v=>({amount:Number(v.amount)}));
   form(body,'Rütbe düzenle',[['rank','Rütbe','select',f.ranks.map(r=>[r.rank,r.title])],['title','Rütbe adı','text'],['salary','Vardiya maaşı','number']],'rank-config',v=>({...v,rank:Number(v.rank),salary:Number(v.salary)}));
   if(m.kind!=='illegal')form(body,'Bulunduğum dış dünya konumuna görev noktası',[['name','Nokta adı','text'],['min_rank','En düşük rütbe numarası (1–20)','number'],['armor','Zırh (yalnız polis)','number']],'duty-create',v=>({...v,min_rank:Number(v.min_rank),armor:Number(v.armor)}));
   for(const p of f.duty){const c=card(body,p.name);dangerous(c,'Görev noktasını kaldır',()=>run('duty-delete',{point:p.id}));}
   if(m.level<5)dangerous(body,`Seviyeyi yükselt · $${m.level*100000}`,()=>run('level',{}));
  }
  if(selected==='create')form(body,'Birlik kuruluşu · $50.000',[['name','Birlik adı','text'],['tag','Etiket','text'],['kind','Tür','select',Object.entries(types) ]],'create');
 }
 return refresh();
}
