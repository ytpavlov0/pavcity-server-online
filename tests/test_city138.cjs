/* City suite on index138 (loader/bridge138, phone138, ui138) against runner135: the 137 checks plus the phone
 * opening styled on the first open, YouTube under maintenance, game sound on by default, eye under the bars. */
const fs=require('fs');const read=fs.readFileSync;
fs.readFileSync=function(path,...rest){let text=read.call(fs,path,...rest);const p=String(path).replace(/\\/g,'/');
 // Innermost hook: older suites' own retargets run after it, so loader and phone names map to 138 here.
 if(/tests\/test_city\d+\.cjs$/.test(p)){text=String(text);
  if(/test_city136\.cjs$/.test(p))text=text.split("old:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v134.js')").join('old:false');
  text=text.replace(/loader-pn-online-v16-gameplay-v1\d\d\.js/g,'loader-pn-online-v16-gameplay-v138.js').replace(/\/pn\/fixes1(26|32)\/phone1(26|32)\.js/g,'/pn/fixes138/phone138.js');}
 return text;};
const extra=String.raw`
const p138=await page.evaluate(()=>({phone:[...document.scripts].some(s=>s.src.includes('/pn/fixes138/phone138.js')),old:[...document.scripts].some(s=>/phone13[0-7]\.js|phone126\.js/.test(s.src)),ui:[...document.scripts].some(s=>s.src.includes('/pn/fixes138/ui138.js')),css:[...document.styleSheets].some(s=>(s.href||'').includes('/pn/fixes138/ui138.css')),consent:localStorage.getItem('pav-sound-consent'),wrapped:!!window.setPNGameVolume?.w138,afk:!!window.PAVMap?.markers?.afk138,loader:document.documentElement.outerHTML.includes('/loader-pn-online-v16-gameplay-v138.js')}));
assert(p138.phone&&!p138.old&&p138.ui&&p138.css&&p138.consent!=='no'&&p138.wrapped&&p138.afk&&p138.loader,'138 layer: '+JSON.stringify(p138));
await page.route('**/api/phone/status',r=>r.fulfill({json:{success:true,has_phone:true,number:21283414,contacts:[],messages:[],unread:0,call:null,call_history:[],bank:100,cash:5000}}));
await page.evaluate(()=>{for(const o of document.querySelectorAll('.rp-overlay,.pav-overlay'))o.remove();PAVGame.uiOpen=false;sessionStorage.setItem('pav-phone-unlocked-'+PAVGame.character.id,'1');});
const first138=await page.evaluate(async()=>{await PAVGame.phone();const root=document.getElementById('pav-iphone126').shadowRoot,g=root.querySelector('svg.g').getBoundingClientRect();return {sheets:root.adoptedStyleSheets.length,link:!!root.querySelector('link'),glyph:Math.max(g.width,g.height)};});
assert(first138.sheets===1&&!first138.link&&first138.glyph<40,'138 phone styled at first paint: '+JSON.stringify(first138));
await page.evaluate(()=>PAVGame.phone126.navigate('tube'));await page.waitForFunction(()=>document.getElementById('pav-iphone126').shadowRoot.querySelector('.maint138'));
await page.screenshot({path:O+'/phone138-tube.png'});await page.evaluate(()=>PAVGame.phone());await page.unroute('**/api/phone/status');
`;
const swap=(text,pairs)=>pairs.reduce((t,[a,b])=>{if(!t.includes(a))throw Error('city138 retarget missing: '+a);return t.split(a).join(b);},text);
const source=swap(fs.readFileSync('tests/test_city137.cjs','utf8'),[
 ["const p137=await page.evaluate(","\n"+extra+"\nconst p137=await page.evaluate("],
 ["release137-checks","release138-checks"],["index137.html","index138.html"],
 ["\"'137 PASS (chat log fixed while typing","\"'138 PASS (phone styled on first open, YouTube maintenance, sound on by default, help text visible, chat log fixed while typing"]
]);
new Function('require','__filename','__dirname',source)(require,__filename,__dirname);
