/* City suite on index110 + 110 client checks: the chat frame is the restyled one, hud110 is
 * loaded, and closing the tab removes the player from the city at once instead of after the
 * 30 s presence timeout. Reuses the 109 chain; the base suite gains the extra steps. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
assert(await page.evaluate(()=>[...document.scripts].some(s=>s.src.includes('/pn/fixes111/services-v111.js'))&&![...document.scripts].some(s=>s.src.includes('/pn/services-v61.js'))),'services111 replaces services61');
assert.equal(await page.evaluate(()=>document.querySelector('#pn-game iframe.pn-chat').getAttribute('src')),'/pn/fixes110/chat.html');
assert(await page.evaluate(()=>[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes110/hud110.css'))),'hud110 layer loaded');
const before110=(await (await fetch(origin+'/api/status')).json()).active_players;assert(before110>=1,'player is in the city: '+before110);
await page.close();await new Promise(r=>setTimeout(r,1500));
const after110=(await (await fetch(origin+'/api/status')).json()).active_players;assert.equal(after110,before110-1,'closing the tab leaves the city immediately');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(p.endsWith('tests/test_city100.cjs')){const anchor="fs.writeFileSync(O+'/city-http.json'";if(!text.includes(anchor))throw Error('city110 anchor missing');text=text.replace(anchor,extra+anchor);}
 return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city110 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city109.cjs','utf8'),[
 ["const O='backups/release109-checks'","const O='backups/release111-checks'"],
 ["O+'/index109.html'","O+'/index111.html'"],
 ["'backups/release109-checks'","'backups/release111-checks'"],
 ["'109 PASS (entry markers + ","'111 PASS (payday chime, tab-close leave, chat frame, hud110 + entry markers + "]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
