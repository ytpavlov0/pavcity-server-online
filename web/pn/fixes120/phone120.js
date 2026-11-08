/* PAVCITY phone 120: when the phone is closed, an incoming call or a new message slides the phone's
 * edge in from the right with an iOS-style banner (4.5 s, or until the call is answered/ended).
 * Reads the phone's own /api/phone/status polling; adds no requests. */
(()=>{'use strict';
const icon=n=>window.PAVIcons105?.svg(n)||'';
function install(g){
 if(!g?.hud||g.phone120)return;g.phone120=true;
 const box=document.createElement('aside');box.className='pk120';box.setAttribute('role','status');box.innerHTML='<span class="pk120-i"></span><div><b></b><small></small></div>';g.hud.append(box);
 let timer=0,lastCall=0,lastUnread=null;
 const peek=(kind,title,text,ms=4500)=>{if(g.phonePanelOpen)return;const i=box.querySelector('.pk120-i');i.className='pk120-i '+kind;i.innerHTML=icon(kind==='call'?'phone':'support');box.querySelector('b').textContent=title;box.querySelector('small').textContent=text;box.classList.add('in');clearTimeout(timer);timer=setTimeout(()=>box.classList.remove('in'),ms);};
 const api=g.api;g.api=async(path,data)=>{const r=await api(path,data);if(path==='/api/phone/status'&&r&&r.has_phone!==false){
  const c=r.call;if(c&&c.state==='ringing'&&c.target===g.character?.id&&c.id!==lastCall){lastCall=c.id;peek('call','Gelen arama',(c.peer_number?String(c.peer_number):'Bilinmeyen')+' · ↑ ile aç',9000);}
  if(!c||c.state!=='ringing')if(box.querySelector('.pk120-i.call'))box.classList.remove('in');
  const unread=Number(r.unread)||0;if(lastUnread!==null&&unread>lastUnread){const m=(r.messages||[]).find(x=>x&&x.sender!==r.number)||(r.messages||[])[0];peek('sms','Yeni mesaj',m?.body?String(m.body).slice(0,80):'Mesajlar · ↑ ile aç');}lastUnread=unread;}
  return r;};
 addEventListener('pav-game-stop',()=>{clearTimeout(timer);box.remove();},{once:true});
}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
