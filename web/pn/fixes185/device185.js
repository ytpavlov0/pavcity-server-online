/* 185: device identity for moderation (ban evasion). A random device id is kept in localStorage, sessionStorage-proof
 * cookie and IndexedDB (restored from whichever survives), and a hardware/browser fingerprint (screen, cores, memory,
 * time zone, languages, platform, WebGL renderer) is hashed with SHA-256. Both travel to the server in the pav_dev
 * cookie (base64url JSON: d = device id, f = fingerprint, z = time zone, l = language) on every request; nothing else
 * is sent. The server uses them for /cihazban and the same-device / VPN hints shown to staff. */
(()=>{'use strict';
const KEY='pav_did',COOKIE='pav_dev';
const rnd=()=>{const b=new Uint8Array(16);crypto.getRandomValues(b);return Array.from(b,x=>x.toString(16).padStart(2,'0')).join('');};
const getCookie=n=>{const m=document.cookie.match(new RegExp('(?:^|; )'+n+'=([^;]*)'));return m?decodeURIComponent(m[1]):'';};
let did='';try{did=localStorage.getItem(KEY)||'';}catch{}
if(!/^[0-9a-f]{32}$/.test(did)){const c=getCookie(KEY);if(/^[0-9a-f]{32}$/.test(c))did=c;}
const idbGet=()=>new Promise(res=>{try{const r=indexedDB.open('pav185',1);r.onupgradeneeded=()=>r.result.createObjectStore('k');r.onerror=()=>res('');r.onsuccess=()=>{try{const g=r.result.transaction('k').objectStore('k').get(KEY);g.onsuccess=()=>res(g.result||'');g.onerror=()=>res('');}catch{res('');}};}catch{res('');}});
const idbSet=v=>{try{const r=indexedDB.open('pav185',1);r.onupgradeneeded=()=>r.result.createObjectStore('k');r.onsuccess=()=>{try{r.result.transaction('k','readwrite').objectStore('k').put(v,KEY);}catch{}};}catch{}};
const tz=(()=>{try{return Intl.DateTimeFormat().resolvedOptions().timeZone||'';}catch{return'';}})(),lang=(navigator.language||'').slice(0,12);
let fp='';
function write(){
 try{localStorage.setItem(KEY,did);}catch{}
 const secure=location.protocol==='https:'?'; Secure':'';
 document.cookie=KEY+'='+did+'; Path=/; Max-Age=31536000; SameSite=Lax'+secure;
 const payload=btoa(JSON.stringify({d:did,f:fp,z:tz,l:lang})).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 document.cookie=COOKIE+'='+payload+'; Path=/; Max-Age=31536000; SameSite=Lax'+secure;}
function gl(){try{const c=document.createElement('canvas'),g=c.getContext('webgl')||c.getContext('experimental-webgl');if(!g)return'';const e=g.getExtension('WEBGL_debug_renderer_info');return e?(g.getParameter(e.UNMASKED_VENDOR_WEBGL)+'|'+g.getParameter(e.UNMASKED_RENDERER_WEBGL)):(g.getParameter(g.VENDOR)+'|'+g.getParameter(g.RENDERER));}catch{return'';}}
async function fingerprint(){
 const parts=[screen.width+'x'+screen.height+'x'+screen.colorDepth,devicePixelRatio,navigator.hardwareConcurrency||0,navigator.deviceMemory||0,tz,(navigator.languages||[]).join(','),navigator.platform||'',gl(),navigator.maxTouchPoints||0];
 try{const h=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(parts.join('#')));return Array.from(new Uint8Array(h).slice(0,16),x=>x.toString(16).padStart(2,'0')).join('');}catch{return'';}}
if(!/^[0-9a-f]{32}$/.test(did))did='';
if(did)write();
(async()=>{const stored=await idbGet();if(!did&&/^[0-9a-f]{32}$/.test(stored))did=stored;if(!did)did=rnd();idbSet(did);write();fp=await fingerprint();write();})();
window.__pavDevice185={get:()=>({did,fp,tz,lang})};
})();
