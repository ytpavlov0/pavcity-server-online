/* City suite on index112 against the production backend chain (runner108, not runner99):
 * the 111/110/109/106 checks plus chat frame 112, vehicle-points-v112 and hud112. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
assert(await page.evaluate(()=>[...document.scripts].some(s=>s.src.includes('/pn/fixes112/vehicle-points-v112.js'))&&![...document.scripts].some(s=>s.src.includes('/pn/vehicle-points-v29.js'))),'vehicle-points-v112 replaces v29');
assert(await page.evaluate(()=>[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes112/hud112.css'))),'hud112 loaded');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(p.endsWith('tests/test_city100.cjs')){
  for(const [a,b] of [['support/dev-tools/run_gameplay_live_v99.py','support/dev-tools/run_gameplay_live_v108.py'],["+'-v99.db'","+'-v108.db'"],['/pn/server-capabilities-v99.json','/pn/server-capabilities-v108.json']]){if(!text.includes(a))throw Error('city112 runner swap missing: '+a);text=text.split(a).join(b);}
  const anchor="fs.writeFileSync(O+'/city-http.json'";text=text.replace(anchor,extra+anchor);}
 return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city112 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city111.cjs','utf8'),[
 ["\"const O='backups/release111-checks'\"","\"const O='backups/release112-checks'\""],
 ["\"O+'/index111.html'\"","\"O+'/index112.html'\""],
 ["\"'backups/release111-checks'\"","\"'backups/release112-checks'\""],
 ["'/pn/fixes110/chat.html'","'/pn/fixes112/chat.html'"],
 ["'111 PASS (payday chime,","'112 PASS (runner108, part prompt, chat label, hud112, payday chime,"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
