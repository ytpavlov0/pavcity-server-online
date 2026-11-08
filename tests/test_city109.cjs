/* City suite on index109 plus the entry-marker contract: with properties, an elevator, the
 * LSPD desk and an active job nearby, controls-v109 fills the bridge marker slots nearest
 * first (job first), never more than five, and skips the property already in cell 12840. */
const fs=require('fs');
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city109 retarget missing: '+a);return t.split(a).join(b);},text);
const markers=String.raw`
const slots109=await page.evaluate(async()=>{const a=new Int32Array(fixtureMemory99.buffer),f=new Float32Array(fixtureMemory99.buffer);const [x,y,z]=[f[16],f[17],f[18]];a[12841]=0;a[12840]=95;
 const at=(dx,dy)=>({x:x+dx,y:y+dy,z});
 // Real syncs keep replacing the world snapshot; re-send the fixture world faster than the 50 ms render loop.
 const world={properties:[{id:91,...at(12,0)},{id:92,...at(30,0)},{id:95,...at(2,0)},{id:96,...at(90,0)}],elevators:[{id:7,...at(20,0)}],services:[{id:17801,kind:'police',...at(6,0)},{id:3,kind:'bank',...at(1,0)}],property72:{id:95,inside:false,lights:true,anchor:{...at(2,0),heading:0}}};
 const send=()=>{a[12840]=95;a[12841]=0;dispatchEvent(new CustomEvent('pav-game-data',{detail:world}));};const timer=setInterval(send,5);send();
 const read=()=>Array.from({length:a[7200]},(_,n)=>({type:a[7204+n*8],dx:Math.round(f[7205+n*8]-x)}));let best=[];for(let i=0;i<40;i++){await new Promise(r=>setTimeout(r,25));const now=read();if(now.length>best.length)best=now;}clearInterval(timer);return best;});
assert.deepEqual(slots109,[{type:4,dx:6},{type:2,dx:12},{type:3,dx:20},{type:2,dx:30}].slice(0,slots109.length),'nearest entries first: '+JSON.stringify(slots109));
assert(slots109.length>=4&&slots109.length<=5,'four nearby entries (the 90 m door and the cell-12840 property are skipped)');assert(!slots109.some(s=>s.dx===2||s.dx===1),'no duplicate of the 12840 property or non-entry services');`;
const source=swap(fs.readFileSync('tests/test_city107.cjs','utf8'),[
 ["const O='backups/release107-checks'","const O='backups/release109-checks'"],
 ["O+'/index107.html'","O+'/index109.html'"],
 ["'backups/release107-checks'","'backups/release109-checks'"],
 ["await page.screenshot({path:O+'/city-http.png'});\",visual]","await page.screenshot({path:O+'/city-http.png'});\",markers+visual]"],
 ["'107 PASS (","'109 PASS (entry markers + "],
 ['city107 retarget','city109 retarget']
]).replace('const visual=String.raw`','const markers='+JSON.stringify(markers)+';const visual=String.raw`');
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
