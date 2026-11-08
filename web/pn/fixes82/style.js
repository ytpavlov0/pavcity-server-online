/* A barber changes hair; a clothing shop sells outfits. Preview is reversible. */
(()=>{'use strict';
addEventListener('pav-game-created',({detail:g})=>queueMicrotask(()=>queueMicrotask(()=>{
 let active=null;
 const clear=()=>{if(!active)return;window.updatePAVPreview?.(g.character.appearance);window.endPAVPreview?.();active=null;};
 const close=g.closeRP;g.closeRP=(...args)=>{clear();return close.apply(g,args);};
 const open=g.openRP;g.openRP=(...args)=>{clear();return open.apply(g,args);};
 g.style82=async kind=>{
  const r=await g.api('/api/style82/list',{kind}),original=structuredClone(r.appearance),title=kind==='barber'?'PAV BARBER · Saç ve bakım':'PAV GİYİM · Yeni tarzın';
  const panel=g.openRP(title,'<div class="p82-style-head"><p>3D önizle. Yalnız değiştirdiğin parçaları satın al.</p><strong data-wallet82></strong></div><form class="p82-style-form">'+PAVCreator.fields(original)+'<div class="p82-style-checkout"><span>Toplam <strong data-cost82>$0</strong></span><button type="submit">Satın al ve uygula</button></div></form><div class="pav-preview-status"></div>'+PAVCreator.controls(),'p82-style');
  const form=panel.querySelector('form'),status=panel.querySelector('.rp-error');form.querySelector('.p82-personas')?.remove();PAVCreator.bind(form);PAVCreator.bindControls(panel);
  panel.querySelector('[data-wallet82]').textContent='Bakiye · $'+Number(r.money).toLocaleString('tr-TR');
  form.querySelector('.look182-head')?.remove();form.querySelector('.look182-tabs')?.remove();
  for(const input of form.querySelectorAll('[name^="look-"]'))if(!Object.hasOwn(r.prices,input.name.slice(5)))input.closest('label').hidden=true;
  for(const box of form.querySelectorAll('[data-group182]')){box.hidden=Number(box.dataset.group182)!==(kind==='barber'?1:2);box.open=!box.hidden;}
  form.querySelector('.look182-features')?.remove();
  // Preserve the original face feature inputs for the complete appearance reader.
  const features=document.createElement('div');features.hidden=true;original.features.forEach((v,i)=>{const f=document.createElement('input');f.name='look-feature'+i;f.value=v;features.append(f);});form.append(features);
  const button=form.querySelector('[type=submit]');let requestId=crypto.randomUUID(),signature='',busy=false;const read=()=>({...original,...PAVCreator.read(form)});
  const quote=()=>{try{const look=read(),cost=Object.entries(r.prices).reduce((sum,[key,price])=>sum+(look[key]!==original[key]?price:0),0),sig=JSON.stringify(look);if(sig!==signature){signature=sig;requestId=crypto.randomUUID();}panel.querySelector('[data-cost82]').textContent='$'+cost.toLocaleString('tr-TR');button.disabled=busy||cost>r.money;button.textContent=cost>r.money?'Bakiye yetersiz':'Satın al ve uygula';window.updatePAVPreview?.(look);}catch(e){status.textContent=e.message;button.disabled=true;}};
  form.addEventListener('input',quote);form.addEventListener('change',quote);active={panel};
  form.onsubmit=async event=>{event.preventDefault();if(busy)return;busy=true;button.disabled=true;status.textContent='';try{const result=await g.api('/api/style82/buy',{kind,appearance:read(),appearance_version:r.appearance_version,request_id:requestId});Object.assign(g.character,{appearance:result.appearance,appearance_version:result.appearance_version});g.notice(result.notice);g.closeRP();}catch(e){status.textContent=e.message;}finally{busy=false;if(panel.isConnected)quote();}};
  panel.querySelector('.rp-close').onclick=()=>g.closeRP();quote();try{await window.startPAVPreview(original,true);if(!panel.isConnected)clear();}catch(e){status.textContent=e.message;}
 };
 g.barber=()=>g.style82('barber');g.clothing=()=>g.style82('clothing');
 const service=g.openService;g.openService=(kind,...args)=>kind==='clothing'?g.clothing():service(kind,...args);
 const command=g.commandRP;g.commandRP=async text=>/^\/(kiyafet|kıyafet|giyim)$/.test(text.trim())?(await g.clothing(),true):command?.(text);
})));})();
