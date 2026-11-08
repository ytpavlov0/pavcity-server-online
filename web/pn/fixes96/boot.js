(()=>{
'use strict';
const mq=new URLSearchParams(location.search);
const mobileLite=window.PAVMobile?.active??(mq.get('mobile')==='1'||mq.get('mobile')!=='0'&&(/iPhone|iPad|Android/i.test(navigator.userAgent)||navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1));
// The phone does not allocate a media element/decoder for optional entry music.
const music=mobileLite?null:new Audio('/pn/pavcity-night.wav');if(music){music.loop=true;music.preload='auto';}
if(music)music.volume=Math.max(0,Math.min(1,Number(localStorage.getItem('pav-music-volume')??40)/100));
let muted=localStorage.getItem('pav-music-muted')==='yes',stopped=false,bootStarted=false,failed=false,pct=0,bytes=0;
let watchOnline=false,worldSignaled=false,engineWatching=false;
let overlay,label,percent,detail,timer,readySince=0,lastActivity=performance.now(),lastStage='Şehir varlıkları hazırlanıyor…',pendingShaders=-1,stallLogged=false;
const updateMusic=()=>music&&document.querySelectorAll('.pav-music-toggle').forEach(b=>{b.textContent=music.paused?'♫ Müziği aç':'♫ Müziği kapat';b.setAttribute('aria-pressed',String(!music.paused));});
const play=()=>{if(!music||muted||stopped)return;music.play().then(updateMusic).catch(updateMusic);};
music?.addEventListener('pause',updateMusic);music?.addEventListener('playing',updateMusic);
function bindMusic(root){if(!music)return;root.querySelectorAll('.pav-music-toggle').forEach(b=>b.onclick=()=>{muted=!music.paused;localStorage.setItem('pav-music-muted',muted?'yes':'no');muted?music.pause():play();});root.querySelectorAll('.pav-music-volume').forEach(input=>{input.value=Math.round(music.volume*100);input.oninput=()=>{music.volume=Number(input.value)/100;localStorage.setItem('pav-music-volume',input.value);document.querySelectorAll('.pav-music-volume').forEach(other=>other.value=input.value);document.querySelectorAll('.pav-music-percent').forEach(other=>other.textContent=input.value+'%');};});updateMusic();}
const musicControls=()=>mobileLite?'':`<div class="pav-music"><button class="pav-music-toggle" type="button">♫ Müziği aç</button><input class="pav-music-volume" aria-label="Giriş müziği sesi" type="range" min="0" max="100" value="${Math.round(music.volume*100)}"><span class="pav-music-percent">${Math.round(music.volume*100)}%</span></div>`;
function stopMusic(){stopped=true;if(music){music.pause();music.removeAttribute('src');music.load();}}
if(!mobileLite)document.addEventListener('pointerdown',play,{once:true});addEventListener('pav-game-created',stopMusic,{once:true});
const translate=stage=>({'First frame':'İlk kare alındı; şehir ve grafik shader’ları hazırlanıyor…','Mounting archives':'Oyun arşivleri açılıyor…','Reading settings':'Ayarlar okunuyor…','Starting graphics':'Grafik motoru hazırlanıyor…','Loading shaders':'Grafik shader’ları yükleniyor…','Loading text':'Şehir arayüzü yükleniyor…','Starting audio':'Oyun sesi hazırlanıyor…','Loading audio metadata':'Ses verileri yükleniyor…','Starting scripts':'Şehir scriptleri başlatılıyor…','Loading the world':'Los Santos yükleniyor…','Ready':'Karakter sahnesi hazırlanıyor…'}[stage]||stage);
function fail(message){
 failed=true;window.PAVMobileSession?.fail(message);window.PAVMobileCheckpoint?.fail(message);clearTimeout(timer);readySince=0;
 if(!overlay?.isConnected)return;
 overlay.classList.remove('ready');label.textContent=message;detail.textContent='Yükleme tamamlanmadı. Yeniden deneyebilir veya düşük bellek profilini açabilirsin.';
 overlay.querySelector('.pav-boot-dismiss').hidden=false;overlay.querySelector('.pav-boot-actions').hidden=false;
}
const channel=new BroadcastChannel('game-progress');
channel.onmessage=({data})=>{
 if(data.gpuFrame)window.PAVMobileGraphicsFrame=true;
 if(data.pnStartupProbe){const p=data.pnStartupProbe;if(p.auto){lastStage=p.ready?'Mobil motor hazır. Los Santos başlatılıyor…':p.instances+' mobil işçi hazır · Başlangıç belleği dengeleniyor (15 sn).';render();return;}if(p.ready){pct=100;lastStage='Yalnızca motor testi tamamlandı · '+p.instances+' işçi hazır. Şehir başlatılmadı.';window.PAVMobileCheckpoint?.probeComplete();clearTimeout(timer);}else{lastStage=p.instances+' işçi hazır · 15 saniye motor kararlılığı izleniyor. Şehir başlatılmadı.';}render();return;}
 if(data.mobileStartup){window.PAVStartupDetails=data.mobileStartup;}
 if(data.error||data.gpuLost){fail(data.error||('Grafik aygıtı bağlantısı kesildi: '+data.gpuLost));return;}
 if(failed)return;
 let moved=!!data.mobileStartup||!!data.mobileIO;
 if(data.dl>0){bytes+=data.dl;moved=true;}
 const nextPct=Math.min(98,Number(data.pct)||0);if(nextPct>pct){pct=nextPct;moved=true;}
 if(typeof data.label==='string'){lastStage=translate(data.label);}
 if(data.compiling!==undefined){if(data.compiling!==pendingShaders)moved=true;pendingShaders=data.compiling;lastStage='Grafik shader’ları hazırlanıyor · '+pendingShaders+' bekliyor';}
 if(data.world){worldSignaled=true;pct=99;lastStage='Karakter modeli ve ten dokuları hazırlanıyor…';moved=true;}
 if(moved){lastActivity=performance.now();stallLogged=false;}
 render();
};
addEventListener('pav-engine-failed',e=>fail(e.detail));addEventListener('pn-native-error',e=>fail(e.detail));
function render(){
 if(!overlay?.isConnected||failed)return;
 overlay.style.setProperty('--loaded',pct+'%');percent.textContent=Math.floor(pct)+'%';label.textContent=lastStage;
 const session=window.PAVMobileSession?.snapshot();
 const quiet=session?session.quietSeconds:Math.max(0,Math.floor((performance.now()-lastActivity)/1000));
 const startup=window.PAVStartupDetails,workers=window.PAVMobileWorkerTrace;
 const fields=['UI23.5 · Motor16.18',window.PAVCapabilities?.engine||'mobil'];
 fields.push(bytes>0?(bytes/1048576).toFixed(1)+' MB oyun verisi alındı':'Veri miktarı henüz bildirilmedi');
 if(workers?.requested>0)fields.push(workers.ready+'/'+workers.requested+' işçi hazır');
 else fields.push('İşçi sayısı henüz bildirilmedi');
 if(startup?.heapMiB)fields.push(startup.heapMiB+' MiB sanal bellek');
 if(session?.file)fields.push('Dosya: '+session.file);
 if(session)fields.push('Ekran açık yükleme: '+session.activeSeconds+' sn');
 if(session?.hidden)fields.push('Ekran kapalı / sekme arka planda; tarayıcı yüklemeyi askıya alabilir.');
 else fields.push(quiet>10?'Son motor/veri ilerlemesi '+quiet+' sn önce.':'Motor/veri ilerlemesi alınıyor.');
 if(session)fields.push(session.wake==='held'?'Ekranı açık tutma etkin.':'Ekranı açık tutma etkin değil; ekran kilidi yüklemeyi kesebilir.');
 detail.textContent=fields.join(' · ');
 if(quiet>=90&&!document.hidden&&engineWatching){overlay.querySelector('.pav-boot-dismiss').hidden=false;overlay.querySelector('.pav-boot-actions').hidden=false;detail.textContent+=' Motor/veriden yeni ilerleme yok. Kapanma nedeni henüz doğrulanmadı; istersen elle yeniden başlat.';
  if(!stallLogged){stallLogged=true;fetch('/log',{method:'POST',body:'[PAV BOOT V16.18] stalled '+quiet+'s at '+pct+'%; stage='+lastStage+'; bytes='+bytes}).catch(()=>{});}
 }
}
async function start(){
 if(!mobileLite){document.getElementById('loading')?.classList.add('done');return;}
 if(bootStarted)return;bootStarted=true;lastActivity=performance.now();
 overlay=document.createElement('section');overlay.id='pav-boot';overlay.innerHTML=`<div class="pav-boot-glow"></div><div class="pav-boot-logo"><img src="/pn/pav-logo.png" alt="PAVCITY"><img class="pav-boot-fill" src="/pn/pav-logo.png" alt=""></div><small>LOS SANTOS ROLEPLAY</small><h1>PAV<span>CITY</span></h1><div class="pav-boot-track"><i></i></div><strong class="pav-boot-percent">0%</strong><p class="pav-boot-stage" role="status">Şehir varlıkları hazırlanıyor…</p><p class="pav-boot-detail"></p>${musicControls()}<div class="pav-boot-actions" hidden><button type="button" class="pav-boot-retry">Yeniden dene</button><button type="button" class="pav-boot-low">Düşük bellek profili</button></div><button class="pav-boot-dismiss" type="button" hidden>Giriş ekranına geç</button>`;
 document.body.append(overlay);label=overlay.querySelector('.pav-boot-stage');percent=overlay.querySelector('.pav-boot-percent');detail=overlay.querySelector('.pav-boot-detail');bindMusic(overlay);if(window.PAVMobile?.active){const debug=document.createElement('button');debug.type='button';debug.textContent='Tanılama kaydını indir';debug.style.cssText='font-size:11px;padding:7px;opacity:.8';debug.onclick=()=>window.PAVMobileCheckpoint?.download();overlay.append(debug);}
 overlay.querySelector('.pav-boot-dismiss').onclick=()=>{overlay.remove();clearTimeout(timer);};
 overlay.querySelector('.pav-boot-retry').onclick=()=>location.reload();
 if(window.PAVMobile?.active){percent.textContent='GİRİŞ';label.textContent='UI23.5 · Mobil giriş · Motor16.18 / 30 FPS';detail.textContent='Telefonu yatay çevir. Önce giriş ekranı açılır; şehir seçilince motor yüklenir.';const launch=document.createElement('button');launch.className='pav-mobile-start';const probe=+new URLSearchParams(location.search).get('startupProbe')>0;launch.textContent=probe?'MOTOR TESTİNİ BAŞLAT':'MOBİL GİRİŞİ AÇ';if(probe){label.textContent='Motor ve bellek tanılaması · Şehir başlatılmayacak';detail.textContent='Aynı motorla 11 işçi açılır; grafik ve şehir yüklemesi çalıştırılmaz. Sonuç için 15 saniye kararlılık izlenir.';}const previous=window.PAVMobileCheckpoint?.previous;if(previous?.state==='loading'||previous?.state==='error'){const note=document.createElement('p');note.className='pav-mobile-recovery';note.textContent='Önceki oturum kesildi; eski motor bu sayfada çalışmıyor. Son kayıt · %'+(previous.pct||0)+' · '+(previous.stage||'Başlatılıyor')+(previous.instances?' · '+previous.instances+' işçi':'')+(previous.heapMiB?' · '+previous.heapMiB+' MiB sanal bellek':'')+(previous.engine?' · '+previous.engine:'')+(previous.workerStage?' · '+previous.workerStage:'');overlay.querySelector('.pav-boot-detail').after(note);}overlay.querySelector('.pav-boot-actions').before(launch);await new Promise(resolve=>launch.onclick=async()=>{launch.disabled=true;try{await window.PAVMobileLease?.acquire();launch.remove();overlay.querySelector('.pav-mobile-recovery')?.remove();window.PAVMobileSession?.arm();resolve();}catch(e){launch.disabled=false;label.textContent=e.message;}});}
 overlay.querySelector('.pav-boot-low').onclick=()=>{const url=new URL(location.href);url.searchParams.set('low','1');url.searchParams.set('fps','30');location.assign(url.href);};play();
 try{
  for(let attempt=0;typeof window.chooseEngineMode!=='function';attempt++){if(attempt>100)throw Error('Motor başlatıcısı hazırlanamadı. Sayfayı yenile.');await new Promise(r=>setTimeout(r,100));}
  await window.checkPNGTAEnvironment();const isProbe=window.PAVMobile?.active&&+new URLSearchParams(location.search).get('startupProbe')>0;
  if(isProbe){engineStarting(false);window.pavEngineStarted=true;window.chooseEngineMode(2);dispatchEvent(new CustomEvent('gta-story-start',{detail:{online:false}}));return;}
  const preview=await window.startPAVPreview({},false);
  if(preview===false){overlay.remove();window.PAVMobileSession?.cancel();return;}
  poll();
 }catch(e){fail(e.message);}
}
function engineStarting(online=true){
 if(!window.PAVMobile?.active||engineWatching)return;
 engineWatching=true;watchOnline=online;failed=false;pct=0;bytes=0;readySince=0;worldSignaled=false;lastActivity=performance.now();lastStage='Motor kodu hazırlanıyor…';
 window.PAVMobileCheckpoint?.start();window.PAVMobileSession?.begin();
 if(overlay){document.body.append(overlay);overlay.classList.remove('ready');overlay.querySelector('.pav-boot-actions').hidden=true;overlay.querySelector('.pav-boot-dismiss').hidden=true;render();clearTimeout(timer);poll();}
}
addEventListener('gta-story-start',e=>engineStarting(!!e.detail?.online));
function poll(){
   if(!overlay.isConnected||failed)return;
   const state=window.getPAVEngineState?.(),a=state?.bridge?new Int32Array(state.bridge.memory.buffer,state.bridge.block,16384):null;
   if(state?.error){fail(state.error);return;}
   const avatarReady=watchOnline?a?.[37]&&a[63]&&!a[72]&&a[8]>0:a?.[73]&&a[63];
   if((state?.worldReady&&avatarReady)||(!watchOnline&&window.PAVMobile?.active&&worldSignaled)){
    if(!readySince)readySince=performance.now();
    if(performance.now()-readySince>1000){window.PAVMobileCheckpoint?.complete();window.PAVMobileSession?.finish();engineWatching=false;pct=100;lastStage='Şehir hazır. Hikâyeni oluştur.';render();overlay.classList.add('ready');setTimeout(()=>{if(failed)return;overlay.remove();if(!watchOnline)window.endPAVPreview?.();dispatchEvent(new Event('pav-assets-ready'));},850);return;}
   }else readySince=0;
   render();timer=setTimeout(poll,250);
}
window.PAVBoot={start,musicControls,bindMusic,stopMusic,engineStarting};
})();
