/* Keep JSON validation reasons even with HTTP400; never replay mutations. */
(()=>{'use strict';const key82='pav-tab-lease82';let client61;try{client61=sessionStorage.getItem(key82);}catch{}if(!/^[a-f0-9-]{36}$/i.test(client61||''))client61=crypto.randomUUID();const save82=()=>{window.PAVClient61=client61;try{sessionStorage.setItem(key82,client61);}catch{}};save82();
 const lease82=!navigator.locks?Promise.resolve():new Promise(resolve=>{const hold=()=>new Promise(()=>{});navigator.locks.request('pav-tab82-'+client61,{signal:AbortSignal.timeout(1200)},()=>{resolve();return hold();}).catch(()=>{client61=crypto.randomUUID();save82();navigator.locks.request('pav-tab82-'+client61,()=>{resolve();return hold();});});});
 window.PAVRequestJSON=async(path,data={})=>{await lease82;data={...data,client61};
 if(typeof path!=='string'||!path.startsWith('/api/'))throw Error('Geçersiz API yolu.');
 const safe=path==='/api/auth/login'||path==='/api/auth/me'||/\/(list|status|profile|catalog|garage)$/.test(path);
 for(let attempt=0;attempt<(safe?3:1);attempt++){
  let r;try{r=await fetch(path,{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(data),signal:AbortSignal.timeout(20000)});}catch{if(safe&&attempt<2){await new Promise(resolve=>setTimeout(resolve,750*(attempt+1)));continue;}throw Error('Sunucuya ulaşılamadı. Bağlantını kontrol edip tekrar dene.');}
  if(safe&&r.status>=500&&attempt<2){await new Promise(resolve=>setTimeout(resolve,750*(attempt+1)));continue;}
  if(!(r.headers.get('Content-Type')||'').toLowerCase().includes('application/json'))throw Error('Sunucu oyun yanıtı veremedi (HTTP '+r.status+'). Biraz bekleyip tekrar dene.');
  let result;try{result=await r.json();}catch{throw Error('Sunucu yanıtı eksik geldi. Biraz bekleyip tekrar dene.');}
  if(!r.ok||!result?.success){const error=Error(typeof result?.error==='string'?result.error:'İşlem tamamlanamadı (HTTP '+r.status+').');error.status=r.status;throw error;}return result;
 }
};})();
