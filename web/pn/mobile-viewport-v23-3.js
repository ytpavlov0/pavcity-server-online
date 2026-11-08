/* Mobile UI viewport and bounded render-target resizing. Pinch zoom on forms remains available. */
(()=>{'use strict';if(!window.PAVMobile?.active)return;
const root=document.documentElement,vv=window.visualViewport;
window.PAVMobileAudio={ready:false,note(phase){
 const record=window.PAVMobileCheckpoint?.debugRecord?.();if(!record?.attempt)return;
 try{fetch('/mobile-diagnostics',{method:'POST',headers:{'Content-Type':'application/json'},keepalive:true,body:JSON.stringify({...record,release:'v16.18-ui23.3',phase:'browser-audio-'+phase})}).catch(()=>{});}catch{}
}};
let scheduled=false,locked=false,online=false,lastWidth=0,lastHeight=0,nativeWidth=0,nativeHeight=0;
function update(){
 scheduled=false;
 // Pinching changes the visual viewport, not the document layout. Do not make
 // the form chase fingers or resize native GPU targets for browser zoom.
 if(vv&&Math.abs((vv.scale||1)-1)>.05)return;
 const width=Math.max(1,Math.round(root.clientWidth||innerWidth));
 const height=Math.max(1,Math.round(vv?.height||innerHeight));
 const top=Math.max(0,Math.round(vv?.offsetTop||0));
 if(width!==lastWidth){root.style.setProperty('--pav-layout-width',width+'px');lastWidth=width;}
 if(height!==lastHeight){root.style.setProperty('--pav-visible-height',height+'px');lastHeight=height;}
 root.style.setProperty('--pav-viewport-top',top+'px');
}
function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(update);}}
function dimensions(){return {width:root.clientWidth||innerWidth,height:root.clientHeight||innerHeight};}
function unlock(){if(!locked)return;locked=false;window.PAVMobileAudio.ready=true;window.tryStartAudio?.();dispatchEvent(new Event('resize'));}
window.PAVMobileViewport={
 renderSize(){const d=dimensions();return locked?{width:nativeWidth,height:nativeHeight}:d;},
 deferNativeResize(){return locked||!!(vv&&Math.abs((vv.scale||1)-1)>.05)||/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName||'');},
};
addEventListener('gta-story-start',event=>{const d=dimensions();nativeWidth=d.width;nativeHeight=d.height;online=!!event.detail?.online;locked=true;});
addEventListener('pav-assets-ready',unlock);
const progress=new BroadcastChannel('game-progress');progress.onmessage=({data})=>{if(data.world&&!online)unlock();};
addEventListener('resize',schedule);addEventListener('orientationchange',schedule);addEventListener('pageshow',schedule);
vv?.addEventListener('resize',schedule);vv?.addEventListener('scroll',schedule);
document.addEventListener('focusin',schedule);document.addEventListener('focusout',()=>{schedule();if(!locked)dispatchEvent(new Event('resize'));});
update();
})();
