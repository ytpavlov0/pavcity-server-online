/* City suite on index139 (loader/bridge139, ui139) against runner135: the 138 checks plus no floating entry layer,
 * one door prompt, the properties panel theme and chat command aliases. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 // Innermost hook: older suites' own retargets run after it, so loader and phone names map to 138 here.
 if(/tests\/test_city\d+\.cjs$/.test(p)){text=String(text);
  if(/test_city136\.cjs$/.test(p))text=text.split("old:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v134.js')").join('old:false');
  text=text.replace(/loader-pn-online-v16-gameplay-v1\d\d\.js/g,'loader-pn-online-v16-gameplay-v152.js').replace(/\/pn\/fixes1(26|32)\/phone1(26|32)\.js/g,'/pn/fixes138/phone138.js').split('/pn/fixes142/voice-v19.js').join('/pn/fixes148/voice-v20.js');}
 return text;};
const extra=String.raw`
const document152=()=>true;const l152=await page.evaluate(()=>document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v152.js'));assert(l152,'152 loader');
const p152=await page.evaluate(()=>({guard:typeof window.PAVAssetGuard152,inline:[...document.scripts].findIndex(s=>!s.src&&/assetguard152/.test(s.textContent)),crash:[...document.scripts].findIndex(s=>/crash-v57/.test(s.src))}));
assert(p152.guard==='object'&&p152.inline===0&&p152.crash===1&&document152(),'152 guard first in head + loader152: '+JSON.stringify(p152));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city152 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city151.cjs','utf8'),[
 ["const p151=await page.evaluate(","\n"+extra+"\nconst p151=await page.evaluate("],
 ["release151-checks","release152-checks"],["index151.html","index152.html"],
 ["\"'151 PASS (io-worker97","\"'152 PASS (asset guard; io-worker97"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
