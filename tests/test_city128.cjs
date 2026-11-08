/* City suite on index128 against the real runner128: the 127 checks on loader128/bridge128/client128,
 * plus the wallet published to the bridge cells and a native spend settled through /api/cash128/native. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).split('loader-pn-online-v16-gameplay-v127.js').join('loader-pn-online-v16-gameplay-v128.js').split("'run_gameplay_live_v122.py'").join("'run_gameplay_live_v128.py'").split("'-v122.db'").join("'-v128.db'").split('/pn/fixes126/client.js').join('/pn/fixes128/client.js');
 return text;};
const extra=String.raw`
const p128=await page.evaluate(()=>({loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v128.js'),client:[...document.scripts].some(s=>s.src.includes('/pn/fixes128/client.js'))}));
assert(p128.loader&&p128.client,'128 layer: '+JSON.stringify(p128));
const w128=await page.evaluate(()=>{const b=PAVGame.bridge,a=new Int32Array(b.memory.buffer,b.block,16384);return{wallet:a[13990],version:a[13991],shown:document.querySelector('.pn-money').title};});
assert(w128.version>0&&String.fromCharCode(36)+w128.wallet.toLocaleString('tr-TR')===w128.shown,'wallet in bridge cells: '+JSON.stringify(w128));
await page.evaluate(()=>{const b=PAVGame.bridge,a=new Int32Array(b.memory.buffer,b.block,16384);Atomics.add(a,13992,40);});
await page.waitForFunction(w=>{const b=PAVGame.bridge,a=new Int32Array(b.memory.buffer,b.block,16384);return a[13990]===w-40;},w128.wallet,{timeout:8000});
assert.equal(await page.evaluate(()=>new Int32Array(PAVGame.bridge.memory.buffer,PAVGame.bridge.block,16384)[13992]),0,'spend settled');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city128 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city127.cjs','utf8'),[
 ["const p127=await page.evaluate(","\n"+extra+"\nconst p127=await page.evaluate("],
 ["release127-checks","release128-checks"],["index127.html","index128.html"],
 ["\"'127 PASS (bridge127","\"'128 PASS (runner128 native cash settled from bridge cells, client128, bridge127"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
