/* City suite on index131 (runner130): the 130 checks on loader131/bridge131 plus ui131 — the inventory
 * opens with capacity bars, no debug ids and clean item tiles. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).split('loader-pn-online-v16-gameplay-v130.js').join('loader-pn-online-v16-gameplay-v131.js');
 return text;};
const extra=String.raw`
const p131=await page.evaluate(()=>({js:[...document.scripts].some(s=>s.src.includes('/pn/fixes131/ui131.js')),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes131/ui131.css')),loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v131.js')}));
assert(p131.js&&p131.css&&p131.loader,'131 layer: '+JSON.stringify(p131));
await page.evaluate(()=>{for(const o of document.querySelectorAll('.rp-overlay,.pav-overlay'))o.remove();PAVGame.uiOpen=false;});
await page.evaluate(()=>PAVGame.inventory?.());await page.waitForSelector('.pav-storage .pav-stock-cell');await page.waitForFunction(()=>document.querySelectorAll('.pav-storage .w131').length>=2,null,{timeout:4000});
const inv131=await page.evaluate(()=>{const s=document.querySelector('.pav-storage');const id=s.querySelector('.pav-stock-cell small');return{bars:s.querySelectorAll('.w131').length,width:getComputedStyle(s.querySelector('.w131 i')).width,idHidden:!id||getComputedStyle(id).display==='none',cols:getComputedStyle(s.querySelector('.pav-storage-layout')).gridTemplateColumns.split(' ').length};});
assert(inv131.bars>=2&&inv131.idHidden&&inv131.cols===3,'inventory 131: '+JSON.stringify(inv131));
await page.screenshot({path:O+'/inventory131.png'});await page.evaluate(()=>{for(const o of document.querySelectorAll('.rp-overlay,.pav-overlay'))o.remove();PAVGame.uiOpen=false;});
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city131 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city130.cjs','utf8'),[
 ["const p130=await page.evaluate(","\n"+extra+"\nconst p130=await page.evaluate("],
 ["release130-checks","release131-checks"],["index130.html","index131.html"],
 ["\"'130 PASS (character history","\"'131 PASS (inventory look + hidden native hints, character history"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
