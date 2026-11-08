/* PAVCITY UI 113: typed notifications with icons, a progress line and short WebAudio cues
 * (money / success / warning / error / private message), a PM "ding", and the city entry
 * button held until Los Santos is actually ready (prevents half-loaded entries). */
(()=>{'use strict';
const icon=n=>window.PAVIcons105?.svg(n)||'';
let audio=null;
const tone=(steps,volume=.18)=>{try{if(localStorage.getItem('pav-ui-sounds113')==='off')return;audio??=new (window.AudioContext||window.webkitAudioContext)();const t=audio.currentTime+.01,out=audio.createGain();out.gain.value=volume;out.connect(audio.destination);
 for(const [freq,delay,len,type='sine'] of steps){const o=audio.createOscillator(),g=audio.createGain();o.type=type;o.frequency.value=freq;g.gain.setValueAtTime(0,t+delay);g.gain.linearRampToValueAtTime(.35,t+delay+.012);g.gain.exponentialRampToValueAtTime(.0001,t+delay+len);o.connect(g).connect(out);o.start(t+delay);o.stop(t+delay+len+.05);}}catch{}};
const sounds={money:[[880,0,.18],[1318.5,.08,.35]],success:[[660,0,.22],[990,.06,.3]],warning:[[520,0,.25,'triangle'],[520,.18,.25,'triangle']],error:[[330,0,.25,'triangle'],[247,.14,.35,'triangle']],pm:[[1567.98,0,.6],[2093,.02,.5]]};
const kinds={money:{title:'Para',icon:'cash'},success:{title:'Bilgi',icon:'star'},warning:{title:'Uyarı',icon:'clock'},error:{title:'Hata',icon:'close'},pm:{title:'Özel mesaj',icon:'support'}};
const classify=(text,error)=>{if(error)return'error';if(/\$\s?\d|\d\s?\$|yatırıldı|hesabına eklendi|kazandın|ödeme/i.test(text))return'money';if(/yaklaş|bekle|gerekli|olmalısın|önce |uyarı|dikkat|sınır/i.test(text))return'warning';return'success';};
function install(g){
 const layer=g.hud.querySelector('.pav-infobox-stack')||(()=>{const n=document.createElement('aside');n.className='pav-infobox-stack';g.hud.append(n);return n;})();
 const show=(text,kind,title)=>{while(layer.children.length>=4)layer.firstElementChild.remove();const k=kinds[kind];const n=document.createElement('div');n.className='pav-infobox v113 '+kind;n.setAttribute('role',kind==='error'?'alert':'status');
  n.innerHTML='<span class="v113-icon">'+icon(k.icon)+'</span><div><small></small><strong></strong></div><button aria-label="Bildirimi kapat">'+icon('close')+'</button><i></i>';
  n.querySelector('small').textContent=title||k.title;n.querySelector('strong').textContent=String(text).slice(0,300);n.querySelector('button').onclick=()=>n.remove();layer.append(n);tone(sounds[kind]);setTimeout(()=>n.classList.add('leaving'),5600);setTimeout(()=>n.remove(),6000);};
 g.toast=(text,error=false)=>show(text,classify(String(text),error));
 g.toast113=show;
 const seen=new Set();
 addEventListener('pav-chat-lines84',({detail:rows})=>{for(const m of rows||[]){if(m.scope!=='pm'||seen.has(m.id))continue;seen.add(m.id);if(Number(m.char_id)===Number(g.character?.id))continue;if(Date.now()/1000-Number(m.created||0)>15)continue;show(String(m.body||''),'pm',(m.name?m.name+' · ':'')+'Özel mesaj');}if(seen.size>400)seen.clear();});
}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
// City entry waits for a ready world whenever the engine is already booting (desktop).
setInterval(()=>{const b=document.getElementById('enter-character');if(!b)return;const state=window.getPAVEngineState?.(),booting=!!window.pavEngineStarted&&!state?.error&&!window.PAVEngineFailed98;/* a dead engine must reach the recovery panel */
 const hold=booting&&!state?.worldReady;if(hold){if(!b.dataset.wait113){b.dataset.wait113='1';b.dataset.label113=b.textContent;}b.disabled=true;b.textContent='LOS SANTOS YÜKLENİYOR…';}
 else if(b.dataset.wait113){delete b.dataset.wait113;b.disabled=false;b.textContent=b.dataset.label113||'ŞEHRE KATIL ↗';}},400);
})();
