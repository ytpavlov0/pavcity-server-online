/* City suite on index133 against the real runner133: the 132 checks plus the ui133 event chip. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).split("'run_gameplay_live_v132.py'").join("'run_gameplay_live_v133.py'").split("'-v132.db'").join("'-v133.db'");
 return text;};
const extra=String.raw`
const p133=await page.evaluate(()=>({js:[...document.scripts].some(s=>s.src.includes('/pn/fixes133/ui133.js')),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes133/ui133.css')),chip:!!document.querySelector('.ev133')}));
assert(p133.js&&p133.css&&p133.chip,'133 layer: '+JSON.stringify(p133));
await page.route('**/api/gta/sync',async r=>{const res=await r.fetch();const j=await res.json();if(j.success)j.event133={id:1,kind:'jobs',mult:2,ends:Date.now()/1000+1500,note:'Hafta sonu',now:Date.now()/1000};await r.fulfill({response:res,json:j});});
await page.waitForFunction(()=>{const c=document.querySelector('.ev133');return c&&!c.hidden&&/2x MESLEK/.test(c.textContent);},null,{timeout:8000});
await page.screenshot({path:O+'/event133.png',clip:{x:380,y:0,width:520,height:120}});await page.unroute('**/api/gta/sync');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city133 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city132.cjs','utf8'),[
 ["const now132=Math.floor(Date.now()/1000);","\n"+extra+"\nconst now132=Math.floor(Date.now()/1000);"],
 ["release132-checks","release133-checks"],["index132.html","index133.html"],
 ["\"'132 PASS (phone132","\"'133 PASS (event chip on runner133, phone132"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
