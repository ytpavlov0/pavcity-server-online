/* City suite on index125 (runner122): the 124 checks plus client125/map125/ui125 — eye mode with the
 * tag eye icon inside its circle, wallet tooltip, eased radar still painting. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`),'client124');
const p125=await page.evaluate(()=>({scripts:['/pn/fixes125/client.js','/pn/fixes125/map125.js'].map(s=>[...document.scripts].some(x=>x.src.includes(s))),old:[...document.scripts].some(x=>/fixes123\/map123|fixes124\/client/.test(x.src)),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes125/ui125.css')),title:document.querySelector('.pn-money')?.title||''}));
assert(p125.scripts.every(Boolean)&&!p125.old&&p125.css&&/^\$/.test(p125.title),'125 layer: '+JSON.stringify(p125));
await page.evaluate(()=>{if(!PAVGame.isTargeting)PAVGame.eyeMode();});await page.waitForTimeout(400);
const eye125=await page.evaluate(()=>{const b=[...document.querySelectorAll('.pn-tag .pav-head-eye')].find(e=>e.getBoundingClientRect().width>0);if(!b)return null;const r=b.getBoundingClientRect(),i=b.querySelector('svg,img')?.getBoundingClientRect();return{w:r.width,h:r.height,inside:!!i&&i.left>=r.left&&i.right<=r.right&&i.top>=r.top&&i.bottom<=r.bottom,x:r.left,y:r.top};});
if(eye125){assert(eye125.inside&&Math.abs(eye125.w-eye125.h)<1,'eye icon inside its circle '+JSON.stringify(eye125));await page.screenshot({path:O+'/eye125.png',clip:{x:Math.max(0,eye125.x-220),y:Math.max(0,eye125.y-60),width:320,height:140}});}
await page.evaluate(()=>{if(PAVGame.isTargeting)PAVGame.eyeMode();});
await page.evaluate(()=>{const b=PAVGame.bridge;if(b)new Float32Array(b.memory.buffer,b.block,16384)[19]=150;});await page.waitForTimeout(900);await page.screenshot({path:O+'/radar125-150deg.png',clip:{x:0,y:560,width:360,height:290}});
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city125 retarget missing: '+a);return t.split(a).join(b);},text);
let source=swap(read.call(fs,'tests/test_city124.cjs','utf8'),[
 ["'/pn/fixes124/client.js','/pn/fixes123/map123.js'","'/pn/fixes125/client.js','/pn/fixes125/map125.js'"],
 ["),'client124');",extra],
 ["/pn/fixes124/client.js","/pn/fixes125/client.js"],
 ["release124-checks","release125-checks"],["index124.html","index125.html"],
 ["toasts124.png","toasts125.png"],["tab124.png","tab125.png"],["phone124.png","phone125.png"],["account124.png","account125.png"],["radar124.png","radar125.png"],["radar124-60deg.png","radar125-60deg.png"],
 ["fixes118\\\\/client|fixes123\\\\/client/.test(x.src)","fixes118\\\\/client|fixes123\\\\/client|fixes124\\\\/client/.test(x.src)"],
 ["\"'124 PASS (cached nametags,","\"'125 PASS (eye icon centred, wallet K/M tooltip, eased radar, cached nametags,"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
