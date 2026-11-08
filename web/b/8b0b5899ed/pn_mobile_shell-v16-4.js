'use strict';
function loadRuntime(event){
 const data=event.data;
 if(data?.cmd!==1||typeof data.pnScript!=='string')throw Error('Mobil işçi ilk görevinde motor bağlantısı bekleniyor.');
 importScripts(data.pnScript);
 const receive=self.onmessage;
 if(receive===loadRuntime||typeof receive!=='function')throw Error('Mobil işçi motor bağlantısı kurulamadı.');
 receive(event);
}
self.onmessage=loadRuntime;
postMessage({pnShellReady:true});
