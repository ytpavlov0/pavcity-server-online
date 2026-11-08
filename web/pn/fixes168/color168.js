/* 168: the "Renk ve görüntü" settings (165) are applied by the GPU worker v58 inside its final present blit as one
 * 3x4 colour matrix (sent on BroadcastChannel 'pav-color', re-sent every 2 s so a worker that starts later gets it).
 * The 165 CSS filter + soft-light layer on the canvas cost an extra compositor pass per frame (slight stutter); both
 * are gone. Same controls, presets and saved values (localStorage pn-color165). */
(()=>{'use strict';
const KEY='pn-color165',DEF={sat:100,con:100,bri:100,hue:0,temp:0};
const RANGE={sat:[50,200],con:[80,140],bri:[80,130],hue:[-20,20],temp:[-50,50]};
const PRESETS=[['Varsayılan',DEF],['Canlı doğa',{sat:125,con:106,bri:102,hue:6,temp:-15}],['Gündüz net',{sat:112,con:112,bri:104,hue:2,temp:-8}],['Sinematik',{sat:92,con:114,bri:97,hue:-3,temp:10}]];
const clamp=(k,v)=>{const[lo,hi]=RANGE[k];v=Number(v);return Number.isFinite(v)?Math.max(lo,Math.min(hi,Math.round(v))):DEF[k];};
function load(){let s=null;try{s=JSON.parse(localStorage.getItem(KEY)||'null');}catch{}
 if(!s){s={...DEF};try{const old=Number(localStorage.getItem('pn-vivid'));if(old>=80&&old<=180&&old!==100)s.sat=old;localStorage.setItem('pn-vivid','100');}catch{}}
 const out={};for(const k of Object.keys(DEF))out[k]=clamp(k,s[k]??DEF[k]);return out;}
let state=load(),layer=null;
function save(){try{localStorage.setItem(KEY,JSON.stringify(state));}catch{}}
// Filter Effects matrices (saturate, hue-rotate), then brightness, contrast around 0.5, then white balance gains.
const mul=(A,B)=>A.map((row,i)=>[0,1,2].map(j=>row[0]*B[0][j]+row[1]*B[1][j]+row[2]*B[2][j]));
function matrix(s){
 const k=s.sat/100,sat=[[.213+.787*k,.715-.715*k,.072-.072*k],[.213-.213*k,.715+.285*k,.072-.072*k],[.213-.213*k,.715-.715*k,.072+.928*k]];
 const r=s.hue*Math.PI/180,co=Math.cos(r),si=Math.sin(r);
 const hue=[[.213+co*.787-si*.213,.715-co*.715-si*.715,.072-co*.072+si*.928],[.213-co*.213+si*.143,.715+co*.285+si*.140,.072-co*.072-si*.283],[.213-co*.213-si*.787,.715-co*.715+si*.715,.072+co*.928+si*.072]];
 const b=s.bri/100,c=s.con/100,t=s.temp/50*.12,gain=[1+t,1+t*.15,1-t];
 let M=mul(hue,sat);M=M.map(row=>row.map(v=>v*b*c));const off=.5-.5*c;
 return M.flatMap((row,i)=>[row[0]*gain[i],row[1]*gain[i],row[2]*gain[i],off*gain[i]]);}
let bc=null;try{bc=new BroadcastChannel('pav-color');}catch{}
function apply(){
 const c=document.getElementById('canvas');if(c&&c.style.filter)c.style.filter='';layer?.remove();layer=null;
 try{bc?.postMessage({m:matrix(state)});}catch{}}
setInterval(apply,2000);
const LABELS=[['sat','Doygunluk','%'],['con','Kontrast / netlik','%'],['bri','Parlaklık','%'],['hue','Doğa tonu (sarı → yeşil)','°'],['temp','Sıcaklık (soğuk ↔ sıcak)','']];
function panel(){
 const host=document.querySelector('[data-settingpanel82="fx"]');if(!host)return false;
 document.querySelectorAll('.pn-vivid').forEach(n=>{const l=n.closest('label');if(l)l.hidden=true;});
 if(host.querySelector('.pav-color165'))return true;
 if(!document.getElementById('pav-color165-style')){const st=document.createElement('style');st.id='pav-color165-style';st.textContent='.pav-color165{display:grid;gap:10px;margin:4px 0 12px}.pav-color165 h4{margin:0;font:700 13px/1.2 inherit;letter-spacing:.04em;text-transform:uppercase;opacity:.85}.pav-color165 .presets{display:flex;flex-wrap:wrap;gap:6px}.pav-color165 .presets button{padding:6px 10px;border-radius:8px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.06);color:inherit;font:600 12px/1 inherit;cursor:pointer}.pav-color165 .presets button:hover{background:rgba(255,255,255,.14)}.pav-color165 label{display:grid;grid-template-columns:1fr auto;gap:4px 10px;align-items:center;font:600 12px/1.2 inherit}.pav-color165 label input{grid-column:1/-1;width:100%}.pav-color165 output{font-variant-numeric:tabular-nums;opacity:.85}.pav-color165 p{margin:0;font:500 11px/1.35 inherit;opacity:.7}';document.head.append(st);}
 const box=document.createElement('section');box.className='pav-color165';box.innerHTML='<h4>Renk ve görüntü</h4><div class="presets"></div><p>Gündüz çimen ve ağaçlar için "Canlı doğa"yı dene, sonra ince ayarı kaydırıcılarla yap. Ayar bu tarayıcıda saklanır.</p>';
 const presets=box.querySelector('.presets'),inputs={};
 for(const[name,p]of PRESETS){const b=document.createElement('button');b.type='button';b.textContent=name;b.onclick=()=>{state={...DEF,...p};save();apply();sync();};presets.append(b);}
 for(const[k,text,unit]of LABELS){const l=document.createElement('label');const span=document.createElement('span');span.textContent=text;const out=document.createElement('output');const inp=document.createElement('input');inp.type='range';inp.min=RANGE[k][0];inp.max=RANGE[k][1];inp.step=1;inp.setAttribute('aria-label',text);
  inp.oninput=()=>{state[k]=clamp(k,inp.value);out.textContent=(k==='temp'&&state[k]>0?'+':'')+state[k]+unit;save();apply();};l.append(span,out,inp);box.append(l);inputs[k]={inp,out,unit};}
 function sync(){for(const[k,{inp,out,unit}]of Object.entries(inputs)){inp.value=state[k];out.textContent=(k==='temp'&&state[k]>0?'+':'')+state[k]+unit;}}
 sync();host.prepend(box);return true;}
apply();if(document.readyState==='loading')addEventListener('DOMContentLoaded',apply,{once:true});
const t=setInterval(()=>{if(panel())clearInterval(t);},1000);
self.__color168={matrix:()=>matrix(state),get:()=>({...state}),set(v){state={...DEF,...v};for(const k of Object.keys(DEF))state[k]=clamp(k,state[k]);save();apply();}};
})();
