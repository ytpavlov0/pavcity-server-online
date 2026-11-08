/* 16 kHz mono PCM capture. No audio leaves this VDS's own API. */
class PNCapture extends AudioWorkletProcessor{
 constructor(){super();this.on=false;this.pcm=new Int16Array(1600);this.used=0;this.clock=0;this.port.onmessage=e=>{if(this.on&&!e.data&&this.used>=160){const pcm=this.pcm.slice(0,this.used).buffer;this.port.postMessage({pcm,tail:true},[pcm]);}this.on=!!e.data;this.used=0;this.clock=0;};}
 process(inputs,outputs){
  const input=inputs[0]?.[0];if(!this.on||!input)return true;
  const step=sampleRate/16000;
  for(;this.clock<input.length;this.clock+=step){const n=Math.floor(this.clock),part=this.clock-n;const v=input[n]+((input[Math.min(n+1,input.length-1)]||0)-input[n])*part;this.pcm[this.used++]=Math.round(Math.max(-1,Math.min(1,v))*32767);if(this.used===1600){const pcm=this.pcm.buffer;this.port.postMessage({pcm,tail:false},[pcm]);this.pcm=new Int16Array(1600);this.used=0;}}
  this.clock-=input.length;return true;
 }
}
registerProcessor('pn-capture',PNCapture);
