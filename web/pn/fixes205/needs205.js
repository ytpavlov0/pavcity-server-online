/* 205: hunger and thirst have a cost. At 0 (server values, every sync) the player loses 2 health every 15 s for each
 * empty need (4 when both are empty), down to 115 (it does not kill on its own); a notice every 60 s says why. The
 * bridge (v205, cell a[16383]: running total of damage points asked for) lowers the native health; the server keeps
 * the lower value as it does for any damage. Nothing happens while dead or before the bridge is up. */
(()=>{'use strict';
const EVERY=15000,FLOOR=115,NOTE=60000;
let g=null,needs=null,health=200,last=0,noted=-Infinity;
addEventListener('pav-game-created',({detail})=>{g=detail;});
addEventListener('pav-game-data',({detail:d})=>{if(d&&d.needs&&typeof d.needs==='object')needs=d.needs;if(Number.isFinite(d?.health))health=d.health;});
function tick(now=performance.now()){
 const b=g?.bridge;if(!b||!needs){last=now;return 0;}
 const hungry=Number(needs.hunger)<=0,thirsty=Number(needs.thirst)<=0;
 if(!(hungry||thirsty)||health<=100){last=now;return 0;}
 if(now-last<EVERY)return 0;last=now;
 const want=(hungry?2:0)+(thirsty?2:0),amount=Math.max(0,Math.min(want,Math.floor(health-FLOOR)));
 if(amount>0){const a=new Int32Array(b.memory.buffer,b.block,16384);Atomics.add(a,16383,amount);}
 if(now-noted>=NOTE){noted=now;const what=hungry&&thirsty?'Açlık ve susuzluk':hungry?'Açlık':'Susuzluk';
  const msg=what+' canını azaltıyor. Bir şeyler '+(hungry&&thirsty?'ye ve iç':hungry?'ye':'iç')+' (envanter veya market).';try{if(g.toast113)g.toast113(msg,'warning','Sağlık');else g.notice?.(msg,true);}catch{}}
 return amount;}
setInterval(()=>tick(),1000);
window.PAVNeeds205={tick,_set:(game,n,h)=>{g=game;needs=n;health=h;}};
})();
