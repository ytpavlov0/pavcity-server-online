/* City suite on index117 against the real runner117 chain: the 116 checks plus client117/ui117
 * loaded, syncs carrying voice117 with the microphone pill wired, and the TAB list opening in the
 * middle as blurred glass with the vignette sliding in and out. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
assert(await page.evaluate(()=>[...document.scripts].some(s=>s.src.includes('/pn/fixes117/client.js'))&&[...document.scripts].some(s=>s.src.includes('/pn/fixes117/ui117.js'))),'client117 + ui117 loaded');
assert(await page.evaluate(()=>document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v117.js')),'loader117 referenced');
const v117=await page.evaluate(()=>new Promise(r=>{const t=setTimeout(()=>r(null),4000);addEventListener('pav-game-data',e=>{if(e.detail?.voice117){clearTimeout(t);r(e.detail.voice117);}});}));
assert(v117&&typeof v117.locked==='boolean'&&v117.required===900,'syncs carry voice117: '+JSON.stringify(v117));
assert(await page.evaluate(()=>!!document.querySelector('.m117')),'microphone pill installed');
await page.evaluate(()=>PAVGame.scoreboard());await page.waitForSelector('.p85-scoreboard .p85-roster article',{timeout:8000});await page.waitForSelector('.v117.in',{timeout:3000});await page.waitForTimeout(450);
const tab117=await page.evaluate(()=>{const b=document.querySelector('.p85-scoreboard'),r=b.getBoundingClientRect(),s=getComputedStyle(b);return{cx:Math.round(r.left+r.width/2-innerWidth/2),cy:Math.round(r.top+r.height/2-innerHeight/2),blur:s.backdropFilter||s.webkitBackdropFilter,w:Math.round(r.width)};});
assert(Math.abs(tab117.cx)<=2&&Math.abs(tab117.cy)<=2&&/blur/.test(tab117.blur)&&tab117.w<=520,'TAB centered blurred glass: '+JSON.stringify(tab117));
await page.screenshot({path:O+'/tab117.png'});
await page.evaluate(()=>PAVGame.scoreboard());await page.waitForTimeout(500);assert(!(await page.$('.v117')),'vignette slides out and is removed');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);if(String(path).replace(/\\/g,'/').endsWith('tests/test_city114.cjs'))text=String(text).split('/loader-pn-online-v16-gameplay-v114.js').join('/loader-pn-online-v16-gameplay-v117.js');return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city117 retarget missing: '+a);return t.split(a).join(b);},text);
let source=swap(read.call(fs,'tests/test_city116.cjs','utf8'),[
 ["'run_gameplay_live_v116.py'","'run_gameplay_live_v117.py'"],["'-v116.db'","'-v117.db'"],
 ["release116-checks","release117-checks"],["index116.html","index117.html"],
 ["/pn/fixes116/client.js","/pn/fixes117/client.js"],
 ["toasts116.png","toasts117.png"],["tab116.png","tab116b.png"],
 ["await page.click('.pav-help115 .rp-close');\n`;","await page.click('.pav-help115 .rp-close');"+extra+"`;"],
 ["\"'116 PASS (glass116,","\"'117 PASS (WASM117 loader, client117 back-off, ui117 mic pill + centered blurred TAB, glass116,"]
]);
// the 116 file's own loader114→116 hook must now point at 117
source=swap(source,[["'/loader-pn-online-v16-gameplay-v116.js'","'/loader-pn-online-v16-gameplay-v117.js'"]]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
