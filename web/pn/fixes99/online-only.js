(()=>{'use strict';
 const url=new URL(location.href);
 if(url.searchParams.get('mode')==='story'){url.searchParams.delete('mode');url.searchParams.delete('newgame');history.replaceState(null,'',url);}
 if(window.PAVOffline94){window.PAVOffline94.bind=()=>{};window.PAVOffline94.boot=async()=>{throw Error('Tek oyunculu mod geliştirme aşamasında. Çevrimiçi karakterini seç.');};}
 addEventListener('gta-story-start',event=>{
  if(window.PAVMobile?.active)return;
  if(event.detail?.online!==true){event.stopImmediatePropagation();return;}
  document.body.classList.add('pav-online-loading97');
 },true);
 addEventListener('pav-scene-ready99',()=>document.body.classList.remove('pav-online-loading97'));
})();
