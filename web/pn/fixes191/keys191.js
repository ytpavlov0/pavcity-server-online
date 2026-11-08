/* 191: key rebinding (Esc -> Ayarlar, "Tuş atamaları"). A binding says "this physical key acts as that game key":
 * in the capture phase the original keydown/keyup is stopped and the same event is dispatched again with the target
 * key's code/key, so the engine input (index, e.code -> VK) and every PAV handler (F, Z, T, B, Ctrl ...) see the
 * target key. The target key itself keeps working unless it is rebound too (swaps are allowed). Saved in localStorage
 * pn-keys191; typing in text fields is never remapped. */
(()=>{'use strict';
const STORE='pn-keys191';
const ACTIONS=[['KeyF','Araca bin / in'],['KeyZ','Bas-konuş (mikrofon)'],['KeyT','Sohbet'],['KeyB','Telsiz / kısayol (B)'],['Tab','Oyuncu listesi'],
 ['KeyE','Etkileşim / korna'],['KeyR','Şarjör'],['KeyV','Kamera görünümü'],['KeyC','Geriye bak'],['ControlLeft','Eğil'],['ShiftLeft','Koş'],['Space','Zıpla / el freni'],
 ['KeyG','G tuşu'],['KeyH','H tuşu'],['KeyX','X tuşu'],['KeyY','Y tuşu'],['KeyM','M tuşu'],['KeyN','N tuşu'],['KeyQ','Q tuşu'],['KeyK','K tuşu'],['KeyL','L tuşu'],['KeyU','U tuşu']];
const load=()=>{try{const m=JSON.parse(localStorage.getItem(STORE)||'{}');return m&&typeof m==='object'?m:{};}catch{return{};}};
let map=load();  // physical code -> target code
const save=()=>{try{localStorage.setItem(STORE,JSON.stringify(map));}catch{}};
const keyOf=code=>code.startsWith('Key')?code.slice(3).toLowerCase():code.startsWith('Digit')?code.slice(5):code==='Space'?' ':code==='Tab'?'Tab':code.replace(/Left|Right/,'');
const label=code=>code==='Space'?'Boşluk':code==='ShiftLeft'?'Sol Shift':code==='ControlLeft'?'Sol Ctrl':code.replace(/^Key|^Digit/,'');
const typing=()=>{const el=document.activeElement;return !!el&&(el.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName));};
const SELF=Symbol('keys191');let capture=null;
function remap(e){
 if(e[SELF]||e.ctrlKey&&e.code!=='ControlLeft'||e.altKey||e.metaKey)return;
 if(capture){if(e.type==='keydown'){e.preventDefault();e.stopImmediatePropagation();capture(e.code);}else{e.preventDefault();e.stopImmediatePropagation();}return;}
 const to=map[e.code];if(!to||to===e.code||typing())return;
 e.preventDefault();e.stopImmediatePropagation();
 const ev=new KeyboardEvent(e.type,{code:to,key:keyOf(to),repeat:e.repeat,bubbles:true,cancelable:true,shiftKey:e.shiftKey});ev[SELF]=true;
 (e.target&&e.target!==window?e.target:document).dispatchEvent(ev);
}
addEventListener('keydown',remap,{capture:true});addEventListener('keyup',remap,{capture:true});
function panel(){
 const host=document.querySelector('[data-settingpanel82="quality"]')||document.querySelector('[data-settingpanel82="fx"]');if(!host)return false;
 if(host.querySelector('.pav-keys191'))return true;
 const box=document.createElement('details');box.className='pav-keys191';box.style.cssText='margin:6px 0 12px;font:600 12px/1.3 inherit';
 box.innerHTML='<summary style="cursor:pointer;margin-bottom:6px">Tuş atamaları</summary><div class="k191-list" style="display:grid;grid-template-columns:1fr auto auto;gap:4px 8px;align-items:center"></div><p class="k191-hint" style="opacity:.75;margin:6px 0 0;font-weight:500"></p><button type="button" class="k191-reset" style="margin-top:6px">Varsayılana dön</button>';
 const list=box.querySelector('.k191-list'),hint=box.querySelector('.k191-hint');
 const draw=()=>{const by={};for(const[from,to]of Object.entries(map))by[to]=from;
  list.innerHTML='';for(const[code,name]of ACTIONS){const t=document.createElement('span');t.textContent=name;const k=document.createElement('b');k.textContent=label(by[code]||code)+(by[code]?' ✱':'');
   const b=document.createElement('button');b.type='button';b.textContent='Değiştir';b.onclick=()=>{hint.textContent=name+' için yeni tuşa bas (Esc: iptal)…';
    capture=pressed=>{capture=null;if(pressed==='Escape'){hint.textContent='';return;}
     for(const[f,t]of Object.entries(map))if(t===code||f===pressed)delete map[f];
     if(pressed!==code){map[pressed]=code;if(!Object.values(map).includes(pressed)&&ACTIONS.some(([c])=>c===pressed))map[code]=pressed;}
     save();hint.textContent=label(pressed)+' artık “'+name+'”'+(map[code]?' · '+label(code)+' tuşu da eski görevini aldı':'');draw();};};
   list.append(t,k,b);}};
 box.querySelector('.k191-reset').onclick=()=>{map={};save();hint.textContent='Tüm tuşlar varsayılana döndü.';draw();};
 draw();host.append(box);return true;}
const timer=setInterval(()=>{if(panel())clearInterval(timer);},1000);
window.PAVKeys191={get map(){return{...map};},set(m){map={...m};save();}};
})();
