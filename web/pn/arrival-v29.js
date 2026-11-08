/* Readiness is an acknowledgement, never a timer or a fabricated percentage. */
(()=>{
 const ready=(a,state)=>!!(state.worldReady&&state.synced&&a&&a[2]===1&&a[37]&&a[63]&&a[7611]&&!a[62]&&!a[71]&&!a[72]);
 function create(name){
  document.querySelector('.pav-arrival24')?.remove();
  const node=document.createElement('section');node.className='pav-arrival24';node.setAttribute('aria-label','Şehre giriş');
  node.innerHTML=`<header><img src="/pn/pav-logo.png" alt=""><strong>PAV<span>CITY</span><small>LOS SANTOS ROLEPLAY</small></strong><span class="pav-arrival-region">LOS SANTOS · SAN ANDREAS</span></header><main><div class="pav-arrival-copy"><small>YENİ BİR GÜN. SENİN HİKÂYEN.</small><h1>Şehir seni<br><em>bekliyor.</em></h1><p class="pav-arrival-name"></p><p>Karakterin ve bulunduğun bölge hazırlanıyor.<br>Hazır olduğunda otomatik olarak oyuna geçeceksin.</p><div class="pav-arrival-status" role="status" aria-live="polite">Sunucuya bağlanılıyor…</div><ol><li data-step="world"><b>01</b><span>Şehir</span><i></i></li><li data-step="model"><b>02</b><span>Karakter</span><i></i></li><li data-step="ground"><b>03</b><span>Güvenli konum</span><i></i></li><li data-step="sync"><b>04</b><span>Bağlantı</span><i></i></li></ol><p class="pav-arrival-error" hidden></p><button type="button" class="pav-arrival-retry" hidden>Yeniden bağlan <span>↗</span></button><p class="pav-arrival-slow" hidden>Hazırlık beklenenden uzun sürüyor. Bağlantını kontrol edip yeniden deneyebilirsin.</p></div><aside aria-hidden="true"><div class="pav-arrival-city"><span>LS</span><i></i><i></i><i></i><i></i><i></i></div><p>LOS SANTOS<span>Her sokakta yeni bir hikâye.</span></p></aside></main><footer><span>PAVCITY / ONLINE</span><span>GİRİŞ TAMAMLANANA KADAR KARAKTER KONTROLLERİ KİLİTLİ</span></footer>`;
  node.querySelector('.pav-arrival-name').textContent=name;
  node.querySelector('button').onclick=()=>location.reload();document.body.append(node);
  let done=false,failed=false;
  const timer=setTimeout(()=>{if(done)return;node.querySelector('.pav-arrival-slow').hidden=false;node.querySelector('button').hidden=false;},45000);
  return {node,
   update({worldReady,a,synced}){if(done||failed)return;const steps={world:worldReady,model:!!(a?.[37]&&a?.[63]),ground:!!(a?.[7611]&&!a?.[72]),sync:synced};let current=false;for(const [key,value] of Object.entries(steps)){const row=node.querySelector('[data-step="'+key+'"]');row.classList.toggle('complete',!!value);row.classList.toggle('current',!value&&!current);if(!value)current=true;}
    node.querySelector('.pav-arrival-status').textContent=!worldReady?'Los Santos yükleniyor…':!steps.model?'Karakter ve kıyafetler hazırlanıyor…':!steps.ground?'Güvenli zemin ve çarpışma hazırlanıyor…':!synced?'Şehir bağlantısı doğrulanıyor…':'Her şey hazır. Şehre giriyorsun…';},
   fail(message){if(done)return;failed=true;clearTimeout(timer);node.classList.add('failed');node.querySelector('h1').innerHTML='Bağlantı<br><em>tamamlanamadı.</em>';node.querySelector('.pav-arrival-status').textContent='Karakterin güvenli biçimde durduruldu.';const error=node.querySelector('.pav-arrival-error');error.hidden=false;error.textContent=String(message);node.querySelector('button').hidden=false;},
   finish(){if(done||failed)return;done=true;clearTimeout(timer);node.remove();},
   destroy(){done=true;clearTimeout(timer);node.remove();}
  };
 }
 window.PAVArrival24={ready,create};
})();
