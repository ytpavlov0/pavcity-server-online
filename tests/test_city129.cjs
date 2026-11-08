/* City suite on index129 against the real runner129: the 128 checks plus ui129 — engine start without a
 * key (server answer) opens the hotwire panel, and the panel closes cleanly. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).split("'run_gameplay_live_v128.py'").join("'run_gameplay_live_v129.py'").split("'-v128.db'").join("'-v129.db'");
 return text;};
const extra=String.raw`
const p129=await page.evaluate(()=>({js:[...document.scripts].some(s=>s.src.includes('/pn/fixes129/ui129.js')),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes129/ui129.css')),api:typeof PAVGame.hotwire129==='function'}));
assert(p129.js&&p129.css&&p129.api,'129 layer: '+JSON.stringify(p129));
await page.route('**/api/hotwire129/start',r=>r.fulfill({json:{success:true,id:1,challenge:'c',step:0,total:5,completed:false,wire:'yellow',ready_in_ms:0,timeout_ms:2400}}));
await page.route('**/api/hotwire129/cancel',r=>r.fulfill({json:{success:true}}));
await page.evaluate(()=>{PAVGame.vehicles.push({id:987654,model:'sultan',plate:'PN129UI',owner:0,locked:false});});
await page.evaluate(()=>PAVGame.hotwire129(987654));await page.waitForSelector('.pav-lockpick.hw129');
const hw=await page.evaluate(()=>{const p=document.querySelector('.pav-lockpick.hw129');return{failed:p.classList.contains('failed'),target:p.querySelector('.hw129-target b').textContent,wires:p.querySelectorAll('[data-wire]').length,car:p.querySelector('.pav-lockpick-car').textContent,ui:PAVGame.uiOpen};});
assert((hw.target==='Sarı kablo'||hw.failed)&&hw.wires===4&&/SULTAN/.test(hw.car)&&hw.ui,'hotwire panel: '+JSON.stringify(hw));
await page.screenshot({path:O+'/hotwire129.png'});
await page.waitForFunction(()=>document.querySelector('.pav-lockpick.hw129')?.classList.contains('failed'),null,{timeout:6000});
await page.click('.pav-lockpick.hw129 header button');assert.equal(await page.evaluate(()=>!!document.querySelector('.hw129')||PAVGame.uiOpen),false,'panel closed, keys back');
await page.unroute('**/api/hotwire129/start');await page.unroute('**/api/hotwire129/cancel');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city129 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city128.cjs','utf8'),[
 ["const p128=await page.evaluate(","\n"+extra+"\nconst p128=await page.evaluate("],
 ["release128-checks","release129-checks"],["index128.html","index129.html"],
 ["\"'128 PASS (runner128","\"'129 PASS (hotwire panel on runner129, runner128"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
