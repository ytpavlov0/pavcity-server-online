/* City suite on index130 against the real runner130: the 129 checks on loader130/bridge130 plus ui130 —
 * the character history panel from ESC › Karakter and the rental chip, panel, rent and countdown. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).split("'run_gameplay_live_v129.py'").join("'run_gameplay_live_v130.py'").split("'-v129.db'").join("'-v130.db'").split('loader-pn-online-v16-gameplay-v128.js').join('loader-pn-online-v16-gameplay-v130.js');
 return text;};
const extra=String.raw`
const p130=await page.evaluate(()=>({js:[...document.scripts].some(s=>s.src.includes('/pn/fixes130/ui130.js')),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes130/ui130.css')),loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v130.js'),api:typeof PAVGame.characterHistory130==='function'}));
assert(p130.js&&p130.css&&p130.loader&&p130.api,'130 layer: '+JSON.stringify(p130));
await page.evaluate(()=>{for(const o of document.querySelectorAll('.rp-overlay,.pav-overlay'))o.remove();PAVGame.uiOpen=false;});
await page.evaluate(()=>PAVGame.characterHistory130());await page.waitForSelector('.pav-c130 .c130-tiles');
const c130=await page.evaluate(()=>({tiles:document.querySelectorAll('.pav-c130 .c130-tiles article').length,secs:document.querySelectorAll('.pav-c130 .c130-sec').length,name:document.querySelector('.pav-c130 .c130-head h3').textContent}));
assert(c130.tiles===6&&c130.secs===6&&c130.name.length>1,'history panel: '+JSON.stringify(c130));
await page.screenshot({path:O+'/history130.png'});await page.evaluate(()=>PAVGame.closeRP?.());
await page.evaluate(()=>{const b=PAVGame.bridge,f=new Float32Array(b.memory.buffer,b.block,16384);f[16]=231.4;f[17]=-874.6;f[18]=30.5;});
await page.waitForFunction(()=>{const c=document.querySelector('.r130-chip');return c&&!c.hidden;},null,{timeout:8000});
await page.click('.r130-chip');await page.waitForSelector('.pav-r130 [data-m=faggio]');await page.screenshot({path:O+'/rental130.png'});
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city130 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city129.cjs','utf8'),[
 ["const p129=await page.evaluate(","\n"+extra+"\nconst p129=await page.evaluate("],
 ["release129-checks","release130-checks"],["index129.html","index130.html"],
 ["\"'129 PASS (hotwire panel","\"'130 PASS (character history + rental UI on runner130, hotwire panel"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
