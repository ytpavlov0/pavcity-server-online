/* City suite on index126 (runner122): the 125 checks plus phone126 (shadow-root iPhone instead of
 * fixes85/phone.js; not a game panel, so movement keys keep reaching the game), ui126 (ESC menu
 * header/footer, centred scrolling info card, soft quickbar). Phone data is a fixture route. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
const p126=await page.evaluate(()=>({client:[...document.scripts].some(s=>s.src.includes('/pn/fixes126/client.js')),js:[...document.scripts].some(s=>s.src.includes('/pn/fixes126/phone126.js')),old:[...document.scripts].some(s=>s.src.includes('/pn/fixes85/phone.js')),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes126/ui126.css'))}));
assert(p126.client&&p126.js&&!p126.old&&p126.css,'126 layer: '+JSON.stringify(p126));
const now126=Math.floor(Date.now()/1000);
await page.route('**/api/phone/status',r=>r.fulfill({json:{success:true,has_phone:true,number:21283414,contacts:[{name:'Ayşe Yılmaz',number:21000001},{name:'Mert Kaya',number:21000002},{name:'Polis Merkezi',number:21000155}],messages:[{id:3,sender:21000001,target:21283414,body:'Akşam galeriye geliyor musun? Yeni gelen Banshee’yi görmen lazım.',created:now126-600},{id:2,sender:21283414,target:21000002,body:'Tofaş hazır, yarın bakarız.',created:now126-90000}],unread:1,call:null,call_history:[{caller:21000002,target:21283414,created:now126-3600},{caller:21283414,target:21000001,created:now126-7200}],bank:17501,cash:7983368}}));
await page.route('**/api/phone/thread',r=>r.fulfill({json:{success:true,has_more:false,messages:[{id:1,sender:21283414,target:21000001,body:'Selam! Galeri kaçta açılıyor?',created:now126-1500},{id:3,sender:21000001,target:21283414,body:'Akşam galeriye geliyor musun? Yeni gelen Banshee’yi görmen lazım.',created:now126-600}]}}));
await page.route('**/api/phone/read',r=>r.fulfill({json:{success:true}}));
await page.evaluate(()=>{for(const o of document.querySelectorAll('.rp-overlay,.pav-overlay'))o.remove();sessionStorage.setItem('pav-phone-unlocked-'+PAVGame.character.id,'1');});
await page.evaluate(()=>PAVGame.phone());await page.waitForFunction(()=>document.getElementById('pav-iphone126')?.shadowRoot?.querySelector('.grid .app'));await page.waitForTimeout(500);
const ph126=await page.evaluate(()=>{const h=document.getElementById('pav-iphone126'),r=h.getBoundingClientRect(),root=h.shadowRoot,dev=root.querySelector('.device').getBoundingClientRect(),apps=[...root.querySelectorAll('.grid .app')].map(a=>{const t=a.querySelector('.tile').getBoundingClientRect(),s=a.querySelector('span').getBoundingClientRect();return[t.width,t.height,s.width<=a.getBoundingClientRect().width+.5];});
 const inside=[...root.querySelectorAll('.grid .app,.dock,.widget')].every(e=>{const b=e.getBoundingClientRect();return b.left>=dev.left-1&&b.right<=dev.right+1&&b.top>=dev.top-1&&b.bottom<=dev.bottom+1;});
 return{inView:r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight,ratio:r.width/r.height,apps:apps.length,same:apps.every(a=>Math.abs(a[0]-apps[0][0])<.5&&Math.abs(a[1]-a[0])<.5),labels:apps.every(a=>a[2]),inside,uiOpen:PAVGame.uiOpen,open:PAVGame.phonePanelOpen,dock:root.querySelectorAll('.dock .app').length,blur:getComputedStyle(root.querySelector('.dock')).backdropFilter};});
assert(ph126.inView&&ph126.apps===12&&ph126.same&&ph126.labels&&ph126.inside&&ph126.dock===4&&ph126.open&&!ph126.uiOpen&&/blur/.test(ph126.blur)&&Math.abs(ph126.ratio-.476)<.01,'phone126 home: '+JSON.stringify(ph126));
await page.screenshot({path:O+'/phone126-home.png'});
await page.waitForTimeout(200);const walk126=await page.evaluate(()=>{const b=PAVGame.bridge;return{controlsOff:b?new Int32Array(b.memory.buffer,b.block,16384)[7612]:0,locked:!!document.pointerLockElement};});
assert.equal(walk126.controlsOff,0,'controls stay on while the phone is open: '+JSON.stringify(walk126));
await page.evaluate(()=>document.getElementById('pav-iphone126').shadowRoot.querySelector('.dock [data-go=sms]').click());await page.waitForTimeout(400);await page.screenshot({path:O+'/phone126-sms.png'});
await page.evaluate(()=>document.getElementById('pav-iphone126').shadowRoot.querySelector('[data-thread]').click());await page.waitForFunction(()=>document.getElementById('pav-iphone126').shadowRoot.querySelector('.bubble.them'));await page.waitForTimeout(300);await page.screenshot({path:O+'/phone126-thread.png'});
const typing126=await page.evaluate(()=>{const ta=document.getElementById('pav-iphone126').shadowRoot.querySelector('.compose textarea');ta.focus();return PAVGame.uiOpen;});assert(typing126,'typing in the phone holds the game keys');await page.waitForTimeout(150);assert.equal(await page.evaluate(()=>new Int32Array(PAVGame.bridge.memory.buffer,PAVGame.bridge.block,16384)[7612]),1,'controls held while typing');
await page.evaluate(()=>{const r=document.getElementById('pav-iphone126').shadowRoot;r.activeElement?.blur();});await page.waitForTimeout(50);assert.equal(await page.evaluate(()=>PAVGame.uiOpen),false,'blur releases the keys');
await page.evaluate(()=>{const r=document.getElementById('pav-iphone126').shadowRoot;r.querySelector('[data-back]').click();});await page.waitForTimeout(250);
await page.evaluate(()=>PAVGame.phone126.navigate('calls'));await page.waitForTimeout(300);await page.screenshot({path:O+'/phone126-calls.png'});
await page.evaluate(()=>PAVGame.phone126.navigate('calculator'));await page.waitForTimeout(300);await page.screenshot({path:O+'/phone126-calc.png'});
await page.evaluate(()=>PAVGame.phone126.navigate('bank'));await page.waitForTimeout(300);await page.screenshot({path:O+'/phone126-wallet.png'});
await page.evaluate(()=>PAVGame.phone());await page.waitForTimeout(300);assert.equal(await page.evaluate(()=>!!document.getElementById('pav-iphone126')||PAVGame.phonePanelOpen),false,'phone closes');
await page.evaluate(()=>PAVGame.setMenu?.(true));await page.waitForTimeout(600);
const m126=await page.evaluate(()=>{const s=document.querySelector('.pn-menu .pav-menu-shell'),h=s.querySelector(':scope>header'),v=s.querySelector(':scope>.pav-menu-view'),r=s.querySelector(':scope>.pn-resume');return{strip:getComputedStyle(s,'::before').display,gap:v.getBoundingClientRect().top-h.getBoundingClientRect().bottom,resume:r.getBoundingClientRect().width<s.getBoundingClientRect().width*.5,x:getComputedStyle(s.querySelector('.p82-menu-close span'),'::after').content};});
assert(m126.strip==='none'&&m126.gap<2&&m126.resume&&/×/.test(m126.x),'ESC menu 126: '+JSON.stringify(m126));
await page.screenshot({path:O+'/menu126.png'});await page.evaluate(()=>PAVGame.setMenu?.(false));await page.waitForTimeout(300);
await page.evaluate(()=>{const b=document.createElement('aside');b.className='pav-info-panel probe126';b.innerHTML='<header><small>PAVCITY · BİLGİ</small><button>×</button></header><h3>Karakter ve araç kayıtları</h3><dl>'+Array.from({length:30},(_,i)=>'<div><dt>Araç #'+(30+i)+'</dt><dd>ZENTORNO · PN89A98A · Dışarıda</dd></div>').join('')+'</dl>';PAVGame.hud.append(b);});
const i126=await page.evaluate(()=>{const b=document.querySelector('.probe126'),r=b.getBoundingClientRect();return{top:r.top,bottom:r.bottom,center:Math.abs((r.top+r.bottom)/2-innerHeight/2),scrolls:b.scrollHeight>b.clientHeight};});
assert(i126.top>=0&&i126.bottom<=await page.evaluate(()=>innerHeight)&&i126.center<2&&i126.scrolls,'info card centred + scrolling: '+JSON.stringify(i126));
await page.screenshot({path:O+'/info126.png'});await page.evaluate(()=>document.querySelector('.probe126')?.remove());
const q126=await page.evaluate(()=>{const q=document.querySelector('.pav-quickbar');if(!q)return null;const r=q.getBoundingClientRect();return{x:r.left,y:r.top,w:r.width,h:r.height,radius:getComputedStyle(q).borderRadius};});
if(q126){assert.equal(q126.radius,'18px');await page.screenshot({path:O+'/quickbar126.png',clip:{x:Math.max(0,q126.x-20),y:Math.max(0,q126.y-20),width:q126.w+40,height:q126.h+40}});}
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city126 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city125.cjs','utf8'),[
 ["await page.screenshot({path:O+'/radar125-150deg.png',clip:{x:0,y:560,width:360,height:290}});","await page.screenshot({path:O+'/radar125-150deg.png',clip:{x:0,y:560,width:360,height:290}});"+extra],
 ["/pn/fixes125/client.js","/pn/fixes126/client.js"],["release125-checks","release126-checks"],["index125.html","index126.html"],
 ["\"'125 PASS (eye icon centred,","\"'126 PASS (shadow iPhone + walk while open, ESC menu header/footer, centred info card, soft quickbar, eye icon centred,"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
