/* City suite on index139 (loader/bridge139, ui139) against runner135: the 138 checks plus no floating entry layer,
 * one door prompt, the properties panel theme and chat command aliases. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 // Innermost hook: older suites' own retargets run after it, so loader and phone names map to 138 here.
 if(/tests\/test_city\d+\.cjs$/.test(p)){text=String(text);
  if(/test_city136\.cjs$/.test(p))text=text.split("old:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v134.js')").join('old:false');
  text=text.replace(/loader-pn-online-v16-gameplay-v1\d\d\.js/g,'loader-pn-online-v16-gameplay-v139.js').replace(/\/pn\/fixes1(26|32)\/phone1(26|32)\.js/g,'/pn/fixes138/phone138.js');}
 return text;};
const extra=String.raw`
const p139=await page.evaluate(()=>({ui:[...document.scripts].some(s=>s.src.includes('/pn/fixes139/ui139.js')),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes139/ui139.css')),layer:getComputedStyle(document.querySelector('#pn-game .e127-layer')||document.body).display,loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v139.js')}));
assert(p139.ui&&p139.css&&p139.layer==='none'&&p139.loader,'139 layer: '+JSON.stringify(p139));
const merged139=await page.evaluate(async()=>{const hud=PAVGame.hud;let door=hud.querySelector('.p72-door'),hold=hud.querySelector('.pav-hold-prompt');const made=[];
 if(!door){door=document.createElement('aside');door.className='p72-door';hud.append(door);made.push(door);}if(!hold){hold=document.createElement('div');hold.className='pav-hold-prompt';hold.innerHTML='<span></span><b></b>';hud.append(hold);made.push(hold);}
 // Their own loops rewrite hidden/text every frame: pin both for the check, then drop the pins.
 const pin=(el,k,v)=>Object.defineProperty(el,k,{configurable:true,get:()=>v,set(){}});pin(door,'hidden',false);pin(hold,'hidden',false);pin(door,'textContent','tes · Kapı · 1.6 m · K: Kilidi aç');
 await new Promise(r=>setTimeout(r,400));const r={doorShown:!door.classList.contains('merged139'),extra:hold.querySelector('span').dataset.extra139};
 delete door.hidden;delete hold.hidden;delete door.textContent;for(const m of made)m.remove();return r;});
assert(!merged139.doorShown&&merged139.extra===' · K: Kilidi aç','139 one door prompt: '+JSON.stringify(merged139));
const chat139=page.frames().find(f=>/\/pn\/fixes116\/chat\.html/.test(f.url()));await chat139.waitForFunction(()=>document.documentElement.dataset.chat139==='1',null,{timeout:10000});
const alias139=await chat139.evaluate(()=>{const i=document.querySelector('.chat__input');const old=i.value;i.value='/meslekler';window.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:13,bubbles:true}));const v=i.value;i.value=old;return v;});
assert.equal(alias139,'/meslek','139 /meslekler alias');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city139 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city138.cjs','utf8'),[
 ["const p138=await page.evaluate(","\n"+extra+"\nconst p138=await page.evaluate("],
 ["release138-checks","release139-checks"],["index138.html","index139.html"],
 ["\"'138 PASS (phone styled on first open","\"'139 PASS (native entry chevrons, one door prompt, properties theme, /meslekler; phone styled on first open"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
