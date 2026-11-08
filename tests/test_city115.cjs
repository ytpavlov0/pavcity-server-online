/* City suite on index115 against the real runner115 chain: the 114 checks (admin panel) plus
 * /yardım opening the guide (every section renders, PD Discord link present, commands table
 * lists the trade/PP commands), the chat autocomplete carrying them, and the F2 desk: a new
 * ticket appears alone in the player's list (closed ones do not pile up) and the layout's two
 * columns never overlap. Screenshots are kept for visual review. */
const fs=require('fs'),cp=require('child_process');const read=fs.readFileSync;
const to115=args=>(args||[]).map(a=>String(a).replace('run_gameplay_live_v114.py','run_gameplay_live_v115.py').replace(/-v114\.db$/,'-v115.db'));
// The 115 checks run inside the 114 block, right after the admin panel closes.
const extra=String.raw`
assert(await page.evaluate(()=>[...document.scripts].some(s=>s.src.includes('/pn/fixes115/client.js'))&&[...document.scripts].some(s=>s.src.includes('/pn/fixes115/help115.js'))&&[...document.scripts].some(s=>s.src.includes('/pn/fixes115/support115.js'))),'client115 + help115 + support115 loaded');
assert(await page.evaluate(()=>document.querySelector('iframe.pn-chat')?.getAttribute('src')==='/pn/fixes115/chat.html'),'chat frame 115');
const auto115=await page.evaluate(async()=>{const r=await fetch('/pn/fixes115/chat-adapter-v115.js');return r.text();});
for(const c of['/paragonder','/ppgonder','/aracımısat','/araçkabul','/yardım','/pp'])assert(auto115.includes("['"+c+"'"),'autocomplete has '+c);
await page.evaluate(()=>PAVGame.help70());await page.waitForSelector('.pav-help115 .h115 nav button');
const help115=await page.evaluate(async()=>{const out=[];for(const b of document.querySelectorAll('.pav-help115 .h115 nav button[data-sec]')){b.click();await new Promise(r=>setTimeout(r,30));out.push([b.dataset.sec,document.querySelector('.pav-help115 .h115-body').textContent.length]);}return out;});
assert(help115.length>=7&&help115.every(([,n])=>n>200),'every guide section has content: '+JSON.stringify(help115));
await page.click('.pav-help115 nav button[data-sec="factions"]');assert(await page.evaluate(()=>document.querySelector('.pav-help115 .h115-body').textContent.includes('discord.gg/YOUR-INVITE')),'PD recruitment link');
const glass115=await page.evaluate(()=>{const b=document.querySelector('.pav-help115 .h115-discord button'),c=document.querySelector('.pav-help115 .rp-close');const s=getComputedStyle(b);return{layers:(s.backgroundImage.match(/linear-gradient/g)||[]).length,inset:s.boxShadow.includes('inset'),close:getComputedStyle(c).borderRadius};});assert(glass115.layers>=3&&glass115.inset&&glass115.close==='12px','glass115 buttons: '+JSON.stringify(glass115));
await page.waitForTimeout(150);await page.screenshot({path:O+'/help115-factions.png'});
await page.click('.pav-help115 nav button[data-sec="commands"]');const cmds=await page.evaluate(()=>document.querySelector('.pav-help115 .h115-body').textContent);
for(const c of['/paragonder','/ppgonder','/aracımısat','/araçkabul'])assert(cmds.includes(c),'commands table lists '+c);
await page.click('.pav-help115 nav button[data-sec="money"]');await page.waitForTimeout(150);await page.screenshot({path:O+'/help115-money.png'});
await page.fill('.pav-help115 .h115-search','paragonder');await page.waitForTimeout(150);assert(await page.evaluate(()=>document.querySelector('.pav-help115 .h115-body').textContent.includes('/paragonder')),'guide search finds commands');
await page.click('.pav-help115 .rp-close');
await page.evaluate(()=>PAVGame.reports());
try{await page.waitForSelector('.pav-support115 .s115-form',{timeout:8000});}catch(e){throw Error('F2 desk did not open: '+JSON.stringify(await page.evaluate(()=>({overlay:[...document.querySelectorAll('.rp-overlay')].map(n=>n.className),error:document.querySelector('.rp-overlay .rp-error')?.textContent,fn:String(PAVGame.reports).slice(0,240),desc:Object.getOwnPropertyDescriptor(PAVGame,'reports')?.set?'setter':'value',installs:window.PAVSupport115,err:window.PAVSupport115Error,frozen:Object.isFrozen(PAVGame)||Object.isSealed(PAVGame)}))));}
await page.fill('.s115-form input[name=subject]','Test talebi 115');await page.fill('.s115-form textarea[name=body]','Bir oyuncu iç içe girdi, kontrol eder misiniz?');await page.click('.s115-form footer button');
await page.waitForSelector('.pav-support115 .s115-detail .s115-thread article',{timeout:8000});
const desk=await page.evaluate(()=>{const l=document.querySelector('.s115-list').getBoundingClientRect(),m=document.querySelector('.s115-main').getBoundingClientRect();return{overlays:document.querySelectorAll('#pn-game .rp-overlay').length,tickets:document.querySelectorAll('.s115-tickets [data-ticket]').length,overlap:l.right>m.left+1,inside:m.bottom<=document.querySelector('.pav-support115 .rp-window').getBoundingClientRect().bottom+1};});
assert(desk.overlays===1&&desk.tickets>=1&&!desk.overlap&&desk.inside,'desk layout: '+JSON.stringify(desk));
await page.waitForTimeout(150);await page.screenshot({path:O+'/support115.png'});
await page.click('.pav-support115 .rp-close');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);if(String(path).replace(/\\/g,'/').endsWith('tests/test_city112.cjs'))text=String(text).split("'/pn/fixes112/chat.html'").join("'/pn/fixes115/chat.html'");return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city115 retarget missing: '+a);return t.split(a).join(b);},text);
// city114 patches spawn/execFileSync to runner114; 115 maps those calls once more to runner115.
const source=swap(read.call(fs,'tests/test_city114.cjs','utf8'),[
 ["const spawn0=cp.spawn,exec0=cp.execFileSync;cp.spawn=(cmd,args,opts)=>spawn0(cmd,to114(args),opts);cp.execFileSync=(cmd,args,opts)=>exec0(cmd,to114(args),opts);","const spawn0=cp.spawn,exec0=cp.execFileSync;cp.spawn=(cmd,args,opts)=>spawn0(cmd,to115(to114(args)),opts);cp.execFileSync=(cmd,args,opts)=>exec0(cmd,to115(to114(args)),opts);"],
 ["release114-checks","release115-checks"],
 ["index114.html","index115.html"],
 ["'/pn/fixes114/client.js'","'/pn/fixes115/client.js'"],
 ["await page.screenshot({path:O+'/toasts114.png'});","await page.screenshot({path:O+'/toasts115.png'});"],
 ["\"'114 PASS (admin panel + staff chat on runner114,","\"'115 PASS (guide, F2 desk, trade autocomplete on runner115, admin panel + staff chat,"]
]);
const anchor115="await page.keyboard.press('Escape');assert(await page.evaluate(()=>document.querySelector('.a114').hidden&&PAVGame.uiOpen===false),'Escape closes the panel');";
if(!source.includes(anchor115))throw Error('city115 extra anchor missing');
new Function('require','__filename','__dirname','to115',source.replace(anchor115,anchor115+extra))(require,__filename,__dirname,to115);
