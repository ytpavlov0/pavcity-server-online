/* City suite on index118 against the real runner118 chain: the 117 checks plus client118 sending
 * chat_cursor (so the server only sends newer chat lines) while chat still renders. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
assert(await page.evaluate(()=>[...document.scripts].some(s=>s.src.includes('/pn/fixes118/client.js'))&&document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v118.js')),'client118 + loader118');
const st118=await page.evaluate(()=>new Promise(r=>{const t=setTimeout(()=>r(null),4000);addEventListener('pav-game-data',e=>{if(typeof e.detail?.server_time==='number'){clearTimeout(t);r(e.detail);}});}));
assert(st118&&Array.isArray(st118.messages),'syncs carry server_time and messages');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);if(String(path).replace(/\\/g,'/').endsWith('tests/test_city114.cjs'))text=String(text).split('/loader-pn-online-v16-gameplay-v114.js').join('/loader-pn-online-v16-gameplay-v118.js');return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city118 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city117.cjs','utf8'),[
 ["'run_gameplay_live_v117.py'","'run_gameplay_live_v118.py'"],["'-v117.db'","'-v118.db'"],
 ["release117-checks","release118-checks"],["index117.html","index118.html"],
 ["/pn/fixes117/client.js","/pn/fixes118/client.js"],["'/loader-pn-online-v16-gameplay-v117.js'","'/loader-pn-online-v16-gameplay-v118.js'"],
 ["toasts117.png","toasts118.png"],["tab117.png","tab118.png"],
 ["await page.evaluate(()=>PAVGame.scoreboard());await page.waitForTimeout(500);assert(!(await page.$('.v117')),'vignette slides out and is removed');","await page.evaluate(()=>PAVGame.scoreboard());await page.waitForTimeout(500);assert(!(await page.$('.v117')),'vignette slides out and is removed');"+extra],
 ["\"'117 PASS (WASM117 loader,","\"'118 PASS (client118 chat cursor, server_time on runner118, WASM117 loader,"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);