/* 178: "Fare hassasiyeti" (Esc -> Ayarlar -> Grafik kalitesi panel, 25-300 %, saved in localStorage pn-mouse-sens).
 * The page's pointer-lock mousemove handler (index178) multiplies movementX/Y by window.__pavSens and keeps the
 * fractional remainder, so slow, precise aiming is possible at low values and nothing is lost at high ones. */
(()=>{'use strict';
const KEY='pn-mouse-sens',get=()=>{try{const v=Number(localStorage.getItem(KEY));return v>=25&&v<=300?v:100;}catch{return 100;}};
window.__pavSens=get()/100;
function panel(){
 const host=document.querySelector('[data-settingpanel82="quality"]')||document.querySelector('[data-settingpanel82="fx"]');if(!host)return false;
 if(host.querySelector('.pav-sens178'))return true;
 const l=document.createElement('label');l.className='pav-sens178';l.style.cssText='display:grid;grid-template-columns:1fr auto;gap:4px 10px;align-items:center;font:600 12px/1.2 inherit;margin:4px 0 12px';
 const t=document.createElement('span');t.textContent='Fare hassasiyeti';const out=document.createElement('output');const inp=document.createElement('input');
 inp.type='range';inp.min=25;inp.max=300;inp.step=5;inp.value=get();inp.style.gridColumn='1/-1';inp.setAttribute('aria-label','Fare hassasiyeti');
 const show=()=>{out.textContent=inp.value+'%';};inp.oninput=()=>{const v=Math.max(25,Math.min(300,Number(inp.value)||100));try{localStorage.setItem(KEY,String(v));}catch{}window.__pavSens=v/100;show();};
 show();l.append(t,out,inp);host.prepend(l);return true;}
const timer=setInterval(()=>{if(panel())clearInterval(timer);},1000);
})();
