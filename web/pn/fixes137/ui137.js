/* PAVCITY 137: chat log stays put when the input opens. Adds chat137.css to the same-origin chat frame and
 * pins its scroll containers at 0 (focus/caret scrolling can no longer shift the log). */
(()=>{'use strict';
const CSS='/pn/fixes137/chat137.css?build='+((document.currentScript?.src||'').split('build=')[1]||'137');
function patch(frame){let doc;try{doc=frame.contentDocument;}catch{return;}if(!doc||!/chat/.test(doc.URL))return;
 if(doc.readyState==='loading'){doc.addEventListener('DOMContentLoaded',()=>patch(frame),{once:true});return;}
 if(doc.documentElement.dataset.chat137)return;doc.documentElement.dataset.chat137='1';
 const link=doc.createElement('link');link.rel='stylesheet';link.href=CSS;doc.head.append(link);
 const pin=el=>el&&el.addEventListener('scroll',()=>{if(el.scrollTop)el.scrollTop=0;},{passive:true});
 pin(doc.querySelector('.chat'));pin(doc.documentElement);pin(doc.body);}
function install(g){if(g?.chat137)return;if(g)g.chat137=true;
 const hook=()=>{const frame=document.querySelector('#pn-game .pn-chat');if(!frame)return false;if(!frame.chat137){frame.chat137=true;frame.addEventListener('load',()=>patch(frame));}patch(frame);return true;};
 if(!hook()){const t=setInterval(()=>{if(hook())clearInterval(t);},500);setTimeout(()=>clearInterval(t),60000);}}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
