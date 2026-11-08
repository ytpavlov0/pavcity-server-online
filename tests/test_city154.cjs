/* City suite on index154: test_city153 (and everything it runs) retargeted to release154-checks/index154.html and the
 * 154 loader (bridge v154: combat/vehicle sync). */
const fs=require('fs');
const extra=String.raw`
const p154=await page.evaluate(()=>document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v154.js'));assert(p154,'154 loader');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b,all])=>{if(!t.includes(a))throw Error('city154 retarget missing: '+a);return all?t.split(a).join(b):t.replace(a,b);},text);
const source=swap(fs.readFileSync('tests/test_city153.cjs','utf8'),[
 ["loader-pn-online-v16-gameplay-v153.js","loader-pn-online-v16-gameplay-v154.js",true],
 ["release153-checks","release154-checks",true],["index153.html","index154.html",true],
 ["const p153=await page.evaluate(",extra+"const p153=await page.evaluate("],
 ["\"'153 PASS (boot packs","\"'154 PASS (bridge154 combat/vehicle sync; boot packs"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
