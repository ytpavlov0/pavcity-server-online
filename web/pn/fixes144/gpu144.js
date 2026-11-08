/* PAVCITY 144: graphics-card failures at the entry screen.
 * - The environment check reports "no WebGPU adapter" in the entry alert line (not the stop card that gpuhelp140
 *   covers), so players saw the bare message while their character was being prepared: the steps now show right
 *   under that line, and the stop card's steps gain the Chrome "force high-performance GPU" flag (dual-GPU laptops).
 * - After a GPU hang / device loss the next starts (24 h) use the low graphics preset ("güvenli mod") without touching
 *   the player's saved settings; a chip on the entry screen says so and turns it off. */
(()=>{'use strict';
const KEY='pav-gpu-safe144',DAY=864e5;
const GPU=/webgpu|grafik aygıt|grafik işçisi|device_hung|device_removed|device lost|aygıt bağlantısı|bc sıkıştırmalı|filtrelenebilir 32 bit/i;
const HUNG=/grafik işçisi durdu|device_hung|device_removed|aygıt bağlantısı kesildi|device lost/i;
const FLAG='Adres çubuğuna chrome://flags/#force-high-performance-gpu yaz, “Enabled” seç ve “Relaunch”a bas (laptopta oyunu harici ekran kartıyla çalıştırır).';
const STEPS=['Chrome’u tamamen kapat (Görev Yöneticisi’nde chrome.exe kalmasın) ve yeniden aç. Ekran kartı bir kez takıldıysa Chrome bu siteyi tarayıcı kapanana kadar engeller.',FLAG,
 'Windows › Ayarlar › Sistem › Ekran › Grafik › Google Chrome › “Yüksek performans”. NVIDIA kartta ayrıca: NVIDIA Denetim Masası › 3D ayarları › chrome.exe › “Yüksek performanslı NVIDIA işlemci”.',
 'Laptop şarjda olsun; ekran kartı sürücüsünü güncelle ve bilgisayarı yeniden başlat.',
 'chrome://gpu sayfasında “WebGPU: Hardware accelerated” yazmalı.'];
const store={get(){try{const v=JSON.parse(localStorage.getItem(KEY)||'null');return v&&Date.now()-v.at<DAY?v:null;}catch{return null;}},set(){try{localStorage.setItem(KEY,JSON.stringify({at:Date.now()}));}catch{}},clear(){try{localStorage.removeItem(KEY);}catch{}}};
/* Safe mode: the engine reads its start-up quality from PAVGraphics79.args(); the low preset is used instead. */
function wrap(){const G=window.PAVGraphics79;if(!G?.args||G.args.safe144)return;const original=G.args;
 const args=function(){if(!store.get())return original.apply(this,arguments);const p=G.presets?.low||{quality:0,distance:.35,vehicle:.5,ped:.35,texture:384};
  return['-textureQuality=0','-shadowQuality=-1','-reflectionQuality=0','-particleQuality=0','-grassQuality=0','-lodScale='+p.distance,'-vehicleLodBias='+p.vehicle,'-pedLodBias='+p.ped,'-availablevidmem='+p.texture];};
 args.safe144=true;G.args=args;}
wrap();addEventListener('DOMContentLoaded',wrap,{once:true});
function box(){const b=document.createElement('div');b.className='gpu144';b.style.cssText='margin:10px 0 0;padding:12px 14px;border-radius:12px;background:rgba(255,255,255,.05);border:1px solid rgba(255,95,168,.35);text-align:left;font:500 12.5px/1.45 "Segoe UI",system-ui,sans-serif;color:rgba(246,241,255,.88)';
 b.innerHTML='<b style="display:block;margin-bottom:6px;font-size:13px;color:#ffb36b">Ekran kartı sorunu · şunları sırayla dene</b><ol style="margin:0;padding-left:18px"></ol><button type="button" style="margin-top:8px;padding:7px 12px;border-radius:9px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.06);color:#fff;font-weight:700;cursor:pointer">Tüm yardım</button>';
 const ol=b.querySelector('ol');for(const s of STEPS){const li=document.createElement('li');li.style.margin='3px 0';li.textContent=s;ol.append(li);}
 b.querySelector('button').onclick=()=>window.PAVEntryHelp141?.();return b;}
let hungSeen=false;
function scan(){
 for(const el of document.querySelectorAll('#yt-auth-modal .pav-alert,#yt-auth-modal .pav-preview-status')){const text=el.textContent||'',next=el.nextElementSibling,has=next?.classList.contains('gpu144');
  if(GPU.test(text)){if(!has)el.after(box());if(HUNG.test(text)&&!hungSeen){hungSeen=true;store.set();}}else if(has)next.remove();}
 const card=document.getElementById('pav-recovery95');
 if(card){const reason=card.querySelector('.reason')?.textContent||'';if(HUNG.test(reason)&&!hungSeen){hungSeen=true;store.set();}
  const ol=card.querySelector('.gpu140 ol');if(ol&&!ol.dataset.f144){ol.dataset.f144='1';const li=document.createElement('li');li.style.margin='3px 0';li.textContent=FLAG;ol.children[0]?ol.children[0].after(li):ol.append(li);}}
 const modal=document.getElementById('yt-auth-modal'),chip=document.getElementById('gpu-safe144');
 if(modal&&store.get()&&!chip){const c=document.createElement('div');c.id='gpu-safe144';c.setAttribute('role','status');
  c.style.cssText='position:fixed;left:16px;bottom:16px;z-index:2147482000;display:flex;align-items:center;gap:10px;max-width:min(520px,calc(100vw - 32px));padding:10px 12px;border-radius:14px;background:linear-gradient(180deg,rgba(28,18,43,.95),rgba(14,9,22,.95));border:1px solid rgba(255,179,107,.45);color:#f6f1ff;font:600 12.5px/1.35 "Segoe UI",system-ui,sans-serif;box-shadow:0 10px 26px rgba(0,0,0,.45)';
  c.innerHTML='<span>Güvenli grafik modu açık: önceki oturumda ekran kartı takıldı, oyun düşük ayarlarla başlayacak.</span><button type="button" style="flex:0 0 auto;padding:7px 10px;border-radius:9px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);color:#fff;font-weight:800;cursor:pointer">Normal moda dön</button>';
  c.querySelector('button').onclick=()=>{store.clear();c.remove();};document.body.append(c);}
 else if(chip&&(!modal||!store.get()))chip.remove();}
new MutationObserver(scan).observe(document.documentElement,{childList:true,subtree:true,characterData:true});scan();
window.PAVGpuSafe144={active:()=>!!store.get(),clear:()=>store.clear()};
})();
