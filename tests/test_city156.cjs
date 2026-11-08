/* City suite on index156: test_city155 (and everything it runs) retargeted to release156-checks/index156.html and the
 * 156 loader (bridge v156: cheat-code control off), plus guard156 loaded before game-v29 and active. */
const fs=require('fs');
const extra=String.raw`
const p156=await page.evaluate(()=>{const s=[...document.scripts].map(x=>x.src);const g=s.findIndex(x=>/\/pn\/fixes156\/guard156\.js/.test(x)),m=s.findIndex(x=>/\/pn\/game-v29\.js/.test(x));return{loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v156.js'),order:g>=0&&m>g,guard:!!window.PAVGuard156,css:!!document.getElementById('pav-guard156')};});
assert(p156.loader&&p156.order&&p156.guard&&p156.css,'156 loader + guard156 before game-v29: '+JSON.stringify(p156));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b,all])=>{if(!t.includes(a))throw Error('city156 retarget missing: '+a);return all?t.split(a).join(b):t.replace(a,b);},text);
const source=swap(fs.readFileSync('tests/test_city155.cjs','utf8'),[
 ["loader-pn-online-v16-gameplay-v155.js","loader-pn-online-v16-gameplay-v156.js",true],
 ["release155-checks","release156-checks",true],["index155.html","index156.html",true],
 ["const p155=await page.evaluate(",extra+"const p155=await page.evaluate("],
 ["\"'155 PASS (gpu worker v56 3D views;","\"'156 PASS (cheat key blocked, Tab list scrolls; gpu worker v56 3D views;"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
