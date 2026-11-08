/* City suite on index134 against the real runner134: the 133 checks on loader134 plus the AFK card. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).split("'run_gameplay_live_v133.py'").join("'run_gameplay_live_v134.py'").split("'-v133.db'").join("'-v134.db'").split('loader-pn-online-v16-gameplay-v131.js').join('loader-pn-online-v16-gameplay-v134.js');
 return text;};
const extra=String.raw`
const p134=await page.evaluate(()=>({js:[...document.scripts].some(s=>s.src.includes('/pn/fixes134/ui134.js')),loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v134.js'),card:!!document.querySelector('.afk134')}));
assert(p134.js&&p134.loader&&p134.card,'134 layer: '+JSON.stringify(p134));
await page.route('**/api/gta/sync',async r=>{const res=await r.fetch();const j=await res.json();if(j.success)j.afk134={active:true,zone:'Vespucci AFK Bölgesi',seconds:1260,cap:14400,earned:3150,pp:2,next_pay:40,capped:false,alive:true,on_foot:true};await r.fulfill({response:res,json:j});});
await page.waitForFunction(()=>{const c=document.querySelector('.afk134');return c&&!c.hidden&&/21 dk/.test(c.textContent);},null,{timeout:8000});
await page.screenshot({path:O+'/afk134.png',clip:{x:420,y:60,width:440,height:200}});await page.unroute('**/api/gta/sync');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city134 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city133.cjs','utf8'),[
 ["const p133=await page.evaluate(","\n"+extra+"\nconst p133=await page.evaluate("],
 ["release133-checks","release134-checks"],["index133.html","index134.html"],
 ["\"'133 PASS (event chip","\"'134 PASS (AFK card + bridge134 on runner134, event chip"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
