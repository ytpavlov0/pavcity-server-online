/* City suite on index158: test_city157 (and everything it runs) retargeted to release158-checks/index158.html, where
 * client158 replaces client157 and roster158 is loaded last; plus: roster158 installed (game.scoreboard replaced). */
const fs=require('fs');
const extra=String.raw`
const p158=await page.evaluate(()=>({client:[...document.scripts].some(s=>/\/pn\/fixes158\/client158\.js/.test(s.src)),old:[...document.scripts].some(s=>/\/pn\/fixes157\/client157\.js/.test(s.src)),roster:[...document.scripts].some(s=>/\/pn\/fixes158\/roster158\.js/.test(s.src)),api:!!window.PAVRoster158}));
assert(p158.client&&!p158.old&&p158.roster&&p158.api,'158 client158 + roster158: '+JSON.stringify(p158));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b,all])=>{if(!t.includes(a))throw Error('city158 retarget missing: '+a);return all?t.split(a).join(b):t.replace(a,b);},text);
const source=swap(fs.readFileSync('tests/test_city157.cjs','utf8'),[
 ["release157-checks","release158-checks",true],["index157.html","index158.html",true],
 [String.raw`\/pn\/fixes157\/client157\.js`,String.raw`\/pn\/fixes158\/client158\.js`,true],
 ["/pn/fixes157/client157.js","/pn/fixes158/client158.js",true],
 ["const p157=await page.evaluate(",extra+"const p157=await page.evaluate("],
 ["\"'157 PASS (client157 realtime channel;","\"'158 PASS (client158 ticker/ping/chat doorbell, roster158; client157 realtime channel;"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
