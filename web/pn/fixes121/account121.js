/* PAVCITY account 121: ESC › Karakter gets "Hesap ayarları" — e-mail (existing /api/account/save),
 * password change (current password required, 3 changes per account, other sessions signed out) and
 * the Discord name (set once, after an explicit confirmation; it cannot be changed later). */
(()=>{'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function install(g){
 if(!g?.hud||g.account121)return;g.account121=true;
 const open=async()=>{let s;try{s=await g.api('/api/account121/status');}catch(e){g.toast113?.(e.message,'error');return;}
  const p=g.openRP('Hesap ayarları','<div class="a121">'+
   '<section><small>HESAP</small><h3>'+esc(s.username)+'</h3><p>Kullanıcı adı değiştirilemez.</p></section>'+
   '<section><small>E-POSTA</small><form data-f="email"><input name="email" type="email" maxlength="254" placeholder="ornek@mail.com" value="'+esc(s.email)+'"><button>Kaydet</button></form></section>'+
   '<section><small>ŞİFRE · '+s.password_changes_left+'/3 HAK</small><form data-f="password"><input name="current" type="password" autocomplete="current-password" placeholder="Mevcut şifre" required><input name="new" type="password" autocomplete="new-password" minlength="8" maxlength="128" placeholder="Yeni şifre (en az 8)" required><input name="again" type="password" autocomplete="new-password" placeholder="Yeni şifre tekrar" required><button'+(s.password_changes_left?'':' disabled')+'>Şifreyi değiştir</button></form><p>Değişince diğer cihazlardaki oturumların kapanır.</p></section>'+
   '<section><small>DISCORD</small>'+(s.discord?'<h3>'+esc(s.discord)+'</h3><p>Discord adın kayıtlı; değiştirilemez.</p>':'<form data-f="discord"><input name="name" maxlength="32" placeholder="discord kullanıcı adın" required><button>Kaydet</button></form><p>Yalnız bir kez kaydedilir, sonra değiştirilemez.</p>')+'</section></div>','pav-account121');
  const err=m=>{p.querySelector('.rp-error').textContent=m;};
  p.querySelector('[data-f=email]').onsubmit=async e=>{e.preventDefault();try{await g.api('/api/account/save',{email:new FormData(e.currentTarget).get('email')});g.toast113?.('E-posta kaydedildi.','success','Hesap');}catch(x){err(x.message);}};
  p.querySelector('[data-f=password]').onsubmit=async e=>{e.preventDefault();const d=new FormData(e.currentTarget);if(d.get('new')!==d.get('again'))return err('Yeni şifreler aynı değil.');try{const r=await g.api('/api/account121/password',{current:d.get('current'),new:d.get('new')});g.toast113?.(r.notice,'success','Hesap');open();}catch(x){err(x.message);}};
  const dc=p.querySelector('[data-f=discord]');let armed='';
  if(dc)dc.onsubmit=async e=>{e.preventDefault();const name=String(new FormData(dc).get('name')).trim().toLowerCase();const b=dc.querySelector('button');
   if(armed!==name){armed=name;b.textContent='Emin misin? “'+name+'” · Evet, kaydet';b.classList.add('danger');return;}
   try{const r=await g.api('/api/account121/discord',{name,confirm:true});g.toast113?.(r.notice,'success','Hesap');open();}catch(x){armed='';b.textContent='Kaydet';b.classList.remove('danger');err(x.message);}};};
 g.account121Open=open;
 // ESC › Karakter: one button under the identity details
 setInterval(()=>{const box=g.hud.querySelector('.pav-menu-identity-details');if(!box||box.querySelector('.a121-open'))return;const b=document.createElement('button');b.type='button';b.className='a121-open';b.textContent='Hesap ayarları · şifre, e-posta, Discord';b.onclick=()=>open();box.append(b);},1000);
}
addEventListener('pav-game-created',({detail})=>setTimeout(()=>install(detail||window.PAVGame),0));
})();
