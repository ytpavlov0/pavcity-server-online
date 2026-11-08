/* City suite on index120 (runner118): the 119 checks plus the iOS phone layer — a phone panel built
 * with phone.js' own classes takes the titanium frame, Dynamic Island, glass dock and iMessage
 * bubbles (screenshot kept), and the closed-phone peek slides in for a ringing call. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
assert(await page.evaluate(()=>[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes120/phone120.css'))&&[...document.scripts].some(s=>s.src.includes('/pn/fixes120/phone120.js'))),'phone120 loaded');
const ph120=await page.evaluate(()=>{const o=document.createElement('section');o.className='pav-overlay rp-overlay pav-source-phone pav-phone21 probe120';
 o.innerHTML='<div class="rp-window"><div class="rp-content"><div class="pav-phone-device"><section class="pav-phone-screen" data-app="sms" style="background:linear-gradient(160deg,#3b1d52,#120a1e 60%,#0b0614)"><div class="pav-phone-island"></div><div class="pav-phone-status"><span>21:47</span><span>LTE</span></div><h2 class="pav-phone-app-heading">Mesajlar</h2><div class="pav-phone-bubbles"><article class="received"><p>Akşam galeriye geliyor musun?</p><time>21:40</time></article><article class="sent"><p>Geliyorum, Tofaş’ı da getiriyorum 😄</p><time>21:41</time></article></div><nav class="pav-phone-dock"><button>A</button><button>B</button><button>C</button><button>D</button></nav><button class="pav-phone-home-indicator"></button></section></div></div></div>';
 PAVGame.hud.append(o);const d=getComputedStyle(o.querySelector('.pav-phone-device')),i=getComputedStyle(o.querySelector('.pav-phone-island')),s=getComputedStyle(o.querySelector('.pav-phone-bubbles>.sent')),k=getComputedStyle(o.querySelector('.pav-phone-dock'));
 return{radius:d.borderTopLeftRadius,island:i.width,sent:s.backgroundImage.includes('gradient'),dockBlur:k.backdropFilter||k.webkitBackdropFilter};});
assert(ph120.radius==='62px'&&ph120.island==='118px'&&ph120.sent&&/blur/.test(ph120.dockBlur),'iOS phone layer: '+JSON.stringify(ph120));
await page.waitForTimeout(500);await page.screenshot({path:O+'/phone120.png'});
await page.evaluate(()=>document.querySelector('.probe120')?.remove());
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);if(String(path).replace(/\\/g,'/').endsWith('tests/test_city114.cjs'))text=String(text).split('/loader-pn-online-v16-gameplay-v114.js').join('/loader-pn-online-v16-gameplay-v119.js');return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city120 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city119.cjs','utf8'),[
 ["release119-checks","release120-checks"],["index119.html","index120.html"],
 ["toasts119.png","toasts120.png"],["tab119.png","tab120.png"],
 ["'loader119 + ui119.css');","'loader119 + ui119.css');"+extra],
 ["\"'119 PASS (loader119 entry arrows,","\"'120 PASS (iOS phone layer + peek, loader119 entry arrows,"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);