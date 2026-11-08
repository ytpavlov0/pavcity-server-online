/* City suite on index116 against the real runner116 chain: the 115 checks plus glass116 replacing
 * glass115 with the phone left out of it, the timed info card instead of the modal, failed actions
 * raising an error notification, the TAB list and ESC menu in the new theme, the armor shield
 * icon and the 116 chat frame. Screenshots are kept for visual review. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
assert(await page.evaluate(()=>[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes116/glass116.css'))&&![...document.styleSheets].some(s=>(s.href||'').includes('glass115.css'))),'glass116 replaces glass115');
const phone116=await page.evaluate(()=>{const o=document.createElement('section');o.className='pav-overlay rp-overlay pav-source-phone pav-phone21';o.innerHTML='<div class="rp-window"><div class="rp-content"><button class="probe116">x</button></div></div>';PAVGame.hud.append(o);const n=(getComputedStyle(o.querySelector('.probe116')).backgroundImage.match(/linear-gradient/g)||[]).length;o.remove();return n;});
assert.equal(phone116,0,'phone buttons keep the device design (no glass layer)');
const preview116=await page.evaluate(()=>{const o=document.createElement('section');o.className='pav-overlay rp-overlay p82-style';o.innerHTML='<div class="rp-window"><div class="rp-content"></div></div>';PAVGame.hud.append(o);const bg=getComputedStyle(o.querySelector('.rp-window')).backgroundImage;o.remove();return bg;});
assert(/linear-gradient\(90deg/.test(preview116)&&!/radial-gradient/.test(preview116),'3D preview panels keep the right side clear: '+preview116);
await page.evaluate(()=>PAVGame.showInfo({title:'Karakter bilgileri',rows:[['İsim','Test Kişi'],['Şehir ID','1'],['Cüzdan','$7.983.368'],['Araç #33','ZENTORNO · PN89A98A']]}));await page.waitForSelector('.i116');
assert(!(await page.$('.pav-info-panel')),'info is a side card, not a modal');
await page.waitForTimeout(250);await page.screenshot({path:O+'/info116.png'});
await page.evaluate(()=>PAVGame.api('/api/reports/thread',{id:987654}).catch(()=>{}));await page.waitForSelector('.pav-infobox.v113.error',{timeout:5000});
assert(await page.evaluate(()=>!!document.querySelector('.pn-stat[data-stat=armor]>span .pav105-i')),'armor shield icon');
await page.evaluate(()=>PAVGame.scoreboard());await page.waitForSelector('.p85-scoreboard .p85-roster article',{timeout:8000});await page.waitForTimeout(300);await page.screenshot({path:O+'/tab116.png'});
assert.equal(await page.evaluate(()=>getComputedStyle(document.querySelector('.p85-scoreboard')).borderTopLeftRadius),'22px','TAB list in the glass sheet');
await page.evaluate(()=>PAVGame.scoreboard());
await page.evaluate(()=>PAVGame.help70());await page.waitForSelector('.pav-help115 .h115 nav button');await page.mouse.move(4,4);await page.waitForTimeout(250);await page.screenshot({path:O+'/help116.png'});
assert.equal(await page.evaluate(()=>getComputedStyle(document.querySelector('.pav-help115 .rp-window>header small')).letterSpacing!=='normal'),true,'header label restyled');
await page.click('.pav-help115 .rp-close');
`;
// city114 (run by city115) asserts loader114; 116 ships loader116.
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);if(String(path).replace(/\\/g,'/').endsWith('tests/test_city114.cjs'))text=String(text).split('/loader-pn-online-v16-gameplay-v114.js').join('/loader-pn-online-v16-gameplay-v116.js');return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city116 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city115.cjs','utf8'),[
 ["'run_gameplay_live_v115.py'","'run_gameplay_live_v116.py'"],["'-v115.db'","'-v116.db'"],
 ["release115-checks","release116-checks"],["index115.html","index116.html"],
 ["/pn/fixes115/client.js","/pn/fixes116/client.js"],["/pn/fixes115/chat.html","/pn/fixes116/chat.html"],["/pn/fixes115/chat-adapter-v115.js","/pn/fixes116/chat-adapter-v116.js"],
 ["toasts115.png","toasts116.png"],
 ["await page.click('.pav-support115 .rp-close');","await page.click('.pav-support115 .rp-close');"+extra],
 ["\"'115 PASS (guide, F2 desk, trade autocomplete on runner115,","\"'116 PASS (glass116, info card, error toasts, TAB/ESC theme, armor shield, chat116 on runner116, guide, F2 desk, trade autocomplete,"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
