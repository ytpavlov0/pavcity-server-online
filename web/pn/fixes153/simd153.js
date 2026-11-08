/* PAVCITY 153: the engine is built with WebAssembly SIMD. A browser that cannot run it stopped only after the 19 MB engine
 * download with "CompileError: WebAssembly.instantiate(): Wasm SIMD unsupported" and no hint (player report, 31 Oct 2026).
 * V8 refuses SIMD when the CPU lacks SSE4.1 (pre-2008 Intel, AMD Phenom/Athlon II), when the browser is old, or when
 * JavaScript optimisation is turned off (Edge "enhanced security", some antivirus browsers). A 30-byte probe module tells
 * at once: the entry screen shows the reason before login, and the "Yükleme durdu" card lists what to try. */
(()=>{'use strict';
// (module (func (result v128) i32.const 0 i8x16.splat i8x16.popcnt))
const PROBE=new Uint8Array([0,97,115,109,1,0,0,0,1,5,1,96,0,1,123,3,2,1,0,10,10,1,8,0,65,0,253,15,253,98,11]);
let ok=true;try{ok=typeof WebAssembly==='object'&&WebAssembly.validate(PROBE);}catch(e){ok=false;}
window.PAVSimd153={supported:ok};
const STEPS=['Tarayıcını güncelle: Chrome veya Edge › Ayarlar › Hakkında, güncelleme bitince tarayıcıyı yeniden başlat.',
 'Edge kullanıyorsan: Ayarlar › Gizlilik, arama ve hizmetler › “Web’de güvenliğinizi artırın” seçeneğini kapat (ya da bu siteyi özel durumlara ekle). Bu mod oyunun motorunu çalıştıran hızlandırmayı kapatır.',
 'Antivirüsün “güvenli tarayıcı” penceresinde değil, normal Chrome/Edge penceresinde aç. Opera GX, Yandex gibi tarayıcılarda olmuyorsa Chrome dene.',
 'Hâlâ olmuyorsa işlemcin oyunun gerektirdiği komutları (SSE4.1) desteklemiyor olabilir — çok eski işlemcilerde (2008 öncesi, AMD Phenom / Athlon II) oyun çalışmaz; başka bir bilgisayar dene.'];
const SIMD=/simd|webassembly\.instantiate|compileerror/i;
function box(title){const b=document.createElement('div');b.className='simd153';
 b.style.cssText='margin:12px 0 14px;padding:12px 14px;border-radius:12px;background:rgba(255,255,255,.05);border:1px solid rgba(255,95,168,.3);text-align:left';
 b.innerHTML='<b style="display:block;margin-bottom:6px;font-size:13px;color:#ffb36b"></b><ol style="margin:0;padding-left:18px;font-size:12.5px;line-height:1.45;color:rgba(246,241,255,.85)">'+STEPS.map(()=>'<li style="margin:3px 0"></li>').join('')+'</ol>';
 b.querySelector('b').textContent=title;b.querySelectorAll('li').forEach((li,i)=>li.textContent=STEPS[i]);return b;}
function onCard(panel){const reason=panel.querySelector('.reason');if(!reason||panel.querySelector('.simd153')||!SIMD.test(reason.textContent))return;
 reason.after(box('Tarayıcın oyun motorunu çalıştıramıyor (WebAssembly SIMD) · şunları dene'));}
function banner(){if(ok||document.getElementById('pav-simd153'))return;const host=document.body;if(!host)return;
 const wrap=document.createElement('div');wrap.id='pav-simd153';wrap.setAttribute('role','alert');
 wrap.style.cssText='position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:2147483646;width:min(560px,calc(100vw - 32px));padding:14px 16px 4px;border-radius:14px;background:rgba(20,12,32,.96);border:1px solid rgba(255,95,168,.55);color:#fff;font:500 13px/1.4 Segoe UI,system-ui,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.5)';
 const head=document.createElement('div');head.style.cssText='font-weight:700;font-size:14px';head.textContent='Bu tarayıcı oyunu çalıştıramaz';
 const close=document.createElement('button');close.type='button';close.textContent='×';close.setAttribute('aria-label','Kapat');close.style.cssText='position:absolute;right:10px;top:8px;background:none;border:0;color:#fff;font-size:20px;cursor:pointer';close.onclick=()=>wrap.remove();
 wrap.append(close,head,box('Oyun motoru WebAssembly SIMD gerektiriyor; bu tarayıcıda kapalı. Şunları dene:'));host.appendChild(wrap);}
const scan=()=>{const panel=document.getElementById('pav-recovery95');if(panel)onCard(panel);banner();};
new MutationObserver(scan).observe(document.documentElement,{childList:true,subtree:true,characterData:true});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan,{once:true});else scan();
})();
