/* 198: after a graphics-card hang. Players' GPUs sometimes miss Windows' 2 s limit on a heavy frame
 * (DXGI_ERROR_DEVICE_HUNG in the reports, 14 in 6 h on 1 Nov): the driver resets and Chrome refuses WebGPU to the site
 * until the browser restarts ("Kullanılabilir WebGPU grafik aygıtı bulunamadı"). Nothing on the page can lift that.
 * When that message or "Grafik aygıtı bağlantısı kesildi" appears, it is remembered (pav-gpu-lost198); on the next
 * visit, once per incident, the lightest settings are stored before the engine reads them: Akıcı profile with 384 MB
 * textures and a 70 % render scale (marked as the player's own choice, so the automatic scale leaves it). A notice
 * says so; Esc -> Ayarlar can raise them again. */
(()=>{'use strict';
const LOST='pav-gpu-lost198',DONE='pav-gpu-safe198';
const get=k=>{try{return localStorage.getItem(k);}catch{return null;}},set=(k,v)=>{try{localStorage.setItem(k,v);}catch{}};
const lost=Number(get(LOST)||0);
if(lost&&Date.now()-lost<7*86400000&&get(DONE)!==String(lost)){
 set('pav-pc-graphics79',JSON.stringify({quality:0,distance:.35,vehicle:.5,ped:.35,texture:384}));
 set('pav-render-scale','0.7');set('pav-scale-user116','1');set(DONE,String(lost));
 const show=()=>{const n=document.createElement('div');n.id='pav-gpusafe198';n.setAttribute('role','status');
  n.style.cssText='position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:2147483000;max-width:min(640px,94vw);padding:12px 16px;border-radius:12px;background:rgba(20,14,30,.95);border:1px solid rgba(255,179,107,.6);color:#fff;font:600 13.5px/1.45 "Segoe UI",system-ui,sans-serif;box-shadow:0 12px 40px rgba(0,0,0,.5);text-align:center';
  n.textContent='Ekran kartın son girişte takıldı; bu yüzden daha hafif grafik ayarları uygulandı (Akıcı profil, %70 görüntü ölçeği). Esc › Ayarlar’dan değiştirebilirsin. Hata yine çıkarsa Chrome’u tamamen kapatıp aç ve ekran kartı sürücünü güncelle.';
  document.body.append(n);setTimeout(()=>n.remove(),15000);};
 if(document.body)show();else addEventListener('DOMContentLoaded',show,{once:true});
}
const RX=/WebGPU grafik aygıtı bulunamadı|Grafik aygıtı bağlantısı kesildi/i;
const seen=node=>{const t=node&&(node.nodeType===3?node.data:node.textContent);if(t&&t.length<4000&&RX.test(t))set(LOST,String(Date.now()));};
const start=()=>new MutationObserver(list=>{for(const m of list){if(m.type==='characterData')seen(m.target);else for(const n of m.addedNodes)seen(n);}}).observe(document.body,{childList:true,subtree:true,characterData:true});
if(document.body)start();else addEventListener('DOMContentLoaded',start,{once:true});
window.PAVGpuSafe198={lost:()=>Number(get(LOST)||0)};
})();
