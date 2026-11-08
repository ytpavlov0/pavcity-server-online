/* City suite on index114 against the real runner114 chain: the 113/112/... checks plus the
 * admin panel end to end — the city user is made staff in SQL, the YETKİLİ button appears,
 * F9 opens the panel with the real player list, a player's actions open, staff chat round
 * trips through /a, and Escape closes it. Screenshots are kept for visual review. */
const fs=require('fs'),cp=require('child_process');const read=fs.readFileSync;
// Runner swap at spawn time (city112 rewrites runner99 → runner108 in source; 114 needs runner114).
const to114=args=>(args||[]).map(a=>String(a).replace('run_gameplay_live_v108.py','run_gameplay_live_v114.py').replace(/-v108\.db$/,'-v114.db'));
const spawn0=cp.spawn,exec0=cp.execFileSync;cp.spawn=(cmd,args,opts)=>spawn0(cmd,to114(args),opts);cp.execFileSync=(cmd,args,opts)=>exec0(cmd,to114(args),opts);
const extra=String.raw`
assert(await page.evaluate(()=>[...document.scripts].some(s=>s.src.includes('/pn/fixes114/client.js'))&&[...document.scripts].some(s=>s.src.includes('/pn/fixes114/admin114.js'))),'client114 + admin114 loaded');
assert(await page.evaluate(()=>document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v114.js')),'loader114 referenced');
assert(await page.evaluate(()=>document.querySelector('.a114-fab')?.hidden===true),'players do not see the staff button');
execFileSync('runtime/python.exe',['-X','utf8','-c',"import sqlite3,sys;d=sqlite3.connect(sys.argv[1]);d.execute('CREATE TABLE IF NOT EXISTS pn_staff(user_id INTEGER PRIMARY KEY,rank INTEGER NOT NULL CHECK(rank BETWEEN 1 AND 3))');d.execute('INSERT OR REPLACE INTO pn_staff SELECT id,2 FROM users');d.commit()",db]);
await page.evaluate(()=>PAVGame.adminPanel114.refresh());await page.waitForSelector('.a114-fab:not([hidden])',{timeout:8000});
await page.keyboard.press('F9');await page.waitForSelector('.a114:not([hidden]) .a114-row',{timeout:8000});
assert(await page.evaluate(()=>PAVGame.uiOpen===true),'game input released while the panel is open');
await page.click('.a114-row');await page.waitForSelector('.a114-detail .a114-quick button');
const panel114=await page.evaluate(()=>({rows:document.querySelectorAll('.a114-row').length,quick:[...document.querySelectorAll('.a114-quick button')].map(b=>b.textContent),rank:document.querySelector('.a114-rank').textContent,forms:document.querySelectorAll('.a114-form').length}));
assert(panel114.rows>=1&&panel114.quick.includes('Can doldur')&&/Yönetici/.test(panel114.rank)&&panel114.forms===4,'panel 114: '+JSON.stringify(panel114));
await page.waitForTimeout(250);await page.screenshot({path:O+'/admin114.png'});
await page.click('.a114-tabs button:nth-child(2)');await page.fill('.a114-say input','Yetkili sohbeti testi');await page.press('.a114-say input','Enter');
await page.waitForFunction(()=>[...document.querySelectorAll('.a114-log span')].some(n=>n.textContent==='Yetkili sohbeti testi'),null,{timeout:8000});
await page.waitForTimeout(250);await page.screenshot({path:O+'/admin114-chat.png'});
await page.keyboard.press('Escape');assert(await page.evaluate(()=>document.querySelector('.a114').hidden&&PAVGame.uiOpen===false),'Escape closes the panel');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(p.endsWith('tests/test_city100.cjs')){const anchor="fs.writeFileSync(O+'/city-http.json'";if(!text.includes(anchor))throw Error('city114 anchor missing');text=text.replace(anchor,extra+anchor);}
 return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city114 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city113.cjs','utf8'),[
 ["[\"release112-checks\",\"release113-checks\"]","[\"release112-checks\",\"release114-checks\"]"],
 ["[\"index112.html\",\"index113.html\"]","[\"index112.html\",\"index114.html\"]"],
 ["await page.screenshot({path:O+'/toasts113.png'});","await page.screenshot({path:O+'/toasts114.png'});"],
 ["[\"'112 PASS (runner108,\",\"'113 PASS (typed notifications, PM ding, runner108,\"]","[\"'112 PASS (runner108,\",\"'114 PASS (admin panel + staff chat on runner114, typed notifications, PM ding,\"]"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
