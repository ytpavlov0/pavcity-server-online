/* City suite on index135 against the real runner135: the 134 checks plus the club chip and people panel. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).split("'run_gameplay_live_v134.py'").join("'run_gameplay_live_v135.py'").split("'-v134.db'").join("'-v135.db'");
 return text;};
const extra=String.raw`
const p135=await page.evaluate(()=>({js:[...document.scripts].some(s=>s.src.includes('/pn/fixes135/ui135.js')),chip:!!document.querySelector('.club135')}));
assert(p135.js&&p135.chip,'135 layer: '+JSON.stringify(p135));
await page.route('**/api/npc135/near',r=>r.fulfill({json:{success:true,club:{key:'unicorn',name:'Vanilla Unicorn'},people:[{id:'selin',name:'Selin Aydın',met:true,closeness:42,number:70000001},{id:'melis',name:'Melis Kara',met:false,closeness:0,number:null}]}}));
await page.evaluate(()=>{for(const o of document.querySelectorAll('.rp-overlay,.pav-overlay'))o.remove();PAVGame.uiOpen=false;const b=PAVGame.bridge,f=new Float32Array(b.memory.buffer,b.block,16384);f[16]=128;f[17]=-1298;f[18]=29.2;});
await page.waitForFunction(()=>{const c=document.querySelector('.club135');return c&&!c.hidden&&/Vanilla Unicorn/.test(c.textContent);},null,{timeout:8000});
await page.click('.club135');await page.waitForSelector('.pav-club135 [data-meet="melis"]');
assert.equal(await page.evaluate(()=>document.querySelectorAll('.pav-club135 article').length),2);
await page.screenshot({path:O+'/club135.png'});await page.evaluate(()=>PAVGame.closeRP?.());await page.unroute('**/api/npc135/near');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city135 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city134.cjs','utf8'),[
 ["const p134=await page.evaluate(","\n"+extra+"\nconst p134=await page.evaluate("],
 ["release134-checks","release135-checks"],["index134.html","index135.html"],
 ["\"'134 PASS (AFK card","\"'135 PASS (club NPC panel on runner135, AFK card"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
