/* City suite on index215: test_city214 retargeted to release215-checks/index215.html (loader215/bridge v215, crime215). */
const fs=require('fs');
const swap=(text,pairs)=>pairs.reduce((t,[a,b,all])=>{if(!t.includes(a))throw Error('city161 retarget missing: '+a);return all?t.split(a).join(b):t.replace(a,b);},text);
const deep={'tests/test_city159.cjs':[[String.raw`\/pn\/fixes159\/roster159\.js`,String.raw`\/pn\/fixes184\/roster184\.js`,true]],'tests/test_city156.cjs':[['loader-pn-online-v16-gameplay-v156.js','loader-pn-online-v16-gameplay-v215.js',true]],
 'tests/test_city160.cjs':[[String.raw`\/pn\/fixes160\/client160\.js`,String.raw`\/pn\/fixes202\/client202\.js`,true],['/pn/fixes160/client160.js','/pn/fixes202/client202.js',true],['fixes158|client159/','fixes158|client159|client160|client163|client167|client170|client172|client173|client176|client177|client178|client183|client188|client190|client191|client192|client196|client197|client201/',true]]};
const fs163=Object.assign(Object.create(fs),{readFileSync(p,...rest){const out=fs.readFileSync(p,...rest);const pairs=deep[String(p).replace(/\\/g,'/')];return pairs&&typeof out==='string'?swap(out,pairs):out;}});
const req163=m=>m==='fs'||m==='node:fs'?fs163:require(m);
const loader=fs.readFileSync('support/fixes215/loader-pn-online-v16-gameplay-v215.js','utf8');
if(!loader.includes('/wgpu_worker-pn-v60.js')||!loader.includes('pn_native_bridge-v215.js'))throw Error('loader215 must load worker v60 + bridge v215');
const source=swap(fs163.readFileSync('tests/test_city160.cjs','utf8'),[
 ["release160-checks","release215-checks",true],["index160.html","index215.html",true],
 ["\"'160 PASS (","\"'163 PASS (client163 realtime voice, bridge v163; "]
]);
new Function('require','__filename','__dirname',source)(req163,__filename,__dirname);
