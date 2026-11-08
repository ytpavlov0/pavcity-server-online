/* 189: a window size change (resize, F11 / leaving fullscreen, browser zoom, another monitor, the ESC scale) made
 * grcDevice::Manage rebuild every render target: grcTextureFactoryDX11::Reset -> CreateRenderTarget ->
 * grcResourceCache::ClearCacheQueue frees a texture twice (pthread memory-bounds in emscripten_builtin_free,
 * ~1/3 of all crash reports on 31 Oct). On desktop the back buffer now keeps its start size for the whole page: the
 * canvas is 100vw x 100vh and mouse input maps through its rect, so the picture is only scaled. A short note says a
 * reload (F5) applies the new size. Mobile keeps its own viewport handling; ?resize=1 restores the old behaviour. */
(()=>{'use strict';
const q=new URLSearchParams(location.search);let shown=0;
function note(){
 const now=performance.now();if(now-shown<60000)return;shown=now;
 document.getElementById('res189')?.remove();const n=document.createElement('div');n.id='res189';n.setAttribute('role','status');
 n.style.cssText='position:fixed;left:50%;top:18px;transform:translateX(-50%);z-index:2147483000;max-width:min(560px,92vw);padding:11px 16px;border-radius:12px;background:rgba(20,14,30,.94);border:1px solid rgba(255,95,168,.45);color:#f6f1ff;font:600 13.5px/1.4 "Segoe UI",system-ui,sans-serif;box-shadow:0 10px 30px rgba(0,0,0,.45);pointer-events:none;text-align:center';
 n.textContent='Pencere boyutu değişti. Oyunun çökmemesi için görüntü yalnızca uyduruldu; tam netlik için uygun bir anda sayfayı yenile (F5).';
 document.body.append(n);setTimeout(()=>n.remove(),7000);
}
// true: keep the engine's back buffer as it is
window.PAVResizeGuard189=()=>{if(q.get('resize')==='1'||window.PAVMobile?.active)return false;note();return true;};
})();
