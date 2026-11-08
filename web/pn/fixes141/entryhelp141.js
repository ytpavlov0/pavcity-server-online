/* PAVCITY 141: a "Yardım" button on the login / register / character screens. It opens a short guide for players
 * who cannot get in: supported browser, the busy-server stop (HTTP 429/503), graphics-card stops, memory, sound. */
(()=>{'use strict';
const SECTIONS=[
 ['Hangi tarayıcı?',['Bilgisayardan güncel Google Chrome veya Microsoft Edge kullan (64 bit).','Telefon, tablet, Safari ve Firefox şu an desteklenmiyor.','En az 8 GB RAM önerilir; oyuna girerken diğer ağır sekmeleri kapat.']],
 ['“Yükleme durdu · HTTP 429 / 503”',['Sunucu o an çok yoğun demektir; oyun dosyaları indirilirken sıra bekleniyor.','10–20 saniye bekle, sonra “Yeniden yükle”ye bas. İndirilen dosyalar saklanır, baştan inmez.','Hata tekrar ederse birkaç dakika sonra dene.']],
 ['Ekran kartı / WebGPU hatası',['Chrome’u tamamen kapat (bütün pencereler ve sağ alttaki simge) ve yeniden aç.','Chrome › Ayarlar › Sistem › “Kullanılabilir olduğunda grafik hızlandırmayı kullan” açık olsun.','Laptopta: şarja tak; Windows › Ayarlar › Sistem › Ekran › Grafik › Google Chrome › “Yüksek performans”.','Ekran kartı sürücüsünü güncelle; adres çubuğuna chrome://gpu yazınca “WebGPU: Hardware accelerated” görünmeli.']],
 ['Takılma, siyah ekran',['Ctrl + F5 ile sayfayı tamamen yenile.','İlk giriş, oyun dosyaları indiği için birkaç dakika sürebilir; yükleme çubuğu ilerliyorsa bekle.']],
 ['Ses ve mikrofon',['Oyun sesi ilk tıklamadan veya tuşa basıştan sonra başlar.','Konuşmak için Z’yi basılı tut; ilk seferde tarayıcı mikrofon izni sorar.']],
 ['Hesap',['Kullanıcı adı ve şifren büyük-küçük harfe duyarlıdır.','Şifreni unuttuysan veya hâlâ giremiyorsan yetkililere hata ekranındaki mesajla birlikte yaz.']]];
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function open(){if(document.getElementById('pav-entry-help141'))return;const box=document.createElement('section');box.id='pav-entry-help141';box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-labelledby','pav-entry-help141-title');
 box.innerHTML='<div class="h141-card"><header><div><small>PAVCITY · YARDIM</small><h2 id="pav-entry-help141-title">Giriş sorunları</h2></div><button type="button" class="h141-close" aria-label="Kapat">×</button></header><div class="h141-body">'+SECTIONS.map(([t,list])=>'<article><h3>'+esc(t)+'</h3><ul>'+list.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></article>').join('')+'</div><footer><button type="button" class="h141-ok">Anladım</button></footer></div>';
 const close=()=>box.remove();box.addEventListener('click',e=>{if(e.target===box||e.target.closest('.h141-close,.h141-ok'))close();});box.addEventListener('keydown',e=>{if(e.key==='Escape'){e.stopPropagation();close();}});
 document.body.append(box);box.querySelector('.h141-close').focus();}
function place(){const header=document.querySelector('#yt-auth-modal .pav-entry-header');if(!header||header.querySelector('.h141-open'))return;
 const b=document.createElement('button');b.type='button';b.className='h141-open';b.innerHTML='<i>?</i><span>Yardım</span>';b.title='Giriş sorunları için yardım';b.onclick=open;header.append(b);}
new MutationObserver(place).observe(document.documentElement,{childList:true,subtree:true});place();
window.PAVEntryHelp141=open;
})();
