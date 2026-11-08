/* City suite on index124 (runner122): the 123 checks plus client124 (cached nametag children). */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
assert(await page.evaluate(()=>[...document.scripts].some(s=>s.src.includes('/pn/fixes124/client.js'))&&![...document.scripts].some(s=>s.src.includes('/pn/fixes123/client.js'))),'client124');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(p.endsWith('tests/test_city118.cjs'))text=String(text).split('/pn/fixes118/client.js').join('/pn/fixes124/client.js');
 return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city124 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city123.cjs','utf8'),[
 ["release123-checks","release124-checks"],["index123.html","index124.html"],
 ["toasts123.png","toasts124.png"],["tab123.png","tab124.png"],["phone123.png","phone124.png"],["account123.png","account124.png"],["radar123.png","radar124.png"],["radar123-60deg.png","radar124-60deg.png"],
 ["'/pn/fixes123/client.js','/pn/fixes123/map123.js'","'/pn/fixes124/client.js','/pn/fixes123/map123.js'"],
 ["fixes118\\/client/.test(x.src)","fixes118\\/client|fixes123\\/client/.test(x.src)"],
 ["assert(rect123,'canvas rect cached');","assert(rect123,'canvas rect cached');"+extra],
 ["\"'123 PASS (perf layer","\"'124 PASS (cached nametags, perf layer"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);