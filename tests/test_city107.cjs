/* The real99 HTTP/SQL city suite against index106, plus visual proof of the 106 Vice layer:
 * in-game HUD, ESC menu tiles on the new icon set, no backdrop blur over the canvas, and
 * illustrated job cards served from /pn/fixes106/jobs. Native/GPU execution is mocked. */
const fs=require('fs');
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city107 retarget missing: '+a);return t.split(a).join(b);},text);
const visual=String.raw`await page.screenshot({path:O+'/city-http.png'});
await page.evaluate(()=>PAVGame.setMenu(true));await page.waitForTimeout(700);await page.screenshot({path:O+'/menu106.png'});
const ui106=await page.evaluate(()=>({layer:document.getElementById('pn-game').classList.contains('pav106'),tiles:[...document.querySelectorAll('.pav-city-launchers>button>span')].filter(s=>s.querySelector('.pav105-i')).length,cash:!!document.querySelector('.pav106-cash .pav105-i'),blur:[...document.querySelectorAll('#pn-game *')].filter(n=>getComputedStyle(n).backdropFilter!=='none').length}));
assert(ui106.layer,'106 layer active');assert(ui106.tiles>=8,'ESC tiles use the 106 icon set: '+ui106.tiles);assert(ui106.cash,'cash icon');assert.equal(ui106.blur,0,'no backdrop blur over the game canvas');
await page.evaluate(()=>PAVGame.setMenu(false));
await page.evaluate(()=>{const hud=document.getElementById('pn-game');const s=document.createElement('section');s.className='pav-overlay rp-overlay rp-jobs';s.innerHTML='<div class="rp-window"><header><div><small>PAVCITY / LOS SANTOS</small><h2>Meslek merkezi</h2></div><button class="rp-close">×</button></header><div class="rp-content"><div class="rp-job-cards">'+[['courier','Kurye',1],['contraband','Kaçak sevkiyat',0],['winery','Bağcılık · Şarap üretimi',1],['assassin','Tetikçilik · RP sözleşmesi',0]].map(([k,n,l])=>'<article><small>'+(l?'LEGAL':'İLLEGAL')+'</small><h3>'+n+'</h3><p>3 durak + görevliye dönüş · $1.200</p><button data-start="'+k+'">İşe başla</button><button data-route="'+k+'">Başlangıç noktası · GPS</button></article>').join('')+'</div></div></div>';hud.append(s);});
await page.waitForTimeout(900);await page.screenshot({path:O+'/jobs106.png'});
const jobs106=await page.evaluate(()=>[...document.querySelectorAll('.rp-jobs .rp-job-cards>article')].map(a=>({img:getComputedStyle(a).backgroundImage.includes('/pn/fixes106/jobs/'),illegal:a.classList.contains('illegal106')})));
assert.equal(jobs106.filter(j=>j.img).length,4,'job cards are illustrated');assert.equal(jobs106.filter(j=>j.illegal).length,2);
const loaded106=await page.evaluate(async()=>(await Promise.all(['courier','winery'].map(k=>fetch('/pn/fixes106/jobs/'+k+'.webp').then(r=>r.ok)))).every(Boolean));assert(loaded106,'job art served');`;
const source=swap(fs.readFileSync('tests/test_city100.cjs','utf8'),[
 ["const O='backups/release100-checks'","const O='backups/release107-checks'"],
 ["O+'/index100.html'","O+'/index107.html'"],
 ["a[2]=1;a[37]=1;a[63]=1;a[73]=1;a[8]=5;f[21]=200;});await page.waitForFunction(()=>getPAVEngineState().worldReady);",
  "a[2]=1;a[37]=1;a[63]=1;a[73]=1;a[8]=5;f[21]=200;a[13893]=1;a[13896]=1;});await page.waitForTimeout(400);assert.equal(await page.evaluate(()=>getPAVEngineState().worldReady),false);await page.evaluate(()=>{new Int32Array(fixtureMemory99.buffer)[13893]=0;});await page.waitForFunction(()=>getPAVEngineState().worldReady);"],
 ["await page.screenshot({path:O+'/city-http.png'});",visual],
 ["'100 PASS:","'107 PASS (Vice HUD layer, icon set, job art, no canvas blur + v100 city suite):"]
]);
fs.mkdirSync('backups/release107-checks',{recursive:true});
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
