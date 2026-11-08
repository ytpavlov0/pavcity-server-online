/* City suite on index119 (runner118, backend unchanged): the 118 checks plus loader119 and the
 * ui119 entry/creator glass stylesheet. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
assert(await page.evaluate(()=>document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v119.js')&&[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes119/ui119.css'))),'loader119 + ui119.css');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);if(String(path).replace(/\\/g,'/').endsWith('tests/test_city114.cjs'))text=String(text).split('/loader-pn-online-v16-gameplay-v114.js').join('/loader-pn-online-v16-gameplay-v119.js');return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city119 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city118.cjs','utf8'),[
 ["release118-checks","release119-checks"],["index118.html","index119.html"],
 ["'/loader-pn-online-v16-gameplay-v118.js'","'/loader-pn-online-v16-gameplay-v119.js'"],
 ["toasts118.png","toasts119.png"],["tab118.png","tab119.png"],
 ["assert(st118&&Array.isArray(st118.messages),'syncs carry server_time and messages');","assert(st118&&Array.isArray(st118.messages),'syncs carry server_time and messages');"+extra],
 ["\"'118 PASS (client118 chat cursor,","\"'119 PASS (loader119 entry arrows, ui119 entry glass, client118 chat cursor,"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);