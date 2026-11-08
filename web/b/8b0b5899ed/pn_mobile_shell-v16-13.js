'use strict';
function loadRuntime(event){
 const data=event.data;
 if(data?.cmd!==1||typeof data.pnScript!=='string')throw Error('Mobil işçi motor bağlantısı bekleniyor.');
 if(data.pnWorkerTrace&&data.pnInstance>0&&data.pnInstance<=32){
  self.__pnWorkerTrace=new Int32Array(data.pnWorkerTrace);self.__pnWorkerID=data.pnInstance;
 }
 const mark=phase=>{const t=self.__pnWorkerTrace,id=self.__pnWorkerID;if(t){Atomics.store(t,16+id*3,phase);Atomics.store(t,2,id);Atomics.store(t,3,phase);Atomics.add(t,1,1);}};
 let held=null;
 self.__pnReleaseImportGate=()=>{if(held){const gate=held;held=null;Atomics.store(gate,0,0);Atomics.notify(gate,0,1);}};
 try{
  if(data.pnStartupGate){
   const gate=new Int32Array(data.pnStartupGate),deadline=Date.now()+30000;mark(10);
   while(Atomics.compareExchange(gate,0,0,1)!==0){if(Date.now()>deadline)throw Error('Mobil işçi başlangıç sırası zaman aşımına uğradı.');Atomics.wait(gate,0,1,1000);}
   held=gate;data.pnImportGateHeld=true;
  }
  mark(1);importScripts(data.pnScript);mark(2);
  const receive=self.onmessage;
  if(receive===loadRuntime||typeof receive!=='function')throw Error('Mobil işçi motor bağlantısı kurulamadı.');
  receive(event);
 }catch(e){self.__pnReleaseImportGate();mark(9);throw e;}
}
self.onmessage=loadRuntime;
postMessage({pnShellReady:true});
