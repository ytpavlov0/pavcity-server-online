/* City suite on index155: test_city154 (and everything it runs) retargeted to release155-checks/index155.html and the
 * 155 loader (wgpu_worker v56: 3D texture views, no fatal stop on a 3D SRV left in a 2D slot). */
const fs=require('fs');
const extra=String.raw`
const p155=await page.evaluate(()=>document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v155.js'));assert(p155,'155 loader');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b,all])=>{if(!t.includes(a))throw Error('city155 retarget missing: '+a);return all?t.split(a).join(b):t.replace(a,b);},text);
const source=swap(fs.readFileSync('tests/test_city154.cjs','utf8'),[
 ["loader-pn-online-v16-gameplay-v154.js","loader-pn-online-v16-gameplay-v155.js",true],
 ["release154-checks","release155-checks",true],["index154.html","index155.html",true],
 ["const p154=await page.evaluate(",extra+"const p154=await page.evaluate("],
 ["\"'154 PASS (bridge154 combat/vehicle sync; boot packs","\"'155 PASS (gpu worker v56 3D views; bridge154 combat/vehicle sync; boot packs"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
