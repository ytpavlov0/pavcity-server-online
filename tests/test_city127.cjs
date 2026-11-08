/* City suite on index127 (runner122): the 126 checks on loader127/bridge127 plus ui127 — projected
 * entry cells (written here, the engine is mocked) become floating glass icons with a close-range label. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');if(/tests\/test_city\d+\.cjs$/.test(p))text=String(text).split('loader-pn-online-v16-gameplay-v119.js').join('loader-pn-online-v16-gameplay-v127.js');return text;};
const extra=String.raw`
const p127=await page.evaluate(()=>({loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v127.js'),js:[...document.scripts].some(s=>s.src.includes('/pn/fixes127/ui127.js')),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes127/ui127.css')),layer:!!document.querySelector('.e127-layer')}));
assert(p127.loader&&p127.js&&p127.css&&p127.layer,'127 layer: '+JSON.stringify(p127));
await page.evaluate(()=>{const b=PAVGame.bridge,a=new Int32Array(b.memory.buffer,b.block,16384),f=new Float32Array(b.memory.buffer,b.block,16384);
 const put=(n,x,y,d,k)=>{const o=13960+n*5;a[o]=1;f[o+1]=x;f[o+2]=y;f[o+3]=d;a[o+4]=k;};put(0,.42,.55,4,6);put(1,.62,.48,16,4);put(2,.2,.5,30,3);
 window.__stamp127=setInterval(()=>Atomics.add(a,13959,1),50);});
await page.waitForTimeout(500);
const e127=await page.evaluate(()=>[...document.querySelectorAll('.e127')].filter(e=>!e.hidden).map(e=>{const r=e.querySelector('.e127-ic').getBoundingClientRect(),t=getComputedStyle(e.querySelector('.e127-tag'));return{kind:e.dataset.kind,x:r.left+r.width/2,y:r.bottom,close:e.classList.contains('close'),tag:t.opacity,title:e.querySelector('b').textContent,sub:e.querySelector('small').textContent};}));
assert(e127.length===3&&e127.some(e=>e.kind==='6'&&e.close&&e.sub.includes('E'))&&e127.some(e=>e.kind==='4'&&!e.close)&&e127.some(e=>e.kind==='3'),'entry icons: '+JSON.stringify(e127));
await page.screenshot({path:O+'/entries127.png'});
await page.evaluate(()=>clearInterval(window.__stamp127));await page.waitForTimeout(600);
assert.equal(await page.evaluate(()=>document.querySelector('.e127-layer').hidden),true,'icons hide when the bridge stops projecting');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city127 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city126.cjs','utf8'),[
 ["const p126=await page.evaluate(","\n"+extra+"\nconst p126=await page.evaluate("],
 ["release126-checks","release127-checks"],["index126.html","index127.html"],
 ["\"'126 PASS (shadow iPhone","\"'127 PASS (bridge127 ground rings + floating entry icons, shadow iPhone"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
