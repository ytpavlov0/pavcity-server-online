/* City suite on index132 against the real runner132: the 131 checks with phone132 instead of phone126,
 * plus the Gruplar app (list, WhatsApp-style thread) on fixture group data. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).split("'run_gameplay_live_v130.py'").join("'run_gameplay_live_v132.py'").split("'-v130.db'").join("'-v132.db'").split('/pn/fixes126/phone126.js').join('/pn/fixes132/phone132.js').split('ph126.apps===12').join('ph126.apps===13');
 return text;};
const extra=String.raw`
const now132=Math.floor(Date.now()/1000);
await page.route('**/api/phone/status',r=>r.fulfill({json:{success:true,has_phone:true,number:21283414,contacts:[{name:'Mert Kaya',number:21000002}],messages:[],unread:0,call:null,call_history:[],bank:100,cash:5000}}));
await page.route('**/api/groups132/list',r=>r.fulfill({json:{success:true,unread:2,groups:[{id:7,name:'Galeri Ekibi',admin:true,members:4,unread:2,last:{name:'Mert Kaya',body:'Tamam, geliyorum.',created:now132-120,mine:false}},{id:8,name:'LSPD Devriye',admin:false,members:9,unread:0,last:{name:'Sen',body:'Bölge temiz.',created:now132-7200,mine:true}}]}}));
await page.route('**/api/groups132/thread',r=>r.fulfill({json:{success:true,id:7,name:'Galeri Ekibi',admin:true,members:[{number:21283414,name:'Visitor Fixture',admin:true},{number:21000002,name:'Mert Kaya',admin:false}],messages:[{id:1,char_id:0,name:'Sistem',body:'Visitor Fixture grubu oluşturdu.',created:now132-900,mine:false,system:true},{id:2,char_id:5,name:'Mert Kaya',body:'Akşam 8’de galeride buluşalım mı?',created:now132-300,mine:false,system:false},{id:3,char_id:1,name:'Visitor Fixture',body:'Olur, Banshee’yi getiriyorum.',created:now132-200,mine:true,system:false},{id:4,char_id:5,name:'Mert Kaya',body:'Tamam, geliyorum.',created:now132-120,mine:false,system:false}]}}));
await page.evaluate(()=>{sessionStorage.setItem('pav-phone-unlocked-'+PAVGame.character.id,'1');});
await page.evaluate(()=>PAVGame.phone());await page.waitForFunction(()=>document.getElementById('pav-iphone126')?.shadowRoot?.querySelector('.grid .app'));
await page.evaluate(()=>PAVGame.phone126.navigate('groups'));await page.waitForFunction(()=>document.getElementById('pav-iphone126').shadowRoot.querySelector('[data-group]'));
const g132=await page.evaluate(()=>{const r=document.getElementById('pav-iphone126').shadowRoot;return{rows:r.querySelectorAll('[data-group]').length,badge:r.querySelector('.wa-count')?.textContent};});
assert(g132.rows===2&&g132.badge==='2','groups list: '+JSON.stringify(g132));await page.screenshot({path:O+'/groups132.png'});
await page.evaluate(()=>document.getElementById('pav-iphone126').shadowRoot.querySelector('[data-group="7"]').click());await page.waitForFunction(()=>document.getElementById('pav-iphone126').shadowRoot.querySelector('.wa-msg'));
const t132=await page.evaluate(()=>{const r=document.getElementById('pav-iphone126').shadowRoot;return{me:r.querySelectorAll('.wa-msg.me').length,them:r.querySelectorAll('.wa-msg.them').length,sys:r.querySelectorAll('.wa-sys').length,names:[...r.querySelectorAll('.wa-msg b')].map(b=>b.textContent)};});
assert(t132.me===1&&t132.them===2&&t132.sys===1&&t132.names.join()==='Mert Kaya,Mert Kaya','group thread: '+JSON.stringify(t132));
await page.screenshot({path:O+'/group132-thread.png'});
await page.evaluate(()=>PAVGame.phone());await page.unroute('**/api/phone/status');await page.unroute('**/api/groups132/list');await page.unroute('**/api/groups132/thread');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city132 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city131.cjs','utf8'),[
 ["const p131=await page.evaluate(","\n"+extra+"\nconst p131=await page.evaluate("],
 ["release131-checks","release132-checks"],["index131.html","index132.html"],
 ["\"'131 PASS (inventory look","\"'132 PASS (phone132 Gruplar on runner132, inventory look"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
