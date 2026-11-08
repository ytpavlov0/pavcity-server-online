/* Shared native input, multi-touch ownership and conservative phone profile. */
(()=>{'use strict';
const q=new URLSearchParams(location.search),active=q.get('mobile')==='1'||q.get('mobile')!=='0'&&(/iPhone|iPad|Android/i.test(navigator.userAgent)||navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
window.PAVMobile={active,maxWidth:960,maxHeight:540,fps:30};document.documentElement.classList.toggle('pav-mobile',active);
class PAVTouchInput{
 constructor(getInput){this.getInput=getInput;this.keys=new Map();this.buttons=new Map();}
 key(owner,vk,on){const held=this.keys.get(vk)||new Set();on?held.add(owner):held.delete(owner);held.size?this.keys.set(vk,held):this.keys.delete(vk);const input=this.getInput();if(input){Atomics.store(input.keys,vk,held.size?128:0);Atomics.store(input.w,6,1);Atomics.store(input.w,7,1);}}
 button(owner,bit,on){const held=this.buttons.get(bit)||new Set();on?held.add(owner):held.delete(owner);held.size?this.buttons.set(bit,held):this.buttons.delete(bit);const input=this.getInput();if(input){held.size?Atomics.or(input.w,5,1<<bit):Atomics.and(input.w,5,~(1<<bit));Atomics.store(input.w,6,1);Atomics.store(input.w,7,1);}}
 move(owner,x,y,driving=false){this.key(owner,0x41,x<-.23);this.key(owner,0x44,x>.23);this.key(owner,0x57,y<-.23);this.key(owner,0x53,y>.23);this.key(owner,0xA0,!driving&&y<-.8);}
 look(dx,dy){const i=this.getInput();if(!i)return;Atomics.add(i.w,2,Math.round(dx));Atomics.add(i.w,3,Math.round(dy));Atomics.store(i.w,6,1);Atomics.store(i.w,7,1);}
 release(owner){for(const vk of [...this.keys.keys()])this.key(owner,vk,false);for(const bit of [...this.buttons.keys()])this.button(owner,bit,false);}
 reset(){for(const owners of [...this.keys.values(),...this.buttons.values()])for(const owner of [...owners])this.release(owner);}
}window.PAVTouchInput=PAVTouchInput;
if(!active)return;
addEventListener('pav-game-created',event=>{
 const game=event.detail,hud=game.hud;if(hud.querySelector('.pav-touch'))return;const input=new PAVTouchInput(()=>window.__wasmInput),pointers=new Map();let disabled=null,stickOwner=null;const voiceOwners=new Set();
 const root=document.createElement('div');root.className='pav-touch';root.innerHTML='<div class="pav-landscape"><b>PAVCITY</b><span>Rahat kontrol için telefonu yatay çevir.</span></div><div class="pav-touch-top"></div><div class="pav-stick" aria-label="Hareket joystick"><i></i></div><div class="pav-touch-actions"></div><div class="pav-touch-hint">SAĞ TARAFTA SÜRÜKLE · KAMERA</div>';hud.append(root);
 const top=root.querySelector('.pav-touch-top'),actions=root.querySelector('.pav-touch-actions'),stick=root.querySelector('.pav-stick'),knob=stick.querySelector('i');
 const ready=()=>hud.dataset.avatarReady==='1'&&Number(hud.dataset.nativeFrames)>0&&!document.hidden;
 const allowed=()=>ready()&&!game.menuOpen&&!game.chatOpen&&!game.uiOpen&&!game.isDead;
 const clear=()=>{pointers.clear();stickOwner=null;voiceOwners.clear();input.reset();knob.style.transform='translate(0,0)';game.pushVoice(false);};
 const button=(parent,label,icon,fn,hold)=>{const b=document.createElement('button');b.innerHTML=PAVIcons.get(icon)+'<span>'+label+'</span>';b.setAttribute('aria-label',label);parent.append(b);if(hold){b.onpointerdown=e=>{if(!allowed())return;e.preventDefault();try{b.setPointerCapture(e.pointerId);}catch{}hold(e.pointerId,true);};b.onpointerup=b.onpointercancel=b.onlostpointercapture=e=>hold(e.pointerId,false);}else b.onclick=()=>Promise.resolve(fn()).catch(e=>game.notice(e.message,true));return b;};
 button(top,'Menü','menu',()=>{const next=!game.menuOpen;clear();game.closeFeatures?.();game.closeOverlay?.();game.closeActions?.();game.setMenu(next);});button(top,'Sohbet','chat',()=>game.openChat('local'));button(top,'Çanta','bag',()=>game.inventory());button(top,'Oyuncular','users',()=>game.scoreboard());button(top,'Telefon','phone',()=>game.phone());
 button(actions,'Ateş','fire',null,(id,on)=>input.button(id,0,on));button(actions,'Nişan','aim',null,(id,on)=>input.button(id,1,on));button(actions,'Zıpla','jump',null,(id,on)=>input.key(id,0x20,on));button(actions,'Doldur','reload',null,(id,on)=>input.key(id,0x52,on));button(actions,'Bin / in','car',()=>game.nearestDoor());button(actions,'Kontak','engine',()=>game.vehicleAction('engine',game.vehicle));button(actions,'Etkileşim','eye',()=>game.eyeMode?game.eyeMode():game.targets());button(actions,'Konuş','mic',null,(id,on)=>{on?voiceOwners.add(id):voiceOwners.delete(id);game.pushVoice(voiceOwners.size>0);});
 stick.onpointerdown=e=>{if(!allowed()||stickOwner!==null)return;e.preventDefault();stickOwner=e.pointerId;try{stick.setPointerCapture(e.pointerId);}catch{}const r=stick.getBoundingClientRect();pointers.set(e.pointerId,{kind:'stick',cx:r.left+r.width/2,cy:r.top+r.height/2,r:r.width*.36});stick.onpointermove(e);};
 stick.onpointermove=e=>{const p=pointers.get(e.pointerId);if(!p||p.kind!=='stick'||stickOwner!==e.pointerId)return;if(!allowed()){clear();return;}const x=(e.clientX-p.cx)/p.r,y=(e.clientY-p.cy)/p.r,len=Math.max(1,Math.hypot(x,y));input.move(e.pointerId,x/len,y/len,!!game.vehicle);knob.style.transform=`translate(${x/len*p.r}px,${y/len*p.r}px)`;};
 stick.onpointerup=stick.onpointercancel=stick.onlostpointercapture=e=>{input.release(e.pointerId);pointers.delete(e.pointerId);if(stickOwner===e.pointerId){stickOwner=null;knob.style.transform='translate(0,0)';}};
 const canvas=document.getElementById('canvas');canvas.addEventListener('pointerdown',e=>{if(e.pointerType==='mouse'||!allowed())return;e.preventDefault();try{canvas.setPointerCapture(e.pointerId);}catch{}pointers.set(e.pointerId,{kind:'look',x:e.clientX,y:e.clientY});},{passive:false});
 canvas.addEventListener('pointermove',e=>{const p=pointers.get(e.pointerId);if(p?.kind!=='look'||!allowed())return;input.look((e.clientX-p.x)*1.2,(e.clientY-p.y)*1.2);p.x=e.clientX;p.y=e.clientY;});
 for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,e=>pointers.delete(e.pointerId));
 const previous=window.pnReleaseGameInput;window.pnReleaseGameInput=()=>{previous?.();clear();};
 addEventListener('blur',clear);addEventListener('pagehide',clear);addEventListener('orientationchange',clear);document.addEventListener('visibilitychange',clear);
 let last=0;function frame(now){if(!hud.isConnected){clear();return;}requestAnimationFrame(frame);if(now-last<100)return;last=now;const next=!allowed();root.classList.toggle('world-loading',!ready());if(next!==disabled){disabled=next;root.classList.toggle('controls-disabled',next);if(next)clear();}root.classList.toggle('driving',!!game.vehicle);}
 root.classList.add('controls-disabled','world-loading');requestAnimationFrame(frame);
});})();
