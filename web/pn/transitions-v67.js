/* One native transition at a time: server targets, geometry preparation, arrival, rollback. */
(()=>{'use strict';
function coordinator(game,{wait=()=>new Promise(r=>setTimeout(r,100)),now=()=>performance.now(),onState=()=>{}}={}){
 let active=null,pendingRecovery=null;const heap=()=>game.bridge&&new Int32Array(game.bridge.memory.buffer,game.bridge.block,16384);
 const clearRecovered=()=>{if(!pendingRecovery)return;const a=heap();if(a&&a[46]!==pendingRecovery.recoverySpawn&&!a[7712]){pendingRecovery=null;onState({busy:false,phase:'idle'});}};
 const cancel=run=>{const a=heap();if(a&&a[7700]===run.seq)a[7708]=run.seq;};
 const finish=run=>{if(active!==run)return;active=null;game.actionBusy=false;onState({busy:false,phase:'idle'});};
 const fail=()=>{const a=heap();game.transitionDiagnostic46=a?{phase:a[7701],interior:!!a[7709],roomReady:!!a[7710],floorFinite:Number.isFinite(new Float32Array(a.buffer,a.byteOffset,a.length)[7711]),engine:a[2]}:null;return Error(a?.[2]===-1?'Oyun motoru bağlantısı durdu. Güvenli konumun korundu; yeniden bağlan.':a?.[7702]===0&&!a?.[7709]?'İç mekân bu oturumda yüklenemedi. Dış kapıdaki konumun korundu.':'Hedefteki zemin veya iç mekân hazırlanamadı. Güvenli konumun korundu.');};
 function mode(target,custody){
  const g=target?.geometry;
  if(g?.kind==='outdoor'&&(target.dimension===0||(custody&&target.dimension===1780000&&Math.hypot(target.x-1690.5,target.y-2565.5,target.z-45.6)<.1))&&(!g.ipl)&&(!target.ipl))return -1;
  if(g?.kind!=='property'||!Number.isInteger(target.dimension)||target.dimension<1)throw Error('Hedefin mekân türü doğrulanmadı.');
  const allowed={apartment:'',office:'',garage:'',market:''};
  if(!Object.hasOwn(allowed,g.type)||g.ipl!==allowed[g.type]||(target.ipl||'')!==allowed[g.type])throw Error('Bu iç mekân paketi desteklenmiyor.');
  return 0;
 }
 async function restore(run){
  cancel(run);const r=await run.rollback(run.context);
  if(r?.spawn||r?.teleport)game.applyLife(r);
  if(!r?.success)throw Error('Sunucu geri alma işlemini doğrulamadı.');
 }
 async function arrival(run){let recoveryError=null,rollbackStarted=false;
  try{
   const end=now()+22000;
   while(!game.hud.hidden&&game.hud.isConnected!==false&&now()<end){
    const a=heap();if(!a||a[7700]!==run.seq)throw fail();
    if(a[7701]===4){await run.onArrived?.(run.context);game.notice('Geçiş tamamlandı.');return;}
    if(a[7701]===-4){game.notice('Geçiş, karakterin yeni konumu nedeniyle iptal edildi.',true);return;}
    if(a[7701]<0)break;
    await wait();
   }
   rollbackStarted=true;onState({busy:true,phase:'rollback'});await restore(run);game.notice('Zemin hazır olmadığı için başlangıç noktasına döndün.',true);
  }catch(error){game.notice('Geçiş tamamlanamadı: '+error.message,true);if(!rollbackStarted){try{onState({busy:true,phase:'rollback'});await restore(run);}catch(backError){recoveryError=backError;}}else recoveryError=error;}
  finally{finish(run);if(recoveryError){run.recoverySpawn=heap()?.[46];pendingRecovery=run;onState({busy:false,phase:'recovery',retry:true});}}
 }
 return {
  get busy(){clearRecovered();return !!active||!!pendingRecovery;},
  async run({prepare,commit,rollback,onArrived,custody=false,geometryBudget=17500}){
   clearRecovered();if(pendingRecovery)throw Error('Önce bekleyen geçişi geri almayı tekrar dene.');
   if(active||game.actionBusy)throw Error('Devam eden işlemin bitmesini bekle.');
   const run={seq:0,context:null,rollback,onArrived,phase:"prepare",cancelled:false};active=run;game.actionBusy=true;let committed=false,sent=false;
   try{
    const a=heap();if(!a||!a[7611]||a[62]||a[64]||game.vehicle||game.isDead)throw Error('Geçiş için dünyaya bağlanmış, hayatta ve yaya olmalısın.');
    const sourceSpawn=Atomics.load(a,46);onState({busy:true,phase:'prepare'});game.release?.();
    run.context=await prepare();const target=run.context.target,xyz=[target?.x,target?.y,target?.z];
    if(!xyz.every(Number.isFinite)||Math.abs(xyz[0])>16000||Math.abs(xyz[1])>16000||Math.abs(xyz[2])>3000)throw fail();
    if(Atomics.load(a,46)!==sourceSpawn)throw Error('Konumun değişti; geçişi yeniden başlat.');
    const m=mode(target,custody),f=new Float32Array(a.buffer,a.byteOffset,a.length);f.set(xyz,7704);a[7702]=m;a[7701]=1;run.seq=Atomics.add(a,7700,1)+1;
    run.phase='geometry';onState({busy:true,phase:'geometry',canCancel:true});const end=now()+Math.min(65000,Math.max(1000,Number.isFinite(geometryBudget)?geometryBudget:17500));let nextProgress46=now()+1000;
    while(now()<end){
     if(run.cancelled)throw Error('İç mekân hazırlığı iptal edildi. Konumun korundu.');if(Atomics.load(a,46)!==sourceSpawn)throw Error('Karakterin konumu değişti; geçiş iptal edildi.');
     if(a[7700]!==run.seq||a[7701]<0||a[2]===-1)throw fail();if(now()>=nextProgress46){nextProgress46=now()+1000;onState({busy:true,phase:'geometry',canCancel:true,detail:a[7702]===-1?'Dış konumun zemini kontrol ediliyor…':!a[7709]?'İç mekân yükleniyor…':!a[7710]?'Oda hazırlanıyor…':'İç mekânın zemini kontrol ediliyor…'});}
     if(a[7701]===2)break;
     await wait();
    }
    if(run.cancelled)throw Error('İç mekân hazırlığı iptal edildi. Konumun korundu.');if(a[7701]!==2)throw fail();
    run.phase='commit';onState({busy:true,phase:'commit'});sent=true;const response=await commit(run.context);
    if(!response?.spawn&&!response?.teleport)throw Error('Sunucu geçişi onaylamadı.');
    committed=true;onState({busy:true,phase:'arrival'});void arrival(run);return response;
   }catch(error){
    // A lost HTTP reply can hide a completed use. Roll back only through the server's bound ticket.
    if(sent&&run.context)try{await restore(run);}catch{}
    throw error;
   }finally{if(!committed){cancel(run);finish(run);}}
  },
  async retryRollback(){
   clearRecovered();if(!pendingRecovery||active)return;
   const run=pendingRecovery;active=run;pendingRecovery=null;game.actionBusy=true;onState({busy:true,phase:'rollback'});
   try{await restore(run);}catch(error){pendingRecovery=run;throw error;}finally{finish(run);if(pendingRecovery)onState({busy:false,phase:'recovery',retry:true});}
  },
  cancelPreparation(){if(!active||active.phase!=='geometry')return false;active.cancelled=true;cancel(active);return true;},
  cancel(){if(active)cancel(active);if(pendingRecovery)cancel(pendingRecovery);}
 };
}
window.PAVTransition32=coordinator;
addEventListener('pav-game-created',({detail:game})=>queueMicrotask(()=>queueMicrotask(()=>{
 if(window.PAVMobile?.active)return;
 const original=game.api,transition=coordinator(game,{onState:s=>dispatchEvent(new CustomEvent('pav-transition-state',{detail:{game,...s}}))});game.transitions32=transition;
 game.api=(path,data,...rest)=>{
  if(path!=='/api/properties/enter')return original(path,data,...rest);
  return transition.run({geometryBudget:65000,
   prepare:async()=>{const r=await original('/api/properties/preflight48',{id:Number(data?.id)});if(!r.success||!r.observation_only||!r.target)throw Error('Mülk erişimi doğrulanamadı.');return r;},
   commit:c=>original(path,{...data,preflight_version:c.version,preflight_life:c.life_id},...rest),rollback:c=>original('/api/properties/exit',{id:c.id})
  });
 };
 game.elevatorTravel32=async id=>{
  const r=await transition.run({prepare:()=>original('/api/elevators/prepare',{id}),commit:c=>original('/api/elevators/use',{ticket:c.ticket,ready:true}),rollback:c=>original('/api/elevators/rollback',{ticket:c.ticket})});
  game.applyLife(r);game.closeRP();game.notice('Geçiş onaylandı; varış kontrol ediliyor.');return r;
 };
})));})();
