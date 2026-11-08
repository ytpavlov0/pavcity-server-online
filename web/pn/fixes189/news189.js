/* 189: a "Güncellemeler" button next to "Yardım" on the login / register / character screens. It opens a short devlog
 * of what changed for players (newest first). A dot marks entries the player has not opened yet (localStorage). */
(()=>{'use strict';
const LATEST='2026-11-01';
const LOG=[
 ['1 Kasım 2026','Çökme düzeltmesi',[
  'Oyun penceresini büyütüp küçültünce, F11 / tam ekrana girip çıkınca veya yakınlaştırınca oyun çöküyordu. Artık çökmüyor; görüntü pencereye uydurulur, tam netlik için sayfayı yenilemen yeterli.',
  'Uzun sonuçlar (/stats, yetkili komutları) artık ekranın ortasında, aranabilir geniş bir panelde açılıyor.']],
 ['31 Ekim 2026','Ayarlar',[
  'Fare hassasiyeti ayarı geldi: ESC menüsünden değiştirebilirsin.',
  '“Renk ve görüntü” ayarları geldi: şehri daha canlı veya daha sade yapabilirsin (ESC menüsü).',
  'Oyun kasıyorsa ESC menüsünden görüntü ölçeğini düşür; daha az piksel çizilir, akıcılık artar.']],
 ['31 Ekim 2026','Bağlantı ve senkron',[
  'Gecikme (ping) büyük ölçüde düşürüldü; oyuncular, araçlar ve sesli sohbet ayrı bir hızlı bağlantıdan gidiyor.',
  'İsim etiketleri artık takılmıyor; duvar arkasındaki ve uzaktaki oyuncuların ismi gösterilmiyor.',
  'Yumruklaşınca karakterlerin kollarını açıp donması (T-poz) düzeltildi.',
  'Araçtan inerken aracın havada veya yerinde donması düzeltildi; iç mekândan çıkınca aracın kaybolması düzeltildi.']],
 ['31 Ekim 2026','Araçlar ve ekonomi',[
  'Aracın kapı, cam ve kilidini dışarıdan yalnızca sahibi, anahtarı olan veya içindekiler kullanabilir.',
  'ATM’ler şehir bankasına bağlandı: bankadaki paranı ATM’den çekip yatırabilirsin.',
  'İlk kez giren oyuncular şehrin farklı noktalarında doğuyor; herkes aynı yerde üst üste doğmuyor.']],
 ['31 Ekim 2026','Güvenlik ve topluluk',[
  'Kayıt olurken gerçek bir e-posta adresi gerekiyor; saçma veya geçici adresler kabul edilmiyor.',
  'Küfürlü ve anlamsız karakter isimleri engelleniyor; sohbette küfür filtresi var, tekrarlayana otomatik susturma uygulanıyor.',
  'Yeni hesaplarda sesli sohbet 2 saat oynadıktan sonra açılır (trollere karşı).']],
 ['Yakında','Üzerinde çalışılanlar',[
  'Herkesin aynı NPC’leri ve aynı trafiği gördüğü ortak şehir.',
  'Daha kalabalık sunucular (100+ oyuncu) için senkron iyileştirmeleri.',
  'Araçta yolcunun da radyoyu duyması.']]];
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const seen=()=>{try{return localStorage.getItem('pav-news189')===LATEST;}catch{return false;}};
const CSS='#yt-auth-modal .pav-entry-header .n189-open{position:relative;display:inline-flex;align-items:center;gap:8px;margin-left:12px;padding:8px 14px 8px 8px;border-radius:999px;border:1px solid rgba(255,179,107,.5);background:linear-gradient(180deg,rgba(28,18,43,.85),rgba(14,9,22,.85));color:#fff;font:800 12.5px/1 PAVSource,"Segoe UI",sans-serif;letter-spacing:.04em;cursor:pointer;box-shadow:0 6px 18px rgba(0,0,0,.35),0 0 14px rgba(255,179,107,.18);pointer-events:auto}'+
'#yt-auth-modal .pav-entry-header .n189-open i{display:grid;place-items:center;width:22px;height:22px;border-radius:50%;font-style:normal;font-size:12px;background:linear-gradient(140deg,#ffb36b,#ff5fa8)}'+
'#yt-auth-modal .pav-entry-header .n189-open:hover{border-color:rgba(255,179,107,.9)}'+
'#yt-auth-modal .pav-entry-header .n189-open[data-new]::after{content:"";position:absolute;top:-2px;right:-2px;width:10px;height:10px;border-radius:50%;background:#ff5fa8;box-shadow:0 0 0 2px #1a1024,0 0 10px #ff5fa8}'+
'#pav-news189{position:fixed;inset:0;z-index:2147483000;display:grid;place-items:center;padding:16px;background:rgba(8,5,14,.72);backdrop-filter:blur(6px)}'+
'#pav-news189 .n189-card{width:min(680px,100%);max-height:min(86vh,800px);display:flex;flex-direction:column;border-radius:20px;background:linear-gradient(170deg,rgba(36,22,54,.98),rgba(16,10,26,.98));border:1px solid rgba(255,255,255,.12);box-shadow:0 30px 80px rgba(0,0,0,.6);color:#f6f1ff;font-family:"Segoe UI",system-ui,sans-serif;overflow:hidden}'+
'#pav-news189 header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:20px 22px 12px;border-bottom:1px solid rgba(255,255,255,.08)}'+
'#pav-news189 header small{color:#ffb36b;font-weight:800;letter-spacing:.14em;font-size:11px}#pav-news189 h2{margin:4px 0 0;font-size:22px;font-weight:800}'+
'#pav-news189 .n189-close{width:34px;height:34px;border-radius:10px;border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.06);color:#fff;font-size:20px;cursor:pointer}'+
'#pav-news189 .n189-body{overflow:auto;padding:6px 22px 14px}#pav-news189 article{padding:14px 0;border-bottom:1px solid rgba(255,255,255,.06)}#pav-news189 article:last-child{border-bottom:0}'+
'#pav-news189 h3{display:flex;align-items:baseline;gap:10px;margin:0 0 8px;font-size:15px;font-weight:800}#pav-news189 h3 time{color:#ff8fc7;font-size:11.5px;letter-spacing:.08em;font-weight:800;text-transform:uppercase}'+
'#pav-news189 ul{margin:0;padding-left:18px;font-size:13.5px;line-height:1.55;color:rgba(246,241,255,.88)}#pav-news189 li{margin:3px 0}';
function open(){if(document.getElementById('pav-news189'))return;
 if(!document.getElementById('n189-style')){const s=document.createElement('style');s.id='n189-style';s.textContent=CSS;document.head.append(s);}
 const box=document.createElement('section');box.id='pav-news189';box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-labelledby','pav-news189-title');
 box.innerHTML='<div class="n189-card"><header><div><small>PAVCITY · GÜNCELLEMELER</small><h2 id="pav-news189-title">Şehirde neler değişti?</h2></div><button type="button" class="n189-close" aria-label="Kapat">×</button></header><div class="n189-body">'+LOG.map(([d,t,list])=>'<article><h3><time>'+esc(d)+'</time>'+esc(t)+'</h3><ul>'+list.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></article>').join('')+'</div></div>';
 const close=()=>box.remove();box.addEventListener('click',e=>{if(e.target===box||e.target.closest('.n189-close'))close();});box.addEventListener('keydown',e=>{if(e.key==='Escape'){e.stopPropagation();close();}});
 document.body.append(box);box.querySelector('.n189-close').focus();
 try{localStorage.setItem('pav-news189',LATEST);}catch{}document.querySelectorAll('.n189-open[data-new]').forEach(b=>b.removeAttribute('data-new'));}
function place(){const header=document.querySelector('#yt-auth-modal .pav-entry-header');if(!header||header.querySelector('.n189-open'))return;
 if(!document.getElementById('n189-style')){const s=document.createElement('style');s.id='n189-style';s.textContent=CSS;document.head.append(s);}
 const b=document.createElement('button');b.type='button';b.className='n189-open';b.innerHTML='<i>★</i><span>Güncellemeler</span>';b.title='Son güncellemeler';b.onclick=open;if(!seen())b.dataset.new='1';
 const help=header.querySelector('.h141-open');help?header.insertBefore(b,help):header.append(b);}
new MutationObserver(place).observe(document.documentElement,{childList:true,subtree:true});place();
window.PAVNews189=open;
})();
