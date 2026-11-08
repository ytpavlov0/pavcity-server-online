/* City suite on index139 (loader/bridge139, ui139) against runner135: the 138 checks plus no floating entry layer,
 * one door prompt, the properties panel theme and chat command aliases. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 // Innermost hook: older suites' own retargets run after it, so loader and phone names map to 138 here.
 if(/tests\/test_city\d+\.cjs$/.test(p)){text=String(text);
  if(/test_city136\.cjs$/.test(p))text=text.split("old:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v134.js')").join('old:false');
  text=text.replace(/loader-pn-online-v16-gameplay-v1\d\d\.js/g,'loader-pn-online-v16-gameplay-v146.js').replace(/\/pn\/fixes1(26|32)\/phone1(26|32)\.js/g,'/pn/fixes138/phone138.js');}
 return text;};
const extra=String.raw`
const p146=await page.evaluate(()=>({loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v146.js')}));
assert(p146.loader,'146 loader: '+JSON.stringify(p146));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city146 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city145.cjs','utf8'),[
 ["const p145=await page.evaluate(","\n"+extra+"\nconst p145=await page.evaluate("],
 ["release145-checks","release146-checks"],["index145.html","index146.html"],
 ["\"'145 PASS (remote on-foot","\"'146 PASS (vehicle interpolation + melee + density bridge146; remote on-foot"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
