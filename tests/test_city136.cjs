/* City suite on index136 (loader/bridge136) against runner135: the 135 checks plus loader136 in the page. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 // Innermost hook: older suites' own loader retargets run after it, so every loader name maps to 136 here.
 if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).replace(/loader-pn-online-v16-gameplay-v1\d\d\.js/g,'loader-pn-online-v16-gameplay-v136.js');
 return text;};
const extra=String.raw`
const p136=await page.evaluate(()=>({loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v136.js'),old:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v134.js')}));
assert(p136.loader&&!p136.old,'136 loader: '+JSON.stringify(p136));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city136 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city135.cjs','utf8'),[
 ["const p135=await page.evaluate(","\n"+extra+"\nconst p135=await page.evaluate("],
 ["release135-checks","release136-checks"],["index135.html","index136.html"],
 ["\"'135 PASS (club NPC panel on runner135","\"'136 PASS (loader/bridge136 hotfix, club NPC panel on runner135"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
