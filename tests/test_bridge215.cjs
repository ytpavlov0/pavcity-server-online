/* 215: bridge v215 = v214 + the NPC ambulance scene (block 215, calls in the 201 buffer cells 970-995), crime215 =
 * crime211 with the ambulance on the death panel (backend v194) and the calls written from each sync; loader215.
 * The scene runs on a fake engine: ambulance from ~140 m with sirens, paramedic out and tending by ~22 s, back in and
 * off without sirens when the call ends, removed later; a late call starts close; an old call plays nothing. */
const fs=require('fs'),crypto=require('crypto'),assert=require('assert/strict'),vm=require('vm');
const b214=fs.readFileSync('support/fixes214/pn_native_bridge-v214.js','utf8'),b=fs.readFileSync('support/fixes215/pn_native_bridge-v215.js','utf8');new vm.Script(b);
const s0=b.indexOf(' /* 215: NPC ambulance'),e0=b.indexOf(" lap213('ems');");const block=b.slice(s0,e0);assert(s0>0&&e0>s0);
const slots=JSON.parse(b.slice(b.indexOf('const nativeSlots=')+18,b.indexOf('}',b.indexOf('const nativeSlots='))+1));
for(const k of['SET_VEHICLE_SIREN','GET_CLOSEST_VEHICLE_NODE_WITH_HEADING','TASK_LEAVE_VEHICLE','TASK_VEHICLE_DRIVE_TO_COORD','TASK_ENTER_VEHICLE','SET_ENTITY_COORDS','SET_ENTITY_HEADING'])assert(Number.isInteger(slots[k]),k);
assert(b.includes('managed101=new Set([ped,showroomHandle,self.__c210?.medicPed||0,...(self.__ems215?.set||[]),')&&b.includes('const managed201=new Set([ped,showroomHandle,...(self.__ems215?.set||[]),'));
function world(){
 const sab=new SharedArrayBuffer(1<<20),ci=new Int32Array(sab,200000,1024),cf=new Float32Array(sab,200000,1024),scratch=new Float32Array(sab,0,16384);
 const W={sab,ci,cf,ents:new Map([[1,{pos:[0,0,30],veh:0}]]),next:100,log:[],siren:new Map(),scen:new Set(),wander:new Set()};let vec=[0,0,0];
 const ent=h=>W.ents.get(h);
 W.e={pn_exists:h=>W.ents.has(h),pn_vehicle:h=>ent(h)?.veh||0,pn_clear_tasks:h=>{W.scen.delete(h);if(ent(h))ent(h).go=null;},pn_mission_entity(){},pn_model_release(){},
  pn_create_vehicle:()=>{const h=W.next++;W.ents.set(h,{pos:[...vec],veh:0,car:true});return h;},pn_create_ped:()=>{const h=W.next++;W.ents.set(h,{pos:[...vec],veh:0});return h;}};
 W.nativeCall=(n,v)=>{W.log.push(n);const f=i=>new Float32Array(new Uint32Array([Number(v[i])]).buffer)[0];
  if(n==='GET_CLOSEST_VEHICLE_NODE_WITH_HEADING'){new Float32Array(sab,60064,3).set([f(0),f(1),f(2)]);return 1;}
  if(n==='SET_PED_INTO_VEHICLE'){ent(v[0]).veh=v[1];ent(v[0]).go=null;return 0;}
  if(n==='TASK_VEHICLE_DRIVE_TO_COORD'){ent(v[1]).drive=[f(2),f(3),f(4)];return 0;}
  if(n==='TASK_VEHICLE_DRIVE_WANDER'){W.wander.add(v[1]);ent(v[1]).drive=[ent(v[1]).pos[0]+500,0,30];return 0;}
  if(n==='SET_VEHICLE_SIREN'){W.siren.set(v[0],v[1]);return 0;}
  if(n==='TASK_LEAVE_VEHICLE'){const p=ent(v[0]);p.pos=ent(p.veh).pos.map((x,i)=>i?x:x+2);p.veh=0;return 0;}
  if(n==='TASK_GO_STRAIGHT_TO_COORD'){ent(v[0]).go=[f(1),f(2),f(3)];return 0;}
  if(n==='TASK_START_SCENARIO_IN_PLACE'){W.scen.add(v[0]);return 0;}
  if(n==='TASK_ENTER_VEHICLE'){ent(v[0]).enter=v[1];return 0;}
  if(n==='SET_ENTITY_COORDS'){ent(v[0]).pos=[f(1),f(2),f(3)];return 0;}
  return 0;};
 W.step=()=>{for(const x of W.ents.values()){if(x.car&&x.drive){const d=[x.drive[0]-x.pos[0],x.drive[1]-x.pos[1]],k=Math.hypot(...d);if(k>8){x.pos=[x.pos[0]+d[0]/k*Math.min(2,k-8),x.pos[1]+d[1]/k*Math.min(2,k-8),x.pos[2]];}}
  if(x.go){const d=[x.go[0]-x.pos[0],x.go[1]-x.pos[1]],k=Math.hypot(...d);x.pos=k<.4?[...x.go]:[x.pos[0]+d[0]/k*.4,x.pos[1]+d[1]/k*.4,x.pos[2]];}
  if(x.enter&&!x.veh){x.veh=x.enter;x.enter=0;}}
  for(const x of W.ents.values())if(x.veh&&W.ents.has(x.veh))x.pos=[...W.ents.get(x.veh).pos];};
 const self={__npc201:{buf:200000}};W.self=self;
 W.run=now=>new Function('self','now','memory','base','ped','e','nativeCall','coords','vector','ptr','loaded','hash','bits','cstring','drop101','console',block)(self,now,{buffer:sab},0,1,W.e,W.nativeCall,h=>[...(ent(h)?.pos||[NaN,NaN,NaN])],(x,y,z)=>{vec=[x,y,z];},0n,()=>true,s=>s.length,x=>{const u=new Uint32Array(new Float32Array([x]).buffer);return BigInt(u[0]);},()=>0n,h=>{W.ents.delete(h);return true;},console);
 W.calls=list=>{ci[970]=(ci[970]|0)+1;list.forEach((c,i)=>{const o=972+8*i;ci[o]=c.id;cf[o+1]=c.pos[0];cf[o+2]=c.pos[1];cf[o+3]=c.pos[2];ci[o+4]=c.age;ci[o+5]=c.me?1:0;});ci[971]=list.length;ci[970]+=1;};
 return W;}
{const W=world();let now=10000,car=0,med=0,tendAt=0,outAt=0;
 for(;now<=10000+60000;now+=100){const age=now-10000;if(age<24000)W.calls([{id:7,pos:[0,0,30],age,me:true}]);else W.calls([]);W.step();W.run(now);
  const sc=W.self.__ems215.scenes.get(7);if(sc&&!car&&sc.veh){car=sc.veh;med=sc.med;const p=W.ents.get(car).pos;assert(Math.hypot(p[0],p[1])>200,'starts far: '+p);assert.equal(W.siren.get(car),1,'sirens on');}
  if(med&&!outAt&&W.ents.get(med)&&!W.ents.get(med).veh)outAt=age;
  if(med&&!tendAt&&W.scen.has(med)){tendAt=age;const p=W.ents.get(med).pos;assert(Math.hypot(p[0],p[1])<1.5,'medic beside the victim '+p);}
  if(age===30000){assert.equal(W.ents.get(med).veh,car,'medic back in');assert.equal(W.siren.get(car),0,'sirens off');assert(W.wander.has(car),'drives off');}}
 assert(car,'ambulance spawned');assert(outAt>=10000&&outAt<=18200,'out at '+outAt);assert(tendAt>outAt&&tendAt<=22500,'tending at '+tendAt);
 assert(!W.ents.has(car)&&!W.ents.has(med)&&W.self.__ems215.scenes.size===0,'removed later');}
{const W=world();for(let now=1000;now<4000;now+=100){W.calls([{id:9,pos:[0,0,30],age:20000+now,me:false}]);W.step();W.run(now);}
 const sc=W.self.__ems215.scenes.get(9);assert(sc&&sc.veh,'late call: scene');assert(W.scen.has(sc.med),'late call tends quickly');}
{const W=world();for(let now=1000;now<3000;now+=100){W.calls([{id:3,pos:[0,0,30],age:40000+now,me:false}]);W.run(now);}assert.equal(W.self.__ems215.scenes.size,0,'old call: nothing');}
{const W=world();W.calls([{id:4,pos:[900,0,30],age:0,me:false}]);W.run(1000);assert.equal(W.self.__ems215.scenes.size,0,'far call: nothing');}
// crime215: calls from the sync into the cells, the button calls the ambulance, the revive at 24 s
const C=fs.readFileSync('support/fixes215/crime215.js','utf8'),L={},sent=[];let clock=0;
let panel=null;const el=()=>{const o={style:{},children:[],append(c){this.children.push(c);},remove(){},set innerHTML(h){this._h=h;this.sm={textContent:''};this.bt={disabled:false,onclick:null};},querySelector(q){return q==='small'?this.sm:q==='button'?this.bt:q==='.pav-medic210'?this.children.find(c=>c.className==='pav-medic210')||null:null;},querySelectorAll:()=>[]};return o;};
const box=el(),doc={querySelector:q=>q==='.pav-death'?box:null,body:{append(){}},head:{append(){}},documentElement:{append(){}},createElement:()=>el()};
const timers=[];new Function('window','document','setInterval','setTimeout','addEventListener','performance',C)({},doc,f=>timers.push(f),f=>f(),(t,f)=>{(L[t]??=[]).push(f);},{now:()=>clock});
const sab=new SharedArrayBuffer(1<<20),A=new Int32Array(sab,0,16384),ci=new Int32Array(sab,200000,1024),cf=new Float32Array(sab,200000,1024);A[16332]=200000;A[16333]=0;
const g={bridge:{memory:{buffer:sab},block:0},isDead:true,api:async(p)=>{sent.push(p);return p==='/api/gta/ems194'?{success:true,ems194:{id:5,age_ms:0},notice:'ok'}:{success:true,notice:'up'};}};
for(const f of L['pav-game-created'])f({detail:g});
const data=d=>{for(const f of L['pav-game-data'])f({detail:{health:100,crime192:{medic_wait:60-clock/1000},...d}});};
data({ems194:[{id:2,x:10,y:20,z:30,age_ms:5000,me:false}]});assert.equal(ci[971],1);assert.equal(ci[972],2);assert.equal(cf[973],10);assert.equal(ci[976],5000);assert.equal(ci[970]&1,0,'seqlock even');
const tick=()=>timers.forEach(f=>f());tick();const ui=box.children[0];assert(ui.bt.disabled,'not in the first 5 s');assert.match(ui.sm.textContent,/sn sonra çağrılabilir/);
clock=6000;data({});assert.equal(ci[971],0,'no calls');tick();assert(!ui.bt.disabled);
(async()=>{await ui.bt.onclick();assert.deepEqual(sent,['/api/gta/ems194']);tick();assert(ui.bt.disabled,'one call');assert.match(ui.sm.textContent,/Ambulans sirenlerle geliyor: 18 sn/);
 clock=6000+19000;data({ems194:[{id:5,x:0,y:0,z:30,age_ms:19000,me:true}]});tick();assert.match(ui.sm.textContent,/müdahale/);assert.equal(sent.length,1,'not before 24 s');
 clock=6000+24100;tick();await new Promise(r=>setTimeout(r,0));assert.deepEqual(sent,['/api/gta/ems194','/api/gta/npcrevive192'],'revive at 24 s');
 const L215=fs.readFileSync('support/fixes215/loader-pn-online-v16-gameplay-v215.js','utf8'),L214=fs.readFileSync('support/fixes214/loader-pn-online-v16-gameplay-v214.js','utf8');
 assert(L215.includes('/pn_native_bridge-v215.js?build='+crypto.createHash('sha256').update(fs.readFileSync('support/fixes215/pn_native_bridge-v215.js')).digest('hex').slice(0,12)+"'"));
 assert.equal(L215.replace(/\/pn_native_bridge-v215\.js\?build=[a-f0-9]+/,'X'),L214.replace(/\/pn_native_bridge-v214\.js\?build=[a-f0-9]+/,'X'));
 console.log('bridge215 PASS: ambulance from far with sirens, paramedic out by 18 s and tending by 22 s, back in and off, removed; late/old/far calls; crime215 cells, button, revive at 24 s; loader215');})().catch(e=>{console.error(e);process.exit(1);});
