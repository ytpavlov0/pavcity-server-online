/* Bounded read-only native observer. Handles are private observation keys. */
(()=>{'use strict';
class PopulationObserver200{
 constructor(peds,cars){this.peds=new Set(peds);this.cars=new Set(cars);this.last=-Infinity;this.seq=0;this.cursor=0;}
 sample(n,now,enabled){
  if(!enabled||now-this.last<500)return null;
  this.last=now;
  const origin=n.position(n.ped),excluded=n.excluded(),seen=new Set(),rows={peds:[],vehicles:[]};
  const collect=(h,kind)=>{
   if(!h||h===n.ped||seen.has(h)||excluded.has(h)||!n.exists(h))return;
   seen.add(h);const model=n.model(h)>>>0;
   if(!(kind==='ped'?this.peds:this.cars).has(model))return;
   const population=n.population(h);
   if(population<1||population>6||n.mission(h)||kind==='ped'&&(n.player(h)||n.vehicle(h)))return;
   if(kind==='vehicle'&&n.hasPlayer(h))return;
   const p=n.position(h),v=n.velocity(h),heading=n.heading(h);
   if(![...p,...v,heading].every(Number.isFinite)||Math.hypot(...p.map((x,i)=>x-origin[i]))>180)return;
   const row={key:h,model_hash:model,x:p[0],y:p[1],z:p[2],heading,vx:v[0],vy:v[1],vz:v[2],population_type:population,mission:false,is_player:false};
   if(kind==='vehicle'){const r=n.rotation(h);if(!Array.isArray(r)||r.length!==3||!r.every(v=>Number.isFinite(v)&&Math.abs(v)<=360))return;row.paint43=n.paint(h);[row.rx,row.ry,row.rz]=r;}
   rows[kind==='ped'?'peds':'vehicles'].push(row);
  };
  for(const h of n.nearbyPeds().slice(0,32)){if(rows.peds.length>=16)break;collect(h,'ped');}
  const cars=n.nearbyCars();
  // Scan a rotating bounded section; never walk an entire global pool per tick.
  for(let i=0;i<Math.min(64,cars.length)&&rows.vehicles.length<8;i++)collect(cars[(this.cursor+i)%cars.length],'vehicle');
  this.cursor=cars.length?(this.cursor+64)%cars.length:0;
  return {version:200,source_seq:++this.seq,...rows};
 }
}
self.PAVPopulationObserver200=PopulationObserver200;
})();

/* PAV protocol 5. All commands execute in the engine's legitimate script TLS.
 * Header 0..127; peers 128/64; projections 2304/12; hits 2800/4;
 * own vehicle 2880; appearance 2944; vehicles 4096/32; scratch byte 64000.
 */
(()=>{
let e,memory,base,ready=false,busy=false,spawned=false,hpVersion=-1,spawnVersion=-1,lastTick=-Infinity,shootUntil=0,peerSequence=-1,receivedAt=0,settingsOpen=false,appearanceVersion=-1,localDamage=0,seatVersion=-1,seatStarted=0,seatWarped=false,remoteGroup=0,lastUnknown=0,previewCam=0,introCam=0,introStarted=0,spawnAt=0,previousPreview=false,previousFly=false,lastSound=0,armorVersion=-1,loadoutVersion=-1,deathSettingsAt=-Infinity,meleeUntil=0,meleeTarget=0,groundPlaced=true,groundRetry=0,phoneState=false,handsState=false,doorCheckAt=-Infinity,trafficCheckAt=-Infinity,bindVersion=0,seatExit46=0;
let interiorGate31=null,interiorSeq31=0;
let showroomHandle=0,showroomCam=0,showroomHash=0,showroomMode=0;const failedModels33=new Set(),modelWait41=new Map();let modelRetry41=0;const serviceNpcs=new Map();const entities=new Map(),vehicles=new Map(),requests=new Map(),attempts=new Map(),serviceBlips=new Map();
const blends=new Map();
let previewHeading=0,previewSpawnVersion=-1,minimapMovie=0,mapRefreshed=false,mapResetTick=false,lastMapSetup=-Infinity;
let nativeTableMode=null;let cameraPed51=0,cameraAt51=-Infinity;
const hash=str=>{let h=0;for(const c of str.toLowerCase()){h=(h+c.charCodeAt(0))|0;h=(h+(h<<10))|0;h^=h>>>6;}h=(h+(h<<3))|0;h^=h>>>11;return (h+(h<<15))|0;};
const modelOf=gender=>hash(gender?'mp_f_freemode_01':'mp_m_freemode_01');
const failBridge=(a,error)=>{
 a[7610]=1;Atomics.store(a,1,0);Atomics.store(a,2,-1);
 try{const ped=e.pn_player_ped();if(ped){e.pn_freeze(ped,1);e.pn_invincible(ped,1);}e.pn_controls_disable(0);}catch{}
 self.postMessage({pnStatus:'Motor bağlantısı durdu: '+error.message});console.error('PAV native bridge',error.stack||error);
};
self.PNBridge={
init(exports,heap){e=exports;memory=heap;base=Number(e.pn_alloc(65536n));if(!Number.isSafeInteger(base)||base<=0)throw Error('PN belleği ayrılamadı.');new Uint8Array(memory.buffer,base,65536).fill(0);new Int32Array(memory.buffer,base,16384)[0]=5;ready=true;self.postMessage({pnBridge:{memory,block:base}});},
tick(){
 if(!ready||busy)return;
 const a=new Int32Array(memory.buffer,base,16384),f=new Float32Array(memory.buffer,base,16384);const tickStart51=performance.now();let phaseAt51=tickStart51;const mark51=phase=>{const at51=performance.now(),elapsed51=at51-phaseAt51;if(a[14102]&&a[14102]<99&&elapsed51>f[14108]){f[14108]=elapsed51;a[14109]=a[14102];}phaseAt51=at51;a[14102]=phase;Atomics.add(a,14104,1);};if(a[62])cameraPed51=0;
 if(!Atomics.load(a,1)){
  if(a[7610]&&e.pn_context()){e.pn_bridge_control(2);try{e.pn_controls_disable(0);const idlePed=e.pn_player_ped();if(idlePed){e.pn_freeze(idlePed,1);e.pn_invincible(idlePed,1);}}finally{e.pn_bridge_control(1);}}
  if((previewCam||introCam)&&e.pn_context()){
   e.pn_bridge_control(2);e.pn_cam_render(0,0,0,1,0,0);
   if(previewCam)e.pn_cam_destroy(previewCam,1);if(introCam)e.pn_cam_destroy(introCam,1);
   previewCam=introCam=0;previousPreview=false;e.pn_destroy_cams(1);e.pn_clear_focus();e.pn_follow_mode(1);e.pn_follow_heading(0);e.pn_hud_show(1);e.pn_radar(a[108]?0:1);const idlePed=e.pn_player_ped();if(idlePed){e.pn_freeze(idlePed,a[7610]?1:0);e.pn_invincible(idlePed,a[7610]?1:0);}e.pn_bridge_control(1);
  }return;
 }if(!e.pn_context())return;
 // These native flags expire each rendered frame; entity sampling stays at 30 Hz.
 mark51(1);e.pn_admin_permission(a[101]?1:0);e.pn_bridge_control(2);
 try{
  e.pn_control_disable(0,45,1);if(a[6600]===4)for(const id of [21,22,24,25,37,140,141,142,257])e.pn_control_disable(0,id,1);for(const id of [14,15,16,17,37])e.pn_control_disable(0,id,1);if(a[7101])for(const id of [23,75])e.pn_control_disable(0,id,1);self.__pavDrawMarkers?.();e.pn_ammo_show(0);for(const id of [2,3,4,6,7,9,13])e.pn_hide_hud(id);
  e.pn_map_reset();e.pn_map_visible(!a[62]&&!a[108]);e.pn_death_fade(0);if(!a[101])e.pn_control_disable(0,27,1);e.pn_hud_show(a[62]?0:1);e.pn_radar(a[62]||a[108]?0:1);
  if(!a[62]){e.pn_radar_exterior();e.pn_custom_map(0);e.pn_map_prologue(0);e.pn_map_island(0);if(!introCam&&!a[6500]){const cameraPed=e.pn_player_ped(),cameraNow51=performance.now();if(cameraPed&&(cameraPed51!==cameraPed||cameraNow51-cameraAt51>=1000)){e.pn_cam_render(0,0,0,1,0,0);cameraPed51=cameraPed;cameraAt51=cameraNow51;}/* SET_GAMEPLAY_CAM_FOLLOW_PED_THIS_UPDATE expires each engine frame. */if(cameraPed)e.pn_follow_ped(cameraPed);}else cameraPed51=0;}
  if(a[7612]||a[62]||a[64]||a[6500]||a[6380]||(a[6600]&&a[6600]!==4)||a[7610]||a[71]||a[72]||a[7701]===1||a[7701]===2||a[7701]===3||a[7712])e.pn_controls_disable(0);
  if(a[62]||a[7610]||a[71]||a[72]||a[7701]===1||a[7701]===2||a[7701]===3||a[7712]){const heldPed=e.pn_player_ped();if(heldPed){e.pn_freeze(heldPed,1);e.pn_invincible(heldPed,1);}}
  self.__pavFiniteAmmo?.();if(a[7830]||a[7831]){for(const id of [21,22,23,24,25,37,44,45,75,140,141,142,257,263,264])e.pn_control_disable(0,id,1);if(a[7831])e.pn_controls_disable(0);}
 }catch(error){failBridge(a,error);return;}finally{e.pn_bridge_control(1);}
 if(mapResetTick){e.pn_bridge_control(2);e.pn_big_map(0,0);e.pn_bridge_control(1);mapResetTick=false;}const now=performance.now();if(now-lastTick<33){mark51(0);return;}const frameDelta44=Math.min(.1,Math.max(.001,Number.isFinite(lastTick)?(now-lastTick)/1000:1/30));lastTick=now;Atomics.add(a,8,1);busy=true;e.pn_bridge_control(2);
 try{
 let ped=e.pn_player_ped();if(!ped||!e.pn_exists(ped))return;if(now-deathSettingsAt>1000){e.pn_ignore_restart(1);deathSettingsAt=now;if(!a[101]&&!a[116])e.pn_destroy_phone();}
 const ptr=BigInt(base+64000),s=new Float32Array(memory.buffer,base+64000,64);
 const vector=(x,y,z)=>{s[0]=x;s[2]=y;s[4]=z;};
 const coords=h=>{e.pn_coords(ptr,h,1);return [s[0],s[2],s[4]];};
 const cstring=(value,offset=64192)=>{const bytes=new Uint8Array(memory.buffer,base+offset,32);bytes.fill(0);for(let i=0;i<Math.min(30,value.length);i++)bytes[i]=value.charCodeAt(i)&127;return BigInt(base+offset);};

 function modelHash23(name){let h=0;for(const c of name){h=(h+c.charCodeAt(0))|0;h=(h+(h<<10))|0;h^=h>>>6;}h=(h+(h<<3))|0;h^=h>>>11;return (h+(h<<15))>>>0;}
 const nativeSlots={"GET_ENTITY_POPULATION_TYPE":46062,"IS_ENTITY_A_MISSION_ENTITY":46068,"IS_PED_A_PLAYER":54772,"GET_PED_NEARBY_PEDS":56019,"SET_FOCUS_POS_AND_VEL":58103,"SET_VEHICLE_CUSTOM_PRIMARY_COLOUR":59104,"GET_VEHICLE_CUSTOM_PRIMARY_COLOUR":59106,"CLEAR_VEHICLE_CUSTOM_PRIMARY_COLOUR":59108,"GET_IS_VEHICLE_PRIMARY_COLOUR_CUSTOM":59110,"SET_VEHICLE_CUSTOM_SECONDARY_COLOUR":59112,"GET_VEHICLE_CUSTOM_SECONDARY_COLOUR":59114,"CLEAR_VEHICLE_CUSTOM_SECONDARY_COLOUR":59116,"GET_IS_VEHICLE_SECONDARY_COLOUR_CUSTOM":59118,"GET_VEHICLE_COLOURS":59179,"CREATE_MOBILE_PHONE":56888,"SET_ENABLE_HANDCUFFS":55260,"IS_ENTITY_PLAYING_ANIM":46106,"START_EXPENSIVE_SYNCHRONOUS_SHAPE_TEST_LOS_PROBE":57090,"GET_SHAPE_TEST_RESULT":57104,"SET_TIMECYCLE_MODIFIER":47109,"SET_TIMECYCLE_MODIFIER_STRENGTH":47111,"GET_TIMECYCLE_MODIFIER_INDEX":47119,"CLEAR_TIMECYCLE_MODIFIER":47117,"pn_v20_arrested": 56437, "pn_v20_arrest_reset": 56440, "pn_v20_wanted_clear": 56308, "pn_v20_fade_in": 45116, "pn_v20_clock": 45410, "pn_v20_pause_clock": 45412, "pn_v20_weather": 48880, "pn_v20_marker": 46537, "pn_v20_force_gps": 47725, "pn_v20_indicators": 59830, "pn_v20_tint": 60794, "pn_v19_waypoint": 48059, "pn_v19_waypoint_off": 48050, "pn_v19_gps_length": 54674, "pn_v19_gps_point": 54678, "pn_v19_fix": 59619, "pn_v19_engine_health": 59682, "pn_v19_anim_request": 58046, "pn_v19_anim_loaded": 58048, "pn_v19_anim": 58375, "pn_v19_clip": 60712, "pn_v19_ipl": 58061, "SET_PED_INFINITE_AMMO": 60676, "SET_PED_INFINITE_AMMO_CLIP": 60678, "SET_VEHICLE_MOD_KIT": 59915, "SET_VEHICLE_MOD": 59944, "GET_NUM_VEHICLE_MODS": 59950, "TOGGLE_VEHICLE_MOD": 59954, "SET_VEHICLE_COLOURS": 59098, "SET_VEHICLE_WHEEL_TYPE": 59923, "SET_VEHICLE_WINDOW_TINT": 59981, "SET_VEHICLE_LOD_MULTIPLIER": 60062, "SET_ENTITY_LOD_DIST": 46256, "GET_VEHICLE_LIGHTS_STATE": 59188, "SET_VEHICLE_LIGHTS": 59286, "SET_VEHICLE_FULLBEAM": 59100, "START_VEHICLE_HORN": 59706, "SET_STATE_OF_CLOSEST_DOOR_OF_TYPE": 54127, "SET_PED_CONFIG_FLAG": 55744, "GET_CLOSEST_OBJECT_OF_TYPE": 54112, "DOOR_SYSTEM_FIND_EXISTING_DOOR": 54178, "DOOR_SYSTEM_SET_DOOR_STATE": 54139, "DOOR_SYSTEM_SET_OPEN_RATIO": 54149, "GET_INTERIOR_AT_COORDS": 48703, "PIN_INTERIOR_IN_MEMORY": 48708, "IS_INTERIOR_READY": 48712, "IS_VALID_INTERIOR": 48673, "REFRESH_INTERIOR": 48736, "NEW_LOAD_SCENE_START_SPHERE": 58132, "NEW_LOAD_SCENE_STOP": 58134};
 const bitBuffer=new ArrayBuffer(4),bitFloat=new Float32Array(bitBuffer),bitUint=new Uint32Array(bitBuffer);const bits=value=>{bitFloat[0]=value;return BigInt(bitUint[0]);};
 const nativeCall=(name,values=[])=>{
  const info=new BigUint64Array(memory.buffer,base+60000,32),args=new BigUint64Array(memory.buffer,base+60256,32),result=new BigUint64Array(memory.buffer,base+60512,1);
  info.fill(0n);result[0]=0n;args.fill(0n);info[0]=BigInt(base+60512);info[1]=BigInt(values.length);info[2]=BigInt(base+60256);
  values.forEach((v,i)=>args[i]=BigInt.asUintN(64,typeof v==='bigint'?v:BigInt(Math.trunc(v))));
  const table=e.__indirect_function_table;let fn=e[name];
  if(!fn&&table){
   const slot=nativeSlots[name];if(!Number.isInteger(slot)||slot<0||slot>=table.length)throw Error('Native slot invalid: '+name);
   if(e.pn_split_slot)e.pn_split_slot.value=slot;
   // Desktop uses table64; mobile uses table32 with the same i64 C++ ABI.
   // Detect once, avoiding a thrown conversion error for every desktop call.
   if(nativeTableMode===null){try{fn=table.get(slot);nativeTableMode=false;}catch(error){if(error?.name!=='TypeError')throw error;fn=table.get(BigInt(slot));nativeTableMode=true;}}
   else fn=table.get(nativeTableMode?BigInt(slot):slot);
  }
  if(!fn)return 0;fn(BigInt(base+60000));return Number(result[0]&0xffffffffn);
 };

 // Audited wrapper bytecode writes scalar outs to the supplied i64 pointers.
 const readPaint43=h=>{
  const out=new Int32Array(memory.buffer,base+64592,8);out.fill(-1);
  nativeCall('GET_VEHICLE_COLOURS',[h,BigInt(base+64592),BigInt(base+64596)]);
  if(![out[0],out[1]].every(v=>v>=0&&v<=160))return null;
  let mask=0;
  for(let i=0;i<2;i++){const side=i?'SECONDARY':'PRIMARY';if(nativeCall('GET_IS_VEHICLE_'+side+'_COLOUR_CUSTOM',[h])){mask|=1<<i;nativeCall('GET_VEHICLE_CUSTOM_'+side+'_COLOUR',[h,...[2+i*3,3+i*3,4+i*3].map(n=>BigInt(base+64592+n*4))]);if(!Array.from(out.slice(2+i*3,5+i*3)).every(v=>v>=0&&v<=255))return null;}}
  return [out[0],out[1],mask,...Array.from(out.slice(2))];
 };

 mark51(2);// Candidate observation only. Main thread must explicitly enable flag14100.
 if(a[14100]&&!a[62]&&!a[7610]&&!a[71]&&!a[72]&&!a[6500]&&!a[7701]&&!a[7712]&&spawned){
  self.__population200??=new self.PAVPopulationObserver200([3382649284, 3014915558, 2705543429, 664399832, 826475330, 2928082356, 3083210802, 3523131524, 587703123, 349505262, 2185745201, 2549481101, 3250873975, 2255803900, 605602864, 1446741360, 1581098148, 368603149, 2974087609, 1096929346, 1939545845, 3008586398, 3065114024],[3950024287, 2485144969, 3144368207, 970598228, 3990165190, 3486135912, 3039514899, 3078201489, 418536135, 2046537925, 2667966721, 1171614426, 3581397346, 3253274834, 3249425686, 2551651283, 3087195462, 1718441594, 2117711508, 2891838741, 408192225, 631542247, 4052294509, 178350184, 1352183536]);
  const observed=self.__population200.sample({ped,
   rotation:h=>{e.pn_rotation(ptr,h,2);return[s[0],s[2],s[4]];},position:coords,exists:h=>!!e.pn_exists(h),model:h=>e.pn_model(h),heading:h=>e.pn_heading(h),
   velocity:h=>{e.pn_velocity(ptr,h);return[s[0],s[2],s[4]];},
   population:h=>nativeCall('GET_ENTITY_POPULATION_TYPE',[h]),mission:h=>!!nativeCall('IS_ENTITY_A_MISSION_ENTITY',[h]),
   player:h=>!!nativeCall('IS_PED_A_PLAYER',[h]),vehicle:h=>e.pn_vehicle(h,0),paint:readPaint43,
   hasPlayer:h=>{for(let seat=-1;seat<8;seat++){const occupant=e.pn_vehicle_seat(h,seat,0);if(occupant&&nativeCall('IS_PED_A_PLAYER',[occupant]))return true;}return false;},
   excluded:()=>new Set([ped,...[...vehicles.values(),...entities.values(),...serviceNpcs.values()].map(v=>v.handle)]),
   nearbyPeds:()=>{const pool=new Int32Array(memory.buffer,base+56640,66);pool.fill(0);pool[0]=32;const count=Math.max(0,Math.min(32,nativeCall('GET_PED_NEARBY_PEDS',[ped,BigInt(base+56640),-1])));return Array.from({length:count},(_,i)=>pool[2+i*2]);},
   nearbyCars:()=>{const pool=new Int32Array(memory.buffer,base+49152,1026);pool.fill(0);pool[0]=512;const count=Math.max(0,Math.min(512,e.pn_all_vehicles(BigInt(base+49152))));return Array.from({length:count},(_,i)=>pool[2+i*2]);}
  },now,true);
  if(observed)self.postMessage({pnPopulation200:{...observed,binding_epoch:a[14101]}});
 }

 // Server restraint flags use separate cells, never movement/combat flag aliases.
 const restraint34=(h,cuffed,prone,state)=>{
  const mode=prone?2:cuffed?1:0;
  if(state.restraint34!==mode){nativeCall('SET_ENABLE_HANDCUFFS',[h,mode?1:0]);if(state.restraint34){e.pn_clear_tasks(h);if(!mode)state.weapon=0;}state.restraint34=mode;state.restraintAt34=-Infinity;}
  if(!mode)return;
  e.pn_select_weapon(h,0xA2719263|0,1);
  if(now-(state.restraintAt34??-Infinity)<1000)return;
  state.restraintAt34=now;
  const dp=cstring(prone?'missfbi3_sniping':'mp_arresting',65120),cp=cstring(prone?'prone_dave':'idle',65160);
  nativeCall('pn_v19_anim_request',[dp]);
  if(nativeCall('pn_v19_anim_loaded',[dp])&&!nativeCall('IS_ENTITY_PLAYING_ANIM',[h,dp,cp,3]))nativeCall('pn_v19_anim',[h,dp,cp,bits(3),bits(-3),-1,prone?1:49,bits(0),0,0,0]);
 };
 self.__pavFiniteAmmo=()=>{const ma=new Int32Array(memory.buffer,base,16384);if(ma[62]||ma[7610]||ma[71]||ma[72]||!ma[102])return;const h=e.pn_player_ped(),w=ma[103];if(!h)return;nativeCall('SET_PED_INFINITE_AMMO_CLIP',[h,0]);if(w&&(w>>>0)!==0xA2719263){nativeCall('SET_PED_INFINITE_AMMO',[h,0,w]);if(e.pn_ammo(h,w)>Math.max(0,ma[104]))e.pn_set_ammo(h,w,Math.max(0,ma[104]),0);if(ma[6608]===ma[102]){const sig=ma[102]+':'+w;let clip=self.__clip33;if(!clip||clip.sig!==sig)self.__clip33=clip={sig,ceiling:Math.max(0,Math.min(ma[7121],ma[7120],ma[104]))};ma[16360]=0;if(e.pn_clip(h,w,BigInt(base+65440))){const n=Math.max(0,ma[16360]);if(n>clip.ceiling)nativeCall('pn_v19_clip',[h,w,clip.ceiling]);else clip.ceiling=n;}if(!clip.ceiling)e.pn_control_disable(0,24,1);}}};
 self.__pavDrawMarkers=()=>{const ma=new Int32Array(memory.buffer,base,16384),mf=new Float32Array(memory.buffer,base,16384);if(ma[62])return;for(let n=0;n<Math.min(5,ma[7200]);n++){const o=7204+n*8;if(Math.hypot(mf[o+1]-mf[16],mf[o+2]-mf[17],mf[o+3]-mf[18])>160)continue;nativeCall('pn_v20_marker',[1,bits(mf[o+1]),bits(mf[o+2]),bits(mf[o+3]-.9),bits(0),bits(0),bits(0),bits(0),bits(0),bits(0),bits(1.6),bits(1.6),bits(.35),190,240,90,130,0,0,2,0,0n,0n,0]);}};
 if(now-(self.__pavArrestPoll||0)>500){self.__pavArrestPoll=now;const player=e.pn_player_id(),arrested=nativeCall('pn_v20_arrested',[player,0]);if(arrested){self.__pavArrestStart??=now;if(now-self.__pavArrestStart>4000&&now-(self.__pavArrestReset||-Infinity)>15000){nativeCall('pn_v20_arrest_reset',[player]);nativeCall('pn_v20_wanted_clear',[player]);nativeCall('pn_v20_fade_in',[300]);self.__pavArrestReset=now;self.__pavArrestStart=undefined;Atomics.add(a,7107,1);}}else self.__pavArrestStart=undefined;}
 if(a[7102]!==self.__pavEnvironment){self.__pavEnvironment=a[7102];nativeCall('pn_v20_pause_clock',[1]);nativeCall('pn_v20_clock',[a[7103],a[7104],a[7106]]);const weather=['EXTRASUNNY','CLEAR','CLOUDS','SMOG','FOGGY','OVERCAST','RAIN','THUNDER','CLEARING','NEUTRAL','SNOW','BLIZZARD','SNOWLIGHT','XMAS'][a[7105]]||'EXTRASUNNY';if(weather!==self.__pavWeather){nativeCall('pn_v20_weather',[cstring(weather,65312)]);self.__pavWeather=weather;}}
 
 // Live, acknowledged engine color grading. Profiles are present in supplied timecycle XML.
 if(a[7800]!==self.__fxSeq33){self.__fxSeq33=a[7800];const name=({1:'NeutralColorCodeLight',2:'NG_filmic03'})[a[7801]];if(name){nativeCall('SET_TIMECYCLE_MODIFIER',[cstring(name,65200)]);nativeCall('SET_TIMECYCLE_MODIFIER_STRENGTH',[bits(Math.max(0,Math.min(1,f[7802]||0)))]);}else nativeCall('CLEAR_TIMECYCLE_MODIFIER');a[7804]=nativeCall('GET_TIMECYCLE_MODIFIER_INDEX')|0;Atomics.store(a,7803,a[7800]);}
 const loaded=model=>{if(!e.pn_model_valid(model))return false;if(e.pn_model_loaded(model))return true;if(now-(requests.get(model)??-Infinity)>1000){requests.set(model,now);e.pn_request_model(model);}return false;};
 const applyLook=(h,o)=>{
  const previous=blends.get(h),headKey=[a[o+1],a[o+2],a[o+36],a[o+37],f[o+3],f[o+4]].join(':');
  if(!previous){e.pn_default_clothes(h);for(let p=0;p<8;p++)e.pn_clear_prop(h,p);e.pn_component(h,0,0,0,2);}
  if(!previous||previous.headKey!==headKey){
   e.pn_head_blend(h,a[o+1],a[o+2],0,a[o+36],a[o+37],0,f[o+3],f[o+4],0,0);
   blends.set(h,{started:now,done:false,headKey});
  }
  const components=[[2,a[o+5]],[11,a[o+7]],[4,a[o+8]],[6,a[o+9]],[3,a[o+10]],[8,a[o+11]]];
  for(const [id,wanted] of components){
   const count=e.pn_component_count(h,id);if(count<=0)continue;
   const drawable=Math.max(0,Math.min(wanted,count-1)),texture=Math.max(0,Math.min(id===2?0:a[o+15],e.pn_texture_count(h,id,drawable)-1));
   if(e.pn_component_valid(h,id,drawable,texture))e.pn_component(h,id,drawable,texture,2);
  }
  const blend=blends.get(h);blend.detail={gender:a[o],color:a[o+6],eye:a[o+12],beard:a[o+13],brow:a[o+14],features:Array.from(f.slice(o+16,o+36))};blend.detailsDirty=true;
 };
 const ownModel=modelOf(a[2944]);a[37]=0;a[61]=(e.pn_model_valid(ownModel)?1:0)|(e.pn_model_loaded(ownModel)?2:0);
 if((e.pn_model(ped)|0)!==ownModel){
  if(loaded(ownModel)){if(spawned&&spawnVersion===Atomics.load(a,46)){const old=coords(ped),heading=e.pn_heading(ped);f.set([...old,heading],40);}blends.delete(ped);e.pn_player_model(e.pn_player_id(),ownModel);ped=e.pn_player_ped();if(!ped||!e.pn_exists(ped))return;spawned=false;hpVersion=-1;armorVersion=-1;a[7613]=-1;appearanceVersion=-1;seatVersion=-1;loadoutVersion=-1;}
 }else a[37]=1;
 if(a[37]&&appearanceVersion!==a[47]){applyLook(ped,2944);appearanceVersion=a[47];}
 for(const [h,blend] of blends){
  if(!e.pn_exists(h)){blends.delete(h);continue;}
  if(!blend.done&&now-blend.started>100&&e.pn_blend_done(h)){e.pn_blend_finish(h);e.pn_palette_disable(h);blend.done=true;}
  if(blend.done&&blend.detailsDirty){const d=blend.detail;e.pn_hair_colour(h,d.color,d.color);e.pn_eye_colour(h,d.eye);e.pn_overlay(h,1,d.beard<0?255:d.beard,d.gender?0:1);e.pn_overlay_colour(h,1,1,d.color,d.color);e.pn_overlay(h,2,d.brow,1);e.pn_overlay_colour(h,2,1,d.color,d.color);d.features.forEach((v,i)=>e.pn_face_feature(h,i,v));blend.detailsDirty=false;}
 }
 a[63]=blends.get(ped)?.done?1:0;[2,11,4,6,3,8].forEach((id,i)=>{a[90+i]=Math.max(0,e.pn_component_count(ped,id)-1);});
 if(a[62]){[2,11,4,6,3,8].forEach((id,i)=>{const desired=a[2944+[5,7,8,9,10,11][i]],draw=Math.max(0,Math.min(a[90+i],desired));a[13860+i]=Math.max(0,e.pn_texture_count(ped,id,draw)-1);});a[13873]=182;}
 if(a[74]!==lastSound){lastSound=a[74];if(lastSound)e.pn_front_sound(-1,cstring('SELECT',64288),cstring('HUD_FRONTEND_DEFAULT_SOUNDSET',64512),1);}
 if(!remoteGroup){a[16064]=0;e.pn_add_group(cstring('PN_REMOTE',64224),BigInt(base+64256));remoteGroup=a[16064];}
 if(remoteGroup)e.pn_damage_group(ped,0,remoteGroup); // Replica bullets animate; server hit reports apply PvP once.
 if(self.__pavOwnRestraint34?.ped!==ped)self.__pavOwnRestraint34={ped,restraint34:self.__pavOwnRestraint34?.restraint34>0?-1:0};
 const wanted=false;Atomics.store(a,12,0);
 if(wanted!==settingsOpen){if(wanted){e.pn_frontend(hash('fe_menu_version_sp_pause'),0,-1);e.pn_frontend_active(1);e.pn_pause_menu(1);e.pn_pause(0);}else{e.pn_frontend_active(0);e.pn_pause_menu(0);}settingsOpen=wanted;}
 if(!wanted)e.pn_pause_menu(0);Atomics.store(a,13,wanted&&e.pn_pause_active()?1:0);

 mark51(3);// Cells7700..7712 are a bounded native preparation handshake, not a teleport request.
 const interiorFloor31=target=>{f[16236]=NaN;if(interiorGate31?.outdoor){vector(target[0],target[1],target[2]+1.2);return !!e.pn_ground(ptr,BigInt(base+64944),0,1)&&Number.isFinite(f[16236])&&Math.abs(f[16236]-target[2])<1.5;}const handle=nativeCall('START_EXPENSIVE_SYNCHRONOUS_SHAPE_TEST_LOS_PROBE',[bits(target[0]),bits(target[1]),bits(target[2]+.7),bits(target[0]),bits(target[1]),bits(target[2]-2.5),1,ped,7]);if(!handle)return false;a[16330]=0;const status=nativeCall('GET_SHAPE_TEST_RESULT',[handle,BigInt(base+65320),BigInt(base+65328),BigInt(base+65344),BigInt(base+65360)]);const hit=Array.from(new Float32Array(memory.buffer,base+60064,3)),normal=Array.from(new Float32Array(memory.buffer,base+60080,3));if(status!==2||!a[16330]||!hit.every(Number.isFinite)||!normal.every(Number.isFinite)||normal[2]<.65||Math.hypot(...normal)<.8||Math.hypot(...normal)>1.2||Math.hypot(hit[0]-target[0],hit[1]-target[1])>.1||Math.abs(hit[2]-target[2])>1.6)return false;f[16236]=hit[2];return true;};
 const releaseInteriorFocus31=()=>{nativeCall('NEW_LOAD_SCENE_STOP');e.pn_clear_focus();e.pn_focus_ped(ped);vector(...coords(ped));e.pn_collision_request(ptr);};
 if(a[7700]&&a[7700]!==interiorSeq31){
  interiorSeq31=a[7700];a[7709]=a[7710]=0;f[7711]=NaN;const target=Array.from(f.slice(7704,7707));
  interiorGate31={seq:interiorSeq31,target,outdoor:a[7702]===-1,sourceSpawn:Atomics.load(a,46),from:[...coords(ped),e.pn_heading(ped)],started:now,last:-Infinity,handle:0,arriving:false};
  if(!target.every(Number.isFinite)||Math.abs(target[0])>16000||Math.abs(target[1])>16000||Math.abs(target[2])>3000){a[7701]=-1;interiorGate31=null;}
  else{a[7701]=1;nativeCall('SET_FOCUS_POS_AND_VEL',[...target.map(bits),bits(0),bits(0),bits(0)]);if(a[7702]===1)nativeCall('pn_v19_ipl',[cstring('ex_dt1_02_office_02b',65200)]);nativeCall('NEW_LOAD_SCENE_START_SPHERE',[...target.map(bits),bits(45),0]);}
 }
 if(interiorGate31){
  const g=interiorGate31;
  if(a[7708]===g.seq){releaseInteriorFocus31();a[7701]=-3;interiorGate31=null;}
  else if(a[7701]===1&&(Atomics.load(a,46)!==g.sourceSpawn||a[62]||a[64]||e.pn_health(ped)<=100)){releaseInteriorFocus31();a[7701]=-4;interiorGate31=null;}
  else if(a[7701]===1){
   vector(...g.from);e.pn_set_coords(ped,ptr,1,1,1);vector(0,0,0);e.pn_set_velocity(ped,ptr);
   if(now-g.started>(g.outdoor?15000:60000)){a[7701]=-2;releaseInteriorFocus31();}
   else if(now-g.last>250){
    g.last=now;nativeCall('SET_FOCUS_POS_AND_VEL',[...g.target.map(bits),bits(0),bits(0),bits(0)]);vector(...g.target);e.pn_collision_request(ptr);
    const handle=g.outdoor?0:nativeCall('GET_INTERIOR_AT_COORDS',g.target.map(bits));a[7709]=handle;a[7710]=0;
    if(g.outdoor){const floorReady=interiorFloor31(g.target);f[7711]=f[16236];if(floorReady){a[7701]=2;g.readyAt=now;releaseInteriorFocus31();}}
    else if(handle&&nativeCall('IS_VALID_INTERIOR',[handle])){
     if(g.handle!==handle){g.handle=handle;nativeCall('PIN_INTERIOR_IN_MEMORY',[handle]);nativeCall('REFRESH_INTERIOR',[handle]);}
     const roomReady=!!nativeCall('IS_INTERIOR_READY',[handle]);a[7710]=roomReady?1:0;const floorReady=roomReady&&interiorFloor31(g.target);f[7711]=f[16236];if(floorReady){a[7701]=2;g.readyAt=now;releaseInteriorFocus31();}
    }
   }
  }else if(a[7701]===2){vector(...g.from);e.pn_set_coords(ped,ptr,1,1,1);vector(0,0,0);e.pn_set_velocity(ped,ptr);if(now-g.readyAt>10000){a[7701]=-2;releaseInteriorFocus31();}}
 }
 if(!spawned||spawnVersion!==Atomics.load(a,46)){
  e.pn_pause(0);spawnVersion=Atomics.load(a,46);a[7712]=0;vector(f[40],f[41],f[42]);
  if(interiorGate31?.arriving&&Math.hypot(f[40]-interiorGate31.target[0],f[41]-interiorGate31.target[1],f[42]-interiorGate31.target[2])>=2){interiorGate31.arriving=false;a[7701]=-4;releaseInteriorFocus31();}
  if(interiorGate31&&a[7701]===2&&Math.hypot(f[40]-interiorGate31.target[0],f[41]-interiorGate31.target[1],f[42]-interiorGate31.target[2])<2){interiorGate31.arriving=true;interiorGate31.arrivedAt=now;interiorGate31.floorOk=false;a[7701]=3;}
  if(e.pn_health(ped)<=100){e.pn_local_resurrect(ptr,f[43],2000,0,1,11,0);ped=e.pn_player_ped();hpVersion=-1;armorVersion=-1;loadoutVersion=-1;e.pn_clear_tasks(ped);e.pn_collision(ped,1,1);e.pn_player_control(e.pn_player_id(),1,0);}
  vector(f[40],f[41],f[42]);e.pn_collision_request(ptr);e.pn_set_coords(ped,ptr,1,1,1);e.pn_set_heading(ped,f[43]);e.pn_fade_in(250);e.pn_clear_focus();e.pn_focus_ped(ped);e.pn_follow_ped(ped);e.pn_radar(a[108]?0:1);e.pn_radar_zoom(110);e.pn_minimap_fow(1);spawned=true;spawnAt=now;a[7611]=0;groundPlaced=!a[112];groundRetry=0;a[113]=0;e.pn_freeze(ped,1);
 }
 const preview=!!a[62],fly=!!a[64];
 if(preview){
  if(!previousPreview){previewHeading=e.pn_heading(ped);previewSpawnVersion=spawnVersion;}
  if(!previewCam)previewCam=e.pn_cam_create(cstring('DEFAULT_SCRIPTED_CAMERA'),1);
  e.pn_freeze(ped,1);e.pn_invincible(ped,1);e.pn_controls_disable(0);e.pn_hud_show(0);e.pn_radar(0);
  const pos=coords(ped),angle=(f[68]||0)*Math.PI/180,distance=Math.max(.8,Math.min(5,f[69]||3.6));
  const shift=f[7130]||0,dx=Math.cos(angle)*shift,dy=-Math.sin(angle)*shift;e.pn_set_heading(ped,0);vector(pos[0]+Math.sin(angle)*distance+dx,pos[1]+Math.cos(angle)*distance+dy,pos[2]+(f[70]||.75)+.15);e.pn_cam_set(previewCam,ptr);vector(pos[0]+dx,pos[1]+dy,pos[2]+(f[70]||.75));e.pn_cam_point(previewCam,ptr);e.pn_cam_fov(previewCam,distance>2?48:38);e.pn_cam_render(1,0,0,1,0,0);a[73]=a[37];previousPreview=true;
 }
 if(previousPreview&&!preview){if(previewCam){e.pn_cam_render(0,0,0,1,0,0);e.pn_cam_destroy(previewCam,1);previewCam=0;}if(previewSpawnVersion===spawnVersion)e.pn_set_heading(ped,previewHeading);previousPreview=false;spawnAt=now;e.pn_destroy_cams(1);e.pn_focus_ped(ped);e.pn_follow_ped(ped);e.pn_follow_mode(1);e.pn_follow_heading(0);}
 if(fly){
  e.pn_freeze(ped,1);e.pn_collision(ped,0,0);e.pn_invincible(ped,1);e.pn_controls_disable(0);
  const pos=coords(ped);e.pn_cam_rot(ptr,2);const yaw=s[4]*Math.PI/180,rate=Math.min(.05,(f[84]||.033))*Math.max(1,Math.min(160,f[83]||28));
  vector(Math.max(-15900,Math.min(15900,pos[0]+(Math.cos(yaw)*f[80]-Math.sin(yaw)*f[81])*rate)),Math.max(-15900,Math.min(15900,pos[1]+(Math.sin(yaw)*f[80]+Math.cos(yaw)*f[81])*rate)),Math.max(-1600,Math.min(2600,pos[2]+f[82]*rate)));e.pn_set_coords(ped,ptr,1,1,1);vector(0,0,0);e.pn_set_velocity(ped,ptr);previousFly=true;
 }else{
  if(previousFly){e.pn_collision(ped,1,1);previousFly=false;spawnAt=now;}
  if(!groundPlaced&&now-groundRetry>350){
   groundRetry=now;vector(f[40],f[41],f[42]);e.pn_collision_request(ptr);
   // Call the script wrapper with its reference output buffer. The wrapper writes
   // a contiguous native vector at Info+64; no script VM finalizer runs here.
   const info=base+64600,args=base+64768,out=base+64832,result=base+64928;
   new Uint8Array(memory.buffer,info,336).fill(0);
   const refs=new BigUint64Array(memory.buffer,info,3);refs[0]=BigInt(result);refs[1]=6n;refs[2]=BigInt(args);
   const av=new BigUint64Array(memory.buffer,args,6),af=new Float32Array(memory.buffer,args,12);
   af[0]=f[40];af[2]=f[41];af[4]=f[42];av[3]=1n;av[4]=BigInt(out);av[5]=16n;
   e.pn_safe_coord(BigInt(info));const candidate=Array.from(new Float32Array(memory.buffer,info+64,3));
   if(new Int32Array(memory.buffer,result,1)[0]&&candidate.every(Number.isFinite)&&Math.hypot(candidate[0]-f[40],candidate[1]-f[41])<8&&Math.abs(candidate[2]-f[42])<2){
    vector(candidate[0],candidate[1],candidate[2]+3);a[16236]=0;
    if(e.pn_ground(ptr,BigInt(base+64944),0,1)&&Number.isFinite(f[16236])&&Math.abs(f[16236]-f[42])<2){
     vector(candidate[0],candidate[1],f[16236]+.15);e.pn_set_coords(ped,ptr,1,1,1);e.pn_collision_request(ptr);groundPlaced=true;spawnAt=now;
    }
   }
  }
  if(interiorGate31?.arriving){
   const g=interiorGate31;
   if(now-g.last>250){g.last=now;g.floorOk=(g.outdoor||!!nativeCall('IS_INTERIOR_READY',[g.handle]))&&interiorFloor31(g.target);}
   if(g.floorOk&&e.pn_collision_ready(ped)&&now-spawnAt>=350){g.arriving=false;a[7701]=4;}
   else if(now-g.arrivedAt>15000){vector(...g.target);e.pn_set_coords(ped,ptr,1,1,1);vector(0,0,0);e.pn_set_velocity(ped,ptr);g.arriving=false;a[7701]=-2;a[7712]=1;releaseInteriorFocus31();}
  }
  const settling=!groundPlaced||!e.pn_collision_ready(ped)||now-spawnAt<350||a[7701]===1||a[7701]===2||a[7701]===3||!!a[7712];
  if(settling&&now-groundRetry>350){groundRetry=now;vector(...coords(ped));e.pn_collision_request(ptr);}
  e.pn_freeze(ped,settling||a[62]||a[6500]||a[7610]||a[71]?1:0);e.pn_invincible(ped,settling||a[62]||a[7610]||a[71]||a[6400]?1:0);a[72]=settling?1:0;
  a[113]=settling&&now-spawnAt>30000?1:0;
 }
 e.pn_hud_show(preview?0:1);e.pn_radar(preview||a[108]?0:1);e.pn_radar_exterior();e.pn_custom_map(0);
 if(!minimapMovie)minimapMovie=e.pn_sf_request(cstring('minimap'));
 if(minimapMovie&&e.pn_sf_loaded(minimapMovie)){
  if(!mapRefreshed){e.pn_big_map(1,0);mapResetTick=true;mapRefreshed=true;}
  if(now-lastMapSetup>1000&&e.pn_sf_begin(minimapMovie,cstring('SETUP_HEALTH_ARMOUR'))){e.pn_sf_int(3);e.pn_sf_end();lastMapSetup=now;}
 }
 a[89]=e.pn_map_rendering()?1:0;
 for(let i=0;i<Math.min(24,a[107]);i++){const o=6000+i*8,id=a[o];if(!id||serviceBlips.has(id))continue;vector(f[o+1],f[o+2],f[o+3]);const blip=e.pn_blip_coord(ptr);e.pn_blip_sprite(blip,a[o+4]);e.pn_blip_colour(blip,a[o+5]);e.pn_blip_scale(blip,.7);e.pn_blip_short(blip,1);serviceBlips.set(id,blip);}
 // Entry uses the normal follow camera; no five-second aerial animation.
 if(a[71]&&!preview&&!a[6500]&&!a[72]&&a[37]&&a[63]){
  e.pn_cam_render(0,0,0,1,0,0);if(introCam)e.pn_cam_destroy(introCam,1);introCam=0;
  e.pn_destroy_cams(1);e.pn_focus_ped(ped);e.pn_follow_ped(ped);e.pn_clear_focus();e.pn_follow_mode(1);e.pn_follow_heading(0);a[71]=0;
 }
 a[7611]=!preview&&!a[71]&&!a[72]&&a[37]&&a[63]?1:0;
 const entryLocked=preview||!!a[7610]||!!a[71]||!!a[72];
 if(entryLocked){
  if(!self.__pavEntryHeld){e.pn_clear_tasks(ped);e.pn_select_weapon(ped,0xA2719263|0,1);self.__pavEntryHeld=true;}
  e.pn_controls_disable(0);e.pn_freeze(ped,1);e.pn_invincible(ped,1);shootUntil=meleeUntil=0;a[106]=0;
 }else if(self.__pavEntryHeld){e.pn_clear_tasks(ped);self.__pavEntryHeld=false;loadoutVersion=-1;}
 nativeCall('SET_PED_INFINITE_AMMO_CLIP',[ped,0]);if(a[103]&&(a[103]>>>0)!==0xA2719263)nativeCall('SET_PED_INFINITE_AMMO',[ped,0,a[103]]);
 if(armorVersion!==a[66]){e.pn_set_armor(ped,a[65]);if(e.pn_armor(ped)===a[65])armorVersion=a[66];}a[7613]=armorVersion;
 if(!a[62]&&a[44]>100&&e.pn_faded_out())e.pn_fade_in(250);
 if(!entryLocked&&(loadoutVersion!==a[102]||a[6608]!==a[102]&&now-(self.__pavEquipAt||0)>500)){self.__pavEquipAt=now;const weapon=a[103];if(weapon&&(weapon>>>0)!==0xA2719263){e.pn_give_weapon(ped,weapon,a[104],0,1);e.pn_set_ammo(ped,weapon,a[104],0);nativeCall('pn_v19_clip',[ped,weapon,Math.max(0,Math.min(a[7121],a[7120],a[104]))]);}e.pn_select_weapon(ped,weapon||0xA2719263|0,1);loadoutVersion=a[102];if((e.pn_weapon(ped)>>>0)===(a[103]>>>0)&&((a[103]>>>0)===0xA2719263||e.pn_ammo(ped,a[103])===a[104]))a[6608]=loadoutVersion;}
 const version=Atomics.load(a,45);if(version!==hpVersion){const hp=Atomics.load(a,44);e.pn_set_health(ped,hp<=100?0:hp,0);hpVersion=version;Atomics.store(a,125,version);}if(!a[72])Atomics.store(a,96,spawnVersion);
 if(!entryLocked&&a[59]!==localDamage){localDamage=a[59];if(localDamage&&e.pn_health(ped)>100){e.pn_ragdoll(ped,1);e.pn_ragdoll_task(ped,a[60]===1?450:180,a[60]===1?450:180,0,0,0,0);}}
 mark51(4);const carSeq=Atomics.load(a,14),carStates=[];
 if(!(carSeq&1)){for(let i=0;i<Math.min(48,Atomics.load(a,15));i++){const o=4096+i*32;carStates.push({id:a[o],model:a[o+1],owner:a[o+2],locked:a[o+3],driver:a[o+4],pos:Array.from(f.slice(o+5,o+8)),heading:f[o+8],rot:Array.from(f.slice(o+9,o+12)),velocity:Array.from(f.slice(o+12,o+15)),body:f[o+15],engine:!!a[o+16],windows:a[o+24],doors:a[o+25],street:!!a[o+26],poseEpoch:a[o+28],repairEpoch:a[o+29],indicators:a[o+31],lights:a[8310+i*16],mods:Array.from(a.slice(8300+i*16,8310+i*16)),paint:Array.from(a.slice(9100+i*8,9108+i*8)),plate:Array.from(new Uint8Array(memory.buffer,base+(o+20)*4,16)).map(byte=>String.fromCharCode(byte)).join('').split('\0')[0]});}}
 if(carSeq!==Atomics.load(a,14))carStates.length=0;
 if(!(carSeq&1)&&carSeq===Atomics.load(a,14)){
  const active=new Set(carStates.map(v=>v.id));
  for(const [id,v] of vehicles)if(!active.has(id)){if(e.pn_exists(v.handle)){a[16008]=v.handle;e.pn_delete_vehicle(BigInt(base+64032));}vehicles.delete(id);attempts.delete('v'+id);}
  let created=false;
  if(a[119]!==bindVersion){const request=Atomics.load(a,119),id=a[120],handle=a[121],snapshot=carStates.find(v=>v.id===id);
   if(snapshot){bindVersion=request;a[123]=-1;
    if(handle&&e.pn_exists(handle)&&e.pn_model(handle)===snapshot.model&&Math.hypot(...coords(handle).map((c,i)=>c-coords(ped)[i]))<=9){
     const old=vehicles.get(id);if(old&&old.handle!==handle&&e.pn_exists(old.handle)&&e.pn_vehicle(ped,0)!==old.handle){a[16008]=old.handle;e.pn_delete_vehicle(BigInt(base+64032));}
     e.pn_mission_entity(handle,1,1);e.pn_vehicle_plate(handle,cstring(snapshot.plate));vehicles.set(id,{handle,locked:-1,grounded:true,pose:[...snapshot.pos,snapshot.heading,...snapshot.rot].join(':')});a[123]=1;
    }Atomics.store(a,122,request);
   }
  }
  const retry41=Atomics.load(a,14000);if(modelRetry41!==retry41){modelRetry41=retry41;const model=Atomics.load(a,14001);failedModels33.delete(model);requests.delete(model);for(const[id,w]of modelWait41)if(w.model===model)modelWait41.delete(id);
   const target41=carStates.find(v=>v.id===a[14002]&&v.model===model&&v.pos.every(Number.isFinite)),local41=target41&&vehicles.get(target41.id);
   if(local41&&local41.grounded===false&&e.pn_exists(local41.handle)){vector(...target41.pos);e.pn_set_coords(local41.handle,ptr,1,1,1);e.pn_set_heading(local41.handle,target41.heading);local41.createdAt=now;local41.groundRetry=-Infinity;local41.warnedGround41=false;}
  }
  for(const[id]of modelWait41)if(!active.has(id))modelWait41.delete(id);
  const modelFailure41=(id,reason)=>{if(!a[109]){a[14003]=reason;a[109]=id;}};
  for(const [i30,v] of carStates.entries()){
   if(!v.id||![...v.pos,v.heading,...v.rot,...v.velocity,v.body].every(Number.isFinite))continue;if(failedModels33.has(v.model))continue;if(!e.pn_vehicle_model(v.model)||!e.pn_model_valid(v.model)){failedModels33.add(v.model);modelFailure41(v.id,1);continue;}let local=vehicles.get(v.id);
   if(!local||!e.pn_exists(local.handle)){
    let wait=modelWait41.get(v.id);if(!wait||wait.model!==v.model){wait={model:v.model,at:now};modelWait41.set(v.id,wait);}
    if(now-wait.at>25000){failedModels33.add(v.model);e.pn_model_release(v.model);modelFailure41(v.id,2);continue;}
    if(created||!e.pn_vehicle_model(v.model)||!loaded(v.model)||now-(attempts.get('v'+v.id)??-Infinity)<1000)continue;
    attempts.set('v'+v.id,now);vector(...v.pos);const handle=e.pn_create_vehicle(v.model,ptr,v.heading,0,1,0);if(!handle)continue;modelWait41.delete(v.id);created=true;if(a[109]===v.id)a[109]=0;e.pn_mission_entity(handle,1,1);e.pn_freeze(handle,1);e.pn_vehicle_plate(handle,cstring(v.plate));local={handle,createdAt:now,locked:-1,grounded:false,groundRetry:-Infinity,pose:[...v.pos,v.heading,...v.rot].join(':')};vehicles.set(v.id,local);e.pn_model_release(v.model);
   }
   const h=local.handle;
   if(!local.renderReady&&[1718441594,2117711508,631542247,-242672787,178350184,1352183536].includes(v.model)){nativeCall('SET_VEHICLE_LOD_MULTIPLIER',[h,bits(5)]);nativeCall('SET_ENTITY_LOD_DIST',[h,200]);local.renderReady=true;}

   if(local.grounded===false){
    if(now-local.groundRetry>350){local.groundRetry=now;vector(...coords(h));e.pn_collision_request(ptr);
     const collision38=!!e.pn_collision_ready(h);local.collision46=collision38;local.floor46=false;let placed38=collision38&&!!e.pn_vehicle_ground(h,5);
     if(!placed38&&collision38&&now-local.createdAt>=3500&&[1718441594,2117711508,631542247,-242672787,178350184,1352183536].includes(v.model)){
      const pos38=coords(h);vector(pos38[0],pos38[1],pos38[2]+1);f[16236]=NaN;
      placed38=!!e.pn_ground(ptr,BigInt(base+64944),0,1)&&Number.isFinite(f[16236])&&Math.abs(f[16236]-pos38[2])<2.5;local.floor46=placed38;local.floorZ46=f[16236];
     }
     if(placed38){local.grounded=true;e.pn_freeze(h,0);}
    }
    if(!local.grounded){if(!local.warnedGround41&&now-local.createdAt>20000){modelFailure41(v.id,3);a[14010]=46;a[14011]=v.id;a[14012]=local.collision46?1:0;a[14013]=local.floor46?1:0;f[14014]=Number.isFinite(local.floorZ46)?local.floorZ46:NaN;f[14015]=v.pos[2];f[14016]=(now-local.createdAt)/1000;local.warnedGround41=true;}continue;}
   }
   if(local.indicators!==v.indicators){nativeCall('pn_v20_indicators',[h,1,v.indicators===1||v.indicators===3?1:0]);nativeCall('pn_v20_indicators',[h,0,v.indicators===2||v.indicators===3?1:0]);local.indicators=v.indicators;}   const sig=v.mods.join(':')+':'+v.paint.join(':');if(local.mods!==sig){local.mods=sig;const m=v.mods;if(m[0]===v.id){nativeCall('SET_VEHICLE_MOD_KIT',[h,0]);if(m[1]>=0||m[2]>=0){const previous43=(m[1]<0||m[2]<0)?readPaint43(h):null;
     if(m[1]>=0&&m[2]>=0||previous43){nativeCall('SET_VEHICLE_COLOURS',[h,m[1]>=0?m[1]:previous43[0],m[2]>=0?m[2]:previous43[1]]);
      for(let side=0;side<2;side++)if(m[1+side]>=0){const name=side?'SECONDARY':'PRIMARY',start=1+side*3;if(v.paint[0]&(1<<side))nativeCall('SET_VEHICLE_CUSTOM_'+name+'_COLOUR',[h,...v.paint.slice(start,start+3)]);else nativeCall('CLEAR_VEHICLE_CUSTOM_'+name+'_COLOUR',[h]);}}
    }local.paintObservation43=null;local.paintAt43=-Infinity;if(m[3]>=-1){nativeCall('SET_VEHICLE_WHEEL_TYPE',[h,0]);const n=nativeCall('GET_NUM_VEHICLE_MODS',[h,23]);nativeCall('SET_VEHICLE_MOD',[h,23,Math.min(m[3],n-1),0]);}if(m[4]>=0)nativeCall('SET_VEHICLE_WINDOW_TINT',[h,m[4]]);for(const [i,slot] of [[5,11],[6,12],[7,15],[8,0]])if(m[i]>=-1){const n=nativeCall('GET_NUM_VEHICLE_MODS',[h,slot]);nativeCall('SET_VEHICLE_MOD',[h,slot,Math.min(m[i],n-1),0]);}if(m[9]>=0)nativeCall('TOGGLE_VEHICLE_MOD',[h,18,m[9]?1:0]);}}
if(local.windows!==v.windows){for(let n=0;n<4;n++)if((local.windows??0)&(1<<n) ^ v.windows&(1<<n))(v.windows&(1<<n)?e.pn_window_down:e.pn_window_up)(h,n);local.windows=v.windows;}
   if(local.doors!==v.doors){for(let n=0;n<6;n++)if((local.doors??0)&(1<<n) ^ v.doors&(1<<n)){if(v.doors&(1<<n))e.pn_door_open(h,n,0,0);else e.pn_door_shut(h,n,0);}local.doors=v.doors;}
   if(a[7601]===v.id&&e.pn_vehicle(ped,0)===h&&now-(self.__pavHornAt||0)>100){self.__pavHornAt=now;nativeCall('START_VEHICLE_HORN',[h,150,0,0]);}if(local.locked!==v.locked){e.pn_vehicle_lock(h,v.locked?2:1);local.locked=v.locked;}if(local.engine!==v.engine||now-(local.engineCheck??-Infinity)>500){local.engineCheck=now;e.pn_vehicle_engine(h,v.engine?1:0,1,1);local.engine=v.engine;local.lightsAt=-Infinity;}
   // Engine/native driver updates may reset lamps. Reapply bounded authoritative
   // state after the engine, with the native output observed on the next update.
   if(local.lights!==v.lights||now-(local.lightsAt??-Infinity)>=500){local.lightsAt=now;const lamp=new Int32Array(memory.buffer,base+64464,2);lamp.fill(0);nativeCall('GET_VEHICLE_LIGHTS_STATE',[h,BigInt(base+64464),BigInt(base+64468)]);const on=v.lights?1:0,beam=v.lights===2?1:0;if(local.lights!==v.lights||lamp[0]!==on||lamp[1]!==beam){nativeCall('SET_VEHICLE_LIGHTS',[h,on?2:1]);nativeCall('SET_VEHICLE_FULLBEAM',[h,beam]);}local.lights=v.lights;const ack=12000+i30*4;a[ack]=v.id;a[ack+1]=v.lights;a[ack+2]=lamp[0];a[ack+3]=lamp[1];}

   const pose=[...v.pos,v.heading,...v.rot].join(':');
   const snapshot44=[pose,...v.velocity,v.driver,v.poseEpoch].join(':');if(local.snapshot44!==snapshot44){local.snapshot44=snapshot44;local.snapshotAt44=now;}
   const nativeDriver46=e.pn_vehicle(ped,0)===h&&e.pn_vehicle_seat(h,-1,0)===ped;
   const actualDriver38=nativeDriver46&&v.driver===a[51]&&a[48]===v.id&&a[49]===-1;
   const remoteDriver38=!!v.driver&&!actualDriver38;
   // Only the reserved, physically seated local driver simulates this car.
   // A remote replica must not also integrate gravity/contact/old velocity.
   const kinematic46=remoteDriver38||nativeDriver46&&!actualDriver38;
   if(!!local.kinematic46!==kinematic46){e.pn_freeze(h,kinematic46?1:0);local.kinematic46=kinematic46;}
   if(kinematic46){vector(0,0,0);e.pn_set_velocity(h,ptr);}
   if(nativeDriver46&&!actualDriver38)for(const control46 of [59,60,71,72])e.pn_control_disable(0,control46,1);
   const placement=local.poseEpoch!==undefined&&v.poseEpoch!==local.poseEpoch;if(local.poseEpoch===undefined)local.poseEpoch=v.poseEpoch;
   if(actualDriver38){local.pose=pose;local.ownUntil=now+3000;local.remoteDriven38=false;}
   else if(remoteDriver38)local.ownUntil=0;
   if(placement||(!actualDriver38&&now>=(local.ownUntil||0)&&(remoteDriver38||local.remoteDriven38))){local.pose=pose;local.poseEpoch=v.poseEpoch;local.remoteDriven38=remoteDriver38;
    if(local.repairEpoch!==v.repairEpoch){if(v.repairEpoch){nativeCall('pn_v19_fix',[h]);nativeCall('pn_v19_engine_health',[h,bits(1000)]);}local.repairEpoch=v.repairEpoch;}const current=coords(h),error=Math.hypot(...v.pos.map((p,i)=>p-current[i]));const age44=Math.max(0,(now-local.snapshotAt44)/1000),prediction44=remoteDriver38&&!placement?Math.min(.5,age44):0,blend44=1-Math.exp(-20*frameDelta44);const goal=v.pos.map((p,i)=>p+v.velocity[i]*prediction44);
    vector(...goal.map((p,i)=>placement||error>6?p:current[i]+(p-current[i])*blend44));e.pn_set_coords(h,ptr,1,1,1);
    e.pn_rotation(ptr,h,2);const rot=[s[0],s[2],s[4]];vector(...v.rot.map((r,i)=>placement?r:rot[i]+(((r-rot[i]+540)%360)-180)*blend44));e.pn_set_rotation(h,ptr,2,1);if(placement&&!v.driver)e.pn_vehicle_ground(h,5);vector(...(kinematic46||!v.driver||remoteDriver38&&age44>.5?[0,0,0]:v.velocity));e.pn_set_velocity(h,ptr);if(local.body!==v.body){e.pn_set_vehicle_body(h,v.body);local.body=v.body;}
   }
  }
 }
 mark51(5);if(now-doorCheckAt>30){doorCheckAt=now;a[114]=0;a[115]=-2;let nearestDoor=2.8,count=0;const local=coords(ped);Atomics.add(a,7500,1);
 if(!a[48]&&!a[62]){const nearbyIds=new Set(carStates.filter(v=>Math.hypot(v.pos[0]-local[0],v.pos[1]-local[1],v.pos[2]-local[2])<16).map(v=>v.id));const candidates=[...vehicles].filter(([id])=>nearbyIds.has(id)).slice(0,8).map(([id,v])=>({id,v,c:coords(v.handle)})).map(r=>({...r,d:Math.hypot(...r.c.map((c,i)=>c-local[i]))})).filter(r=>r.d<7).sort((a,b)=>a.d-b.d).slice(0,2);
 for(const {id,v} of candidates){const names=['door_dside_f','door_pside_f','door_dside_r','door_pside_r','bonnet','boot'];for(let i=0;i<names.length;i++){if(i<4&&i>=e.pn_vehicle_seats(e.pn_model(v.handle)))continue;const bone=e.pn_bone_index(v.handle,cstring(names[i]));if(bone<0)continue;e.pn_bone_position(ptr,v.handle,bone);const d=Math.hypot(s[0]-local[0],s[2]-local[1],s[4]-local[2]);if(d>3.5)continue;const visible=e.pn_project(ptr,BigInt(base+25240),BigInt(base+25244));if(!visible)continue;const o=7510+count*8;a[o]=id;a[o+1]=i;f[o+2]=f[6310];f[o+3]=f[6311];f[o+4]=d;a[o+5]=1;count++;if(i<4&&d<nearestDoor){nearestDoor=d;a[114]=id;a[115]=i-1;}}}}
 a[7501]=count;Atomics.add(a,7500,1);}
 const desired=a[48],desiredSeat=a[49];let ownCar=e.pn_vehicle(ped,0);
 if(!entryLocked&&seatVersion!==a[50]){
  if(!desired){seatExit46=ownCar&&[...vehicles.values()].some(v=>v.handle===ownCar)?ownCar:0;if(ownCar)e.pn_leave_vehicle(ped,ownCar,0);else if(seatStarted)e.pn_clear_tasks(ped);seatVersion=a[50];seatStarted=now;seatWarped=false;}
  else {const v=vehicles.get(desired);if(v&&v.grounded!==false){if(desiredSeat+2>e.pn_vehicle_seats(e.pn_model(v.handle))){a[56]=2;seatWarped=true;}else{e.pn_enter_vehicle(ped,v.handle,8000,desiredSeat,1,8,0n);seatWarped=false;}seatVersion=a[50];seatStarted=now;}}
 }
 if(!entryLocked&&desired&&vehicles.has(desired)&&vehicles.get(desired).grounded!==false&&seatVersion===a[50]&&now-seatStarted>8500&&!seatWarped&&e.pn_vehicle_seat(vehicles.get(desired).handle,desiredSeat,0)!==ped){e.pn_warp_vehicle(ped,vehicles.get(desired).handle,desiredSeat);seatWarped=true;}
 ownCar=e.pn_vehicle(ped,0);
 if(!entryLocked&&!desired&&ownCar&&ownCar===seatExit46&&seatVersion===a[50]&&now-seatStarted>3000){e.pn_leave_vehicle(ped,ownCar,16);seatStarted=now;ownCar=e.pn_vehicle(ped,0);}
 const carPair=[...vehicles].find(([id,v])=>v.handle===ownCar);
 if(ownCar&&!carPair){a[56]=1;}else if(!ownCar&&(!desired||a[56]!==2))a[56]=0;
 // Ambient discovery is bounded and sampled, not performed per rendered frame.
 if(now-trafficCheckAt>350&&!a[62]){trafficCheckAt=now;a[7602]=0;for(const v of carStates){if(v.owner!==0||Math.hypot(v.pos[0]-f[16],v.pos[1]-f[17],v.pos[2]-f[18])>7)continue;const h=vehicles.get(v.id)?.handle;if(!h)continue;const driver=e.pn_vehicle_seat(h,-1,0);if(driver&&driver!==ped&&!entities.size){a[7602]=v.id;a[7603]=e.pn_model(h);a[7604]=Math.min(8,e.pn_vehicle_seats(a[7603]));break;}if(driver&&driver!==ped&&![...entities.values()].some(e=>e.handle===driver)){a[7602]=v.id;a[7603]=e.pn_model(h);a[7604]=Math.min(8,e.pn_vehicle_seats(a[7603]));break;}}const local=coords(ped),managed=new Set([...vehicles.values()].map(v=>v.handle));
  const pool=new Int32Array(memory.buffer,base+49152,1026);pool.fill(0);pool[0]=512;const count=Math.max(0,Math.min(512,e.pn_all_vehicles(BigInt(base+49152))));
  vector(...local);const closest=e.pn_closest_vehicle?e.pn_closest_vehicle(ptr,7,0,127):0;let candidate=0,distance=7.01,pickCost=Infinity;const trying=e.pn_vehicle_trying(ped),inside=ownCar&&!carPair?ownCar:0;
  for(let i=-3;i<count;i++){const h=i===-3?closest:i===-2?inside:i===-1?trying:pool[2+i*2];if(!h||managed.has(h)||!e.pn_exists(h))continue;const cls=e.pn_vehicle_class(h);if(cls===14||cls===15||cls===16||cls===21)continue;const c=coords(h),d=Math.hypot(...c.map((v,n)=>v-local[n]));if(d>7||h!==inside&&e.pn_speed(h)>=5)continue;let score=d;if(a[6254]&&h!==inside){vector(c[0],c[1],c[2]+.5);if(!e.pn_project(ptr,BigInt(base+25240),BigInt(base+25244)))continue;score=Math.hypot(f[6310]-f[6252],f[6311]-f[6253]);if(score>.22)continue;}if(score<pickCost){candidate=h;distance=d;pickCost=score;}}
  Atomics.add(a,6208,1);a[6209]=candidate;a[6224]=candidate===inside?1:0;a[6225]=-2;if(candidate===inside&&inside)for(let seat=-1;seat<7;seat++)if(e.pn_vehicle_seat(candidate,seat,0)===ped){a[6225]=seat;break;}
  if(candidate){a[6210]=e.pn_model(candidate);const lock=e.pn_vehicle_lock_status(candidate);a[6211]=lock===0||lock===1?0:1;f.set(coords(candidate),6212);f[6215]=e.pn_heading(candidate);f[6216]=e.pn_vehicle_body(candidate);a[6217]=Math.min(8,e.pn_vehicle_seats(a[6210]));const driver=e.pn_vehicle_seat(candidate,-1,0);a[6226]=driver&&driver!==ped?1:0;f[6223]=distance;
   const p=Number(e.pn_vehicle_plate_text(candidate)),plate=new Uint8Array(memory.buffer,base+6218*4,16);plate.fill(0);if(p>0&&p+8<memory.buffer.byteLength){const src=new Uint8Array(memory.buffer,p,8);for(let n=0;n<8&&src[n];n++)plate[n]=src[n];}
   a[6222]=-2;let door=5;for(const [i,name] of ['door_dside_f','door_pside_f','door_dside_r','door_pside_r'].entries()){if(i>=a[6217])continue;const bone=e.pn_bone_index(candidate,cstring(name));if(bone<0)continue;e.pn_bone_position(ptr,candidate,bone);const d=Math.hypot(s[0]-local[0],s[2]-local[1],s[4]-local[2]);if(d<door){door=d;a[6222]=i-1;}}
  }Atomics.add(a,6208,1);
 }

 // One selected nearby car; an inexpensive projected model boundary, not a render effect.
 if(a[6254]&&!preview){
  const local=coords(ped),targetX=Number.isFinite(f[6252])?f[6252]:.5,targetY=Number.isFinite(f[6253])?f[6253]:.5;
  const candidates=carStates.filter(v=>Math.hypot(v.pos[0]-f[16],v.pos[1]-f[17],v.pos[2]-f[18])<9).slice(0,3).map(v=>({id:v.id,h:vehicles.get(v.id)?.handle})).filter(v=>v.h);if(a[6209])candidates.push({id:0,h:a[6209]});
  let chosen=null,cost=.22;
  for(const v of candidates){if(!e.pn_exists(v.h))continue;const pos=coords(v.h);if(Math.hypot(...pos.map((x,i)=>x-local[i]))>7)continue;
   vector(pos[0],pos[1],pos[2]+.5);if(!e.pn_project(ptr,BigInt(base+25240),BigInt(base+25244)))continue;
   const d=Math.hypot(f[6310]-targetX,f[6311]-targetY);if(d<cost){cost=d;chosen={...v,pos};}}
  Atomics.add(a,6255,1);a[6250]=chosen?.h||0;a[6251]=chosen?.id||0;
  if(chosen){const yaw=e.pn_heading(chosen.h)*Math.PI/180;let min=[-1,-2.4,-.4],max=[1,2.4,1.5];
   if(e.pn_model_dimensions){e.pn_model_dimensions(e.pn_model(chosen.h),BigInt(base+25280),BigInt(base+25312));const rawMin=Array.from(new Float32Array(memory.buffer,base+25280,3)),rawMax=Array.from(new Float32Array(memory.buffer,base+25312,3));if([...rawMin,...rawMax].every(Number.isFinite)&&rawMax[1]-rawMin[1]>.2&&rawMax[1]-rawMin[1]<20){min=rawMin;max=rawMax;}}
   for(let i=0;i<8;i++){const x=i&1?max[0]:min[0],y=i&2?max[1]:min[1],z=i&4?max[2]:min[2];vector(chosen.pos[0]+x*Math.cos(yaw)-y*Math.sin(yaw),chosen.pos[1]+x*Math.sin(yaw)+y*Math.cos(yaw),chosen.pos[2]+z);const valid=e.pn_project(ptr,BigInt(base+25240),BigInt(base+25244));f.set([f[6310],f[6311],valid?1:0],6260+i*3);}
  }Atomics.add(a,6255,1);
 }else a[6250]=0;
 a[58]=vehicles.size;a[126]=ownCar;if(ownCar){e.pn_control_disable(0,74,1);e.pn_control_disable(0,86,1);}if(ownCar&&carPair&&!carStates.find(v=>v.id===carPair[0])?.engine)e.pn_control_disable(0,71,1);
 let actualSeat=-2,carSample=Array(11).fill(0),paintSample43=null;
 if(carPair){for(let seat=-1;seat<Math.min(7,e.pn_vehicle_seats(e.pn_model(ownCar))-1);seat++)if(e.pn_vehicle_seat(ownCar,seat,0)===ped)actualSeat=seat;
  const pos=coords(ownCar);e.pn_rotation(ptr,ownCar,2);const rotation=[s[0],s[2],s[4]];e.pn_velocity(ptr,ownCar);carSample=[...pos,e.pn_heading(ownCar),...rotation,s[0],s[2],s[4],e.pn_vehicle_body(ownCar)];
 }
 if(carPair&&actualSeat===-1&&!entryLocked&&!a[7830]&&!a[7831]&&e.pn_health(ped)>100&&carPair[1].grounded!==false){
  const local=carPair[1];if(local.paintAt43===undefined||now-local.paintAt43>=500){local.paintAt43=now;local.paintObservation43=readPaint43(ownCar);}paintSample43=local.paintObservation43;
 }
 // Confirm only the actual driver's native pose/body, after corrections ran.
 a[13900]=0;a[13901]=a[13902]=-1;
 if(carPair){const v35=carStates.find(v=>v.id===carPair[0]),l35=carPair[1];if(v35){a[13900]=v35.id;
  const close35=v35.rot.every((r,i)=>Math.abs(((carSample[4+i]-r+540)%360)-180)<2);
  if(l35.poseEpoch===v35.poseEpoch&&close35)a[13901]=v35.poseEpoch;
  if(!v35.repairEpoch||(l35.repairEpoch===v35.repairEpoch&&carSample[10]>=999))a[13902]=v35.repairEpoch;
 }}
 if(self.__pavPhonePed42!==ped){if(phoneState)e.pn_destroy_phone();phoneState=false;self.__pavPhonePed42=ped;}
 const wantPhone=!entryLocked&&e.pn_health(ped)>100&&!a[7830]&&!a[7831]&&!!a[116];if(wantPhone!==phoneState){e.pn_admin_permission(1);if(wantPhone)nativeCall('CREATE_MOBILE_PHONE',[0]);e.pn_phone_task(ped,wantPhone?1:0,0);if(!wantPhone)e.pn_destroy_phone();e.pn_admin_permission(a[101]?1:0);phoneState=wantPhone;self.__pavPhoneAt42=now;}
 else if(wantPhone&&now-(self.__pavPhoneAt42||0)>1000&&!e.pn_phone_active(ped)){e.pn_phone_task(ped,1,0);self.__pavPhoneAt42=now;}
 const wantHands=!entryLocked&&!!a[117]&&e.pn_health(ped)>100&&!ownCar;if(wantHands!==handsState){if(wantHands){e.pn_clear_tasks(ped);e.pn_select_weapon(ped,0xA2719263|0,1);e.pn_hands_up(ped,-1,0,-1,0);}else if(handsState)e.pn_clear_tasks(ped);handsState=wantHands;}
 // Render a local showroom object without changing ownership or player loadout.
 // World simulation and peer sampling continue after this block.
 if(a[6500]){
  const mode=a[6500],requested=a[6501],assetModel=mode===2?modelOf(0):requested;
  if(showroomHash!==requested||showroomMode!==mode){
   if(showroomHandle&&e.pn_exists(showroomHandle)){a[16008]=showroomHandle;if(showroomMode===1)e.pn_delete_vehicle(BigInt(base+64032));else e.pn_delete(BigInt(base+64032));}
   showroomHandle=0;showroomHash=requested;showroomMode=mode;a[6503]=0;
  }
  if(!showroomHandle&&loaded(assetModel)){
   const position=coords(ped);vector(position[0]+6,position[1],position[2]+3);e.pn_collision_request(ptr);a[16236]=0;
   if(e.pn_ground(ptr,BigInt(base+64944),0,1)&&Math.abs(f[16236]-position[2])<2){
    vector(position[0]+6,position[1],f[16236]+.1);
    showroomHandle=mode===2?e.pn_create_ped(4,assetModel,ptr,0,0,1):e.pn_create_vehicle(assetModel,ptr,0,0,1,0);
    if(showroomHandle){e.pn_mission_entity(showroomHandle,1,1);if(mode===1){e.pn_vehicle_ground(showroomHandle,0);e.pn_vehicle_engine(showroomHandle,0,1,1);}else{e.pn_block_events(showroomHandle,1);e.pn_give_weapon(showroomHandle,requested,0,0,1);e.pn_select_weapon(showroomHandle,requested,1);}e.pn_freeze(showroomHandle,1);e.pn_collision(showroomHandle,0,0);e.pn_invincible(showroomHandle,1);e.pn_model_release(assetModel);}
   }
  }
  if(showroomHandle){
   if(!showroomCam)showroomCam=e.pn_cam_create(cstring('DEFAULT_SCRIPTED_CAMERA'),1);
   const position=coords(showroomHandle),angle=f[6505]*Math.PI/180,distance=Math.max(mode===2?1.2:3,Math.min(9,f[6506]||(mode===2?2.3:6)));
   vector(position[0]+Math.sin(angle)*distance,position[1]+Math.cos(angle)*distance,position[2]+(mode===2?1.2:1.4));e.pn_cam_set(showroomCam,ptr);vector(position[0],position[1],position[2]+(mode===2?1.1:.6));e.pn_cam_point(showroomCam,ptr);e.pn_cam_fov(showroomCam,42);e.pn_cam_render(1,0,0,1,0,0);a[6503]=1;
  }
  e.pn_controls_disable(0);
 }else if(showroomCam||showroomHandle){
  if(showroomCam){e.pn_cam_render(0,0,0,1,0,0);e.pn_cam_destroy(showroomCam,1);showroomCam=0;}
  if(showroomHandle&&e.pn_exists(showroomHandle)){a[16008]=showroomHandle;if(showroomMode===1)e.pn_delete_vehicle(BigInt(base+64032));else e.pn_delete(BigInt(base+64032));}
  showroomHandle=0;showroomHash=0;showroomMode=0;a[6503]=0;e.pn_focus_ped(ped);e.pn_follow_ped(ped);e.pn_follow_mode(1);e.pn_follow_heading(0);
 }


 // Existing native GPS owns road routing. Sample only128points once/second.
 if(a[6650]!==self.__pavWaypointEpoch){self.__pavWaypointEpoch=a[6650];if(a[6651]){nativeCall('pn_v20_force_gps',[1]);nativeCall('pn_v19_waypoint',[bits(f[6652]),bits(f[6653])]);}else{nativeCall('pn_v19_waypoint_off');nativeCall('pn_v20_force_gps',[0]);}self.__pavRouteAt=0;}
 if(a[6651]&&now-(self.__pavRouteAt||0)>1000){self.__pavRouteAt=now;const origin=coords(ped),step=Math.max(20,Math.hypot(f[6652]-origin[0],f[6653]-origin[1])/80);let count=0,last=null;Atomics.add(a,6700,1);for(let n=0;n<128;n++){const out=BigInt(base+64704);new Float32Array(memory.buffer,Number(out),6).fill(0);if(!nativeCall('pn_v19_gps_point',[out,1,bits(n*step),0]))break;const reference=Array.from(new Float32Array(memory.buffer,base+60064,3)),point=new Float32Array(memory.buffer,Number(out),6),variants=[reference,[point[0],point[1],point[2]],[point[0],point[2],point[4]]];if(n===0){const viable=variants.map((v,i)=>({i,v,d:Math.hypot(...v.map((x,j)=>x-origin[j]))})).filter(o=>o.v.every(Number.isFinite)&&o.v.some(x=>Math.abs(x)>.0001));viable.sort((a,b)=>a.d-b.d);self.__pavGpsLayout=viable[0]?.i??0;}const xyz=variants[self.__pavGpsLayout??0];if(!xyz.every(Number.isFinite)||last&&Math.hypot(...xyz.map((x,i)=>x-last[i]))<.05)break;f.set(xyz,6702+count*3);count++;last=xyz;}a[6701]=count;Atomics.add(a,6700,1);}else if(!a[6651])a[6701]=0;
 // A finite, requested native animation. Clear only this task on completion.
 const kind=entryLocked?0:a[6600],actionSeq=a[6601];if(actionSeq!==self.__pavActionSeq){self.__pavActionSeq=actionSeq;self.__pavActionStarted=false;if(!kind&&self.__pavActionActive){e.pn_clear_tasks(ped);self.__pavActionActive=false;}}
 if(kind&&!self.__pavActionStarted){const dict=kind===1?'mp_player_inteat@burger':kind===2?'mp_player_intdrink':kind===4?'weapons@pistol@combat_pistol':'clothingtie',clip=kind===1?'mp_player_int_eat_burger':kind===2?'loop_bottle':kind===4?'reload_aim':'try_tie_positive_a';const dp=cstring(dict,65120),cp=cstring(clip,65160);nativeCall('pn_v19_anim_request',[dp]);if(nativeCall('pn_v19_anim_loaded',[dp])){nativeCall('pn_v19_anim',[ped,dp,cp,bits(3),bits(-3),Math.max(500,a[6602]),49,bits(0),0,0,0]);self.__pavActionStarted=true;self.__pavActionActive=true;}}
 if(!entryLocked&&a[6604]!==self.__pavReloadSeq){self.__pavReloadSeq=a[6604];if(a[6604]){nativeCall('pn_v19_clip',[ped,a[103],Math.min(a[7120]||30,a[104])]);}}
 if(a[6660]!==self.__pavInteriorSeq){self.__pavInteriorSeq=a[6660];if(a[6661])nativeCall('pn_v19_ipl',[cstring('ex_dt1_02_office_02b',65200)]);}

 const xyz=coords(ped),heading=e.pn_heading(ped),speed=e.pn_speed(ped),health=e.pn_health(ped);
 e.pn_velocity(ptr,ped);const velocity=[s[0],s[2],s[4]];e.pn_cam_coord(ptr);const camera=[s[0],s[2],s[4]];e.pn_cam_rot(ptr,2);const pitch=s[0]*Math.PI/180,yaw=s[4]*Math.PI/180;
 const aim=[camera[0]-Math.sin(yaw)*Math.cos(pitch)*80,camera[1]+Math.cos(yaw)*Math.cos(pitch)*80,camera[2]+Math.sin(pitch)*80];
 if(!entryLocked&&e.pn_is_melee(ped))meleeUntil=now+250;if(!entryLocked&&e.pn_shooting(ped))shootUntil=now+180;const shooting=now<shootUntil,flags=entryLocked?0:(shooting?1:0)|(e.pn_aiming(e.pn_player_id())?2:0)|(e.pn_jumping(ped)?4:0)|(e.pn_reloading(ped)?8:0)|(e.pn_is_ragdoll(ped)?16:0)|(now<meleeUntil?32:0)|(wantPhone?64:0)|(wantHands?128:0);
 const own=[...xyz,heading,speed,health,...velocity];if(!own.every(Number.isFinite))throw Error('Geçersiz motor konumu.');
 if(!entryLocked&&a[103]&&a[6608]===a[102]&&!a[62]&&!a[6600]&&!a[116]&&!a[117]&&e.pn_health(ped)>100&&now-(self.__pavEquipAt||0)>500&&(e.pn_weapon(ped)>>>0)!==(a[103]>>>0)){self.__pavEquipAt=now;e.pn_select_weapon(ped,a[103],1);}
 if(a[103]&&self.__pavTint!==ped+':'+a[103]+':'+a[7100]){nativeCall('pn_v20_tint',[ped,a[103],a[7100]]);self.__pavTint=ped+':'+a[103]+':'+a[7100];}const weapon=e.pn_weapon(ped);a[16020]=0;const clipOK=e.pn_clip(ped,weapon,BigInt(base+64080));const ammo=e.pn_ammo(ped,weapon),stamina=e.pn_stamina(e.pn_player_id()),safezone=e.pn_safezone();
 const projectHead=h=>{s[12]=0;s[14]=0;s[16]=0;const root=coords(h);e.pn_head(BigInt(base+64096),h,0x796e,BigInt(base+64048));const head=new Float32Array(memory.buffer,base+64096,6);self.__pavHeadHeights??=new Map();let height=self.__pavHeadHeights.get(h);if(height===undefined){height=Math.max(.6,Math.min(1.9,head[4]-root[2]));self.__pavHeadHeights.set(h,height);if(self.__pavHeadHeights.size>100)self.__pavHeadHeights.delete(self.__pavHeadHeights.keys().next().value);}const seated=!!e.pn_vehicle(h,0),bone=[head[0],head[2],head[4]],valid=bone.every(Number.isFinite)&&Math.hypot(bone[0]-root[0],bone[1]-root[1],bone[2]-root[2])<5;if(seated&&valid)vector(bone[0],bone[1],bone[2]+.25);else vector(root[0],root[1],root[2]+height+.20);return e.pn_project(ptr,BigInt(base+64024),BigInt(base+64028));};
 const ownVisible=projectHead(ped),headXY=[s[6],s[7]];
 const info=new BigUint64Array(memory.buffer,base+64400,4),args=new BigUint64Array(memory.buffer,base+64432,4);info.fill(0n);info[2]=BigInt(base+64432);for(let i=0;i<4;i++)args[i]=BigInt(base+64320+i*4);e.pn_hud_minimap(BigInt(base+64400));const map=new Float32Array(memory.buffer,base+64320,4);
 if(!(map[2]>.02&&map[3]>.02)){e.pn_minimap_position(BigInt(base+64560));e.pn_minimap_size(BigInt(base+64576));const pos=new Float32Array(memory.buffer,base+64560,2),size=new Float32Array(memory.buffer,base+64576,2);if(size[0]>.02&&size[1]>.02)map.set([pos[0],pos[1],size[0],size[1]]);}
 a[67]=e.pn_armor(ped);
 Atomics.add(a,4,1);f.set(own,16);a[25]=weapon;a[26]=a[7612]?0:flags;const meleePed=e.pn_melee_target(ped),targetEntry=[...entities].find(([id,v])=>v.handle===meleePed);if(targetEntry)meleeTarget=targetEntry[0];a[106]=!a[7612]&&now<meleeUntil?meleeTarget:0;f.set(aim,27);a[30]=Math.max(0,ammo);a[31]=clipOK?Math.max(0,a[16020]):0;f[32]=Math.max(0,Math.min(100,100-stamina));f[33]=safezone;a[34]=ownVisible;f.set(headXY,35);f.set([map[0],map[1]],38);f.set([map[2],map[3]],52);a[54]=carPair?.[0]||0;a[55]=actualSeat;f.set(carSample,2880);a.fill(0,2891,2903);if(paintSample43){a[2891]=43;a[2892]=carPair[0];a.set(paintSample43,2893);}Atomics.store(a,3,ped);Atomics.store(a,2,1);Atomics.add(a,4,1);

 mark51(6);// Only four nearby service attendants share one streamed model. Native ground
 // readiness precedes creation; no distant ped pool or per-frame pose reset.
 const nearServices=[];for(let i=0;i<Math.min(24,a[107]);i++){const o=6000+i*8,id=a[o];if(!id)continue;const d=Math.hypot(f[o+1]-f[16],f[o+2]-f[17],f[o+3]-f[18]);if(d<55)nearServices.push({id,x:f[o+1],y:f[o+2],z:f[o+3],d});}
if(!a[62])for(const v of nearServices.filter(v=>v.d<18).slice(0,4))nativeCall('pn_v20_marker',[1,bits(v.x),bits(v.y),bits(v.z-.9),bits(0),bits(0),bits(0),bits(0),bits(0),bits(0),bits(.6),bits(.6),bits(.18),176,235,121,150,0,0,2,0,0n,0n,0]);
 // Resolve the actual streamed door, not the attendant's approximate position.
 if(!a[62]&&now-(self.__pavShopDoorsAt||-Infinity)>600){self.__pavShopDoorsAt=now;
  const doorModels=['v_ilev_gunshopdoor','v_ilev_gunshopdoor_r','v_ilev_gc_door04','v_ilev_gc_door03','v_ilev_gc_door01','v_ilev_gc_door02','v_ilev_bs_door','v_ilev_bs_door01','v_ilev_ss_door01','v_ilev_ss_door02','v_ilev_store_door','v_ilev_cs_door01','v_ilev_cs_door01r','v_ilev_clothmiddoor','v_ilev_clothmiddoor2','v_ilev_clothlowdoor','v_ilev_clothlowdoor2'];
  if(nearServices.some(v=>v.d<35))for(const name of doorModels){const model=modelHash23(name),h=nativeCall('GET_CLOSEST_OBJECT_OF_TYPE',[bits(f[16]),bits(f[17]),bits(f[18]),bits(14),model,0,0,0]);if(!h||!e.pn_exists(h))continue;const pos=coords(h),d=Math.hypot(...pos.map((x,i)=>x-f[16+i]));e.pn_freeze(h,0);nativeCall('SET_STATE_OF_CLOSEST_DOOR_OF_TYPE',[model,...pos.map(bits),0,bits(d<3?1:0),0]);a[16272]=0;if(nativeCall('DOOR_SYSTEM_FIND_EXISTING_DOOR',[...pos.map(bits),model,BigInt(base+65088)])){const inline=a[15016]>>>0,door=a[16272]>>>0||(inline!==((base+65088)>>>0)?inline:0);if(!door)continue;nativeCall('DOOR_SYSTEM_SET_DOOR_STATE',[door,0,0,1]);nativeCall('DOOR_SYSTEM_SET_OPEN_RATIO',[door,bits(d<3?1:0),0,1]);}}
 }
 nearServices.sort((x,y)=>x.d-y.d||x.id-y.id);const wantedNpcs=[];for(const v of nearServices){if(wantedNpcs.length>=4)break;if(!wantedNpcs.some(n=>n.id===v.id||Math.hypot(n.x-v.x,n.y-v.y,n.z-v.z)<1.6))wantedNpcs.push(v);}const wantedIds=new Set(wantedNpcs.map(v=>v.id));
 for(const [id,npc] of serviceNpcs)if(!wantedIds.has(id)){if(e.pn_exists(npc.handle)){a[16008]=npc.handle;e.pn_delete(BigInt(base+64032));}serviceNpcs.delete(id);}
 let madeNpc=false;const npcModel=hash('a_m_m_business_01');Atomics.add(a,3001,1);let seenNpc=0;
 for(const v of wantedNpcs){let npc=serviceNpcs.get(v.id);if(npc&&!e.pn_exists(npc.handle)){serviceNpcs.delete(v.id);npc=null;}
  if(!npc&&!madeNpc&&loaded(npcModel)){vector(v.x,v.y,v.z+.25);e.pn_collision_request(ptr);f[16236]=NaN;if(e.pn_ground(ptr,BigInt(base+64944),0,1)&&Number.isFinite(f[16236])&&Math.abs(f[16236]+1-v.z)<.8){const floor42=f[16236];vector(v.x,v.y,floor42+.05);const handle=e.pn_create_ped(4,npcModel,ptr,180,0,1);if(handle){vector(v.x,v.y,floor42+1);e.pn_set_coords(handle,ptr,1,1,1);npc={handle};serviceNpcs.set(v.id,npc);madeNpc=true;e.pn_mission_entity(handle,1,1);e.pn_block_events(handle,1);e.pn_invincible(handle,1);e.pn_clear_tasks(handle);e.pn_freeze(handle,1);e.pn_collision(handle,0,0);e.pn_model_release(npcModel);}}}
  if(!npc){if(v.d<=18){vector(v.x,v.y,v.z+1.2);const visible=e.pn_project(ptr,BigInt(base+64024),BigInt(base+64028)),o=3010+seenNpc*8;a[o]=v.id;a[o+1]=visible;f[o+2]=s[6];f[o+3]=s[7];f[o+4]=v.d;seenNpc++;}continue;}const pos=coords(npc.handle),o=3010+seenNpc*8,visible=projectHead(npc.handle);a[o]=v.id;a[o+1]=visible;f[o+2]=s[6];f[o+3]=s[7];f[o+4]=Math.hypot(...pos.map((x,i)=>x-f[16+i]));seenNpc++;
 }Atomics.store(a,3000,seenNpc);Atomics.add(a,3001,1);
 if(!entryLocked&&!a[62]&&!a[6500]&&e.pn_health(ped)>100){restraint34(ped,!!a[7830],!!a[7831],self.__pavOwnRestraint34);if(a[7831])e.pn_freeze(ped,1);}
 const sequence=Atomics.load(a,6),peers=[];if(sequence&1)return;
 for(let i=0;i<Math.min(32,Atomics.load(a,5));i++){const o=128+i*64;peers.push({o,id:a[o],x:f[o+1],y:f[o+2],z:f[o+3],heading:f[o+4],speed:f[o+5],health:f[o+6],vx:f[o+7],vy:f[o+8],vz:f[o+9],weapon:a[o+10],flags:a[o+11],aim:[f[o+12],f[o+13],f[o+14]],vehicle:a[o+15],seat:a[o+16],version:a[o+17],damage:a[o+18],damageKind:a[o+19],tint:a[o+58],armor:a[o+60],meleeTarget:a[o+61],carriedBy:a[o+62],fly:!!a[o+63],cuffed:!(a[o+11]&256)&&a[7840+i*4]===a[o]&&!!a[7841+i*4],prone:!(a[o+11]&256)&&a[7840+i*4]===a[o]&&!!a[7842+i*4],ambient:!!(a[o+11]&256),model:(a[o+11]&256)?a[o+19]:modelOf(a[o+20])});}
 if(sequence!==Atomics.load(a,6))return;if(sequence!==peerSequence){peerSequence=sequence;receivedAt=now;}const prediction=Math.min(.2,Math.max(0,(now-receivedAt)/1000));
 const active=new Set(peers.map(p=>p.id));
 const remove=entity=>{
  if(entity.blip){a[16008]=entity.blip;e.pn_remove_blip(BigInt(base+64032));entity.blip=0;}
  if(!e.pn_exists(entity.handle))return true;
  entity.retiring38=true;if(now-(entity.deleteAt38??-Infinity)<500)return false;
  entity.deleteAt38=now;a[16008]=entity.handle;e.pn_delete(BigInt(base+64032));return !e.pn_exists(entity.handle);
 };
 for(const [id,entity] of entities)if(!active.has(id)&&remove(entity)){entities.delete(id);attempts.delete(id);}
 let created=false;Atomics.add(a,9,1);let observed=0;
 mark51(7);for(const p of peers){
  if(!p.id||![p.x,p.y,p.z,p.heading,p.health,...p.aim].every(Number.isFinite))continue;
  let entity=entities.get(p.id);if(entity&&entity.model!==p.model){if(!remove(entity))continue;entities.delete(p.id);entity=null;}
  if(!entity||!e.pn_exists(entity.handle)){
   if(created||!loaded(p.model)||now-(attempts.get(p.id)??-Infinity)<1000)continue;attempts.set(p.id,now);vector(p.x,p.y,p.z);const handle=e.pn_create_ped(4,p.model,ptr,p.heading,0,1);if(!handle)continue;
   created=true;entity={handle,model:p.model,version:-1,lastTask:0,weapon:0,mode:'',health:-1,damage:p.damage,vehicle:0,seat:-2,blip:p.ambient?0:e.pn_blip(handle),hitUntil:0};entities.set(p.id,entity);e.pn_mission_entity(handle,1,1);
   e.pn_block_events(handle,1);e.pn_combat_attr(handle,17,0);e.pn_combat_attr(handle,58,1);e.pn_flee_attr(handle,-1,0);e.pn_keep_task(handle,1);e.pn_ambient_anim(handle,0);e.pn_ambient_base(handle,0);e.pn_evasive_dive(handle,0);e.pn_critical_hits(handle,0);e.pn_invincible(handle,p.ambient?1:0);e.pn_ragdoll(handle,p.ambient?0:1);if(remoteGroup)e.pn_group(handle,remoteGroup);e.pn_blip_colour(entity.blip,2);e.pn_blip_scale(entity.blip,.75);e.pn_clear_tasks(handle);e.pn_model_release(p.model);
  }
  if(entity.retiring38){entity.retiring38=false;entity.deleteAt38=-Infinity;entity.version=-1;entity.health=-1;entity.mode='';entity.vehicle=0;entity.seat=-2;entity.lastTask=0;e.pn_clear_tasks(entity.handle);if(!entity.blip&&!p.ambient){entity.blip=e.pn_blip(entity.handle);e.pn_blip_colour(entity.blip,2);e.pn_blip_scale(entity.blip,.75);}}
  const h=entity.handle;if(entity.mode==='phone' &&!(p.flags&64))e.pn_phone_task(h,0,0);if(entity.version!==p.version){if(!p.ambient)applyLook(h,p.o+20);entity.version=p.version;}
  if(e.pn_armor(h)!==p.armor)e.pn_set_armor(h,p.armor);
  const current=coords(h),quietMotion42=!p.vehicle&&p.speed<=.35&&Math.hypot(p.vx,p.vy)<=.35&&Math.hypot(p.x-current[0],p.y-current[1])>.25,moving=p.speed>.35||Math.hypot(p.vx,p.vy)>.35||quietMotion42,goal=[p.x+(moving?p.vx*prediction:0),p.y+(moving?p.vy*prediction:0),p.z],error=Math.hypot(...goal.map((v,i)=>v-current[i]));
  if(e.pn_damaged_by(h,ped,1)){if(entryLocked){e.pn_clear_damage(h);}else{const seq=Atomics.load(a,10)+1,o=2800+(seq%16)*4;a[o]=seq;a[o+1]=p.id;a[o+2]=shooting||(!(flags&32)&&(e.pn_weapon(ped)>>>0)!==0xA2719263)?1:0;Atomics.store(a,10,seq);if(!a[o+2]){meleeTarget=p.id;meleeUntil=now+250;}e.pn_clear_damage(h);}}
  const targetHealth=p.health<=100?0:Math.round(p.health),nativeHealth=e.pn_health(h);if(entity.health!==p.health||nativeHealth!==targetHealth){if(p.health>100&&nativeHealth<=100)e.pn_resurrect(h);e.pn_set_health(h,targetHealth,0);entity.health=p.health;}
  if(p.damage!==entity.damage){entity.damage=p.damage;if(p.damage&&p.health>100){const duration=p.damageKind===1?450:180;e.pn_ragdoll_task(h,duration,duration,0,0,0,0);entity.hitUntil=now+duration;}}

  const activity=a[p.o+59];if(entity.activity!==activity){entity.activity=activity;entity.actionStarted=false;if(!activity)e.pn_clear_tasks(h);}
  if(activity&&!entity.actionStarted){const d=activity===1?'mp_player_inteat@burger':activity===2?'mp_player_intdrink':activity===4?'weapons@pistol@combat_pistol':'clothingtie',c=activity===1?'mp_player_int_eat_burger':activity===2?'loop_bottle':activity===4?'reload_aim':'try_tie_positive_a';const dp=cstring(d,65120),cp=cstring(c,65160);nativeCall('pn_v19_anim_request',[dp]);if(nativeCall('pn_v19_anim_loaded',[dp])){nativeCall('pn_v19_anim',[h,dp,cp,bits(3),bits(-3),3000,49,bits(0),0,0,0]);entity.actionStarted=true;}}
  if(entity.weapon!==p.weapon&&p.weapon){e.pn_give_weapon(h,p.weapon,999,0,1);e.pn_select_weapon(h,p.weapon,1);entity.weapon=p.weapon;}if(p.weapon&&entity.tint!==p.weapon+':'+p.tint){nativeCall('pn_v20_tint',[h,p.weapon,p.tint]);entity.tint=p.weapon+':'+p.tint;}
  const car=vehicles.get(p.vehicle);const inCar=e.pn_vehicle(h,0);
  if(p.fly&&p.health>100&&!car){
   if(!entity.fly){e.pn_clear_tasks(h);e.pn_freeze(h,1);e.pn_collision(h,0,0);entity.fly=true;}
   vector(...goal.map((v,i)=>error>8?v:current[i]+(v-current[i])*.4));e.pn_set_coords(h,ptr,1,1,1);e.pn_set_heading(h,p.heading);entity.mode='fly';
  }else{
  if(entity.fly){e.pn_freeze(h,0);e.pn_collision(h,1,1);entity.fly=false;}

  if(car&&p.health>100){if(inCar!==car.handle||entity.seat!==p.seat)e.pn_warp_vehicle(h,car.handle,p.seat);entity.vehicle=p.vehicle;entity.seat=p.seat;entity.mode='vehicle';}
  else if(inCar){if(entity.mode!=='exit'){e.pn_leave_vehicle(h,inCar,0);entity.mode='exit';entity.exitAt42=now;entity.hitUntil=now+2000;}
   else if(!p.vehicle&&p.health>100&&now-(entity.exitAt42??now)>3000){e.pn_leave_vehicle(h,inCar,16);entity.exitAt42=now;if(!e.pn_vehicle(h,0)){vector(...goal);e.pn_set_coords(h,ptr,1,1,1);e.pn_set_heading(h,p.heading);entity.vehicle=0;entity.seat=-2;entity.mode='';entity.hitUntil=now;}}}
  else if(p.health>100&&!p.prone&&now>=entity.hitUntil&&(!activity||moving)){
   entity.vehicle=0;entity.seat=-2;if(error>4){vector(...goal);e.pn_set_coords(h,ptr,1,1,1);}else if(quietMotion42){vector(...goal.map((v,i)=>current[i]+(v-current[i])*.35));e.pn_set_coords(h,ptr,1,1,1);}
   const mode=p.cuffed?(moving?'walk':'idle'):p.flags&64?'phone':p.flags&128?'hands':p.flags&16?'ragdoll':p.flags&32&&p.meleeTarget?'melee':p.flags&8?'reload':p.flags&4?'jump':p.flags&1?(moving?'move-shoot':'shoot'):p.flags&2?(moving?'move-aim':'aim'):moving?'walk':'idle';
   if(mode==='idle'){const angle=((p.heading-e.pn_heading(h)+540)%360)-180;if(Math.abs(angle)>.5)e.pn_set_heading(h,p.heading);}
   const previousMode=entity.mode,changed=mode!==previousMode;const interval=mode==='walk'?650:mode.startsWith('move-')?400:220;
   if(changed||now-entity.lastTask>interval){
    if(changed&&['hands','phone'].includes(previousMode)&&!['hands','phone'].includes(mode))e.pn_clear_tasks(h);

    if(mode==='phone'){if(entity.mode!=='phone')e.pn_phone_task(h,1,0);}
    else if(mode==='hands'){if(entity.mode!=='hands')e.pn_hands_up(h,-1,0,-1,0);}
    else if(mode==='melee'){const target=p.meleeTarget===a[51]?ped:entities.get(p.meleeTarget)?.handle;if(target&&(mode!==entity.mode||entity.meleeTarget!==p.meleeTarget)){e.pn_direct_melee(h,target,0,-1,0,0);entity.meleeTarget=p.meleeTarget;}}
    else if(mode==='move-shoot'||mode==='move-aim'){vector(goal[0]+p.vx*.18,goal[1]+p.vy*.18,goal[2]);s[12]=p.aim[0];s[14]=p.aim[1];s[16]=p.aim[2];e.pn_move_aim(h,ptr,BigInt(base+64048),p.speed>4?3:p.speed>1.8?2:1,mode==='move-shoot'?1:0,.12,0,0,0,1,0xC6EE6B4C|0);}
    else if(mode==='shoot'||mode==='aim'){vector(...p.aim);if(mode==='shoot')e.pn_shoot(h,ptr,250,0xC6EE6B4C|0);else e.pn_aim(h,ptr,300,0,0);}
    else if(mode==='jump'){if(entity.mode!=='jump')e.pn_jump(h,0,0,0);}
    else if(mode==='reload'){if(entity.mode!=='reload')e.pn_reload(h,0);}
    else if(mode==='ragdoll'){if(entity.mode!=='ragdoll')e.pn_ragdoll_task(h,500,500,0,0,0,0);}
    else if(mode==='walk'){vector(goal[0]+p.vx*.8,goal[1]+p.vy*.8,goal[2]);e.pn_walk(h,ptr,Math.max(1,Math.min(3,p.speed>4?3:p.speed>1.8?2:1)),1000,p.heading,.15);}
    else if(entity.mode!=='idle'){e.pn_clear_tasks(h);e.pn_set_heading(h,p.heading);}
    entity.mode=mode;entity.lastTask=now;
   }
  }
  }
  restraint34(h,p.cuffed,p.prone,entity);if(p.prone){vector(...goal);e.pn_set_coords(h,ptr,1,1,1);e.pn_set_heading(h,p.heading);}
  const carrier=p.carriedBy===a[51]?ped:entities.get(p.carriedBy)?.handle;
  if(carrier&&entity.carriedBy!==p.carriedBy){const bone=e.pn_bone_index(carrier,cstring('SKEL_Spine2'));vector(0,-.25,.2);s[12]=0;s[14]=0;s[16]=180;e.pn_attach(h,carrier,Math.max(0,bone),ptr,BigInt(base+64048),0,0,0,1,2,1,0);entity.carriedBy=p.carriedBy;}
  else if(!carrier&&entity.carriedBy){e.pn_detach(h,1,1);entity.carriedBy=0;}
  const actual=coords(h),o=2304+observed*12,visible=projectHead(h);a[o]=p.id;a[o+1]=visible;f[o+2]=s[6];f[o+3]=s[7];f[o+4]=Math.hypot(...actual.map((v,i)=>v-xyz[i]));f[o+5]=p.health;f.set(actual,o+6);const actualCar=e.pn_vehicle(h,0);a[o+9]=[...vehicles].find(([id,v])=>v.handle===actualCar)?.[0]||0;observed++;
 }
 const localCarrier=entities.get(a[118])?.handle;
 if(localCarrier&&self.__pavCarriedBy!==a[118]){const bone=e.pn_bone_index(localCarrier,cstring('SKEL_Spine2'));vector(0,-.25,.2);s[12]=0;s[14]=0;s[16]=180;e.pn_attach(ped,localCarrier,Math.max(0,bone),ptr,BigInt(base+64048),0,0,0,1,2,1,0);self.__pavCarriedBy=a[118];}
 else if(!localCarrier&&self.__pavCarriedBy){e.pn_detach(ped,1,1);self.__pavCarriedBy=0;}
 if(a[118]||entryLocked)e.pn_controls_disable(0);
 Atomics.store(a,11,observed);Atomics.add(a,9,1);Atomics.store(a,7,entities.size);
 }catch(error){failBridge(a,error);}
 finally{e.pn_bridge_control(1);busy=false;const elapsed51=performance.now()-tickStart51;f[14105]=elapsed51;f[14106]=Math.max(f[14106],elapsed51);if(elapsed51>33)Atomics.add(a,14107,1);mark51(a[2]===-1?99:0);}
}
};
})();
