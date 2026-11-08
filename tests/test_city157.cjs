/* City suite on index157: test_city156 (and everything it runs) retargeted to release157-checks/index157.html, where
 * client157 (realtime channel) replaces client153. Older suites assert the client by name: the fs handed down the chain
 * renames client153 -> client157 inside test_city153's text (its own check and the asset-rename hook it added).
 * The suite's backend fixture is an older runner without rt172 tickets, so this run also proves the HTTP-only path. */
const fs=require('fs');
const extra=String.raw`
const p157=await page.evaluate(()=>({client:[...document.scripts].some(s=>/\/pn\/fixes157\/client157\.js/.test(s.src)),old:[...document.scripts].some(s=>/\/pn\/fixes153\/client153\.js/.test(s.src)),rt:typeof self.__rt157}));
assert(p157.client&&!p157.old,'157 client157 replaces client153: '+JSON.stringify(p157));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b,all])=>{if(!t.includes(a))throw Error('city157 retarget missing: '+a);return all?t.split(a).join(b):t.replace(a,b);},text);
const deep={'tests/test_city153.cjs':[[String.raw`\/pn\/fixes153\/client153\.js`,String.raw`\/pn\/fixes157\/client157\.js`,true],[".join('/pn/fixes153/client153.js');}",".join('/pn/fixes157/client157.js');}"]]};
const fs157=Object.assign(Object.create(fs),{readFileSync(p,...rest){const out=fs.readFileSync(p,...rest);const key=String(p).replace(/\\/g,'/');const pairs=deep[key];return pairs&&typeof out==='string'?swap(out,pairs):out;}});
const req157=m=>m==='fs'||m==='node:fs'?fs157:require(m);
const source=swap(fs.readFileSync('tests/test_city156.cjs','utf8'),[
 ["release156-checks","release157-checks",true],["index156.html","index157.html",true],
 ["const p156=await page.evaluate(",extra+"const p156=await page.evaluate("],
 ["\"'156 PASS (cheat key blocked","\"'157 PASS (client157 realtime channel; cheat key blocked"]
]);
new Function('require','__filename','__dirname',source)(req157,__filename,__dirname);
