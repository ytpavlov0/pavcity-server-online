(()=>{'use strict';
 const key='pavcity-tour93-checks';let dataPromise;
 const data=()=>dataPromise??=fetch('/pn/fixes93/tour.json').then(r=>{if(!r.ok)throw Error('Rehber yüklenemedi.');return r.json();}).catch(e=>{dataPromise=null;throw e;});
 const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 async function render(host){
  host.replaceChildren(node('p','Rehber yükleniyor…'));let d;try{d=await data();}catch(e){host.replaceChildren(node('p',e.message));return;}
  if(!host.isConnected)return;host.replaceChildren();let saved={};try{saved=JSON.parse(localStorage.getItem(key)||'{}');if(!saved||typeof saved!=='object'||Array.isArray(saved))saved={};}catch{}
  const head=node('header',undefined,'tour93-hero');head.append(node('small','PAVCITY / ÇEKİM REHBERİ · 93'),node('h1',d.title),node('p',d.intro));
  const progress=node('p','', 'tour93-progress');progress.setAttribute('role','status');head.append(progress);host.append(head);
  const tools=node('div',undefined,'tour93-tools'),search=node('input');search.type='search';search.placeholder='Sahne veya komut ara';search.setAttribute('aria-label','Sahne veya komut ara');
  const download=node('button','Kontrol listesini indir');download.type='button';tools.append(search,download);host.append(tools);
  const grid=node('div',undefined,'tour93-grid');host.append(grid);const update=()=>{progress.textContent=d.chapters.filter(c=>saved[c.id]===true).length+' / '+d.chapters.length+' sahne senin tarafından kontrol edildi';};
  for(const c of d.chapters){const card=node('article',undefined,'tour93-card'),label=node('label'),box=node('input');box.type='checkbox';box.checked=saved[c.id]===true;box.setAttribute('aria-label',c.title+' kontrol edildi');label.append(box,node('h2',c.title));card.append(label,node('code',c.command),node('p',c.step),node('p',c.check,'tour93-check'));grid.append(card);
   box.onchange=()=>{saved[c.id]=box.checked;try{localStorage.setItem(key,JSON.stringify(saved));}catch{}update();};card.dataset.search=(c.title+' '+c.command+' '+c.step).toLocaleLowerCase('tr');
  }
  update();search.oninput=()=>{const value=search.value.trim().toLocaleLowerCase('tr');for(const card of grid.children)card.hidden=!card.dataset.search.includes(value);};
  const limits=node('details',undefined,'tour93-limits');limits.append(node('summary','Test kapsamı ve açık noktalar'));for(const text of d.limits)limits.append(node('p',text));host.append(limits);
  const credits=node('footer');credits.append(node('h2','Model ve doku kaynakları'));for(const c of d.credits){const a=node('a',c.name);a.href=c.url;a.target='_blank';a.rel='noopener noreferrer';credits.append(a);}host.append(credits);
  download.onclick=()=>{const report={release:d.release,checked_at:new Date().toISOString(),checks:d.chapters.map(c=>({id:c.id,title:c.title,user_checked:saved[c.id]===true})),limits:d.limits};const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const a=node('a');a.href=url;a.download='pavcity-test93.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 }
 const standalone=document.getElementById('tour93');if(standalone)void render(standalone);
 addEventListener('pav-game-created',({detail:g})=>queueMicrotask(()=>{g.showcase93=()=>{const p=g.openRP('PAVCITY · Tanıtım ve test','<div class="tour93"></div>','tour93-panel');void render(p.querySelector('.tour93'));};const links=g.hud.querySelector('.pav-menu-extras');if(links){const b=node('button','Tanıtım ve test rehberi');b.type='button';b.onclick=g.showcase93;links.append(b);}}));
})();
