(()=>{'use strict';
 let panel,failed=false;
 function fail(message){
  if(failed){if(panel&&!panel.isConnected){document.body.append(panel);panel.querySelector("button").focus();}return;}failed=true;window.PAVEngineFailed98=true;document.body.classList.add("pav-engine-failed98");
  document.exitPointerLock?.();
  panel=document.createElement('section');panel.id='pav-recovery95';panel.setAttribute('role','alertdialog');panel.setAttribute('aria-labelledby','pav-recovery95-title');
  panel.innerHTML='<div><small>PAVCITY · BAĞLANTI VE MOTOR</small><h2 id="pav-recovery95-title">Yükleme durdu</h2><p class="reason"></p><p>Sayfayı yeniden yükleyerek devam et. Kaydedilmiş karakterin ve oyun kayıtların korunur; görünüm taslağın bu sekmede saklanır.</p><button type="button">Yeniden yükle</button><button type="button" class="recovery-back96">Giriş ekranına dön</button></div>';
  panel.querySelector('.reason').textContent=String(message||'Oyun motoru beklenmedik şekilde durdu.').slice(0,400);
  panel.querySelector('button').onclick=()=>{const url=new URL(location.href);url.searchParams.set('gameplay','110');location.replace(url.href);};
  panel.querySelector('.recovery-back96').onclick=()=>{panel.remove();document.getElementById('pav-boot')?.remove();document.getElementById('loading')?.classList.add('done');const status=document.querySelector('#yt-auth-modal .pav-preview-status');if(status)status.textContent='3D motor durdu. Devam etmek için yeniden yükle.';};document.body.append(panel);panel.querySelector('button').focus();
 }
 addEventListener('click',event=>{if(!failed||!event.target.closest?.('#yt-auth-modal button')||event.target.closest('#logout'))return;event.preventDefault();event.stopImmediatePropagation();fail();},true);addEventListener('submit',event=>{if(!failed||!event.target.closest?.('#yt-auth-modal'))return;event.preventDefault();event.stopImmediatePropagation();fail();},true);
 addEventListener('pn-native-error',e=>fail(e.detail));addEventListener('pav-engine-failed',e=>fail(e.detail));
 const progress=new BroadcastChannel('game-progress');progress.onmessage=({data})=>{if(data.error||data.gpuLost)fail(data.error||'Grafik aygıtı bağlantısı kesildi.');};
 // Keep this page's recovery isolated from other open tabs. Main/pthread traps
 // already use the private crash channel; expose them even if the main loop dies.
 window.PAVRecovery95={bind(nonce){if(!/^[a-f0-9]{32}$/.test(nonce||''))return;const channel=new BroadcastChannel('game-crash56:'+nonce);channel.onmessage=({data})=>{if(data?.pnCrash56)fail('Oyun motoru durdu ('+String(data.pnCrash56.trap||'runtime')+').');};addEventListener('pagehide',()=>channel.close(),{once:true});}};
})();
