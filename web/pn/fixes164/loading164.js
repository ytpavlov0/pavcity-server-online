/* 164: live detail under the "Los Santos yükleniyor NN%" bar of the character screen (client .pav-load104). A long wait
 * near 76 % looked frozen; the engine was downloading / reading game data the whole time. This listens to the same
 * game-progress channel the page uses ({dl} downloaded bytes, {lines} engine log, {label}) and shows: downloaded MB and
 * speed, the file / step being read now, and after 6 s without new data a "preparing files, not frozen" note.
 * Stops for good when the character is in the world (pav-game-ready). */
(()=>{'use strict';
const css='.pav-load164{display:flex;flex-direction:column;gap:3px;margin-top:2px;font:500 12px/1.35 inherit;color:rgba(255,255,255,.86)}.pav-load164 b{color:#8ff0c4;font-variant-numeric:tabular-nums}.pav-load164 .w{color:#ffd27a}.pav-load164 small{font:500 11px/1.3 Consolas,monospace;color:rgba(220,230,240,.7);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:min(420px,72vw)}';
let bytes=0,lastLine='',lastLabel='',changedAt=performance.now(),timer=0,bc=null;const samples=[];
try{bc=new BroadcastChannel('game-progress');bc.onmessage=e=>{const m=e.data||{};
 if(m.dl){bytes+=m.dl;samples.push([performance.now(),m.dl]);changedAt=performance.now();}
 if(Array.isArray(m.lines)&&m.lines.length){lastLine=String(m.lines[m.lines.length-1]);changedAt=performance.now();}
 if(m.label){lastLabel=String(m.label);}};}catch{}
const short=s=>{s=s.replace(/\s+/g,' ').trim();return s.length>150?s.slice(0,147)+'…':s;};
function tick(){
 const box=document.querySelector('.pav-load104');if(!box)return;
 if(!document.getElementById('pav-load164-style')){const s=document.createElement('style');s.id='pav-load164-style';s.textContent=css;document.head.append(s);}
 let el=box.querySelector('.pav-load164');if(!el){el=document.createElement('div');el.className='pav-load164';el.setAttribute('role','status');box.append(el);}
 const now=performance.now();while(samples.length&&now-samples[0][0]>3000)samples.shift();const speed=samples.reduce((n,s)=>n+s[1],0)/3/1048576;
 el.textContent='';const row=document.createElement('div');
 const add=(tag,t,cls)=>{const n=document.createElement(tag);if(cls)n.className=cls;n.textContent=t;row.append(n);};
 add('span','İndirilen oyun verisi: ');add('b',(bytes/1048576|0)+' MB');if(speed>.05)add('span',' · '+speed.toFixed(1)+' MB/s');
 if(now-changedAt>6000)add('span',' · Dosyalar hazırlanıyor, lütfen bekle — oyun donmadı','w');
 el.append(row);const detail=lastLine||lastLabel;if(detail){const s=document.createElement('small');s.textContent=short(detail);el.append(s);}
}
timer=setInterval(tick,400);
addEventListener('pav-game-ready',()=>{clearInterval(timer);try{bc?.close();}catch{}document.querySelectorAll('.pav-load164').forEach(n=>n.remove());},{once:true});
})();
