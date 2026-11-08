(()=>{'use strict';
 window.PAVCrash96={bind(nonce){
  if(!/^[a-f0-9]{32}$/.test(nonce||''))return;
  const channel=new BroadcastChannel('game-crash56:'+nonce),seen=new Set();let count=0;
  channel.onmessage=async({data})=>{
   const d=data?.pnCrash56;if(!d||count>=6)return;
   const frames=Array.isArray(d.frames)?d.frames.slice(0,24).filter(f=>Number.isInteger(f?.fn)&&f.fn>=0&&f.fn<=1000000&&/^0x[0-9a-f]{1,8}$/.test(f.offset)).map(f=>({fn:f.fn,offset:f.offset})):[];
   const report={version:98,id:'C98-'+crypto.randomUUID().replaceAll('-','').slice(0,12).toUpperCase(),role:d.role==='pthread'?'pthread':'main',stage:['event','rejection','pthread-catch','main-catch','bridge-catch'].includes(d.stage)?d.stage:'event',trap:['unreachable','memory-bounds','oom','runtime','other'].includes(d.trap)?d.trap:'other',frames,reason:['short-read','stream-queue','allocation','pool'].includes(d.reason)?d.reason:'unspecified',read:Array.isArray(d.read)&&d.read.length===4&&d.read.every(Number.isSafeInteger)?d.read:[]};
   report.archive=Array.isArray(d.archive)&&d.archive.length===5&&d.archive.every(n=>Number.isInteger(n)&&n>=0&&n<=1000000)?d.archive:[];const key=JSON.stringify([report.role,report.stage,report.trap,frames,report.reason]);if(seen.has(key))return;seen.add(key);count++;
   try{sessionStorage.setItem('pav-crash98',JSON.stringify(report));}catch{}
   let saved=false;try{saved=(await fetch('/api/engine98/crash',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(report),keepalive:true})).ok;}catch{}
   const host=document.querySelector('#pav-recovery95>div')||document.getElementById('hud');if(host){let note=host.querySelector('.crash96-note');if(!note){note=document.createElement('p');note.className='crash96-note';host.append(note);}note.textContent='Hata kodu: '+report.id+(saved?' · Kaydedildi':' · Bu sekmede saklandı');}
  };
  addEventListener('pagehide',()=>channel.close(),{once:true});
 }};
})();
