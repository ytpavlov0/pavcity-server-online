/* One mobile engine per origin. Desktop sessions retain existing behavior. */
(()=>{'use strict';
const key='pav-mobile-engine-lease',id=crypto.randomUUID(),period=6000;
let held=false,releaseLock=null,heartbeat=0;
const read=()=>{try{return JSON.parse(localStorage.getItem(key)||'null');}catch{return null;}};
const mobile=()=>!!window.PAVMobile?.active;
async function acquire(){
 if(!mobile()||held)return;
 if(navigator.locks?.request){
  await new Promise((resolve,reject)=>navigator.locks.request('pav-mobile-engine',{ifAvailable:true},async lock=>{
   if(!lock){reject(Error('Mobil oyun başka bir sekmede açık. O sekmeyi kapatıp tekrar başlat.'));return;}
   held=true;resolve();await new Promise(done=>releaseLock=done);
  }).catch(reject));return;
 }
 const prior=read();if(prior&&prior.id!==id&&Date.now()-prior.updated<period*2)throw Error('Başka bir mobil oyun sekmesi etkin. O sekmeyi kapat; kapanmışsa 12 saniye sonra tekrar başlat.');
 localStorage.setItem(key,JSON.stringify({id,updated:Date.now()}));await new Promise(resolve=>setTimeout(resolve,150));
 if(read()?.id!==id)throw Error('Mobil oyun başka bir sekmede başlatıldı. Tek sekmeden devam et.');
 held=true;heartbeat=setInterval(()=>localStorage.setItem(key,JSON.stringify({id,updated:Date.now()})),period);
}
function release(){clearInterval(heartbeat);if(read()?.id===id)localStorage.removeItem(key);releaseLock?.();releaseLock=null;held=false;}
window.PAVMobileLease={acquire,release,get held(){return held;}};addEventListener('pagehide',release);
})();
