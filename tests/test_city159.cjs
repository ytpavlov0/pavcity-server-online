/* City suite on index159: test_city158 retargeted to release159-checks/index159.html (client159, roster159 loaded early
 * instead of roster158). test_city117 asserted the 158-era TAB width (<=520 px); 159 widens the sheet to 780 px. */
const fs=require('fs');
const extra=String.raw`
const p159=await page.evaluate(()=>({client:[...document.scripts].some(s=>/\/pn\/fixes159\/client159\.js/.test(s.src)),roster:[...document.scripts].some(s=>/\/pn\/fixes159\/roster159\.js/.test(s.src)),old:[...document.scripts].some(s=>/fixes158/.test(s.src)),api:!!window.PAVRoster159,chat:typeof self.__openChat159}));
assert(p159.client&&p159.roster&&!p159.old&&p159.api,'159 client159 + roster159: '+JSON.stringify(p159));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b,all])=>{if(!t.includes(a))throw Error('city159 retarget missing: '+a);return all?t.split(a).join(b):t.replace(a,b);},text);
const deep={'tests/test_city117.cjs':[['tab117.w<=520','tab117.w<=780']]};
const fs159=Object.assign(Object.create(fs),{readFileSync(p,...rest){const out=fs.readFileSync(p,...rest);const pairs=deep[String(p).replace(/\\/g,'/')];return pairs&&typeof out==='string'?swap(out,pairs):out;}});
const req159=m=>m==='fs'||m==='node:fs'?fs159:require(m);
const source=swap(fs.readFileSync('tests/test_city158.cjs','utf8'),[
 ["release158-checks","release159-checks",true],["index158.html","index159.html",true],
 [String.raw`\/pn\/fixes158\/client158\.js`,String.raw`\/pn\/fixes159\/client159\.js`,true],
 ["/pn/fixes158/client158.js","/pn/fixes159/client159.js",true],
 [String.raw`\/pn\/fixes158\/roster158\.js`,String.raw`\/pn\/fixes159\/roster159\.js`,true],
 ["window.PAVRoster158","window.PAVRoster159",true],
 ["const p158=await page.evaluate(",extra+"const p158=await page.evaluate("],
 ["\"'158 PASS (","\"'159 PASS (roster159 wide, TAB closes, click -> /pm; client159 realtime seat + instant chat; "]
]);
new Function('require','__filename','__dirname',source)(req159,__filename,__dirname);
