/* City suite on index137 against runner135: the 136 checks plus the chat frame staying put while the input opens. */
const fs=require('fs');
const extra=String.raw`
const p137=await page.evaluate(()=>({js:[...document.scripts].some(s=>s.src.includes('/pn/fixes137/ui137.js'))}));
assert(p137.js,'137 layer: '+JSON.stringify(p137));
const chat137=page.frames().find(f=>/\/pn\/fixes116\/chat\.html/.test(f.url()));assert(chat137,'chat frame');
await chat137.waitForFunction(()=>document.documentElement.dataset.chat137==='1'&&[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes137/chat137.css'))&&getComputedStyle(document.querySelector('.chat__input-block')).bottom==='6px',null,{timeout:10000});
const send137=m=>page.evaluate(m=>document.querySelector('#pn-game .pn-chat').contentWindow.postMessage(Object.assign({pnChat:true},m),location.origin),m);
await send137({type:'messages',messages:Array.from({length:30},(_,i)=>'sohbet satırı '+(i+1))});await page.waitForTimeout(300);
const look137=()=>chat137.evaluate(()=>{const c=document.querySelector('.chat'),m=document.querySelector('.chat__messages'),i=document.querySelector('.chat__input').getBoundingClientRect();return {chat:c.scrollTop,top:Math.round(m.getBoundingClientRect().top),height:Math.round(m.getBoundingClientRect().height),inputBottom:Math.round(i.bottom),frame:innerHeight};});
const shut137=await look137();await send137({type:'open',scope:'ic'});await page.waitForTimeout(300);await chat137.type('.chat__input','merhaba millet nasılsınız',{delay:3});const open137=await look137();
await send137({type:'close'});await page.waitForTimeout(200);
assert(open137.chat===0&&open137.top===shut137.top&&open137.height===shut137.height&&open137.inputBottom<=open137.frame,'137 chat log moved: '+JSON.stringify({shut137,open137}));
await page.evaluate(()=>{PAVGame.uiOpen=false;});
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city137 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city136.cjs','utf8'),[
 ["const p136=await page.evaluate(","\n"+extra+"\nconst p136=await page.evaluate("],
 ["release136-checks","release137-checks"],["index136.html","index137.html"],
 ["\"'136 PASS (loader/bridge136 hotfix","\"'137 PASS (chat log fixed while typing, loader/bridge136 hotfix"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
