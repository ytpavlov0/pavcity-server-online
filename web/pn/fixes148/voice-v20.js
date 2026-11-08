/* Separate playback consent from microphone consent; bounded own-server PCM.
 * 19: voice no longer drops in and out over a slow tunnel. The sender queued at most 3 chunks of 100 ms and sent them one
 * request at a time, so any round trip over 100 ms dropped audio; queued chunks now go together (up to the server's
 * 8000-byte packet), the queue holds 10 and only audio older than 1.2 s is dropped. The receiver starts each burst
 * 250 ms ahead (was 100 ms) and keeps up to 1.2 s scheduled (was 0.5 s), so poll jitter no longer leaves gaps.
 * 20: no more slight tremble. Each 100-200 ms chunk had its own gain node set to the distance at that moment (volume
 * stepped at every chunk boundary) and was resampled by the browser on its own (an edge at every boundary). Now one
 * gain node per speaker follows the distance smoothly (150 ms), the 16 kHz stream is resampled here to the context rate
 * continuously across chunks, and chunks are scheduled back to back on exact sample frames. */
(()=>{'use strict';
const MIC='<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="7" y="2" width="6" height="10" rx="3" fill="currentColor"/><path d="M4 9a6 6 0 0012 0M10 15v3m-3 0h6" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>';
window.PNMicIcon=MIC;
window.PNVoice=class{
 constructor(send,onState){Object.assign(this,{send,onState,enabled:false,listening:false,talking:false,opening:false,pending:false,volume:1,lastSend:0,closed:false,error:null});this.queue=new Map();this.received=new Map();this.nodes=new Set();this.outgoing=[];}
 async listen(){if(this.closed)return;this.context??=new (window.AudioContext||window.webkitAudioContext)();await this.context.resume();this.listening=this.context.state==='running';}
 async toggle(){
  if(this.opening||this.closed)return;
  if(this.enabled){this.push(false);this.enabled=false;this.outgoing.length=0;this.stream?.getTracks().forEach(t=>t.enabled=false);this.onState('Dinleme açık · Mikrofon kapalı',false);return;}
  this.opening=true;this.error=null;let cancelled=false;
  try{
   if(!this.stream){
    if(!navigator.mediaDevices?.getUserMedia)throw Error('Mikrofon için HTTPS bağlantısı gerekli.');
    // Both permission and AudioContext.resume begin inside the tap gesture.
    // Waiting for resume before getUserMedia loses activation on some WebKit builds.
    const capture=navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true,autoGainControl:true},video:false}).then(stream=>{if(cancelled||this.closed){stream.getTracks().forEach(t=>t.stop());return null;}this.stream=stream;return stream;});
    const [stream]=await Promise.all([capture,this.listen()]);if(!stream)return;
    if(this.closed){stream.getTracks().forEach(t=>t.stop());return;}
    this.stream=stream;await this.context.audioWorklet.addModule('/pn/voice-worklet-v18.js');
    this.capture=new AudioWorkletNode(this.context,'pn-capture');this.source=this.context.createMediaStreamSource(stream);this.silence=this.context.createGain();this.silence.gain.value=0;
    this.source.connect(this.capture);this.capture.connect(this.silence).connect(this.context.destination);
    this.capture.port.onmessage=({data})=>{if(!this.enabled||(!this.talking&&!data.tail))return;const bytes=new Uint8Array(data.pcm);let str='';for(const b of bytes)str+=String.fromCharCode(b);this.outgoing.push({str,at:Date.now()});while(this.outgoing.length>10)this.outgoing.shift();this.drain();};
    for(const t of stream.getTracks())t.onended=()=>{this.enabled=false;this.push(false);this.cleanupMic();this.onState('Mikrofon bağlantısı kesildi · Yeniden aç',false);};
   }else await this.listen();
   this.stream.getTracks().forEach(t=>t.enabled=true);this.enabled=true;this.onState('Z basılı tut · 30 m',true);
  }catch(error){cancelled=true;this.cleanupMic();this.enabled=false;this.talking=false;const labels={NotAllowedError:'Mikrofon izni yok · Dinleme açık',NotFoundError:'Mikrofon bulunamadı · Dinleme açık',NotReadableError:'Mikrofon kullanılamıyor · Dinleme açık'};this.error=labels[error.name]||('Mikrofon: '+error.message);this.onState(this.error,false);}
  finally{this.opening=false;}
  return {enabled:this.enabled,error:this.error};
 }
 cleanupMic(){this.stream?.getTracks().forEach(t=>{t.onended=null;t.stop();});for(const n of [this.capture,this.source,this.silence])n?.disconnect();if(this.capture)this.capture.port.onmessage=null;this.stream=this.capture=this.source=this.silence=null;this.outgoing.length=0;}
 async drain(){if(this.pending)return;this.pending=true;try{while(this.enabled&&this.outgoing.length){const wait=100-(Date.now()-this.lastSend);if(wait>0)await new Promise(r=>setTimeout(r,wait));if(!this.enabled)break;const p=this.outgoing.shift();if(Date.now()-p.at>1200)continue;let str=p.str;while(this.outgoing.length&&str.length+this.outgoing[0].str.length<=8000)str+=this.outgoing.shift().str;this.lastSend=Date.now();try{await this.send({audio:btoa(str)});}catch(e){this.outgoing.length=0;this.onState('Ses gönderilemedi: '+e.message,this.enabled);}}}finally{this.pending=false;}}
 push(active){this.talking=!!active&&this.enabled;this.capture?.port.postMessage(this.talking);this.onState(this.talking?'Konuşuyorsun · 30 m':this.enabled?'Z basılı tut · 30 m':this.listening?'Dinleme açık · Mikrofon kapalı':'Sesi aç',this.enabled,this.talking);}
 play(packets,own,serverTime){
  if(!this.listening||!this.context||this.context.state!=='running'||!own)return;
  const ctx=this.context,sr=ctx.sampleRate,step=16000/sr,volume=Math.max(0,Math.min(1,this.volume));this.speakers??=new Map();
  for(const p of packets||[]){
   if(!Number.isInteger(p.seq)||p.seq<=(this.received.get(p.char_id)||0))continue;
   this.received.set(p.char_id,p.seq);
   const age=Number.isFinite(p.age)?p.age:(serverTime??Date.now()/1000)-(p.time||0);if(age>1.5)continue;
   const d=Math.hypot(p.x-own.x,p.y-own.y,p.z-own.z);if(!Number.isFinite(d)||d>30)continue;
   let bytes;try{bytes=Uint8Array.from(atob(p.audio),c=>c.charCodeAt(0));}catch{continue;}if(bytes.length<320||bytes.length>8000||bytes.length%2)continue;
   const now=ctx.currentTime,level=(1-d/30)*volume;let sp=this.speakers.get(p.char_id);
   if(!sp){sp={gain:ctx.createGain(),at:0,last:0,phase:0,seen:now};sp.gain.gain.value=level;sp.gain.connect(ctx.destination);this.speakers.set(p.char_id,sp);}
   sp.seen=now;sp.gain.gain.setTargetAtTime(level,now,.15);if(sp.at-now>1.2)continue;
   const pcm=new DataView(bytes.buffer),n=bytes.length/2,x=i=>i<0?sp.last:pcm.getInt16(i*2,true)/32768;
   if(sp.at<now+.005){sp.at=Math.round((now+.25)*sr)/sr;sp.phase=0;sp.last=x(0);}
   // positions phase+k*step that still have a right neighbour in this chunk; the rest continue in the next one
   const count=n-1-sp.phase>0?Math.ceil((n-1-sp.phase)/step):0;
   if(count>0){const buffer=ctx.createBuffer(1,count,sr),out=buffer.getChannelData(0);
    for(let k=0;k<count;k++){const pos=sp.phase+k*step,i=Math.floor(pos),a=x(i);out[k]=a+(x(i+1)-a)*(pos-i);}
    const node=ctx.createBufferSource();node.buffer=buffer;node.connect(sp.gain);node.start(sp.at);sp.at+=count/sr;
    this.nodes.add(node);node.onended=()=>{this.nodes.delete(node);node.disconnect();};}
   sp.phase=sp.phase+count*step-n;sp.last=x(n-1);
  }
  for(const [id,sp] of this.speakers)if(sp.seen<ctx.currentTime-10){sp.gain.disconnect();this.speakers.delete(id);}
  while(this.received.size>64)this.received.delete(this.received.keys().next().value);
 }
 resetReceive(){for(const n of this.nodes){try{n.stop();}catch{}}this.nodes.clear();this.queue.clear();for(const sp of this.speakers?.values()||[])sp.gain.disconnect();this.speakers?.clear();this.received.clear();}
 close(){this.closed=true;this.enabled=false;this.push(false);this.cleanupMic();this.resetReceive();this.context?.close();this.listening=false;}
};
})();
