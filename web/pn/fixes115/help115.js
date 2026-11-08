/* PAVCITY şehir rehberi 115 (/yardım · /help · /rehber · /komutlar). Every number below comes
 * from the live server chain (jobs, payday, prices, commands); GPS buttons reuse findService. */
(()=>{'use strict';
const icon=n=>window.PAVIcons105?.svg(n)||'';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const DISCORD='discord.gg/YOUR-INVITE';
const cards=list=>'<div class="h115-cards">'+list.map(([t,d,pay,gps])=>'<article><b>'+esc(t)+'</b><span>'+esc(d)+'</span>'+(pay?'<br><em>'+esc(pay)+'</em>':'')+(gps?'<br><button class="h115-gps" data-gps="'+gps+'">Yakın nokta · GPS</button>':'')+'</article>').join('')+'</div>';
const table=rows=>'<div class="h115-table">'+rows.map(([c,d])=>'<div><code>'+esc(c)+'</code><span>'+esc(d)+'</span></div>').join('')+'</div>';
const keys=rows=>'<div class="h115-keys">'+rows.map(([k,d])=>'<div><kbd>'+esc(k)+'</kbd><span>'+esc(d)+'</span></div>').join('')+'</div>';
const SECTIONS=[
 ['start','Başlangıç','compass','Şehre hoş geldin','PAVCITY bir rol yapma (RP) sunucusu: karakterine uygun davran, oyun içi ve dışı (OOC) konuşmayı ayır.',
  '<h4>İlk 10 dakika</h4>'+cards([['1 · İhtiyaçlar','Marketten su ($100) ve yiyecek ($150) al; /su ve /ye ile tüket. Açlık ve susuzluk sağlığını etkiler.','','market'],['2 · İlk para','/meslek ile bir iş seç (ör. Kurye $1.200 / sefer). Ehliyet veya birlik gerekmez.',''],['3 · Telefon','Digital Den’den PAV Phone al ($8.500). ↑ ile aç; mesaj, arama ve banka.','','electronics'],['4 · Banka','Fleeca şubesinde para yatır/çek, karakter ID’sine havale yap.','','bank']])+
  '<h4>Temel kurallar</h4>'+cards([['RP dışı öldürme yok','Sebepsiz saldırı (RDM) ve araçla ezme (VDM) yasak.',''],['Metagaming yok','Discord / yayın bilgisini oyunda kullanma.',''],['Yetkiliye ulaş','Sorun mu var? F2 veya /rapor ile destek talebi aç.','']])],
 ['money','Para kazanma','cash','Nasıl para kazanılır?','Ödemeler nakit olarak cüzdanına gelir; maaş bankaya yatar. Bakiyeni HUD’da ve telefonda görürsün.',
  '<h4>Meslekler · /meslek</h4>'+cards([['Kurye','Paketleri duraklara teslim et (Blista verilir).','$1.200 / sefer'],['Geri dönüşüm','Depodan atık topla ve taşı (Burrito verilir).','$850 / sefer'],['Bağcılık · Üzüm','Üzüm topla ve sat.','$1.800 / sefer'],['Çiftçilik · Karpuz','Tarlada dur ve hasat et.','$650'],['Çiftçilik · Domates','Tarlada dur ve hasat et.','$500'],['Şarap üretimi','Meslek seviyesi 2 gerekir.','$1.000'],['Şirket işleri · /sirketis','Evrak dağıtımı / tedarik sevkiyatı; ödeme şirket kasasına.','$1.500 – $2.200']])+
  '<h4>İllegal işler (risklidir, polis takip edebilir)</h4>'+cards([['Kaçak sevkiyat','Sultan ile teslimat.','$2.400'],['Kaçak ürün toplama','Toplama ve teslimat.','$2.800 – $3.600'],['RP sözleşmesi','Yalnız sözleşmeye katılmayı kabul etmiş hedefler.','$8.000']])+
  '<h4>Saatlik maaş</h4>'+cards([['Her 1 saat oyunda','Birlik dışı $500; polis / EMS / devlet birliklerinde rütbe maaşı ($500–$2.500). Her VIP seviyesi +$500.',''],['Maaşı almak','/maas kodu gösterir, /onayla KOD ile bankaya yatar (kod 15 dk geçerli). VIP’ler otomatik alır.',''],['Ofis bonusu','Sahip olduğun her ofis için +$500 (en fazla 3).','']])+
  '<h4>Diğer kazançlar</h4>'+cards([['Günlük çark','PAV Oyun Salonu’nda 24 saatte bir: $500 – $10.000.',''],['Mülk','Mülk satınca bedelin %50’si geri döner.',''],['Araç satışı','Aracını başka oyuncuya /aracımısat ile sat.','']])+
  '<p class="h115-note">İpucu: meslek sırasında ölürsen iş iptal olur ve ödeme yapılmaz. Görev aracını bırakıp başka araçla gidersen durak tamamlanmaz (araç 30 m içinde olmalı).</p>'],
 ['spend','Harcama · fiyatlar','bank','Şehirde neler alınır?','Tüm fiyatlar sunucuda belirlenir.',
  cards([['Galeri · /galeri','Faggio $8.000 · Blista $18.000 · Sultan $85.000 · Buffalo $110.000 · Baller $125.000 · Schafter $160.000 · Tofaş $3M · Skyline $15M · Adder $22M','','dealer'],['Yakıt','$45 / litre, depo 60 L.',''],['Anahtar kopyası','Çilingir · $2.500 (en fazla 20).',''],['Park noktası · /park','$250.',''],['Mekanik tamir','$250 · /mekanik.',''],['Modifiye · /modifiye','Boya $3.000–$4.500 · jant $8.500 · motor $35.000 · turbo $75.000 · hava süspansiyonu $18.000.',''],['Berber / giyim · /berber','Saç $500 · sakal $250 · üst $1.200 · kıyafet kaydı $3.500.',''],['Mülkler · /mulkler','Garaj $180.000 · daire $285.000 · ofis $690.000.',''],['Marina · /marina','Dinghy $65.000 · Jetmax $185.000 · Marquis $350.000.',''],['Hastane','Tedavi $2.500.','','hospital'],['Şirket · /holding','Kuruluş $10.000 (ofis gerekir).',''],['Kumarhane','Bahis $10–$5.000 · rulet, slot, at yarışı.','']])],
 ['trade','Para · PP · ticaret','players','Oyuncular arası işlemler','Tüm işlemler kayıt altına alınır; dolandırıcılık rapor edilebilir.',
  table([['/paragonder ID MİKTAR','Yanındaki (5 m) oyuncuya nakit ver. En fazla $1.000.000. Karşı tarafa özel mesaj gider.'],['/pp','PAV Puan (PP) bakiyeni ve son hareketlerini gösterir.'],['/ppgonder ID MİKTAR','Çevrim içi oyuncuya PP gönder.'],['/aracımısat ID FİYAT','Aracının sürücü koltuğunda dur, alıcı 5 m içinde olsun. Teklif 90 sn geçerli. Donate araçlar satılamaz.'],['/araçkabul · /araçreddet','Sana gelen son araç teklifini kabul et / reddet (ID gerekmez). /teklifler ile listele.'],['Banka havalesi','Fleeca’da karakter ID’sine havale ($1 – $10.000.000).']])+
  '<p class="h115-note">PAV Puan (PP) hesabına bağlıdır, karakter değiştirsen de kalır. PP yalnızca kurucu tarafından yüklenir; PP ile VIP ve özel içerikler yakında.</p>'],
 ['vehicles','Araçlar','car','Araç sahibi olmak','Araçlarının ID’si /stats ve Araçlarım’da görünür.',
  table([['/galeri · /arac MODEL','Galeriyi aç / modeli satın al.'],['/garaj · /cikar ID','Garajdaki aracı çıkar.'],['/park ID','$250 ile dönüş noktası belirle.'],['/aracimigetir ID','Aracını yanına getir (günde 3).'],['/kilit ID · K','Kilitle / aç.'],['/motor · M','Motoru çalıştır / durdur.'],['/anahtarlar','Anahtar kopyala veya iptal et (çilingir).'],['/maymuncuk','Kilit kırma (illegal, risk taşır).']])],
 ['factions','Birlikler · PD alımı','police','Polis, sağlık ve birlikler','Birliğe katılmak için liderin 5 m yakınında davet al, Birlik › Davetler’den kabul et.',
  cards([['LSPD · Polis','Görev masası: Mission Row. /pduty ile göreve gir (rozet gerekir). Kelepçe, yere yatırma, hapis, cephanelik.','',''],['EMS · Sağlık','Pillbox. /mduty ile göreve gir; yaralılara yardım et.','','hospital'],['Legal / illegal birlikler','Oyuncular kurabilir: araç filosu, kasa, rütbe maaşları.',''],['Telsiz','/telsiz aç-kapa · /r mesaj.','']])+
  '<div class="h115-discord"><div><b>LSPD alımları Discord’da</b><span>Polis başvurusu ve mülakatlar için: '+DISCORD+'</span></div><button data-copy="https://'+DISCORD+'">Bağlantıyı kopyala</button></div>'],
 ['commands','Komutlar','settings','Tüm komutlar','Sohbette / yazınca öneriler açılır.',
  '<h4>Sohbet</h4>'+table([['T · B','IC sohbet (25 m) · OOC sohbet (40 m)'],['/me EYLEM · /do DURUM','Rol eylemi / ortam durumu (20 m)'],['/b · /ooc MESAJ','Yakın OOC'],['/pm ID MESAJ','Özel mesaj'],['/p MESAJ','Telefon görüşmesine yaz']])+
  '<h4>Karakter ve bilgi</h4>'+table([['/stats','Karakter, araç ID’leri, can/zırh'],['/hesap · F1','Hesabım, VIP, mülkler'],['/admins','Aktif yetkililer'],['/ulkesec','Ülke seçimi'],['/edithud','HUD’u düzenle'],['/anim','Animasyonlar'],['/su · /ye','İç / ye']])+
  '<h4>Para ve ticaret</h4>'+table([['/paragonder ID MİKTAR','Yanındakine nakit ver'],['/pp · /ppgonder ID MİKTAR','PAV Puan'],['/aracımısat ID FİYAT','Araç satış teklifi'],['/araçkabul · /araçreddet','Son teklifi yanıtla'],['/teklifler','Araç teklifleri'],['/maas · /onayla KOD','Saatlik maaş'],['/banka','Banka']])+
  '<h4>Meslek ve şehir</h4>'+table([['/meslek','Meslek merkezi'],['/meslekdurum · /meslekayril','Görev adımı · işi bırak'],['/meslekaracim','Görev aracı'],['/sirketis · /holding','Şirket işleri'],['/mulkler · /ev','Mülkler · evin'],['/isikac · /isikkapat','Ev ışıkları'],['/berber · /modifiye · /mekanik','Hizmetler'],['/marina · /kafe · /silahci','Mekanlar'],['/mekanlar','Mekan listesi']])+
  '<h4>Destek</h4>'+table([['/rapor · F2','Destek talebi aç / takip et'],['/yardım · /komutlar','Bu rehber']])],
 ['keys','Tuşlar','key','Kontroller','Masaüstü varsayılanları.',
  keys([['T','IC sohbet'],['B','OOC sohbet'],['Z','Bas-konuş (ses)'],['ESC','Menü'],['F','Araca bin / in'],['E','Etkileşim (basılı tut)'],['ALT','Yakındaki etkileşimler'],['I','Envanter'],['0–5','Hızlı yuvalar'],['G','En yakın kapı'],['↑','Telefon'],['Sol Ctrl','Eğil'],['M','Motor'],['K','Kilit'],['L','Farlar'],['H','Korna (sürücü)'],['U','Emniyet kemeri'],[', .','Sinyaller'],['J','Dörtlü'],['TAB','Oyuncu listesi'],['F1','Hesabım / VIP'],['F2','Destek'],['F3','İmleç'],['F11','Harita / GPS']])],
 ['vip','VIP','trophy','VIP ve PAV Puan','VIP seviyeleri: Standart, VIP I – VIP VI.',
  cards([['Saatlik maaş','Her VIP seviyesi saatlik ödemene +$500 ekler.',''],['Otomatik maaş','VIP’ler /onayla kodu beklemeden maaşı bankaya alır.',''],['Rozet','Nametag ve HUD’da VIP rozeti.',''],['Nasıl alınır?','VIP ve PP için Discord: '+DISCORD,'']])]
];
addEventListener('pav-game-created',({detail})=>setTimeout(()=>{const g=detail||window.PAVGame;let current='start';
 const render=(p,query='')=>{const nav=p.querySelector('.h115 nav'),body=p.querySelector('.h115-body');const q=query.trim().toLocaleLowerCase('tr');
  nav.querySelectorAll('[data-sec]').forEach(b=>b.classList.toggle('on',!q&&b.dataset.sec===current));
  if(q){const hits=SECTIONS.filter(s=>(s[3]+' '+s[5]).toLocaleLowerCase('tr').includes(q)||s[4].toLocaleLowerCase('tr').includes(q));
   body.innerHTML='<h3>Arama: '+esc(query)+'</h3>'+(hits.length?'<p class="lead">'+hits.length+' bölüm eşleşti.</p>'+hits.map(s=>'<h4>'+esc(s[1])+'</h4>'+s[5]).join(''):'<p class="lead">Sonuç yok. Başka bir kelime dene.</p>');}
  else{const s=SECTIONS.find(x=>x[0]===current);body.innerHTML='<h3>'+esc(s[3])+'</h3><p class="lead">'+esc(s[4])+'</p>'+s[5];}
  body.scrollTop=0;
  body.querySelectorAll('[data-gps]').forEach(b=>b.onclick=()=>g.findService?.(b.dataset.gps));
  body.querySelectorAll('[data-copy]').forEach(b=>b.onclick=async()=>{try{await navigator.clipboard.writeText(b.dataset.copy);g.notice?.('Discord bağlantısı kopyalandı: '+DISCORD);}catch{g.notice?.('Discord: '+DISCORD);}});};
 g.help70=async(section)=>{if(section&&SECTIONS.some(s=>s[0]===section))current=section;
  const p=g.openRP('Şehir rehberi · /yardım','<div class="h115"><nav><input class="h115-search" placeholder="Rehberde ara…" aria-label="Rehberde ara">'+SECTIONS.map(s=>'<button data-sec="'+s[0]+'">'+icon(s[2])+'<span>'+esc(s[1])+'</span></button>').join('')+'</nav><div class="h115-body"></div></div>','pav-help115');
  p.querySelectorAll('[data-sec]').forEach(b=>b.onclick=()=>{current=b.dataset.sec;p.querySelector('.h115-search').value='';render(p);});
  const s=p.querySelector('.h115-search');s.oninput=()=>render(p,s.value);render(p);};
},0));
})();
