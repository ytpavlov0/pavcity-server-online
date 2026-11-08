/* City suite on index113 (runner108) + typed notifications: money / error / PM render with
 * their kind, icon and progress line; a screenshot is kept for visual review. */
const fs=require('fs');const read=fs.readFileSync;
const extra=String.raw`
await page.evaluate(()=>{PAVGame.toast('Saatlik $500 banka hesabına yatırıldı.');PAVGame.toast('Görev noktasına 5 metre yaklaş.');PAVGame.toast('Araç kilitli.',true);dispatchEvent(new CustomEvent('pav-chat-lines84',{detail:[{id:'pm-test-113',scope:'pm',char_id:999,name:'Deniz Yılmaz',body:'Merhaba, buluşalım mı?',created:Date.now()/1000}]}));});
await page.waitForTimeout(450);await page.screenshot({path:O+'/toasts113.png'});
const kinds113=await page.evaluate(()=>[...document.querySelectorAll('.pav-infobox.v113')].map(n=>[...n.classList].find(c=>['money','warning','error','success','pm'].includes(c))+':'+!!n.querySelector('.v113-icon .pav105-i')));
assert.deepEqual(kinds113,['money:true','warning:true','error:true','pm:true'],'typed notifications: '+JSON.stringify(kinds113));
assert(await page.evaluate(()=>[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes113/ui113.css'))),'ui113 loaded');
`;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 if(p.endsWith('tests/test_city100.cjs')){const anchor="fs.writeFileSync(O+'/city-http.json'";text=text.replace(anchor,extra+anchor);}
 return text;};
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city113 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(read.call(fs,'tests/test_city112.cjs','utf8'),[
 ["release112-checks","release113-checks"],
 ["index112.html","index113.html"],
 ["'112 PASS (runner108,","'113 PASS (typed notifications, PM ding, runner108,"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
