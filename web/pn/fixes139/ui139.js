/* PAVCITY 139: one door prompt and chat command aliases.
 * - When the E prompt (controls 109) and the door prompt (city-ui 72) show together, the door prompt's key hints
 *   (K: lock, E: exit) are appended to the E prompt and the door prompt is hidden.
 * - Chat: /meslekler (and /isler, /işler) run /meslek; /help runs /yardim; /komut runs /komutlar. */
(()=>{'use strict';
const ALIAS=[[/^\/(meslekler|isler|işler)(?=\s|$)/i,'/meslek'],[/^\/help(?=\s|$)/i,'/yardim'],[/^\/komut(?=\s|$)/i,'/komutlar']];
function chat(frame){let doc;try{doc=frame.contentDocument;}catch{return;}if(!doc||!/chat/.test(doc.URL))return;
 if(doc.readyState==='loading'){doc.addEventListener('DOMContentLoaded',()=>chat(frame),{once:true});return;}
 if(doc.documentElement.dataset.chat139)return;doc.documentElement.dataset.chat139='1';
 // Window capture runs before the chat's own document-level Enter handler reads the field.
 doc.defaultView.addEventListener('keydown',e=>{if(e.key!=='Enter'&&e.keyCode!==13)return;const input=doc.querySelector('.chat__input');if(!input)return;const v=input.value.trim();for(const [rx,to] of ALIAS)if(rx.test(v)){input.value=v.replace(rx,to);break;}},true);}
function install(g){if(!g?.hud||g.ui139)return;g.ui139=true;
 const hook=()=>{const frame=document.querySelector('#pn-game .pn-chat');if(!frame)return false;if(!frame.chat139){frame.chat139=true;frame.addEventListener('load',()=>chat(frame));}chat(frame);return true;};
 if(!hook()){const t=setInterval(()=>{if(hook())clearInterval(t);},500);setTimeout(()=>clearInterval(t),60000);}
 const t=setInterval(()=>{if(!g.hud.isConnected){clearInterval(t);return;}
  const door=g.hud.querySelector('.p72-door'),hold=g.hud.querySelector('.pav-hold-prompt'),span=hold?.querySelector('span');
  const both=!!door&&!door.hidden&&!!hold&&!hold.hidden&&!!span;
  const extra=both?(door.textContent.match(/[EK]: [^·]+/g)||[]).filter(k=>!k.startsWith('E: Gir')).map(k=>' · '+k.trim()).join(''):'';
  if(door&&door.classList.contains('merged139')!==both)door.classList.toggle('merged139',both);
  if(span&&(span.dataset.extra139||'')!==extra){if(extra)span.dataset.extra139=extra;else delete span.dataset.extra139;}},150);}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
