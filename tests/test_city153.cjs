/* City suite on index153: test_city152 (and everything it runs) retargeted to release153-checks/index153.html and the
 * 153 loader, plus: client153 replaces fixes128/client.js, simd153 is loaded and reports SIMD support. */
const fs=require('fs');
const extra=String.raw`
const p153=await page.evaluate(()=>({client:[...document.scripts].some(s=>/\/pn\/fixes153\/client153\.js/.test(s.src)),old:[...document.scripts].some(s=>/\/pn\/fixes128\/client\.js/.test(s.src)),simd:window.PAVSimd153&&window.PAVSimd153.supported,banner:!!document.getElementById('pav-simd153')}));
assert(p153.client&&!p153.old&&p153.simd===true&&!p153.banner,'153 client153 + simd153: '+JSON.stringify(p153));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b,all])=>{if(!t.includes(a))throw Error('city153 retarget missing: '+a);return all?t.split(a).join(b):t.replace(a,b);},text);
const source=swap(fs.readFileSync('tests/test_city152.cjs','utf8'),[
 ["loader-pn-online-v16-gameplay-v152.js","loader-pn-online-v16-gameplay-v153.js",true],
 // older suites (128 and those it retargets) assert the fixes128 client; 153 replaces it with client153
 [".split('/pn/fixes142/voice-v19.js').join('/pn/fixes148/voice-v20.js');}",".split('/pn/fixes142/voice-v19.js').join('/pn/fixes148/voice-v20.js').split('/pn/fixes128/client.js').join('/pn/fixes153/client153.js');}"],
 ["release152-checks","release153-checks",true],["index152.html","index153.html",true],
 ["const p152=await page.evaluate(",extra+"const p152=await page.evaluate("],
 ["\"'152 PASS (asset guard; io-worker97","\"'153 PASS (boot packs, client153, simd153; asset guard; io-worker97"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
