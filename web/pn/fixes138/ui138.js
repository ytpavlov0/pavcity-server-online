/* PAVCITY 138: game audio. The engine's gain stayed at 0 unless the "Oyun sesini aç" button in the city tab had
 * been pressed once, so ambient, weapon and NPC sounds were silent while the "Oyun sesi" slider showed 100%.
 * The entry now treats sound as on unless it was turned off on purpose, and raising the slider turns it on. */
(()=>{'use strict';
function wrap(){const set=window.setPNGameVolume;if(typeof set!=='function'||set.w138)return !!set;
 const next=value=>{if(Number(value)>0&&localStorage.getItem('pav-sound-consent')!=='yes'){try{localStorage.setItem('pav-sound-consent','yes');}catch{}window.enablePAVAudio?.(true);}return set(value);};
 next.w138=true;window.setPNGameVolume=next;return true;}
if(!wrap())addEventListener('DOMContentLoaded',wrap,{once:true});
addEventListener('pav-game-created',()=>{wrap();zone();});
/* 138: the AFK zone (features134, Vespucci) is not a server service, so the radar and map never drew it. */
const AFK={x:-1270,y:-1520};
function zone(){const map=window.PAVMap;if(!map?.markers||map.markers.afk138)return;const original=map.markers;
 const markers=function(ctx,point,data,width,height){original.apply(this,arguments);try{const [x,y]=point(AFK.x,AFK.y);if(x<12||y<12||x>width-12||y>height-20)return;
  ctx.save();ctx.translate(x,y);ctx.shadowColor='rgba(0,0,0,.55)';ctx.shadowBlur=6;ctx.fillStyle='#140c20f2';ctx.beginPath();ctx.arc(0,0,11,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
  ctx.lineWidth=2;ctx.strokeStyle='#5ee6a8';ctx.stroke();ctx.fillStyle='#5ee6a8';ctx.font='800 7.5px "Segoe UI",sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('AFK',0,.5);ctx.restore();}catch{}};
 markers.afk138=true;map.markers=markers;}
zone();
/* 138: Z only talks while the microphone is on (voice.push needs voice.enabled); turning it on meant clicking the
 * mic pill, which is awkward in a vehicle. Z now switches the microphone on and starts talking if still held. */
let held138=false,starting138=false;
addEventListener('keyup',e=>{if(e.code==='KeyZ')held138=false;},true);
addEventListener('keydown',e=>{if(e.code!=='KeyZ'||e.repeat||e.ctrlKey||e.altKey)return;held138=true;const g=window.PAVGame,v=g?.voice;
 if(!v||v.enabled||starting138||g.uiOpen||g.isDead||g.menuOpen||document.activeElement?.matches?.('input,textarea,select,[contenteditable]'))return;
 starting138=true;Promise.resolve(v.toggle()).then(()=>{if(held138&&v.enabled)g.pushVoice?g.pushVoice(true):v.push(true);}).catch(x=>g.notice?.(x.message,true)).finally(()=>{starting138=false;});},true);
})();
