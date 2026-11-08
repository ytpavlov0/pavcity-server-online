/* City suite on index123 against the real runner122 chain: the 121 checks plus the 123 performance
 * layer (client123, map123 heading-up radar, vehicle-points-v123, pc diagnostics v123, perf123) with
 * the radar still drawing and a screenshot of it. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
const p123=await page.evaluate(()=>({scripts:['/pn/fixes123/client.js','/pn/fixes123/map123.js','/pn/fixes123/vehicle-points-v123.js','/pn/fixes123/pc-diagnostics-v123.js','/pn/fixes123/perf123.js'].map(s=>[...document.scripts].some(x=>x.src.includes(s))),old:[...document.scripts].some(x=>/fixes106\/map\.js|vehicle-points-v112|pc-diagnostics-v51|fixes118\/client/.test(x.src)),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes123/perf123.css')),radar:!!document.querySelector('canvas.pav-map')}));
assert(p123.scripts.every(Boolean)&&!p123.old&&p123.css&&p123.radar,'123 layer: '+JSON.stringify(p123));
const rect123=await page.evaluate(()=>{const c=document.getElementById('canvas');const a=c.getBoundingClientRect(),b=c.getBoundingClientRect();return a===b&&a.width>0;});assert(rect123,'canvas rect cached');
await page.mouse.move(4,4);await page.waitForTimeout(1300);await page.screenshot({path:O+'/radar123.png',clip:{x:0,y:560,width:360,height:290}});
await page.evaluate(()=>{const b=PAVGame.bridge;if(b)new Float32Array(b.memory.buffer,b.block,16384)[19]=60;});await page.waitForTimeout(1300);await page.screenshot({path:O+'/radar123-60deg.png',clip:{x:0,y:560,width:360,height:290}});
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(p.endsWith('tests/test_city114.cjs'))text=String(text).split('/loader-pn-online-v16-gameplay-v114.js').join('/loader-pn-online-v16-gameplay-v119.js');
 if(p.endsWith('tests/test_city112.cjs'))text=String(text).split('/pn/fixes112/vehicle-points-v112.js').join('/pn/fixes123/vehicle-points-v123.js');
 if(p.endsWith('tests/test_city118.cjs'))text=String(text).split("'run_gameplay_live_v118.py'").join("'run_gameplay_live_v122.py'").split("'-v118.db'").join("'-v122.db'").split('/pn/fixes118/client.js').join('/pn/fixes123/client.js');
 return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city123 retarget missing: '+a);return t.split(a).join(b);},text);
let source=swap(read.call(fs,'tests/test_city121.cjs','utf8'),[
 ["release121-checks","release123-checks"],["index121.html","index123.html"],
 ["toasts121.png","toasts123.png"],["tab121.png","tab123.png"],["phone121.png","phone123.png"],["account121.png","account123.png"],
 ["await page.click('.pav-account121 .rp-close');","await page.click('.pav-account121 .rp-close');"+extra],
 ["\"'121 PASS (account settings on runner121,","\"'123 PASS (perf layer + heading-up radar on runner122, account settings,"]
]);
// city121 hooks city118 to runner121; 123 runs on runner122
source=swap(source,[["join(\"'run_gameplay_live_v121.py'\")","join(\"'run_gameplay_live_v122.py'\")"],["join(\"'-v121.db'\")","join(\"'-v122.db'\")"]]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);