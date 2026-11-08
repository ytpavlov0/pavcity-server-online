/* City suite on index160: test_city159 retargeted to release160-checks/index160.html (client160 = client159 + position
 * jump / join spawn diagnostics to the server log). */
const fs=require('fs');
const swap=(text,pairs)=>pairs.reduce((t,[a,b,all])=>{if(!t.includes(a))throw Error('city160 retarget missing: '+a);return all?t.split(a).join(b):t.replace(a,b);},text);
const source=swap(fs.readFileSync('tests/test_city159.cjs','utf8'),[
 ["release159-checks","release160-checks",true],["index159.html","index160.html",true],
 [String.raw`\/pn\/fixes159\/client159\.js`,String.raw`\/pn\/fixes160\/client160\.js`,true],
 ["/pn/fixes159/client159.js","/pn/fixes160/client160.js",true],
 ["old:[...document.scripts].some(s=>/fixes158/.test(s.src))","old:[...document.scripts].some(s=>/fixes158|client159/.test(s.src))"],
 ["\"'159 PASS (","\"'160 PASS (client160 jump/spawn diagnostics; "]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
