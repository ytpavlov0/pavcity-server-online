/* PAVCITY 140: graphics-device help on the "Yükleme durdu" card. When the stop reason is a WebGPU / graphics-device
 * failure (no adapter, device lost, DXGI_ERROR_DEVICE_HUNG), the card lists the steps that bring the GPU back:
 * Chrome turns hardware acceleration off for the session after a GPU crash, laptops may run Chrome on the weak GPU. */
(()=>{'use strict';
const GPU=/webgpu|grafik aygıt|grafik işçisi|device_hung|device_removed|device lost|aygıt bağlantısı|gpu/i;
const STEPS=['Chrome’u tamamen kapat (bütün pencereler ve sağ alttaki simge) ve yeniden aç. Ekran kartı bir kez çöktüyse Chrome onu o oturum boyunca kapatır.',
 'Chrome › Ayarlar › Sistem › “Kullanılabilir olduğunda grafik hızlandırmayı kullan” açık olsun.',
 'Laptopta: şarja tak; Windows › Ayarlar › Sistem › Ekran › Grafik › Google Chrome › “Yüksek performans” seç.',
 'Ekran kartı sürücüsünü güncelle (NVIDIA / AMD / Intel) ve bilgisayarı yeniden başlat.',
 'Adres çubuğuna chrome://gpu yaz: “WebGPU: Hardware accelerated” görünmüyorsa bu cihaz oyunu çalıştıramaz.'];
function help(panel){const reason=panel.querySelector('.reason');if(!reason||panel.querySelector('.gpu140')||!GPU.test(reason.textContent))return;
 const box=document.createElement('div');box.className='gpu140';
 box.style.cssText='margin:12px 0 14px;padding:12px 14px;border-radius:12px;background:rgba(255,255,255,.05);border:1px solid rgba(255,95,168,.3);text-align:left';
 box.innerHTML='<b style="display:block;margin-bottom:6px;font-size:13px;color:#ffb36b">Ekran kartı sorunu · şunları dene</b><ol style="margin:0;padding-left:18px;font-size:12.5px;line-height:1.45;color:rgba(246,241,255,.85)">'+STEPS.map(s=>'<li style="margin:3px 0"></li>').join('')+'</ol>';
 box.querySelectorAll('li').forEach((li,i)=>li.textContent=STEPS[i]);reason.after(box);}
const scan=()=>{const panel=document.getElementById('pav-recovery95');if(panel)help(panel);};
new MutationObserver(scan).observe(document.documentElement,{childList:true,subtree:true,characterData:true});scan();
})();
