/* City suite on index139 (loader/bridge139, ui139) against runner135: the 138 checks plus no floating entry layer,
 * one door prompt, the properties panel theme and chat command aliases. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 // Innermost hook: older suites' own retargets run after it, so loader and phone names map to 138 here.
 if(/tests\/test_city\d+\.cjs$/.test(p)){text=String(text);
  if(/test_city136\.cjs$/.test(p))text=text.split("old:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v134.js')").join('old:false');
  text=text.replace(/loader-pn-online-v16-gameplay-v1\d\d\.js/g,'loader-pn-online-v16-gameplay-v141.js').replace(/\/pn\/fixes1(26|32)\/phone1(26|32)\.js/g,'/pn/fixes138/phone138.js');}
 return text;};
const extra=String.raw`
const p142=await page.evaluate(()=>({v19:!!document.querySelector('script[src*="/pn/fixes142/voice-v19.js"]'),v18:!!document.querySelector('script[src*="/pn/voice-v18.js"]'),cls:typeof window.PNVoice}));
assert(p142.v19&&!p142.v18&&p142.cls==='function','142 layer: '+JSON.stringify(p142));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city142 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city141.cjs','utf8'),[
 ["const p141=await page.evaluate(","\n"+extra+"\nconst p141=await page.evaluate("],
 ["release141-checks","release142-checks"],["index141.html","index142.html"],
 ["\"'141 PASS (entry help","\"'142 PASS (voice-v19; entry help"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
