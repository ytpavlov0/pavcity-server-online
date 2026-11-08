/* An explicitly exterior meeting point; no unavailable interior is advertised. */
(()=>{'use strict';const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
addEventListener('pav-game-created',({detail:g})=>queueMicrotask(()=>queueMicrotask(()=>{
 const previous=g.openService;g.community40=async()=>{const r=await g.api('/api/community179/open',{}),s=r.service,p=g.openRP(s.name,'<p>'+esc(r.description)+'</p><p>Yakın IC sohbet ve sesli konuşma için bu buluşma noktasını kullanabilirsin.</p><button data-cafe-gps>Konumu GPS’e işle</button>','pav-community40');p.querySelector('[data-cafe-gps]').onclick=()=>{g.setWaypoint(s.x,s.y);g.notice('Buluşma noktası GPS’e işlendi.');};};
 g.openService=(kind,...args)=>kind==='cafe'?g.community40():previous(kind,...args);
 const old=g.commandRP;g.commandRP=async text=>{if(/^\/(uwu|mekanlar)$/.test(text.trim())){const r=await g.api('/api/community179/list',{}),s=r.venues[0];if(s){g.setWaypoint(s.x,s.y);g.notice(s.name+' · Dış buluşma noktası GPS’e işlendi.');}return true;}return old?old(text):false;};
})));})();
