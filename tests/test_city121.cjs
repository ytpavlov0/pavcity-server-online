/* City suite on index121 against the real runner121 chain: the 120 checks plus ESC › Hesap ayarları
 * (status from /api/account121/status: 3/3 password changes, no Discord yet). */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
await page.evaluate(()=>PAVGame.account121Open());await page.waitForSelector('.pav-account121 .a121 form[data-f=password]',{timeout:8000});
const acc121=await page.evaluate(()=>document.querySelector('.pav-account121 .a121').textContent);
assert(/3\/3 HAK/.test(acc121)&&acc121.includes('Yalnız bir kez kaydedilir'),'account panel: '+acc121.slice(0,200));
await page.mouse.move(4,4);await page.waitForTimeout(300);await page.screenshot({path:O+'/account121.png'});
await page.click('.pav-account121 .rp-close');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(p.endsWith('tests/test_city114.cjs'))text=String(text).split('/loader-pn-online-v16-gameplay-v114.js').join('/loader-pn-online-v16-gameplay-v119.js');
 if(p.endsWith('tests/test_city118.cjs'))text=String(text).split("'run_gameplay_live_v118.py'").join("'run_gameplay_live_v121.py'").split("'-v118.db'").join("'-v121.db'");
 return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city121 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city120.cjs','utf8'),[
 ["release120-checks","release121-checks"],["index120.html","index121.html"],
 ["toasts120.png","toasts121.png"],["tab120.png","tab121.png"],["phone120.png","phone121.png"],
 ["await page.evaluate(()=>document.querySelector('.probe120')?.remove());","await page.evaluate(()=>document.querySelector('.probe120')?.remove());"+extra],
 ["\"'120 PASS (iOS phone layer + peek,","\"'121 PASS (account settings on runner121, iOS phone layer + peek,"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);