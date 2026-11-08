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
const p141=await page.evaluate(()=>({help:!!document.querySelector('script[src*="/pn/fixes141/entryhelp141.js"]'),fn:typeof window.PAVEntryHelp141,loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v141.js')}));
assert(p141.help&&p141.fn==='function'&&p141.loader,'141 layer: '+JSON.stringify(p141));
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city141 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city139.cjs','utf8'),[
 ["const p139=await page.evaluate(","\n"+extra+"\nconst p139=await page.evaluate("],
 ["release139-checks","release141-checks"],["index139.html","index141.html"],
 ["\"'139 PASS (native entry chevrons","\"'141 PASS (entry help, io-worker96 loader; native entry chevrons"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
