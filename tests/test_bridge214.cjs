/* 214: bridge v214 = v213 with (a) the ATM lookup only after standing still 0.8 s at a new spot, ATMs remembered, and
 * (b) street props looked up only after an impact (12 common models, 3 per tick), reported where they lie and hidden
 * with 3 m by others; loader214. Run on fake engines: no GET_CLOSEST_OBJECT_OF_TYPE while walking or cruising. */
const fs=require('fs'),crypto=require('crypto'),assert=require('assert/strict'),vm=require('vm');
const b=fs.readFileSync('support/fixes214/pn_native_bridge-v214.js','utf8');new vm.Script(b);
// ---- ATM statement
const a0=b.indexOf('if(now-(self.__atmAt163||0)>250){'),a1=b.indexOf('a[16300]=atm163;}',a0)+'a[16300]=atm163;}'.length;const atmCode=b.slice(a0,a1);
const sab=new SharedArrayBuffer(1<<17),a=new Int32Array(sab,0,16384),f=new Float32Array(sab,0,16384);let calls=0,pos=[0,0,30];const self={};
const runAtm=now=>new Function('self','now','coords','e','ped','nativeCall','bits','modelHash23','a','f',atmCode)(self,now,h=>h===1?pos.slice():[0.5,0,30],{pn_vehicle:()=>0,pn_exists:()=>true},1,(n)=>{calls++;return n==='GET_CLOSEST_OBJECT_OF_TYPE'?7:0;},x=>x,()=>1,a,f);
for(let t=0;t<5000;t+=260){pos=[t/100,0,30];runAtm(t);}assert.equal(calls,0,'walking: no engine lookups');
let t=6000;pos=[0,0,30];for(let i=0;i<6;i++){runAtm(t);t+=260;}assert.equal(calls,1,'standing still: one lookup (first model found)');assert.equal(a[16300],1,'ATM prompt');
for(let i=0;i<20;i++){runAtm(t);t+=260;}assert.equal(calls,1,'same spot: remembered');
pos=[50,0,30];runAtm(t);t+=260;pos=[0.2,0,30];runAtm(t);assert.equal(a[16300],1,'back at the ATM: from memory, no lookup');assert.equal(calls,1);
// ---- props statement
const p0=b.indexOf('{const P197=self.__props197??='),p1=b.indexOf(" lap213('props');mark51(5)");const propsCode=b.slice(p0,p1);
const sv=new Float32Array(sab,64000,64);let speed=20,lookups=0;const S2={},queue=[];
const runProps=now=>new Function('self','now','e','ped','ptr','s','coords','nativeCall','bits','modelHash23','a','f','console',propsCode)(S2,now,
 {pn_vehicle:()=>9,pn_velocity:()=>{sv[0]=speed;sv[2]=0;sv[4]=0;},pn_exists:()=>true,pn_rotation:()=>{sv[0]=40;sv[1]=0;}},1,64000n,sv,()=>[1,2,3],(n)=>{if(n==='GET_CLOSEST_OBJECT_OF_TYPE'){lookups++;return 100+lookups;}return 0;},x=>x,s=>s.length,a,f,console);
for(let i=0;i<30;i++)runProps(i*33);assert.equal(lookups,0,'cruising: no lookups');
speed=12;runProps(1000);assert.equal(lookups,3,'impact: 3 lookups this tick');for(let i=1;i<6;i++)runProps(1000+i*33);assert.equal(lookups,12,'12 models over 4 ticks');
assert.equal(a[16340],12,'tipped props reported');
assert(b.includes("bits(3),h,1]);"),'others hide with 3 m');
const L=fs.readFileSync('support/fixes214/loader-pn-online-v16-gameplay-v214.js','utf8'),L213=fs.readFileSync('support/fixes213/loader-pn-online-v16-gameplay-v213.js','utf8');
assert(L.includes('/pn_native_bridge-v214.js?build='+crypto.createHash('sha256').update(fs.readFileSync('support/fixes214/pn_native_bridge-v214.js')).digest('hex').slice(0,12)+"'"));
assert.equal(L.replace(/\/pn_native_bridge-v214\.js\?build=[a-f0-9]+/,'X'),L213.replace(/\/pn_native_bridge-v213\.js\?build=[a-f0-9]+/,'X'));
console.log('bridge214 PASS: no ATM lookups while walking (one when standing, then remembered), props only after an impact (12 over 4 ticks), loader214');
