/* 195: players who never saved a PC graphics profile start with "Akıcı" (shadows off, 35 % scenery distance, lower
 * vehicle/ped detail), with 512 MB of texture memory so close-up textures stay sharp. Measured on 1 Nov: the frame
 * time is set by the number of draw calls the browser has to translate per frame (2000-2500 at the old default),
 * not by the graphics card. A saved profile (Esc -> Ayarlar -> PC görüntü profili) is never touched, so anyone can
 * raise it again; the engine reads the profile when the city starts. */
(()=>{'use strict';
try{
 const key='pav-pc-graphics79';
 if(localStorage.getItem(key)===null&&localStorage.getItem('pav-pc-view31')===null&&localStorage.getItem('pav-gfx195')===null){
  localStorage.setItem(key,JSON.stringify({quality:0,distance:.35,vehicle:.5,ped:.35,texture:512}));
  localStorage.setItem('pav-gfx195','1');
 }
}catch{}
})();
