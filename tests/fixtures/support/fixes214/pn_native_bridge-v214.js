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
let e,memory,base,ready=false,busy=false,spawned=false,hpVersion=-1,spawnVersion=-1,lastTick=-Infinity,shootUntil=0,peerSequence=-1,receivedAt=0,settingsOpen=false,appearanceVersion=-1,localDamage=0,seatVersion=-1,seatStarted=0,seatWarped=false,remoteGroup=0,lastUnknown=0,previewCam=0,introCam=0,introStarted=0,spawnAt=0,previousPreview=false,previousFly=false,lastSound=0,armorVersion=-1,loadoutVersion=-1,deathSettingsAt=-Infinity,meleeUntil=0,meleeTarget=0,groundPlaced=true,groundRetry=0,phoneState=false,handsState=false,doorCheckAt=-Infinity,trafficCheckAt=-Infinity,bindVersion=0,seatExit46=0,seatTask62=false,customCam72=0,airProbe72=null,reconCam72=0,reconActive72=false,reconReturn72=0;
let interiorGate31=null,interiorSeq31=0;
let showroomHandle=0,showroomCam=0,showroomHash=0,showroomMode=0;const verifiedCars77=new Set(),failedModels33=new Set(),modelWait41=new Map();let modelRetry41=0;const serviceNpcs=new Map();const entities=new Map(),vehicles=new Map(),requests=new Map(),attempts=new Map(),serviceBlips=new Map();
const blends=new Map();
let previewHeading=0,previewSpawnVersion=-1,minimapMovie=0,mapRefreshed=false,mapResetTick=false,lastMapSetup=-Infinity;
let nativeTableMode=null;let cameraPed51=0,cameraAt51=-Infinity;let cameraVerified60=false,cameraJoining60=false,cameraReleaseAt60=-Infinity,cameraCheckAt60=-Infinity;
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
 const a=new Int32Array(memory.buffer,base,16384),f=new Float32Array(memory.buffer,base,16384);const tickStart51=performance.now();let phaseAt51=tickStart51;const mark51=phase=>{const at51=performance.now(),elapsed51=at51-phaseAt51;if(a[14102]&&a[14102]<99){const ph107=self.__phase107??=new Float32Array(16);ph107[a[14102]]=Math.max(ph107[a[14102]],elapsed51);}if(a[14102]&&a[14102]<99&&elapsed51>f[14108]){f[14108]=elapsed51;a[14109]=a[14102];}phaseAt51=at51;a[14102]=phase;Atomics.add(a,14104,1);};if(a[62]){cameraPed51=0;cameraVerified60=false;}
 if(!Atomics.load(a,1)){
  if((self.__phone85?.handle||self.__room85?.id)&&e.pn_context()){e.pn_bridge_control(2);try{if(self.__phone85?.handle){e.pn_mission_entity(self.__phone85.handle,1,1);a[16008]=self.__phone85.handle;e.pn_delete(BigInt(base+64032));self.__phone85.handle=0;}if(self.__room85?.id){/* UNPIN through the registered reset callback */self.__releaseRoom85?.();}}finally{e.pn_bridge_control(1);}}
  if(self.__police84?.applied&&e.pn_context()){e.pn_bridge_control(2);try{self.__resetPolice84?.();}finally{e.pn_bridge_control(1);}}
  if(a[7610]&&e.pn_context()){e.pn_bridge_control(2);try{e.pn_controls_disable(0);const idlePed=e.pn_player_ped();if(idlePed){e.pn_freeze(idlePed,1);e.pn_invincible(idlePed,1);}}finally{e.pn_bridge_control(1);}}
  if((previewCam||introCam||customCam72||reconCam72||reconActive72)&&e.pn_context()){
   e.pn_bridge_control(2);e.pn_cam_render(0,0,0,1,0,0);
   if(previewCam)e.pn_cam_destroy(previewCam,1);if(introCam)e.pn_cam_destroy(introCam,1);
   if(customCam72)e.pn_cam_destroy(customCam72,1);if(reconCam72)e.pn_cam_destroy(reconCam72,1);customCam72=reconCam72=0;reconActive72=false;reconReturn72=0;const restore72=e.pn_player_ped();if(restore72){e.pn_collision(restore72,1,1);self.__restoreVisibility72?.(restore72);}previewCam=introCam=0;previousPreview=false;e.pn_destroy_cams(1);e.pn_clear_focus();e.pn_follow_mode(1);e.pn_follow_heading(0);e.pn_hud_show(1);e.pn_radar(a[108]?0:1);const idlePed=e.pn_player_ped();if(idlePed){e.pn_freeze(idlePed,a[7610]?1:0);e.pn_invincible(idlePed,a[7610]?1:0);}e.pn_bridge_control(1);
  }return;
 }if(!e.pn_context())return;
 // These native flags expire each rendered frame; entity sampling stays at 30 Hz.
 mark51(1);e.pn_admin_permission(a[101]?1:0);e.pn_bridge_control(2);
 try{
  e.pn_control_disable(0,45,1);e.pn_control_disable(0,243,1);e.pn_control_disable(0,27,1);/* 162: INPUT_PHONE off: the native cellphone no longer pops into the hand *//* 156: INPUT_ENTER_CHEAT_CODE (key under Esc) off every frame: CCheat::DoCheats opens the cheat box */if(a[6600]===4)for(const id of [21,22,24,25,37,140,141,142,257])e.pn_control_disable(0,id,1);for(const id of [14,15,16,17,37])e.pn_control_disable(0,id,1);for(const id of [23,75,36])e.pn_control_disable(0,id,1);self.__pavDrawMarkers?.();e.pn_ammo_show(0);for(const id of [1,2,3,4,6,7,9,13])e.pn_hide_hud(id);
  e.pn_map_reset();e.pn_map_visible(!a[62]&&!a[108]);e.pn_death_fade(0);e.pn_control_disable(0,27,1);e.pn_hud_show(a[62]?0:1);e.pn_radar(a[62]||a[108]?0:1);if(!a[62])self.__hud136?.();self.__pop144?.();
  if(!a[62]){e.pn_radar_exterior();e.pn_custom_map(0);e.pn_map_prologue(0);e.pn_map_island(0);if(!introCam&&!a[6500]&&!a[12800]&&!a[13300]){const cameraPed=e.pn_player_ped(),cameraNow51=performance.now();if(cameraPed&&(cameraPed51!==cameraPed||cameraNow51-cameraAt51>=1000)){e.pn_cam_render(0,0,0,1,0,0);cameraPed51=cameraPed;cameraAt51=cameraNow51;}/* SET_GAMEPLAY_CAM_FOLLOW_PED_THIS_UPDATE expires each engine frame. */if(cameraPed&&!e.pn_vehicle(cameraPed,0))e.pn_follow_ped(cameraPed);}else cameraPed51=0;}
  if(a[13300]||a[12800]||a[7612]||a[62]||a[64]||a[6500]||a[6380]||(a[6600]&&a[6600]!==4)||a[7610]||a[71]||a[72]||a[7701]===1||a[7701]===2||a[7701]===3||a[7712])e.pn_controls_disable(0);
  if(a[62]||a[7610]||a[71]||a[72]||a[7701]===1||a[7701]===2||a[7701]===3||a[7712]){const heldPed=e.pn_player_ped();if(heldPed){e.pn_freeze(heldPed,1);e.pn_invincible(heldPed,1);}}
  {const sp154=e.pn_player_ped(),on154=!!(sp154&&e.pn_shooting(sp154)),t154=performance.now();if(on154&&(!self.__shotOn154||t154-(self.__shotRep154||0)>=120)){self.__shotN154=((self.__shotN154|0)+1)|0;self.__shotRep154=t154;}self.__shotOn154=on154;}
  self.__veh49?.();self.__pavFiniteAmmo?.();try{self.__tagFrame187?.();}catch{self.__tagFrame187=null;}if(a[7830]||a[7831]){for(const id of [21,22,23,24,25,37,44,45,75,140,141,142,257,263,264])e.pn_control_disable(0,id,1);if(a[7831])e.pn_controls_disable(0);}
 }catch(error){failBridge(a,error);return;}finally{e.pn_bridge_control(1);}
 if(mapResetTick){e.pn_bridge_control(2);e.pn_big_map(0,0);e.pn_bridge_control(1);mapResetTick=false;}const now=performance.now();if(now-lastTick<33){mark51(0);return;}const frameDelta44=Math.min(.1,Math.max(.001,Number.isFinite(lastTick)?(now-lastTick)/1000:1/30));lastTick=now;Atomics.add(a,8,1);busy=true;e.pn_bridge_control(2);
 try{
 let ped=e.pn_player_ped();a[13880]=ped;a[13882]=modelOf(a[2944]);if(!ped||!e.pn_exists(ped)){a[13881]=0;return;}a[13881]=e.pn_model(ped)|0;if(now-deathSettingsAt>1000){e.pn_ignore_restart(1);deathSettingsAt=now;if(!a[101]&&!a[116])e.pn_destroy_phone();}
 const ptr=BigInt(base+64000),s=new Float32Array(memory.buffer,base+64000,64);
 const vector=(x,y,z)=>{s[0]=x;s[2]=y;s[4]=z;};
 const coords=h=>{e.pn_coords(ptr,h,1);return [s[0],s[2],s[4]];};
 // Read before changing velocity/freeze. Wrapped Euler angles are equivalent.
 // Native entity rotation order 2 is ZXY. Interpolate orientation, not the
// individual Euler coordinates, which have multiple equivalent forms.
const orientation64=(()=>{
 const rad=Math.PI/180,clamp=x=>Math.max(-1,Math.min(1,x));
 const quaternion=angles=>{
  const [x,y,z]=angles.map(v=>v*rad/2),a=Math.cos(x),b=Math.cos(y),c=Math.cos(z),d=Math.sin(x),e=Math.sin(y),f=Math.sin(z);
  return[d*b*c-a*e*f,a*e*c+d*b*f,a*b*f+d*e*c,a*b*c-d*e*f];
 };
 const euler=q=>{
  const [x,y,z,w]=q,m32=2*(y*z+w*x);let a=Math.asin(clamp(m32)),b,c;
  if(Math.abs(m32)<.9999999){b=Math.atan2(2*(w*y-x*z),1-2*(x*x+y*y));c=Math.atan2(2*(w*z-x*y),1-2*(x*x+z*z));}
  else{b=0;c=Math.atan2(2*(x*y+w*z),1-2*(y*y+z*z));}
  return[a/rad,b/rad,c/rad];
 };
 const tilt=angles=>{
  if(!angles.every(Number.isFinite))return NaN;
  // World up projected onto the rotated local up; yaw has no effect.
  return Math.acos(clamp(Math.cos(angles[0]*rad)*Math.cos(angles[1]*rad)))/rad;
 };
 const blend=(from,to,t)=>{
  const a=quaternion(from),b=quaternion(to);let dot=a.reduce((s,v,i)=>s+v*b[i],0);
  if(dot<0){dot=-dot;for(let i=0;i<4;i++)b[i]=-b[i];}
  let q;
  if(dot>.9995)q=a.map((v,i)=>v+(b[i]-v)*t);
  else{const theta=Math.acos(clamp(dot)),den=Math.sin(theta),u=Math.sin((1-t)*theta)/den,v=Math.sin(t*theta)/den;q=a.map((x,i)=>x*u+b[i]*v);}
  const length=Math.hypot(...q);return euler(q.map(x=>x/length));
 };
 return{tilt,blend};
})();

 // pn_rotation returns packed Vector3; other vector commands use scrVector.
 const entryPose62=h=>{e.pn_rotation(ptr,h,2);const pitch=s[0],roll=s[1],yaw=s[2],speed=e.pn_speed(h);
  const tilt=orientation64.tilt([pitch,roll,yaw]);
  return {tilt,speed,safe:[pitch,roll,speed].every(Number.isFinite)&&tilt<45&&speed<3};};
 const cstring=(value,offset=64192,capacity=32)=>{const bytes=new Uint8Array(memory.buffer,base+offset,capacity);bytes.fill(0);for(let i=0;i<Math.min(capacity-2,value.length);i++)bytes[i]=value.charCodeAt(i)&127;return BigInt(base+offset);};

 function modelHash23(name){let h=0;for(const c of name){h=(h+c.charCodeAt(0))|0;h=(h+(h<<10))|0;h^=h>>>6;}h=(h+(h<<3))|0;h^=h>>>11;return (h+(h<<15))>>>0;}
 const nativeSlots={"HAS_ENTITY_CLEAR_LOS_TO_ENTITY":45974,"SET_VEHICLE_RADIO_ENABLED":44516,"IS_PED_RAGDOLL":55510,"IS_PED_GETTING_UP":58720,"SET_PED_SHOOTS_AT_COORD":55759,"SET_PED_CAN_SWITCH_WEAPON":55826,"REMOVE_ALL_PED_WEAPONS":60686,"HAS_PED_GOT_WEAPON":60664,"IS_PED_PERFORMING_MELEE_ACTION":55857,"SET_PED_INTO_VEHICLE":54815,"HIDE_HELP_TEXT_THIS_FRAME":48156,"THEFEED_HIDE_THIS_FRAME":47452,"HIDE_HUD_COMPONENT_THIS_FRAME":48296,"CLEAR_PRINTS":47632,"STAT_SET_INT":57349,"STAT_GET_INT":57369,"GET_PED_BONE_INDEX":55933,"GET_PED_NEARBY_VEHICLES":56017,"GET_WATER_HEIGHT":60606,"IS_THIS_MODEL_A_BOAT":59462,"SET_BOAT_ANCHOR":59145,"CREATE_OBJECT_NO_OFFSET":54096,"GET_INTERIOR_FROM_ENTITY":48683,"UNPIN_INTERIOR":48710,"SET_VEHICLE_DEFORMATION_FIXED":59621,"SET_VEHICLE_DIRT_LEVEL":59504,"GET_PED_TYPE":55189,"GET_PLAYER_WANTED_LEVEL":56318,"SET_POLICE_IGNORE_PLAYER":56324,"SET_ENTITY_VISIBLE":46243,"DRAW_LIGHT_WITH_RANGE":46523,"RESTORE_PLAYER_STAMINA":56413,"SET_HYDRAULIC_SUSPENSION_RAISE_FACTOR":60324,"GET_HYDRAULIC_SUSPENSION_RAISE_FACTOR":60326,"SET_CAN_USE_HYDRAULICS":60328,"SET_HYDRAULIC_VEHICLE_STATE":60330,"SET_HYDRAULIC_WHEEL_STATE":60332,"DISABLE_INTERIOR":48743,"IS_INTERIOR_DISABLED":48745,"CAP_INTERIOR":48747,"IS_INTERIOR_CAPPED":48749,"IS_GAMEPLAY_CAM_RENDERING":45164,"GET_ENTITY_POPULATION_TYPE":46062,"IS_ENTITY_A_MISSION_ENTITY":46068,"IS_PED_A_PLAYER":54772,"GET_PED_NEARBY_PEDS":56019,"SET_FOCUS_POS_AND_VEL":58103,"SET_VEHICLE_CUSTOM_PRIMARY_COLOUR":59104,"GET_VEHICLE_CUSTOM_PRIMARY_COLOUR":59106,"CLEAR_VEHICLE_CUSTOM_PRIMARY_COLOUR":59108,"GET_IS_VEHICLE_PRIMARY_COLOUR_CUSTOM":59110,"SET_VEHICLE_CUSTOM_SECONDARY_COLOUR":59112,"GET_VEHICLE_CUSTOM_SECONDARY_COLOUR":59114,"CLEAR_VEHICLE_CUSTOM_SECONDARY_COLOUR":59116,"GET_IS_VEHICLE_SECONDARY_COLOUR_CUSTOM":59118,"GET_VEHICLE_COLOURS":59179,"CREATE_MOBILE_PHONE":56888,"SET_ENABLE_HANDCUFFS":55260,"IS_ENTITY_PLAYING_ANIM":46106,"START_EXPENSIVE_SYNCHRONOUS_SHAPE_TEST_LOS_PROBE":57090,"GET_SHAPE_TEST_RESULT":57104,"SET_TIMECYCLE_MODIFIER":47109,"SET_TIMECYCLE_MODIFIER_STRENGTH":47111,"GET_TIMECYCLE_MODIFIER_INDEX":47119,"CLEAR_TIMECYCLE_MODIFIER":47117,"SET_PED_DENSITY_MULTIPLIER_THIS_FRAME":54849,"SET_SCENARIO_PED_DENSITY_MULTIPLIER_THIS_FRAME":54851,"SET_VEHICLE_DENSITY_MULTIPLIER_THIS_FRAME":59033,"pn_v20_arrested": 56437, "pn_v20_arrest_reset": 56440, "pn_v20_wanted_clear": 56308, "pn_v20_fade_in": 45116, "pn_v20_clock": 45410, "pn_v20_pause_clock": 45412, "pn_v20_weather": 48880, "pn_v20_marker": 46537, "pn_v20_force_gps": 47725, "pn_v20_indicators": 59830, "pn_v20_tint": 60794, "pn_v19_waypoint": 48059, "pn_v19_waypoint_off": 48050, "pn_v19_gps_length": 54674, "pn_v19_gps_point": 54678, "pn_v19_fix": 59619, "pn_v19_engine_health": 59682, "pn_v19_anim_request": 58046, "pn_v19_anim_loaded": 58048, "pn_v19_anim": 58375, "pn_v19_clip": 60712, "pn_v19_ipl": 58061, "SET_PED_INFINITE_AMMO": 60676, "SET_PED_INFINITE_AMMO_CLIP": 60678, "SET_VEHICLE_MOD_KIT": 59915, "SET_VEHICLE_MOD": 59944, "GET_NUM_VEHICLE_MODS": 59950, "TOGGLE_VEHICLE_MOD": 59954, "SET_VEHICLE_COLOURS": 59098, "SET_VEHICLE_WHEEL_TYPE": 59923, "SET_VEHICLE_WINDOW_TINT": 59981, "SET_VEHICLE_LOD_MULTIPLIER": 60062, "SET_ENTITY_LOD_DIST": 46256, "GET_VEHICLE_LIGHTS_STATE": 59188, "SET_VEHICLE_LIGHTS": 59286, "SET_VEHICLE_FULLBEAM": 59100, "START_VEHICLE_HORN": 59706, "SET_STATE_OF_CLOSEST_DOOR_OF_TYPE": 54127, "SET_PED_CONFIG_FLAG": 55744, "GET_CLOSEST_OBJECT_OF_TYPE": 54112, "HAS_OBJECT_BEEN_BROKEN": 54114, "CREATE_MODEL_HIDE": 46285, "REMOVE_MODEL_HIDE": 46289, "GET_ENTITY_MODEL": 46020, "SET_ENTITY_VELOCITY": 46249, "SET_ENTITY_ANGULAR_VELOCITY": 46251, "DOOR_SYSTEM_FIND_EXISTING_DOOR": 54178, "DOOR_SYSTEM_SET_DOOR_STATE": 54139, "DOOR_SYSTEM_SET_OPEN_RATIO": 54149, "GET_INTERIOR_AT_COORDS": 48703, "PIN_INTERIOR_IN_MEMORY": 48708, "IS_INTERIOR_READY": 48712, "IS_VALID_INTERIOR": 48673, "REFRESH_INTERIOR": 48736, "NEW_LOAD_SCENE_START_SPHERE": 58132, "NEW_LOAD_SCENE_STOP": 58134, "TERMINATE_THREAD": 57027, "GET_NAME_OF_SCRIPT_WITH_THIS_ID": 57031, "SCRIPT_THREAD_ITERATOR_RESET": 57033, "SCRIPT_THREAD_ITERATOR_GET_NEXT_THREAD_ID": 57035, "GET_ID_OF_THIS_THREAD": 57037, "SHUTDOWN_LOADING_SCREEN": 57059, "GET_IS_LOADING_SCREEN_ACTIVE": 47342, "BUSYSPINNER_OFF": 47426, "IS_PLAYER_SWITCH_IN_PROGRESS": 58146, "STOP_PLAYER_SWITCH": 58144, "GET_PED_DRAWABLE_VARIATION": 55329, "GET_PED_TEXTURE_VARIATION": 55333, "GET_PED_PROP_INDEX": 55451, "REQUEST_ANIM_SET": 58052, "HAS_ANIM_SET_LOADED": 58054, "SET_PED_MOVEMENT_CLIPSET": 55277, "RESET_PED_MOVEMENT_CLIPSET": 55279, "SET_PED_STRAFE_CLIPSET": 55281, "RESET_PED_STRAFE_CLIPSET": 55283, "TASK_VEHICLE_DRIVE_WANDER": 58300, "TASK_WANDER_STANDARD": 58332, "SET_ENTITY_AS_NO_LONGER_NEEDED": 46183, "TASK_GO_STRAIGHT_TO_COORD": 58305, "SET_RANDOM_VEHICLE_DENSITY_MULTIPLIER_THIS_FRAME": 59035, "SET_PED_COMPONENT_VARIATION": 55353, "SET_VEHICLE_ENGINE_ON": 59512, "SET_BLOCKING_OF_NON_TEMPORARY_EVENTS": 55474, "SET_PED_KEEP_TASK": 55229, "SET_PED_POPULATION_BUDGET": 58099, "GET_ENTITY_HEALTH": 46008, "GET_PLAYER_RADIO_STATION_INDEX": 44441, "SET_RADIO_TO_STATION_INDEX": 44473, "CLEAR_PED_TASKS_IMMEDIATELY": 58566, "SET_VEHICLE_POPULATION_BUDGET": 58097, "SET_PLAYER_WANTED_LEVEL": 56292, "SET_PLAYER_WANTED_LEVEL_NOW": 56296, "TASK_START_SCENARIO_IN_PLACE": 58653, "SET_VEHICLE_DOOR_BROKEN": 59530, "SET_VEHICLE_TYRE_BURST": 59248, "GIVE_WEAPON_COMPONENT_TO_PED": 60753, "REMOVE_WEAPON_COMPONENT_FROM_PED": 60755, "HAS_PED_GOT_WEAPON_COMPONENT": 60757};
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
 self.__restoreVisibility72=h=>nativeCall('SET_ENTITY_VISIBLE',[h,1,0]); // 138: help text stays visible (NPC interaction prompts: pick-ups, shop and service hints); only the story feed, cash HUD and subtitles are hidden.
 self.__hud136=()=>{nativeCall('THEFEED_HIDE_THIS_FRAME',[]);for(const c131 of [3,4,13])nativeCall('HIDE_HUD_COMPONENT_THIS_FRAME',[c131]);if(performance.now()-(self.__prints131||0)>2000){self.__prints131=performance.now();nativeCall('CLEAR_PRINTS',[]);}}; /* 154: shots/swings/weapons/vehicle playout, see tests/sync154. */ /* 149: remote-driven cars: snapshot interpolation every rendered frame at now-200 ms. Rows carry no sample time, so samples are re-timed from distance/speed and loosely locked to arrival. */ self.__phys199=(cur,curRot,out,pos,pos2,rot,rot2)=>{
 /* 199: a car driven by another player was moved by writing its position and rotation every frame, so the physics never
  ran: wheels did not turn, no suspension, it slid like a log. Now, while it is close to where it should be (< 3 m,
  < 25 deg), it is driven: velocity = the smoothed path's own velocity + 6/s of the remaining gap, yaw rate likewise;
  the physics turns the wheels and works the suspension. Farther off, the old exact write is used (returns null). */
 const d=Math.hypot(out[0]-cur[0],out[1]-cur[1],out[2]-cur[2]),wrap=x=>((x%360)+540)%360-180;
 const eY=wrap(rot[2]-curRot[2]),eP=wrap(rot[0]-curRot[0]),eR=wrap(rot[1]-curRot[1]);
 if(!(d<3)||!(Math.abs(eY)<25)||!(Math.abs(eP)<25)||!(Math.abs(eR)<25))return null;
 const vel=pos2.map((p,k)=>(p-pos[k])*20+(out[k]-cur[k])*6);
 if(!vel.every(Number.isFinite)||Math.hypot(...vel)>120)return null;
 const yaw=(wrap(rot2[2]-rot[2])*20+eY*6)*Math.PI/180;if(!Number.isFinite(yaw))return null;
 return{vel,ang:[0,0,yaw]};};
const pose49=(H,rt)=>{let i=H.length-1;while(i>0&&H[i].t>rt)i--;const A=H[i],B=H[i+1];if(!B||rt<=A.t){const x=B?0:Math.max(0,Math.min(300,rt-A.t))/1000;return [A.pos.map((p,k)=>p+A.vel[k]*x),A.rot];}const span=(B.t-A.t)/1000,u=Math.min(1,(rt-A.t)/(B.t-A.t)),u2=u*u,u3=u2*u;return [A.pos.map((p,k)=>(2*u3-3*u2+1)*p+(u3-2*u2+u)*span*A.vel[k]+(3*u2-2*u3)*B.pos[k]+(u3-u2)*span*B.vel[k]),orientation64.blend(A.rot,B.rot,u)];}; const push49=(local,v,now)=>{const key=[...v.pos,...v.rot,...v.velocity].join(':'),tr=local.track49;if(tr&&tr.key===key)return;const seqAt=self.__carSeqAt49,at=Number.isFinite(seqAt)&&seqAt<=now&&now-seqAt<50?seqAt:now,speed=Math.hypot(...v.velocity),last=tr&&tr.h[tr.h.length-1],sample={a:at,t:at,pos:v.pos,rot:v.rot,vel:v.velocity};const fresh49=()=>{local.track49={key,h:[sample],err:[0,0,0],fresh:false};};if(!last){fresh49();return;}const d=Math.hypot(...v.pos.map((p,i)=>p-last.pos[i])),avg=(speed+Math.hypot(...last.vel))/2,gap=Math.max(1,at-last.a);if(d>8+Math.max(speed,avg)*Math.max(.5,Math.min(1.5,gap/1000))*1.5){fresh49();return;}const step=avg>2&&d>.05?Math.max(20,Math.min(500,d/avg*1000)):Math.min(gap,500);if(gap>1500)tr.h=[{...last,t:at-step}];else{const t=last.t+step;sample.t=Math.max(last.t+10,Math.min(at+100,Math.max(at-150,t+(at-t)*.15)));}tr.gaps=(tr.gaps||[]).concat(gap).slice(-8);tr.key=key;tr.h.push(sample);if(tr.h.length>8)tr.h.shift();tr.fresh=true;}; self.__npc201Off=self.__npc201Off||/[?&]npc=0\b/.test(self.location?.search||'');self.__veh199Off=self.__veh199Off||/[?&]carphys=0\b/.test(self.location?.search||'');self.__veh49=()=>{try{const t0=performance.now(),sq=Atomics.load(new Int32Array(memory.buffer,base,16384),14);if(sq!==self.__carSeq49){self.__carSeq49=sq;self.__carSeqAt49=t0;}const me=e.pn_player_ped();for(const local of vehicles.values()){const tr=local.track49;if(!tr)continue;const h=local.handle;if(!h||!e.pn_exists(h)||me&&e.pn_vehicle_seat(h,-1,0)===me){local.track49=null;continue;}const dt154=Math.min(.1,Math.max(0,(t0-(tr.at??t0))/1000)),want154=tr.gaps&&tr.gaps.length>=3?Math.max(200,Math.min(420,Math.max(...tr.gaps)+40)):200;tr.delay=tr.delay===undefined?want154:tr.delay+Math.max(-50*dt154,Math.min(50*dt154,want154-tr.delay));const rt=t0-tr.delay;const [pos,rot]=pose49(tr.h,rt);if(tr.fresh&&tr.h.length>1){const jump=pose49(tr.h.slice(0,-1),rt)[0].map((p,k)=>p-pos[k]);tr.err=Math.hypot(...jump)>4+Math.hypot(...tr.h[tr.h.length-1].vel)*.75?[0,0,0]:tr.err.map((x,k)=>x+jump[k]);}tr.fresh=false;const dt=Math.min(.1,Math.max(0,(t0-(tr.at??t0))/1000)),keep=Math.exp(-dt/.12);tr.at=t0;tr.err=tr.err.map(x=>x*keep);const out=pos.map((p,k)=>p+tr.err[k]);if(!out.every(Number.isFinite)||!rot.every(Number.isFinite)){local.track49=null;continue;}let r154=rot;if(Math.abs(rot[0])<60&&Math.abs(rot[1])<60){const k154=1-Math.exp(-dt/.25);tr.pr=tr.pr?[tr.pr[0]+(rot[0]-tr.pr[0])*k154,tr.pr[1]+(rot[1]-tr.pr[1])*k154]:[rot[0],rot[1]];r154=[tr.pr[0],tr.pr[1],rot[2]];}else tr.pr=null;let ph199=null;if(!self.__veh199Off&&!(me&&e.pn_vehicle(me,0)===h)){try{const c199=coords(h);e.pn_rotation(ptr,h,2);const cr199=[s[0],s[1],s[2]];const [p2199,r2199]=pose49(tr.h,rt+50);ph199=self.__phys199(c199,cr199,out,pos,p2199,r154,r2199);if(ph199){vector(...ph199.vel);e.pn_set_velocity(h,ptr);nativeCall('SET_ENTITY_ANGULAR_VELOCITY',[h,...ph199.ang.map(bits)]);}}catch(e199){self.__veh199Off=true;ph199=null;console.error('PAV vehicle physics off',e199?.stack||e199);}}if(!ph199){vector(...out);e.pn_set_coords(h,ptr,1,1,self.__veh154NoWarp&&me&&e.pn_vehicle(me,0)===h?0:1);vector(...r154);e.pn_set_rotation(h,ptr,2,1);}}}catch(error){self.__veh49Off=true;for(const local of vehicles.values())local.track49=null;console.error('PAV vehicle smoothing off',error?.stack||error);}};
 // 144: GTA spawns ambient peds/traffic locally per client, so players side by side see different crowds. Near a real player (flag 256 = ambient188 replica, ignored) thin local spawning to 35% so the shared ambient188 actors dominate. THIS_FRAME multipliers expire each engine frame: this 30 Hz pass picks near/far (200 m in, 260 m out), the per-frame block applies it; a native error switches the hook off instead of stopping the bridge.
 {let near144=false;const n144=Math.min(32,Math.max(0,a[5]|0));for(let i=0;i<n144&&!near144;i++){const o=128+i*64;if(!a[o]||(a[o+11]&256))continue;const d144=Math.hypot(f[o+1]-f[16],f[o+2]-f[17]);near144=Number.isFinite(d144)&&d144<(self.__popNear144?260:200);}self.__popNear144=near144;}
 self.__pop144=self.__pop144Off?null:()=>{if(!self.__popNear144||self.__npc201Mode)return;try{const m144=bits(.35);nativeCall('SET_PED_DENSITY_MULTIPLIER_THIS_FRAME',[m144]);nativeCall('SET_SCENARIO_PED_DENSITY_MULTIPLIER_THIS_FRAME',[m144,m144]);nativeCall('SET_VEHICLE_DENSITY_MULTIPLIER_THIS_FRAME',[m144]);}catch(error144){self.__pop144Off=true;self.__pop144=null;console.warn('PAV pop144 off',error144);}};
 // 101: DELETE_* only succeeds for the owning script. This tick borrows whichever
 // script thread just ran, so take ownership first and retry until it is gone.
 self.__retiring101??=new Map();
 const drop101=(h,vehicle=false)=>{if(!h||!e.pn_exists(h)){self.__retiring101.delete(h);return true;}e.pn_mission_entity(h,1,1);a[16008]=h;(vehicle?e.pn_delete_vehicle:e.pn_delete)(BigInt(base+64032));if(!e.pn_exists(h)){self.__retiring101.delete(h);return true;}if(self.__retiring101.size<64)self.__retiring101.set(h,vehicle);return false;};
 // 101: the vanilla Story bootstrap loops CREATE_PED + CHANGE_PLAYER_PED to restore
 // a protagonist. With that change guarded it leaves a clone on every pass and never
 // reaches its loading-screen shutdown. Online owns the player: retire the Story
 // controllers, remove protagonist peds that are not players, close the loading screen.
 self.__story101??={at:-Infinity,retired:new Map(),killed:0,swept:0,closed:0,census:''};const story101=self.__story101;
 if(now-story101.at>=500){story101.at=now;
  // 104: field report showed `main` relaunching every retired controller each second
  // (~190 relaunches) and a Michael mission ped recreated on the player each second.
  // `main` and the other Story-only controllers go too; engine/HUD/phone/stat scripts stay.
  const storyNames101=new Set(['atm_trigger','main','initial','selector','player_controller','player_controller_b','player_timetable_scene','respawn_controller','flow_controller','flow_help','friends_controller','friends_debug','comms_controller','randomchar_controller','vehicle_gen_controller','mission_repeat_controller','replay_controller','candidate_controller','blip_controller','bootycallhandler','event_controller','photographymonkey','taxilauncher','emergencycalllauncher','completionpercentage_controller','social_controller','email_controller','stock_controller','shop_controller','animal_controller','building_controller','flyunderbridges','controller_ambientarea']);
  const storyScript101=name=>storyNames101.has(name)||['player_scene_','family_','re_','mission_triggerer','switch_'].some(prefix=>name.startsWith(prefix));
  const scriptName101=pointer=>{pointer>>>=0;if(!pointer||pointer+64>memory.buffer.byteLength)return '';const bytes=new Uint8Array(memory.buffer,pointer,64);let text='';for(let i=0;i<64&&bytes[i];i++)text+=String.fromCharCode(bytes[i]);return text.toLowerCase();};
  const current101=nativeCall('GET_ID_OF_THIS_THREAD'),seen101=[],live102=new Map(),threads104=[];nativeCall('SCRIPT_THREAD_ITERATOR_RESET');
  for(let n=0;n<160;n++){const id=nativeCall('SCRIPT_THREAD_ITERATOR_GET_NEXT_THREAD_ID');if(!id)break;const name=scriptName101(nativeCall('GET_NAME_OF_SCRIPT_WITH_THIS_ID',[id]));seen101.push(name||'?');threads104.push([id,name]);}
  // The bridge itself runs on script threads: never retire below four survivors.
  const keep104=threads104.filter(([id,name])=>id===current101||!name||!storyScript101(name)).length;
  for(const [id,name] of threads104){if(keep104>=4&&id!==current101&&name&&storyScript101(name)){nativeCall('TERMINATE_THREAD',[id]);story101.killed++;story101.retired.set(name,(story101.retired.get(name)||0)+1);}else live102.set(id,name);}
  // 102: WASM102 turns a script VM fault into ABORTED for that thread only. Threads that
  // vanish without our TERMINATE are recorded so the next fix targets the real script.
  story101.faulted??=new Map();for(const [id,name] of story101.live??[])if(!live102.has(id)&&name)story101.faulted.set(name,(story101.faulted.get(name)||0)+1);story101.live=live102;a[13897]=[...story101.faulted.values()].reduce((s,v)=>s+v,0);
  const protagonists101=new Set([225514697,2602752943,2608926626].map(v=>v|0)),managed101=new Set([ped,showroomHandle,self.__c210?.medicPed||0,...[...(self.__npc201?.clones?.values()||[])].flatMap(c=>[c.h,c.driver]),...[...entities.values(),...serviceNpcs.values()].map(v=>v.handle)]);
  const pool101=new Int32Array(memory.buffer,base+56640,66);pool101.fill(0);pool101[0]=32;const count101=Math.max(0,Math.min(32,nativeCall('GET_PED_NEARBY_PEDS',[ped,BigInt(base+56640),-1])));
  // 103: online scripts are only Story scripts, so any mission ped we do not manage is theirs.
  story101.nearby=[];story101.foreign??=0;
  for(const h of Array.from({length:count101},(_,i)=>pool101[2+i*2])){if(!h||!e.pn_exists(h))continue;const model103=e.pn_model(h)|0,mission103=!!nativeCall('IS_ENTITY_A_MISSION_ENTITY',[h]),ours103=managed101.has(h),player103=!!nativeCall('IS_PED_A_PLAYER',[h]);
   if(story101.nearby.length<16){const p103=coords(h);story101.nearby.push([model103>>>0,mission103?1:0,ours103?1:0,player103?1:0,Math.round(Math.hypot(p103[0]-coords(ped)[0],p103[1]-coords(ped)[1]))]);}
   if(ours103||player103||!(protagonists101.has(model103)||mission103))continue;if(!protagonists101.has(model103)&&e.pn_vehicle(h,0))continue;if(drop101(h)){if(protagonists101.has(model103))story101.swept++;else story101.foreign++;}}
  a[13899]=story101.foreign;
  // 103: the local avatar keeps exactly the server look; foreign props/clothes are undone.
  const own103=blends.get(ped);if(own103?.done&&!own103.pendingComponents?.length&&(e.pn_model(ped)|0)===modelOf(a[2944])){
   for(const prop of [0,1,2,6,7])if((nativeCall('GET_PED_PROP_INDEX',[ped,prop])|0)!==-1){e.pn_clear_prop(ped,prop);story101.props=(story101.props||0)+1;}
   const wanted103=new Map([[2,5],[11,7],[4,8],[6,9],[3,10],[8,11]]);
   for(const [id,key] of [...own103.appliedComponents]){const now103=(nativeCall('GET_PED_DRAWABLE_VARIATION',[ped,id])|0)+':'+(nativeCall('GET_PED_TEXTURE_VARIATION',[ped,id])|0);if(now103!==key){own103.appliedComponents.delete(id);own103.pendingComponents.push({id,wanted:a[2944+wanted103.get(id)],texture:a[2959]});story101.outfit=(story101.outfit||0)+1;}}
  }
  for(const [h,vehicle] of [...self.__retiring101])drop101(h,vehicle);
  if(nativeCall('IS_PLAYER_SWITCH_IN_PROGRESS'))nativeCall('STOP_PLAYER_SWITCH');
  if(a[37]&&nativeCall('GET_IS_LOADING_SCREEN_ACTIVE')){nativeCall('SHUTDOWN_LOADING_SCREEN');nativeCall('BUSYSPINNER_OFF');e.pn_fade_in(250);story101.closed++;}
  a[13890]=story101.killed;a[13891]=seen101.length;a[13892]=story101.swept;a[13893]=nativeCall('GET_IS_LOADING_SCREEN_ACTIVE')?1:0;a[13894]=story101.closed;a[13895]=self.__retiring101.size;Atomics.add(a,13896,1);
  const census101=seen101.slice().sort().join(',');if(census101!==story101.census){story101.census=census101;globalThis.console?.info?.('[PAV107] scripts:',census101,'| retired:',JSON.stringify(Object.fromEntries(story101.retired)),'| ended by itself:',JSON.stringify(Object.fromEntries(story101.faulted)),'| clones removed:',story101.swept);}
  // 103: bounded field report to the authenticated engine log; numbers and script names only.
  const report103=JSON.stringify({v:107,sub:self.__sub213||{},phases:Array.from(self.__phase107||[]).map(Math.round),slow:a[14107],wanted:a[14504],cops:a[14505],cars:vehicles.size,peers:entities.size,doors:a[13912],scripts:census101,retired:Object.fromEntries(story101.retired),ended:Object.fromEntries(story101.faulted),clones:story101.swept,foreign:story101.foreign,props:story101.props||0,outfit:story101.outfit||0,reverted:story101.reverted||0,model:[a[13881]>>>0,modelOf(a[2944])>>>0],swaps:a[13883],spawns:a[13885],preview:a[62],loading:a[13893],nearby:story101.nearby}).slice(0,6000);
  if(typeof fetch==='function'&&report103!==story101.sent&&now-(story101.sentAt??-Infinity)>=10000){story101.sent=report103;story101.sentAt=now;fetch('/log',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'text/plain'},body:'[PAV107] '+report103}).catch(()=>{});self.__phase107?.fill(0);self.__sub213={};}
 }
 // 103: undo an unexplained teleport of the local ped (Story scripts or saved-game restore).
 {const pos103=coords(ped),car103=!!e.pn_vehicle(ped,0),last103=self.__pose103;
  const exempt103=!spawned||!last103||last103.ped!==ped||last103.spawn!==spawnVersion||last103.car||car103||!!a[64]||!!interiorGate31||!!a[7701]||!!a[13300]||!!a[118]||!!self.__pavCarriedBy||now-last103.at>500;
  if(!exempt103&&Math.hypot(pos103[0]-last103.pos[0],pos103[1]-last103.pos[1])>60){vector(...last103.pos);e.pn_set_coords(ped,ptr,1,1,1);story101.reverted=(story101.reverted||0)+1;a[13898]=story101.reverted;last103.at=now;}
  else self.__pose103={ped,pos:pos103,spawn:spawnVersion,at:now,car:car103};}
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
   rotation:h=>{e.pn_rotation(ptr,h,2);return[s[0],s[1],s[2]];},position:coords,exists:h=>!!e.pn_exists(h),model:h=>e.pn_model(h),heading:h=>e.pn_heading(h),
   velocity:h=>{e.pn_velocity(ptr,h);return[s[0],s[2],s[4]];},
   population:h=>nativeCall('GET_ENTITY_POPULATION_TYPE',[h]),mission:h=>!!nativeCall('IS_ENTITY_A_MISSION_ENTITY',[h]),
   player:h=>!!nativeCall('IS_PED_A_PLAYER',[h]),vehicle:h=>e.pn_vehicle(h,0),paint:readPaint43,
   hasPlayer:h=>{for(let seat=-1;seat<8;seat++){const occupant=e.pn_vehicle_seat(h,seat,0);if(occupant&&nativeCall('IS_PED_A_PLAYER',[occupant]))return true;}return false;},
   excluded:()=>new Set([ped,...[...(self.__npc201?.clones?.values()||[])].flatMap(c=>[c.h,c.driver]),...[...vehicles.values(),...entities.values(),...serviceNpcs.values()].map(v=>v.handle)]),
   nearbyPeds:()=>{const pool=new Int32Array(memory.buffer,base+56640,66);pool.fill(0);pool[0]=32;const count=Math.max(0,Math.min(32,nativeCall('GET_PED_NEARBY_PEDS',[ped,BigInt(base+56640),-1])));return Array.from({length:count},(_,i)=>pool[2+i*2]);},
   nearbyCars:()=>{const pool=new Int32Array(memory.buffer,base+49152,1026);pool.fill(0);pool[0]=512;const count=Math.max(0,Math.min(512,e.pn_all_vehicles(BigInt(base+49152))));return Array.from({length:count},(_,i)=>pool[2+i*2]);}
  },now,true);
  if(observed)self.postMessage({pnPopulation200:{...observed,binding_epoch:a[14101]}});
 }

 self.__police84??=new self.PAVPolice84();
 self.__resetPolice84=()=>{nativeCall('SET_POLICE_IGNORE_PLAYER',[e.pn_player_id(),0]);self.__police84.applied=false;self.__police84.publish(new Int32Array(memory.buffer,base,16384),new Float32Array(memory.buffer,base,16384),0,[]);};
 let policeExcluded90;
 self.__police84.step({ped,
  ignore:on=>nativeCall('SET_POLICE_IGNORE_PLAYER',[e.pn_player_id(),on?1:0]),
  wanted:()=>nativeCall('GET_PLAYER_WANTED_LEVEL',[e.pn_player_id()]),
  clearWanted:()=>nativeCall('pn_v20_wanted_clear',[e.pn_player_id()]),
  position:coords,exists:h=>!!e.pn_exists(h),health:h=>e.pn_health(h),
  player:h=>!!nativeCall('IS_PED_A_PLAYER',[h]),type:h=>nativeCall('GET_PED_TYPE',[h]),vehicle:h=>e.pn_vehicle(h,0),
  excluded:h=>(policeExcluded90??=new Set([...entities.values(),...serviceNpcs.values()].map(v=>v.handle))).has(h),
  occupants:h=>[e.pn_vehicle_seat(h,-1,0),e.pn_vehicle_seat(h,0,0)],
  nearbyVehicles:()=>{const pool=new Int32Array(memory.buffer,base+56640,66);pool.fill(0);pool[0]=16;const count=Math.max(0,Math.min(16,nativeCall('GET_PED_NEARBY_VEHICLES',[ped,BigInt(base+56640)])));return Array.from({length:count},(_,i)=>pool[2+i*2]);},
  nearby:()=>{const pool=new Int32Array(memory.buffer,base+56640,66);pool.fill(0);pool[0]=32;
   const count=Math.max(0,Math.min(32,nativeCall('GET_PED_NEARBY_PEDS',[ped,BigInt(base+56640),-1])));
   return Array.from({length:count},(_,i)=>pool[2+i*2]);}
 },a,f,now,!a[62]&&!a[7610]&&!a[71]&&!a[72]&&!!a[7611]);
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
 // 103: melee weapons have no clip. The clip ceiling disabled INPUT_ATTACK for a knife, so the
 // ped fell back to an unarmed punch; ammo rules now apply to firearms only.
 self.__melee103??=new Set(['weapon_knife','weapon_dagger','weapon_switchblade','weapon_machete','weapon_hatchet','weapon_battleaxe','weapon_stone_hatchet','weapon_nightstick','weapon_hammer','weapon_bat','weapon_golfclub','weapon_crowbar','weapon_bottle','weapon_knuckle','weapon_flashlight','weapon_poolcue','weapon_wrench'].map(modelHash23));
 self.__pavFiniteAmmo=()=>{const ma=new Int32Array(memory.buffer,base,16384);if(ma[62]||ma[7610]||ma[71]||ma[72]||!ma[102])return;const h=e.pn_player_ped(),w=ma[103];if(!h)return;nativeCall('SET_PED_INFINITE_AMMO_CLIP',[h,0]);if(w&&(w>>>0)!==0xA2719263&&!self.__melee103.has(w>>>0)){nativeCall('SET_PED_INFINITE_AMMO',[h,0,w]);if(e.pn_ammo(h,w)>Math.max(0,ma[104]))e.pn_set_ammo(h,w,Math.max(0,ma[104]),0);if(ma[6608]===ma[102]){const sig=ma[102]+':'+w;let clip=self.__clip33;if(!clip||clip.sig!==sig)self.__clip33=clip={sig,ceiling:Math.max(0,Math.min(ma[7121],ma[7120],ma[104]))};ma[16360]=0;if(e.pn_clip(h,w,BigInt(base+65440))){const n=Math.max(0,ma[16360]);if(n>clip.ceiling)nativeCall('pn_v19_clip',[h,w,clip.ceiling]);else clip.ceiling=n;}if(!clip.ceiling)e.pn_control_disable(0,24,1);}}};
 self.__ring127=(x,y,z,r,g,b)=>{const pink139=r===255&&g===255;nativeCall('pn_v20_marker',[2,bits(x),bits(y),bits(z+.2),bits(0),bits(0),bits(0),bits(0),bits(180),bits(0),bits(.42),bits(.42),bits(.32),pink139?255:r,pink139?95:g,pink139?168:b,210,1,1,2,0,0n,0n,0]);nativeCall('pn_v20_marker',[25,bits(x),bits(y),bits(z-.97),bits(0),bits(0),bits(0),bits(0),bits(0),bits(0),bits(1.45),bits(1.45),bits(1),r,g,b,215,0,0,2,0,0n,0n,0]);nativeCall('pn_v20_marker',[23,bits(x),bits(y),bits(z-.975),bits(0),bits(0),bits(0),bits(0),bits(0),bits(0),bits(2.05),bits(2.05),bits(1),r,g,b,48,0,0,2,0,0n,0n,0]);};
 self.__proj127=(n,x,y,z,kind)=>{const ma=new Int32Array(memory.buffer,base,16384),mf=new Float32Array(memory.buffer,base,16384),o=13960+n*5,d=Math.hypot(x-mf[16],y-mf[17],z-mf[18]);if(d>45){ma[o]=0;return;}vector(x,y,z+.95);const visible=e.pn_project(ptr,BigInt(base+64024),BigInt(base+64028));ma[o]=visible?1:0;mf[o+1]=s[6];mf[o+2]=s[7];mf[o+3]=d;ma[o+4]=kind;};
 self.__pavDrawMarkers=()=>{const ma=new Int32Array(memory.buffer,base,16384),mf=new Float32Array(memory.buffer,base,16384);for(let n=0;n<6;n++)ma[13960+n*5]=0;Atomics.add(ma,13959,1);if(ma[62])return;if(ma[12840]&&mf.slice(12843,12846).every(Number.isFinite)){
 const x=mf[12843],y=mf[12844],z=mf[12845];
 if(Math.hypot(x-mf[16],y-mf[17],z-mf[18])<30){self.__ring127(x,y,z,ma[12841]?120:255,ma[12841]?200:255,255);self.__proj127(0,x,y,z,ma[12841]?7:6);}
 /* 204: home lights. They were drawn at the viewer's own position (three lights following the player, moved 30 times a
  second while the picture runs faster: they jumped, and every player lit the room around himself). Now at fixed
  points of a 6 m world grid around the player (the same points for everybody standing there, nothing moves with
  the player) and faded over 350 ms when switched instead of popping. */
 {const L=self.__light204??={v:0,at:performance.now()},tn=performance.now(),step=Math.min(1,(tn-L.at)/350),want=ma[12841]&&ma[12842]?1:0;L.at=tn;L.v=want?Math.min(1,L.v+step):Math.max(0,L.v-step);
  if(ma[12841]&&L.v>.01&&mf.slice(16,19).every(Number.isFinite)){const G=6,cx=Math.round(mf[16]/G)*G,cy=Math.round(mf[17]/G)*G,lz=Math.round(mf[18]*2)/2+1.6;
   for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)nativeCall('DRAW_LIGHT_WITH_RANGE',[bits(cx+dx*G),bits(cy+dy*G),bits(lz),255,238,210,bits(7.5),bits(.75*L.v)]);}}
}for(let n=0;n<Math.min(5,ma[7200]);n++){const o=7204+n*8;if(Math.hypot(mf[o+1]-mf[16],mf[o+2]-mf[17],mf[o+3]-mf[18])>30)continue;self.__ring127(mf[o+1],mf[o+2],mf[o+3],255,255,255);self.__proj127(n+1,mf[o+1],mf[o+2],mf[o+3],ma[o]);}};
 if(now-(self.__pavArrestPoll||0)>500){self.__pavArrestPoll=now;const player=e.pn_player_id(),arrested=nativeCall('pn_v20_arrested',[player,0]);if(arrested){self.__pavArrestStart??=now;if(now-self.__pavArrestStart>4000&&now-(self.__pavArrestReset||-Infinity)>15000){nativeCall('pn_v20_arrest_reset',[player]);nativeCall('pn_v20_wanted_clear',[player]);nativeCall('pn_v20_fade_in',[300]);self.__pavArrestReset=now;self.__pavArrestStart=undefined;Atomics.add(a,7107,1);}}else self.__pavArrestStart=undefined;}
 if(a[7102]!==self.__pavEnvironment){self.__pavEnvironment=a[7102];nativeCall('pn_v20_pause_clock',[1]);nativeCall('pn_v20_clock',[a[7103],a[7104],a[7106]]);const weather=['EXTRASUNNY','CLEAR','CLOUDS','SMOG','FOGGY','OVERCAST','RAIN','THUNDER','CLEARING','NEUTRAL','SNOW','BLIZZARD','SNOWLIGHT','XMAS'][a[7105]]||'EXTRASUNNY';if(weather!==self.__pavWeather){nativeCall('pn_v20_weather',[cstring(weather,65312)]);self.__pavWeather=weather;}}
 
 // Live, acknowledged engine color grading. Profiles are present in supplied timecycle XML.
 if(a[7800]!==self.__fxSeq33){self.__fxSeq33=a[7800];const name=({1:'NeutralColorCodeLight',2:'NG_filmic03',3:'NG_filmic04',4:'NG_filmic01'})[a[7801]];if(name){nativeCall('SET_TIMECYCLE_MODIFIER',[cstring(name,65200)]);nativeCall('SET_TIMECYCLE_MODIFIER_STRENGTH',[bits(Math.max(0,Math.min(1,f[7802]||0)))]);}else nativeCall('CLEAR_TIMECYCLE_MODIFIER');a[7804]=nativeCall('GET_TIMECYCLE_MODIFIER_INDEX')|0;Atomics.store(a,7803,a[7800]);}
 const loaded=model=>{if(!e.pn_model_valid(model))return false;if(e.pn_model_loaded(model))return true;if(now-(requests.get(model)??-Infinity)>1000){requests.set(model,now);e.pn_request_model(model);}return false;};
 const applyLook=(h,o)=>{
  const seq=o===2944?Atomics.load(a,13877):0;if(seq&1)return false;const ia=a.slice(o,o+38),fa=f.slice(o,o+38);if(o===2944&&seq!==Atomics.load(a,13877))return false;
  const previous=blends.get(h),headKey=[ia[1],ia[2],ia[36],ia[37],fa[3],fa[4]].join(':');
  if(!previous){e.pn_default_clothes(h);for(let p=0;p<8;p++)e.pn_clear_prop(h,p);e.pn_component(h,0,0,0,2);}
  if(!previous||previous.headKey!==headKey){
   if(o===2944)a[13884]++;e.pn_head_blend(h,ia[1],ia[2],0,ia[36],ia[37],0,fa[3],fa[4],0,0);
   blends.set(h,{started:now,done:false,headKey});
  }
  const components=[[2,ia[5]],[11,ia[7]],[4,ia[8]],[6,ia[9]],[3,ia[10]],[8,ia[11]]];
  const state=blends.get(h);state.appliedComponents=previous?.appliedComponents||new Map();state.pendingComponents=components.map(([id,wanted])=>({id,wanted,texture:ia[15]}));
  const blend=blends.get(h);blend.detail={gender:ia[0],color:ia[6],eye:ia[12],beard:ia[13],brow:ia[14],features:Array.from(fa.slice(16,36))};blend.detailsDirty=true;return true;
 };
 if(Atomics.load(a,13877)&1)return;
 const ownModel=modelOf(a[2944]);a[37]=0;a[61]=(e.pn_model_valid(ownModel)?1:0)|(e.pn_model_loaded(ownModel)?2:0);
 if((e.pn_model(ped)|0)!==ownModel){
  a[63]=0;a[13876]=0;
  if(self.__model84?.model!==ownModel)self.__model84={model:ownModel,at:now,requested:-Infinity};
  const sw=self.__model84;
  if(loaded(ownModel)&&now-sw.requested>=750){
   if(spawned&&spawnVersion===Atomics.load(a,46)){const old=coords(ped),heading=e.pn_heading(ped);f.set([...old,heading],40);}
   sw.requested=now;a[13883]++;blends.delete(ped);e.pn_player_model(e.pn_player_id(),ownModel);ped=e.pn_player_ped();
   if(!ped||!e.pn_exists(ped))return;blends.delete(ped);spawned=false;hpVersion=-1;armorVersion=-1;a[7613]=-1;appearanceVersion=-1;seatVersion=-1;loadoutVersion=-1;
  }
  if((e.pn_model(ped)|0)!==ownModel){if(now-sw.at>15000)a[13876]=-1;return;}
 }
 a[37]=1;a[13874]=a[2944];self.__model84=null;
 if(a[37]&&appearanceVersion!==a[47]&&(!blends.get(ped)||blends.get(ped).done)){const revision=a[47];if(applyLook(ped,2944))appearanceVersion=revision;}
 for(const [h,blend] of blends){
  if(!e.pn_exists(h)){blends.delete(h);continue;}
  if(!blend.done&&now-blend.started>100&&e.pn_blend_done(h)){e.pn_blend_finish(h);e.pn_palette_disable(h);blend.done=true;}
  if(blend.done&&blend.pendingComponents?.length&&now-(blend.componentAt??-Infinity)>=90){
   const next=blend.pendingComponents.shift(),count=e.pn_component_count(h,next.id);
   if(count>0){const drawable=Math.max(0,Math.min(next.wanted,count-1)),textures=e.pn_texture_count(h,next.id,drawable),texture=Math.max(0,Math.min(next.id===2?0:next.texture,Math.max(0,textures-1))),key=drawable+':'+texture;
    if(blend.appliedComponents.get(next.id)!==key&&e.pn_component_valid(h,next.id,drawable,texture)){e.pn_component(h,next.id,drawable,texture,2);blend.appliedComponents.set(next.id,key);blend.componentAt=now;}
   }
  }
  if(blend.done&&blend.detailsDirty){const d=blend.detail;e.pn_hair_colour(h,d.color,d.color);e.pn_eye_colour(h,d.eye);e.pn_overlay(h,1,d.beard<0?255:d.beard,d.gender?0:1);e.pn_overlay_colour(h,1,1,d.color,d.color);e.pn_overlay(h,2,d.brow,1);e.pn_overlay_colour(h,2,1,d.color,d.color);d.features.forEach((v,i)=>e.pn_face_feature(h,i,v));blend.detailsDirty=false;}
 }
 const ownBlend100=blends.get(ped);a[13886]=ownBlend100?Math.max(0,Math.min(600000,Math.round(now-ownBlend100.started))):0;a[13887]=ownBlend100?.pendingComponents?.length||0;
 a[63]=blends.get(ped)?.done&&!blends.get(ped)?.pendingComponents?.length?1:0;a[13875]=appearanceVersion;a[13876]=a[63]?1:(ownBlend100&&!ownBlend100.done&&now-ownBlend100.started>15000?-2:0);[2,11,4,6,3,8].forEach((id,i)=>{a[90+i]=Math.max(0,e.pn_component_count(ped,id)-1);});
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
     if(g.handle!==handle){g.handle=handle;if(nativeCall('IS_INTERIOR_DISABLED',[handle]))nativeCall('DISABLE_INTERIOR',[handle,0]);if(nativeCall('IS_INTERIOR_CAPPED',[handle]))nativeCall('CAP_INTERIOR',[handle,0]);nativeCall('PIN_INTERIOR_IN_MEMORY',[handle]);nativeCall('REFRESH_INTERIOR',[handle]);}
     const roomReady=!!nativeCall('IS_INTERIOR_READY',[handle]);a[7710]=roomReady?1:0;const floorReady=roomReady&&interiorFloor31(g.target);f[7711]=f[16236];if(floorReady){a[7701]=2;g.readyAt=now;releaseInteriorFocus31();}
    }
   }
  }else if(a[7701]===2){vector(...g.from);e.pn_set_coords(ped,ptr,1,1,1);vector(0,0,0);e.pn_set_velocity(ped,ptr);if(now-g.readyAt>10000){a[7701]=-2;releaseInteriorFocus31();}}
 }
 if(!spawned||spawnVersion!==Atomics.load(a,46)){
  a[13885]++;e.pn_pause(0);spawnVersion=Atomics.load(a,46);cameraVerified60=false;cameraReleaseAt60=-Infinity;a[7712]=0;vector(f[40],f[41],f[42]);
  if(interiorGate31?.arriving&&Math.hypot(f[40]-interiorGate31.target[0],f[41]-interiorGate31.target[1],f[42]-interiorGate31.target[2])>=2){interiorGate31.arriving=false;a[7701]=-4;releaseInteriorFocus31();}
  if(interiorGate31&&a[7701]===2&&Math.hypot(f[40]-interiorGate31.target[0],f[41]-interiorGate31.target[1],f[42]-interiorGate31.target[2])<2){interiorGate31.arriving=true;interiorGate31.arrivedAt=now;interiorGate31.floorOk=false;a[7701]=3;}
  if(e.pn_health(ped)<=100){e.pn_local_resurrect(ptr,f[43],2000,0,1,11,0);ped=e.pn_player_ped();hpVersion=-1;armorVersion=-1;loadoutVersion=-1;e.pn_clear_tasks(ped);e.pn_collision(ped,1,1);e.pn_player_control(e.pn_player_id(),1,0);}
  vector(f[40],f[41],f[42]);e.pn_collision_request(ptr);e.pn_set_coords(ped,ptr,1,1,1);e.pn_set_heading(ped,f[43]);e.pn_fade_in(250);e.pn_clear_focus();e.pn_focus_ped(ped);e.pn_follow_ped(ped);e.pn_radar(a[108]?0:1);e.pn_radar_zoom(110);e.pn_minimap_fow(1);spawned=true;spawnAt=now;a[7611]=0;groundPlaced=!a[112];groundRetry=0;a[113]=0;e.pn_freeze(ped,1);
 }
 const preview=!!a[62],fly=!!a[64];
 if(preview){
  if(!previousPreview){previewHeading=e.pn_heading(ped);previewSpawnVersion=spawnVersion;}
  if(!previewCam||!e.pn_cam_exists(previewCam))previewCam=e.pn_cam_create(cstring('DEFAULT_SCRIPTED_CAMERA'),1);
  e.pn_freeze(ped,1);e.pn_invincible(ped,1);e.pn_controls_disable(0);e.pn_hud_show(0);e.pn_radar(0);
  const pos=coords(ped),angle=(f[68]||0)*Math.PI/180,distance=Math.max(.8,Math.min(5,f[69]||3.6));
  const shift=f[7130]||0,dx=Math.cos(angle)*shift,dy=-Math.sin(angle)*shift;e.pn_set_heading(ped,0);vector(pos[0]+Math.sin(angle)*distance+dx,pos[1]+Math.cos(angle)*distance+dy,pos[2]+(f[70]||.75)+.15);e.pn_cam_set(previewCam,ptr);vector(pos[0]+dx,pos[1]+dy,pos[2]+(f[70]||.75));e.pn_cam_point(previewCam,ptr);e.pn_cam_fov(previewCam,distance>2?48:38);e.pn_cam_render(1,0,0,1,0,0);a[73]=a[37];previousPreview=true;
 }
 if(previousPreview&&!preview){if(previewCam){e.pn_cam_render(0,0,0,1,1,0);e.pn_cam_destroy(previewCam,1);previewCam=0;}if(previewSpawnVersion===spawnVersion)e.pn_set_heading(ped,previewHeading);previousPreview=false;spawnAt=now;e.pn_destroy_cams(1);e.pn_focus_ped(ped);e.pn_follow_ped(ped);e.pn_follow_mode(1);e.pn_follow_heading(0);}
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
 // Entry is acknowledged only AFTER a subsequent native frame renders gameplay.
 const joining60=!!(a[71]||a[7610]);
 if(joining60&&!cameraJoining60){cameraVerified60=false;cameraReleaseAt60=-Infinity;}
 cameraJoining60=joining60;
 const releaseCamera60=()=>{
  e.pn_cam_render(0,0,0,1,1,0);
  if(introCam)e.pn_cam_destroy(introCam,1);introCam=0;
  e.pn_destroy_cams(1);e.pn_follow_ped(ped);e.pn_follow_mode(1);e.pn_follow_heading(0);
  cameraReleaseAt60=now;Atomics.add(a,14111,1);
 };
 const mayFollow60=!preview&&!a[6500]&&!a[12800]&&!a[13300]&&!fly&&!a[72]&&a[37]&&a[63];
 if(mayFollow60&&(!cameraVerified60||a[71])){
  if(now-cameraReleaseAt60>=1000){releaseCamera60();e.pn_clear_focus();e.pn_focus_ped(ped);}
  a[14110]=nativeCall('IS_GAMEPLAY_CAM_RENDERING')?1:0;
  if(now>cameraReleaseAt60&&a[14110]){cameraVerified60=true;a[71]=0;}
 }else if(mayFollow60&&!joining60&&e.pn_health(ped)>0&&!e.pn_vehicle(ped,0)&&now-cameraCheckAt60>=1000){
  cameraCheckAt60=now;a[14110]=nativeCall('IS_GAMEPLAY_CAM_RENDERING')?1:0;
  // A late script camera must not strand an already joined player. Never
  // touch preview/showroom/fly/death or change the player's coordinates.
  if(!a[14110])releaseCamera60();
 }
 a[7611]=mayFollow60&&!a[71]&&cameraVerified60?1:0;
 const entryLocked=preview||!!a[7610]||!!a[71]||!!a[72];
  // 144 melee sync: the peer whose relayed melee_target is this victim (server relays it only within 4 m while flags&32),
  // and a swing queued on that attacker's clone (played after its own tasks; one swing per 500 ms).
  const attacker144=victim=>{if(!victim)return -1;for(let i=0;i<Math.min(32,a[5]);i++){const o=128+i*64;if(a[o]&&a[o+61]===victim&&(a[o+11]&32)&&!(a[o+11]&256))return o;}return -1;};
  const swing144=o=>{if(a[15901]===154)return;const attacker=o<0?null:entities.get(a[o]);if(attacker&&now-(attacker.swungAt144??-Infinity)>500)attacker.swing144=now;};
 if(entryLocked){
  if(!self.__pavEntryHeld){e.pn_clear_tasks(ped);e.pn_select_weapon(ped,0xA2719263|0,1);self.__pavEntryHeld=true;}
  e.pn_controls_disable(0);e.pn_freeze(ped,1);e.pn_invincible(ped,1);shootUntil=meleeUntil=0;a[106]=0;
 }else if(self.__pavEntryHeld){e.pn_clear_tasks(ped);self.__pavEntryHeld=false;loadoutVersion=-1;}
 // 104: Left Ctrl crouch (client toggles a[13910]); stock stealth duck (control 36) is disabled.
 {const crouch104=self.__crouch104??={on:false,ped:0},want104=!!a[13910]&&!entryLocked&&!fly&&!e.pn_vehicle(ped,0)&&e.pn_health(ped)>100&&!a[7830]&&!a[7831];
  if(crouch104.ped!==ped){crouch104.ped=ped;crouch104.on=false;}
  if(want104&&!crouch104.on){const move=cstring('move_ped_crouched');nativeCall('REQUEST_ANIM_SET',[move]);if(nativeCall('HAS_ANIM_SET_LOADED',[move])){nativeCall('SET_PED_MOVEMENT_CLIPSET',[ped,cstring('move_ped_crouched'),bits(.25)]);const strafe=cstring('move_ped_crouched_strafing');nativeCall('REQUEST_ANIM_SET',[strafe]);if(nativeCall('HAS_ANIM_SET_LOADED',[strafe]))nativeCall('SET_PED_STRAFE_CLIPSET',[ped,cstring('move_ped_crouched_strafing')]);crouch104.on=true;}}
  else if(!want104&&crouch104.on){nativeCall('RESET_PED_MOVEMENT_CLIPSET',[ped,bits(.25)]);nativeCall('RESET_PED_STRAFE_CLIPSET',[ped]);crouch104.on=false;}
  a[13911]=crouch104.on?1:0;}
 nativeCall('SET_PED_INFINITE_AMMO_CLIP',[ped,0]);if(a[103]&&(a[103]>>>0)!==0xA2719263)nativeCall('SET_PED_INFINITE_AMMO',[ped,0,a[103]]);
 if(armorVersion!==a[66]){e.pn_set_armor(ped,a[65]);if(e.pn_armor(ped)===a[65])armorVersion=a[66];}a[7613]=armorVersion;
 if(!a[62]&&a[44]>100&&e.pn_faded_out())e.pn_fade_in(250);
 if(!entryLocked&&(loadoutVersion!==a[102]||a[6608]!==a[102]&&now-(self.__pavEquipAt||0)>500)){self.__pavEquipAt=now;const weapon=a[103],melee103=self.__melee103.has(weapon>>>0);if(weapon&&(weapon>>>0)!==0xA2719263){e.pn_give_weapon(ped,weapon,melee103?0:a[104],0,1);if(!melee103){e.pn_set_ammo(ped,weapon,a[104],0);nativeCall('pn_v19_clip',[ped,weapon,Math.max(0,Math.min(a[7121],a[7120],a[104]))]);}}e.pn_select_weapon(ped,weapon||0xA2719263|0,1);loadoutVersion=a[102];if((e.pn_weapon(ped)>>>0)===(a[103]>>>0)&&((a[103]>>>0)===0xA2719263||melee103||e.pn_ammo(ped,a[103])===a[104]))a[6608]=loadoutVersion;}
 const version=Atomics.load(a,45);if(version!==hpVersion){const hp=Atomics.load(a,44);e.pn_set_health(ped,hp<=100?0:hp,0);hpVersion=version;Atomics.store(a,125,version);}if(!a[72])Atomics.store(a,96,spawnVersion);
 if(!entryLocked&&a[59]!==localDamage){localDamage=a[59];if(localDamage&&e.pn_health(ped)>100){e.pn_ragdoll(ped,1);e.pn_ragdoll_task(ped,a[60]===1?260:180,a[60]===1?260:180,0,0,0,0);if(a[60]===1)swing144(attacker144(a[51]));}}
 mark51(4);const sub213=self.__sub213??={};let t213=performance.now();const lap213=k=>{const n=performance.now(),d=n-t213;t213=n;if(!(sub213[k]>=d))sub213[k]=Math.round(d*10)/10;};/* 213: phase 4 by parts */const localVehicle77=e.pn_vehicle(ped,0);const carSeq=Atomics.load(a,14),carStates=[];
 if(!(carSeq&1)){for(let i=0;i<Math.min(48,Atomics.load(a,15));i++){const o=4096+i*32;carStates.push({id:a[o],model:a[o+1],owner:a[o+2],locked:a[o+3],driver:a[o+4],pos:Array.from(f.slice(o+5,o+8)),heading:f[o+8],rot:Array.from(f.slice(o+9,o+12)),velocity:Array.from(f.slice(o+12,o+15)),body:f[o+15],engine:!!a[o+16],windows:a[o+24],doors:a[o+25],street:!!a[o+26],poseEpoch:a[o+28],repairEpoch:a[o+29],indicators:a[o+31],lights:a[8310+i*16],mods:Array.from(a.slice(8300+i*16,8310+i*16)),paint:Array.from(a.slice(9100+i*8,9108+i*8)),plate:Array.from(new Uint8Array(memory.buffer,base+(o+20)*4,16)).map(byte=>String.fromCharCode(byte)).join('').split('\0')[0]});}}
 if(carSeq!==Atomics.load(a,14))carStates.length=0;
 if(!(carSeq&1)&&carSeq===Atomics.load(a,14)){
  const active=new Set(carStates.map(v=>v.id));
  for(const [id,v] of vehicles)if(!active.has(id)){drop101(v.handle,true);vehicles.delete(id);attempts.delete('v'+id);}
  let created=false;
  if(a[119]!==bindVersion){const request=Atomics.load(a,119),id=a[120],handle=a[121],snapshot=carStates.find(v=>v.id===id);
   if(snapshot){bindVersion=request;a[123]=-1;
    if(handle&&e.pn_exists(handle)&&e.pn_model(handle)===snapshot.model&&Math.hypot(...coords(handle).map((c,i)=>c-coords(ped)[i]))<=9){
     const old=vehicles.get(id);if(old&&old.handle!==handle&&e.pn_exists(old.handle)&&localVehicle77!==old.handle)drop101(old.handle,true);
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
  if(now-(self.__fmPurge169??0)>20000){self.__fmPurge169=now;if(failedModels33.size){for(const m of failedModels33)requests.delete(m);failedModels33.clear();}}
  for(const [i30,v] of carStates.entries()){
   if(!v.id||![...v.pos,v.heading,...v.rot,...v.velocity,v.body].every(Number.isFinite))continue;if(!v.owner&&v.id!==a[48]&&!v.driver&&!vehicles.has(v.id)&&Math.hypot(...v.pos.map((p,i)=>p-f[16+i]))>120){modelWait41.delete(v.id);continue;}if(failedModels33.has(v.model))continue;if(!verifiedCars77.has(v.model)){if(!e.pn_vehicle_model(v.model)||!e.pn_model_valid(v.model)){failedModels33.add(v.model);modelFailure41(v.id,1);continue;}verifiedCars77.add(v.model);}let local=vehicles.get(v.id);
   if(!local||!e.pn_exists(local.handle)){
    let wait=modelWait41.get(v.id);if(!wait||wait.model!==v.model){wait={model:v.model,at:now};modelWait41.set(v.id,wait);}
    if(now-wait.at>25000){failedModels33.add(v.model);e.pn_model_release(v.model);modelFailure41(v.id,2);continue;}
    if(created||!loaded(v.model)||now-(attempts.get('v'+v.id)??-Infinity)<1000)continue;
    attempts.set('v'+v.id,now);vector(...v.pos);const handle=e.pn_create_vehicle(v.model,ptr,v.heading,0,1,0);if(!handle)continue;modelWait41.delete(v.id);created=true;if(a[109]===v.id)a[109]=0;e.pn_mission_entity(handle,1,1);e.pn_freeze(handle,1);e.pn_vehicle_plate(handle,cstring(v.plate));local={handle,createdAt:now,locked:-1,grounded:false,groundRetry:-Infinity,pose:[...v.pos,v.heading,...v.rot].join(':')};vehicles.set(v.id,local);e.pn_model_release(v.model);
   }
   const h=local.handle;
   if(!local.renderReady&&[1718441594,2117711508,631542247,-242672787,178350184,1352183536].includes(v.model)){nativeCall('SET_VEHICLE_LOD_MULTIPLIER',[h,bits(1)]);nativeCall('SET_ENTITY_LOD_DIST',[h,200]);local.renderReady=true;}

   if(local.grounded===false){
    if(now-local.groundRetry>350){local.groundRetry=now;vector(...coords(h));e.pn_collision_request(ptr);
     const collision38=!!e.pn_collision_ready(h);local.collision46=collision38;local.floor46=false;
     if(local.boat88===undefined)local.boat88=['dinghy','jetmax','marquis'].some(name=>modelHash23(name)===(v.model>>>0));
     let placed38=false;
     if(local.boat88){const p88=coords(h);f[16237]=NaN;const water88=!!nativeCall('GET_WATER_HEIGHT',[...p88.map(bits),BigInt(base+64948)]);
      if(water88&&Number.isFinite(f[16237])&&Math.abs(f[16237]-p88[2])<5&&collision38){vector(p88[0],p88[1],f[16237]+.15);e.pn_set_coords(h,ptr,1,1,1);nativeCall('SET_BOAT_ANCHOR',[h,0]);placed38=true;}
     }else placed38=collision38&&!!e.pn_vehicle_ground(h,5);
     if(!placed38&&collision38&&now-local.createdAt>=3500&&[1718441594,2117711508,631542247,-242672787,178350184,1352183536].includes(v.model)){
      const pos38=coords(h);vector(pos38[0],pos38[1],pos38[2]+1);f[16236]=NaN;
      placed38=!!e.pn_ground(ptr,BigInt(base+64944),0,1)&&Number.isFinite(f[16236])&&Math.abs(f[16236]-pos38[2])<2.5;local.floor46=placed38;local.floorZ46=f[16236];
     }
     if(!placed38&&collision38&&!local.boat88&&now-local.createdAt>=2000){placed38=true;local.dropped163=true;}
     if(placed38){local.grounded=true;e.pn_freeze(h,0);local.kinematic46=false;}
    }
    if(!local.grounded){if(!local.warnedGround41&&now-local.createdAt>20000){modelFailure41(v.id,3);a[14010]=46;a[14011]=v.id;a[14012]=local.collision46?1:0;a[14013]=local.floor46?1:0;f[14014]=Number.isFinite(local.floorZ46)?local.floorZ46:NaN;f[14015]=v.pos[2];f[14016]=(now-local.createdAt)/1000;local.warnedGround41=true;}continue;}
   }
   if(local.boat88&&local.anchored88!==!v.driver){nativeCall('SET_BOAT_ANCHOR',[h,v.driver?0:1]);local.anchored88=!v.driver;}
   if(local.indicators!==v.indicators){nativeCall('pn_v20_indicators',[h,1,v.indicators===1||v.indicators===3?1:0]);nativeCall('pn_v20_indicators',[h,0,v.indicators===2||v.indicators===3?1:0]);local.indicators=v.indicators;}   const kit72=12900+i30*4,airVersion72=a[kit72+1];
   if(a[kit72]===v.id&&airVersion72&&local.airVersion72!==airVersion72){
    nativeCall('SET_CAN_USE_HYDRAULICS',[h,1]);
    for(let wheel=0;wheel<4;wheel++)nativeCall('SET_HYDRAULIC_SUSPENSION_RAISE_FACTOR',[h,wheel,bits(f[kit72+(wheel<2?2:3)])]);
    local.airVersion72=airVersion72;
   }
   if(a[12800]&&a[12801]===v.id){
    if(!local.customKit72){const saved72=readPaint43(h);nativeCall('SET_VEHICLE_MOD_KIT',[h,0]);if(saved72){nativeCall('SET_VEHICLE_COLOURS',[h,saved72[0],saved72[1]]);for(let side=0;side<2;side++)if(saved72[2]&(1<<side))nativeCall('SET_VEHICLE_CUSTOM_'+(side?'SECONDARY':'PRIMARY')+'_COLOUR',[h,...saved72.slice(3+side*3,6+side*3)]);}local.customKit72=true;}
    a[12804]=1;const capSlots72=[23,11,12,15,0];for(let k=0;k<capSlots72.length;k++)a[12820+k]=nativeCall('GET_NUM_VEHICLE_MODS',[h,capSlots72[k]]);
    if(a[12810]){v.mods=[...v.mods];v.paint=[...v.paint];for(const [cell,index]of [[12811,1],[12812,2],[12813,3],[12814,4]])if(a[cell]>=-1){v.mods[index]=a[cell];if(index<=2)v.paint[0]&=~(1<<(index-1));}}
   }
   const sig=v.mods.join(':')+':'+v.paint.join(':');if(local.mods!==sig){local.mods=sig;const m=v.mods;if(m[0]===v.id){if(m.slice(3).some(v=>v>=-1))nativeCall('SET_VEHICLE_MOD_KIT',[h,0]);if(m[1]>=0||m[2]>=0){const previous43=(m[1]<0||m[2]<0)?readPaint43(h):null;
     if(m[1]>=0&&m[2]>=0||previous43){nativeCall('SET_VEHICLE_COLOURS',[h,m[1]>=0?m[1]:previous43[0],m[2]>=0?m[2]:previous43[1]]);
      for(let side=0;side<2;side++)if(m[1+side]>=0){const name=side?'SECONDARY':'PRIMARY',start=1+side*3;if(v.paint[0]&(1<<side))nativeCall('SET_VEHICLE_CUSTOM_'+name+'_COLOUR',[h,...v.paint.slice(start,start+3)]);else nativeCall('CLEAR_VEHICLE_CUSTOM_'+name+'_COLOUR',[h]);}}
    }local.paintObservation43=null;local.paintAt43=-Infinity;if(m[3]>=-1&&v.model!==631542247){nativeCall('SET_VEHICLE_WHEEL_TYPE',[h,0]);const n=nativeCall('GET_NUM_VEHICLE_MODS',[h,23]);nativeCall('SET_VEHICLE_MOD',[h,23,Math.min(m[3],n-1),0]);}if(m[4]>=0)nativeCall('SET_VEHICLE_WINDOW_TINT',[h,m[4]]);for(const [i,slot] of [[5,11],[6,12],[7,15],[8,0]])if(m[i]>=-1){const n=nativeCall('GET_NUM_VEHICLE_MODS',[h,slot]);nativeCall('SET_VEHICLE_MOD',[h,slot,Math.min(m[i],n-1),0]);}if(m[9]>=0)nativeCall('TOGGLE_VEHICLE_MOD',[h,18,m[9]?1:0]);}}
if(local.windows!==v.windows){for(let n=0;n<4;n++)if((local.windows??0)&(1<<n) ^ v.windows&(1<<n))(v.windows&(1<<n)?e.pn_window_down:e.pn_window_up)(h,n);local.windows=v.windows;}
   if(local.doors!==v.doors){for(let n=0;n<6;n++)if((local.doors??0)&(1<<n) ^ v.doors&(1<<n)){if(v.doors&(1<<n))e.pn_door_open(h,n,0,0);else e.pn_door_shut(h,n,0);}local.doors=v.doors;}
   if(!a[8311+i30*16]&&a[7601]===v.id&&localVehicle77===h&&now-(self.__pavHornAt||0)>100){self.__pavHornAt=now;nativeCall('START_VEHICLE_HORN',[h,150,0,0]);}if(local.locked!==v.locked){e.pn_vehicle_lock(h,v.locked?2:1);local.locked=v.locked;}if(local.engine!==v.engine||now-(local.engineCheck??-Infinity)>500){local.engineCheck=now;e.pn_vehicle_engine(h,v.engine?1:0,1,1);local.engine=v.engine;local.lightsAt=-Infinity;}
   // Engine/native driver updates may reset lamps. Reapply bounded authoritative
   // state after the engine, with the native output observed on the next update.
   if(local.lights!==v.lights||now-(local.lightsAt??-Infinity)>=500){local.lightsAt=now;const lamp=new Int32Array(memory.buffer,base+64464,2);lamp.fill(0);nativeCall('GET_VEHICLE_LIGHTS_STATE',[h,BigInt(base+64464),BigInt(base+64468)]);const on=v.lights?1:0,beam=v.lights===2?1:0;if(local.lights!==v.lights||lamp[0]!==on||lamp[1]!==beam){nativeCall('SET_VEHICLE_LIGHTS',[h,on?2:1]);nativeCall('SET_VEHICLE_FULLBEAM',[h,beam]);}local.lights=v.lights;const ack=12000+i30*4;a[ack]=v.id;a[ack+1]=v.lights;a[ack+2]=lamp[0];a[ack+3]=lamp[1];}

   if(local.repairEpoch!==v.repairEpoch){if(v.repairEpoch){nativeCall('pn_v19_fix',[h]);nativeCall('SET_VEHICLE_DEFORMATION_FIXED',[h]);nativeCall('SET_VEHICLE_DIRT_LEVEL',[h,bits(0)]);nativeCall('pn_v19_engine_health',[h,bits(1000)]);for(let n=0;n<6;n++)e.pn_door_shut(h,n,1);local.doors=0;}local.repairEpoch=v.repairEpoch;}
   const pose=[...v.pos,v.heading,...v.rot].join(':');
   const snapshot44=[pose,...v.velocity,v.driver,v.poseEpoch].join(':');if(local.snapshot44!==snapshot44){local.snapshot44=snapshot44;local.snapshotAt44=now;}
   const nativeDriver46=localVehicle77===h&&e.pn_vehicle_seat(h,-1,0)===ped;
   const actualDriver38=nativeDriver46&&v.driver===a[51]&&a[48]===v.id&&a[49]===-1;
   const pendingDriver61=v.driver===a[51]&&a[48]===v.id&&a[49]===-1&&!nativeDriver46;
   if(!!v.driver&&v.driver!==a[51])local.remoteAt172=now;
   const trailing172=!v.driver&&now-(local.remoteAt172??-1e9)<6000&&now-(local.drove164??-1e9)>=6000&&now-(local.snapshotAt44??-1e9)<600&&Math.hypot(...v.velocity)>.3;
   const remoteDriver38=!!v.driver&&v.driver!==a[51]||trailing172;
   {/* 203: a passenger hears the station the (remote) driver plays */let st203=0;if(!nativeDriver46&&v.driver&&v.driver!==a[51]&&e.pn_vehicle(ped,0)===h){for(let j203=0,n203=Math.min(32,Math.max(0,a[5]|0));j203<n203;j203++){const o203=128+j203*64;if(a[o203]===v.driver){st203=(a[o203+11]>>>16)&255;break;}}}if(st203){local.st203=st203;local.st203At=now;}else if(now-(local.st203At??-1e9)<1500&&e.pn_vehicle(ped,0)===h)st203=local.st203;const radio164=nativeDriver46||st203?1:0;if(local.radio164!==radio164){try{nativeCall('SET_VEHICLE_RADIO_ENABLED',[h,radio164]);}catch{}local.radio164=radio164;}if(st203&&local.station203!==st203){try{nativeCall('SET_RADIO_TO_STATION_INDEX',[st203-1]);}catch{}local.station203=st203;}else if(!st203)local.station203=0;}
   if(actualDriver38)local.drove164=now;
   // Only the reserved, physically seated local driver simulates this car.
   // A remote replica must not also integrate gravity/contact/old velocity.
   const entryPose= pendingDriver61 ? entryPose62(h) : null;
   const holdEntry62=!(now-(local.drove164??-1e9)<4000)&&pendingDriver61&&(entryPose.safe||seatVersion===a[50]&&seatTask62&&!seatWarped)&&!(seatVersion===a[50]&&seatWarped);
   const kinematic46=remoteDriver38||holdEntry62||nativeDriver46&&!actualDriver38&&!(now-(local.drove164??-1e9)<4000);
   const live163=remoteDriver38&&!holdEntry62&&!(nativeDriver46&&!actualDriver38)&&Math.hypot(v.pos[0]-f[16],v.pos[1]-f[17],v.pos[2]-f[18])<150,frozen163=kinematic46&&!live163;
   if(!!local.kinematic46!==frozen163){e.pn_freeze(h,frozen163?1:0);local.kinematic46=frozen163;}
   if(frozen163){vector(0,0,0);e.pn_set_velocity(h,ptr);}
   if(nativeDriver46&&!actualDriver38)for(const control46 of [59,60,71,72])e.pn_control_disable(0,control46,1);
   const placement=local.poseEpoch!==undefined&&v.poseEpoch!==local.poseEpoch;if(local.poseEpoch===undefined)local.poseEpoch=v.poseEpoch;
   if(actualDriver38||pendingDriver61){local.pose=pose;local.ownUntil=now+3000;local.remoteDriven38=false;}
   else if(remoteDriver38)local.ownUntil=0;const live49=remoteDriver38&&!placement&&!nativeDriver46&&!self.__veh49Off&&now>=(local.ownUntil||0);if(!live49)local.track49=null;
   if(placement||(!actualDriver38&&now>=(local.ownUntil||0)&&(remoteDriver38||local.remoteDriven38))){local.pose=pose;local.poseEpoch=v.poseEpoch;local.remoteDriven38=remoteDriver38;if(live49){push49(local,v,now);if(local.body!==v.body){e.pn_set_vehicle_body(h,v.body);local.body=v.body;}}else{
    const current=coords(h),error=Math.hypot(...v.pos.map((p,i)=>p-current[i]));const age44=Math.max(0,(now-local.snapshotAt44)/1000),prediction44=remoteDriver38&&!placement?Math.min(.7,age44):0,blend44=1-Math.exp(-20*frameDelta44);const goal=v.pos.map((p,i)=>p+v.velocity[i]*prediction44);
    vector(...goal.map((p,i)=>placement||!remoteDriver38||error>6+Math.hypot(...v.velocity)*.3?p:current[i]+(p-current[i])*blend44));e.pn_set_coords(h,ptr,1,1,1);
    e.pn_rotation(ptr,h,2);const rot=[s[0],s[1],s[2]];vector(...(placement||!remoteDriver38?v.rot:orientation64.blend(rot,v.rot,blend44)));e.pn_set_rotation(h,ptr,2,1);if(placement&&!v.driver){e.pn_freeze(h,1);local.grounded=false;local.createdAt=now;local.groundRetry=-Infinity;local.kinematic46=true;}vector(...(frozen163||!v.driver&&!trailing172||remoteDriver38&&age44>.5?[0,0,0]:v.velocity));e.pn_set_velocity(h,ptr);if(local.body!==v.body){e.pn_set_vehicle_body(h,v.body);local.body=v.body;}}
   }
  }
 }
 lap213('veh');if(now-(self.__atmAt163||0)>250){self.__atmAt163=now;let atm163=0;const p163=coords(ped),A214=self.__atm214??={known:[],still:0,last:null,askAt:-1e9};if(!e.pn_vehicle(ped,0)){const moved=!A214.last||Math.hypot(p163[0]-A214.last[0],p163[1]-A214.last[1])>.25;A214.last=p163;A214.still=moved?now:A214.still||now;for(const c of A214.known)if(Math.hypot(c[0]-p163[0],c[1]-p163[1],c[2]-p163[2])<1.8){atm163=1;f[16301]=c[0];f[16302]=c[1];f[16303]=c[2];break;}if(!atm163&&now-A214.still>=800&&(!A214.ask||Math.hypot(p163[0]-A214.ask[0],p163[1]-A214.ask[1])>2)&&now-A214.askAt>1500){A214.ask=p163;A214.askAt=now;for(const m163 of ['prop_atm_01','prop_atm_02','prop_atm_03','prop_fleeca_atm']){const o163=nativeCall('GET_CLOSEST_OBJECT_OF_TYPE',[...p163.map(bits),bits(1.6),modelHash23(m163),0,0,0]);if(o163&&e.pn_exists(o163)){const c163=coords(o163);if(!A214.known.some(c=>Math.hypot(c[0]-c163[0],c[1]-c163[1],c[2]-c163[2])<.5)){A214.known.push(c163);if(A214.known.length>64)A214.known.shift();}if(Math.hypot(c163[0]-p163[0],c163[1]-p163[1],c163[2]-p163[2])<1.8){atm163=1;f[16301]=c163[0];f[16302]=c163[1];f[16303]=c163[2];break;}}}}}a[16300]=atm163;}
 lap213('atm');
 /* 201: shared street population. Players close together see the same traffic and pedestrians: one of them (the host,
  chosen by the page, npc201.js) keeps the engine's own population and reports it 4 times a second; the others
  (followers) switch their own ambient population off and drive copies of the host's cars and pedestrians.
  Cells (page <-> us): a[16331] mode wanted by the page (0 own population, 1 host, 2 follower); a[16332..16333] address
  of the clone buffer we allocate (lo, hi); a[16334] clones alive; a[16335] local ambient removed (total); a[16336]
  claim counter, a[16337] host char id, a[16338] host handle of a copied car the local player got into (the page asks
  the host to remove its own); a[16339] a handle the host is asked to remove (page writes, we clear); a[16382] 1 while
  we can take part (outdoors, not wanted). Clone buffer (Int32/Float32, 1024 cells): [0] seqlock (odd while the page
  writes), [1] rows, row i at 8+20*i: host char id, host handle, kind (0 ped, 1 car), model, x, y, z, rx, ry, rz, vx, vy,
  vz, a, b, c, d, age ms. Car: a driver model, b/c colours. Ped: a/b/c component variations (8 bits each: drawable
  5, texture 3). The bridge reads the buffer, never trusts it for anything but poses of entities it created. */
 if(self.__npc201Off){if(!self.__npc201OffDone){self.__npc201OffDone=true;a[16382]=0;self.__npc201Mode=0;try{nativeCall('SET_PED_POPULATION_BUDGET',[3]);for(const c of self.__npc201?.clones?.values()||[]){if(c.driver)drop101(c.driver);drop101(c.h,c.kind===1);}}catch{}}a[16382]=0;}
 else try{const N=self.__npc201??={mode:0,clones:new Map(),claimed:new Set(),seq:-1,recvAt:0,want:new Map(),sampleAt:0,sampleSeq:0,sweepAt:0,cache:new Map(),budget:-1,buf:0,removed:0,claims:0,errors:0};
  if(!N.buf){N.buf=Number(e.pn_alloc(4096n));if(N.buf>0){new Uint8Array(memory.buffer,N.buf,4096).fill(0);a[16332]=N.buf%4294967296|0;a[16333]=Math.floor(N.buf/4294967296);}}
  const interior201=!!nativeCall('GET_INTERIOR_FROM_ENTITY',[ped]),able201=!interior201&&!(a[14504]>0)&&spawned&&!a[62]&&!a[6500];
  a[16382]=able201?1:0;
  const wanted201=a[16331]|0,mode201=able201&&N.buf>0&&(wanted201===1||wanted201===2)?wanted201:0;
  const managed201=new Set([ped,showroomHandle,...[...vehicles.values(),...entities.values(),...serviceNpcs.values()].map(v=>v.handle)]);
  for(const c of N.clones.values()){managed201.add(c.h);if(c.driver)managed201.add(c.driver);}
  const pop201=h=>nativeCall('GET_ENTITY_POPULATION_TYPE',[h])|0,isPlayer201=h=>!!nativeCall('IS_PED_A_PLAYER',[h]),isMission201=h=>!!nativeCall('IS_ENTITY_A_MISSION_ENTITY',[h]);
  const copType201=h=>{const t=nativeCall('GET_PED_TYPE',[h])|0;return t===6||t===27||t===29;};
  const nearPeds201=()=>{const pool=new Int32Array(memory.buffer,base+56640,66);pool.fill(0);pool[0]=32;const n=Math.max(0,Math.min(32,nativeCall('GET_PED_NEARBY_PEDS',[ped,BigInt(base+56640),-1])));return Array.from({length:n},(_,i)=>pool[2+i*2]);};
  const nearCars201=()=>{const pool=new Int32Array(memory.buffer,base+49152,66);pool.fill(0);pool[0]=32;const n=Math.max(0,Math.min(32,nativeCall('GET_PED_NEARBY_VEHICLES',[ped,BigInt(base+49152)])));return Array.from({length:n},(_,i)=>pool[2+i*2]);};
  const playerIn201=car=>{for(let seat=-1;seat<6;seat++){const o=e.pn_vehicle_seat(car,seat,0);if(o&&isPlayer201(o))return true;}return false;};
  const rot201=h=>{e.pn_rotation(ptr,h,2);return[s[0],s[1],s[2]];},vel201=h=>{e.pn_velocity(ptr,h);return[s[0],s[2],s[4]];};
  const release201=(h,wander,driver)=>{if(!h||!e.pn_exists(h))return;e.pn_mission_entity(h,1,1);
   if(wander===1&&driver&&e.pn_exists(driver)){e.pn_mission_entity(driver,1,1);nativeCall('SET_BLOCKING_OF_NON_TEMPORARY_EVENTS',[driver,0]);nativeCall('TASK_VEHICLE_DRIVE_WANDER',[driver,h,bits(12),786603]);nativeCall('SET_PED_KEEP_TASK',[driver,1]);a[16008]=driver;nativeCall('SET_ENTITY_AS_NO_LONGER_NEEDED',[BigInt(base+64032)]);}
   if(wander===0){nativeCall('SET_BLOCKING_OF_NON_TEMPORARY_EVENTS',[h,0]);nativeCall('TASK_WANDER_STANDARD',[h,bits(10),10]);nativeCall('SET_PED_KEEP_TASK',[h,1]);}
   a[16008]=h;nativeCall('SET_ENTITY_AS_NO_LONGER_NEEDED',[BigInt(base+64032)]);};
  // leaving follower mode: the copies become ordinary population (cars drive on, pedestrians wander), nothing pops
  if(N.mode===2&&mode201!==2){for(const c of N.clones.values())release201(c.h,c.kind,c.driver);N.clones.clear();N.want.clear();N.seq=-1;}
  const base206=(()=>{const v=N.buf>0?new Int32Array(memory.buffer,N.buf,1024)[1000]|0:0;return v>=1&&v<=3?v:3;})();/* 206: chosen NPC/traffic density */if(N.budget!==(mode201===2?0:base206)){N.budget=mode201===2?0:base206;nativeCall('SET_PED_POPULATION_BUDGET',[N.budget]);}if(N.vbudget!==base206){N.vbudget=base206;nativeCall('SET_VEHICLE_POPULATION_BUDGET',[base206]);}
  N.mode=mode201;self.__npc201Mode=mode201;
  if(mode201===2){const z201=bits(0);nativeCall('SET_PED_DENSITY_MULTIPLIER_THIS_FRAME',[z201]);nativeCall('SET_SCENARIO_PED_DENSITY_MULTIPLIER_THIS_FRAME',[z201,z201]);nativeCall('SET_RANDOM_VEHICLE_DENSITY_MULTIPLIER_THIS_FRAME',[z201]);}
  const me201=coords(ped);
  // ---- host: report our own population (4 Hz)
  let listener201=false;for(let i=0,n=Math.min(32,Math.max(0,a[5]|0));i<n&&!listener201;i++){const o=128+i*64;listener201=!!a[o]&&Math.hypot(f[o+1]-me201[0],f[o+2]-me201[1])<400;}
  if(mode201===1&&listener201&&now-N.sampleAt>=333){N.sampleAt=now;const rows=[],r1=x=>Math.round(x*10)/10,r2=x=>Math.round(x*100)/100;
   if(a[16339]){const h=a[16339];a[16339]=0;if(e.pn_exists(h)&&!isMission201(h)&&!managed201.has(h)&&!playerIn201(h)){const d=e.pn_vehicle_seat(h,-1,0);if(d&&!isPlayer201(d))drop101(d);drop101(h,true);N.claims++;}}
   for(const h of nearCars201()){if(rows.length>=20)break;if(!h||managed201.has(h)||!e.pn_exists(h)||isMission201(h))continue;
    const p=coords(h);if(Math.hypot(p[0]-me201[0],p[1]-me201[1])>160)continue;/* 213: distance first */
    const driver=e.pn_vehicle_seat(h,-1,0);if(!driver||isPlayer201(driver)||copType201(driver)||playerIn201(h))continue;
    let col=N.cache.get(h);if(!col||col.length!==3||col[2]!==(e.pn_model(h)>>>0)){const out=new Int32Array(memory.buffer,base+64592,2);out.fill(0);nativeCall('GET_VEHICLE_COLOURS',[h,BigInt(base+64592),BigInt(base+64596)]);col=[out[0],out[1],e.pn_model(h)>>>0];N.cache.set(h,col);}
    const r=rot201(h),v=vel201(h);rows.push([h,1,e.pn_model(h)>>>0,...p.map(r2),...r.map(r1),...v.map(r2),e.pn_model(driver)>>>0,col[0],col[1],0]);}
   let nPed=0;for(const h of nearPeds201()){if(nPed>=24)break;if(!h||managed201.has(h)||!e.pn_exists(h)||isPlayer201(h)||isMission201(h)||e.pn_vehicle(h,0)||copType201(h))continue;
    const pt=pop201(h);if(pt<1||pt>6||!(nativeCall('GET_ENTITY_HEALTH',[h])>0))continue;
    const p=coords(h);if(Math.hypot(p[0]-me201[0],p[1]-me201[1])>120)continue;
    let look=N.cache.get(h);if(!look||look.length!==3||look.model!==(e.pn_model(h)>>>0)){look=[0,0,0];for(let k=0;k<12;k++){const d=Math.max(0,Math.min(31,nativeCall('GET_PED_DRAWABLE_VARIATION',[h,k])|0)),t=Math.max(0,Math.min(7,nativeCall('GET_PED_TEXTURE_VARIATION',[h,k])|0));look[k>>2]|=(d|t<<5)<<((k&3)*8);}look=look.map(x=>x>>>0);look.model=e.pn_model(h)>>>0;N.cache.set(h,look);}
    const v=vel201(h);rows.push([h,0,e.pn_model(h)>>>0,...p.map(r2),0,0,r1(e.pn_heading(h)),...v.map(r2),look[0],look[1],look[2],0]);nPed++;}
   if(N.cache.size>400)for(const k of N.cache.keys())if(!e.pn_exists(k))N.cache.delete(k);
   self.postMessage({pnNpc201:{seq:++N.sampleSeq,pos:me201.map(x=>Math.round(x*10)/10),rows}});}
  // ---- follower: copies of the host's population
  if(mode201===2){
   const bi=new Int32Array(memory.buffer,N.buf,1024),bf=new Float32Array(memory.buffer,N.buf,1024),seq=Atomics.load(bi,0);
   if(!(seq&1)&&seq!==N.seq){const rows=new Map(),n=Math.min(48,bi[1]|0);
    for(let i=0;i<n;i++){const o=8+i*20,kind=bi[o+2];if(kind!==0&&kind!==1)continue;
     const row={host:bi[o],handle:bi[o+1],kind,model:bi[o+3],pos:[bf[o+4],bf[o+5],bf[o+6]],rot:[bf[o+7],bf[o+8],bf[o+9]],vel:[bf[o+10],bf[o+11],bf[o+12]],x:[bi[o+13]>>>0,bi[o+14]>>>0,bi[o+15]>>>0,bi[o+16]>>>0],age:bf[o+17]};
     if([...row.pos,...row.rot,...row.vel,row.age].every(Number.isFinite))rows.set(row.host+':'+row.handle,row);}
    if(Atomics.load(bi,0)===seq){N.seq=seq;N.recvAt=now;for(const[k,r]of rows)N.want.set(k,{...r,seen:now});}}
   for(const[k,r]of N.want)if(now-r.seen>2500)N.want.delete(k);
   // a copied car the local player sits in is no longer a copy: keep it, ask the host to remove its own
   const inCar201=e.pn_vehicle(ped,0);
   for(const[k,c]of N.clones){const r=N.want.get(k);
    if(!e.pn_exists(c.h)){if(c.driver)drop101(c.driver);N.clones.delete(k);continue;}
    if(c.kind===1&&inCar201===c.h){N.clones.delete(k);N.claimed.add(k);a[16337]=c.host;a[16338]=c.handle;Atomics.add(a,16336,1);if(c.driver&&e.pn_exists(c.driver)){nativeCall('SET_BLOCKING_OF_NON_TEMPORARY_EVENTS',[c.driver,0]);}continue;}
    // gone from the host's report (it left the host's range): it carries on as our own population and leaves with
    // the sweep below once off screen, instead of vanishing in front of us
    if(!r){release201(c.h,c.kind,c.driver);N.clones.delete(k);}}
   // a claimed car stays ours even while the host still reports its original (until the host removes it)
   for(const k of N.claimed)if(!N.want.has(k))N.claimed.delete(k);
   let madeCar=0,madePed=0;
   for(const[k,r]of N.want){let c=N.clones.get(k);const age=Math.min(1.2,Math.max(0,(r.age+now-r.seen)/1000)),pred=r.pos.map((x,i)=>x+r.vel[i]*age);
    if(!c){if(N.claimed.has(k)||Math.hypot(pred[0]-me201[0],pred[1]-me201[1])>180)continue;
     if(r.kind===1){if(madeCar||!e.pn_vehicle_model(r.model)||!loaded(r.model)||(r.x[0]&&!loaded(r.x[0])))continue;
      vector(...pred);const h=e.pn_create_vehicle(r.model,ptr,r.rot[2],0,1,0);if(!h)continue;madeCar++;e.pn_mission_entity(h,1,1);
      if(r.x[1]<=160&&r.x[2]<=160)nativeCall('SET_VEHICLE_COLOURS',[h,r.x[1],r.x[2]]);nativeCall('SET_VEHICLE_ENGINE_ON',[h,1,1,0]);
      let driver=0;if(r.x[0]){vector(pred[0],pred[1],pred[2]+2);driver=e.pn_create_ped(4,r.x[0],ptr,r.rot[2],0,1);if(driver){e.pn_mission_entity(driver,1,1);nativeCall('SET_PED_INTO_VEHICLE',[driver,h,-1]);nativeCall('SET_BLOCKING_OF_NON_TEMPORARY_EVENTS',[driver,1]);e.pn_model_release(r.x[0]);}}
      vector(...r.rot);e.pn_set_rotation(h,ptr,2,1);vector(...r.vel);e.pn_set_velocity(h,ptr);e.pn_model_release(r.model);
      c={h,driver,kind:1,host:r.host,handle:r.handle,taskAt:0};N.clones.set(k,c);}
     else{if(madePed>=2||!loaded(r.model))continue;
      vector(...pred);const h=e.pn_create_ped(4,r.model,ptr,r.rot[2],0,1);if(!h)continue;madePed++;e.pn_mission_entity(h,1,1);
      for(let k2=0;k2<12;k2++){const v=(r.x[k2>>2]>>>((k2&3)*8))&255;nativeCall('SET_PED_COMPONENT_VARIATION',[h,k2,v&31,v>>5,0]);}
      nativeCall('SET_BLOCKING_OF_NON_TEMPORARY_EVENTS',[h,1]);nativeCall('SET_PED_KEEP_TASK',[h,1]);e.pn_model_release(r.model);
      c={h,driver:0,kind:0,host:r.host,handle:r.handle,taskAt:0,target:null};N.clones.set(k,c);}
     continue;}
    const cur=coords(c.h),d=Math.hypot(pred[0]-cur[0],pred[1]-cur[1],pred[2]-cur[2]);
    if(c.kind===1){
     if(!(d<10)){vector(...pred);e.pn_set_coords(c.h,ptr,1,1,1);vector(...r.rot);e.pn_set_rotation(c.h,ptr,2,1);vector(...r.vel);e.pn_set_velocity(c.h,ptr);continue;}
     const cmd=r.vel.map((v,i)=>v+(pred[i]-cur[i])*2),sp=Math.hypot(...cmd);if(sp>60)cmd.forEach((v,i)=>cmd[i]=v*60/sp);
     vector(...cmd);e.pn_set_velocity(c.h,ptr);const cr=rot201(c.h),wrap=x=>((x%360)+540)%360-180,yaw=wrap(r.rot[2]-cr[2]);
     nativeCall('SET_ENTITY_ANGULAR_VELOCITY',[c.h,bits(0),bits(0),bits(Math.max(-3,Math.min(3,yaw*2.5*Math.PI/180)))]);}
    else{
     if(!(Math.hypot(pred[0]-cur[0],pred[1]-cur[1])<6)){vector(...pred);e.pn_set_coords(c.h,ptr,1,1,1);e.pn_set_heading(c.h,r.rot[2]);c.target=null;continue;}
     const sp=Math.hypot(r.vel[0],r.vel[1]);
     if(sp<.25){if(c.target!=='still'){e.pn_clear_tasks(c.h);e.pn_set_heading(c.h,r.rot[2]);c.target='still';}}
     else{const tgt=pred.map((x,i)=>x+r.vel[i]*1.5);if(now-c.taskAt>600||!Array.isArray(c.target)||Math.hypot(tgt[0]-c.target[0],tgt[1]-c.target[1])>2){c.taskAt=now;c.target=tgt;
      nativeCall('TASK_GO_STRAIGHT_TO_COORD',[c.h,bits(tgt[0]),bits(tgt[1]),bits(tgt[2]),bits(sp>4.5?3:sp>2.2?2:1),2500,bits(r.rot[2]),bits(.5)]);}}}}
   // our own ambient traffic and pedestrians that were already there (or slipped in between ticks) leave: far ones at
   // once, near ones only while off screen
   if(now-N.sweepAt>=400){N.sweepAt=now;let left=6;
    const offScreen=p=>{vector(p[0],p[1],p[2]+1);return!e.pn_project(ptr,BigInt(base+64024),BigInt(base+64028));};
    for(const h of nearCars201()){if(!left)break;if(!h||managed201.has(h)||!e.pn_exists(h)||isMission201(h))continue;const driver=e.pn_vehicle_seat(h,-1,0);
     if(!driver||isPlayer201(driver)||copType201(driver)||playerIn201(h)||isMission201(driver))continue;const pt=pop201(h);if(pt!==1&&pt!==3&&pt!==5)continue;
     const p=coords(h);if(Math.hypot(p[0]-me201[0],p[1]-me201[1])<35&&!offScreen(p))continue;
     for(let seat=-1;seat<4;seat++){const o=e.pn_vehicle_seat(h,seat,0);if(o&&!isPlayer201(o))drop101(o);}drop101(h,true);N.removed++;left--;}
    for(const h of nearPeds201()){if(!left)break;if(!h||managed201.has(h)||!e.pn_exists(h)||isPlayer201(h)||isMission201(h)||e.pn_vehicle(h,0)||copType201(h))continue;
     const pt=pop201(h);if(pt!==1&&pt!==3&&pt!==4&&pt!==5)continue;const p=coords(h);if(Math.hypot(p[0]-me201[0],p[1]-me201[1])<35&&!offScreen(p))continue;
     drop101(h);N.removed++;left--;}}
  }
  a[16334]=N.clones.size;a[16335]=N.removed;
 }catch(error201){const N=self.__npc201;if(!N||++N.errors>=3)self.__npc201Off=true;a[16382]=0;console.warn('PAV npc201',error201?.stack||error201);}

 lap213('npc');
 /* 205: hunger/thirst damage. The page (needs205.js) adds the health points to lose to a[16383] (a running total);
  the difference since the last tick is taken from the native health, never below 115 and never while dead. */
 {const want205=a[16383]|0,N205=self.__starve205??={seen:want205};if(want205!==N205.seen){const d205=Math.max(0,Math.min(20,(want205-N205.seen)|0));N205.seen=want205;
  if(d205&&spawned&&!entryLocked){const hp205=e.pn_health(ped);if(hp205>115)e.pn_set_health(ped,Math.max(115,hp205-d205),0);}}}
 /* 210: crime and rescue in the engine. The page (crime210.js) writes cells of the 201 buffer: 1004 wanted seq, 1005
  level; 1006 animation seq, 1007 animation (1 kneel and work, 0 stop); 1008 part seq, 1009 server vehicle id, 1010
  part (0-3 door, 4-7 wheel); 1011 carried part (0 none, 1 door, 2 wheel); 1012 paramedic seq; 1013 component seq,
  1014 weapon hash, 1015 count, 1016-1019 component hashes; 1020 chop spot known, 1021-1023 its x, y, z. A native
  error turns the block off for this session. */
 if(!self.__c210Off)try{const N210=self.__npc201,C=self.__c210??={wanted:0,anim:0,part:0,medic:0,comp:0,compAt:0,comps:[],weapon:0,carry:0,carryAt:0,prop:0,medicPed:0,medicAt:0,medicWant:0};
  if(N210&&N210.buf>0){const ci=new Int32Array(memory.buffer,N210.buf,1024),cf=new Float32Array(memory.buffer,N210.buf,1024);
   if(ci[1004]!==C.wanted){C.wanted=ci[1004];const lv=Math.max(0,Math.min(5,ci[1005]|0));if(lv){const pid=e.pn_player_id();nativeCall('SET_PLAYER_WANTED_LEVEL',[pid,lv,0]);nativeCall('SET_PLAYER_WANTED_LEVEL_NOW',[pid,0]);}}
   if(ci[1006]!==C.anim){C.anim=ci[1006];if(ci[1007]===1&&!e.pn_vehicle(ped,0))nativeCall('TASK_START_SCENARIO_IN_PLACE',[ped,cstring('WORLD_HUMAN_WELDING',65400),0,1]);else e.pn_clear_tasks(ped);}
   if(ci[1008]!==C.part){C.part=ci[1008];const v210=vehicles.get(ci[1009]),pi=ci[1010]|0;
    if(v210&&e.pn_exists(v210.handle)){if(pi>=0&&pi<4)nativeCall('SET_VEHICLE_DOOR_BROKEN',[v210.handle,pi,1]);else if(pi>=4&&pi<8)nativeCall('SET_VEHICLE_TYRE_BURST',[v210.handle,[0,1,4,5][pi-4],1,bits(1000)]);}}
   const carry=ci[1011]|0;if(carry!==C.carry){if(C.prop){drop101(C.prop);C.prop=0;}C.carry=carry;C.carryAt=now;}
   if(C.carry&&!C.prop&&now-C.carryAt<10000){const m=hash(C.carry===1?'prop_car_door_01':'prop_wheel_01');
    if(e.pn_model_valid(m)&&loaded(m)){const p0=coords(ped),o=nativeCall('CREATE_OBJECT_NO_OFFSET',[m,...p0.map(bits),0,0,0]);
     if(o){e.pn_mission_entity(o,1,1);e.pn_collision(o,0,0);vector(0,.3,.05);s[12]=0;s[14]=0;s[16]=C.carry===1?90:0;e.pn_attach(o,ped,Math.max(0,nativeCall('GET_PED_BONE_INDEX',[ped,57005])),ptr,BigInt(base+64048),0,0,0,0,2,1,0);C.prop=o;e.pn_model_release(m);}}}
   if(ci[1012]!==C.medic){C.medic=ci[1012];C.medicWant=now;}
   if(C.medicWant&&!C.medicPed){const m=hash('s_m_m_paramedic_01');if(now-C.medicWant>5000)C.medicWant=0;
    else if(loaded(m)){const p0=coords(ped);vector(p0[0]+1.1,p0[1]+.4,p0[2]);const h=e.pn_create_ped(4,m,ptr,0,0,1);
     if(h){e.pn_mission_entity(h,1,1);nativeCall('SET_BLOCKING_OF_NON_TEMPORARY_EVENTS',[h,1]);nativeCall('TASK_START_SCENARIO_IN_PLACE',[h,cstring('CODE_HUMAN_MEDIC_TEND_TO_DEAD',65400),0,1]);C.medicPed=h;C.medicAt=now;e.pn_model_release(m);}C.medicWant=0;}}
   if(C.medicPed&&now-C.medicAt>14000){drop101(C.medicPed);C.medicPed=0;}
   if(ci[1013]!==C.comp||now-C.compAt>2000){C.comp=ci[1013];C.compAt=now;const w=ci[1014]>>>0,n=Math.max(0,Math.min(4,ci[1015]|0)),list=Array.from({length:n},(_,i)=>ci[1016+i]>>>0);
    if(w&&(e.pn_weapon(ped)>>>0)===w){if(C.weapon===w)for(const old of C.comps)if(!list.includes(old))nativeCall('REMOVE_WEAPON_COMPONENT_FROM_PED',[ped,w,old]);
     for(const c of list)if(!nativeCall('HAS_PED_GOT_WEAPON_COMPONENT',[ped,w,c]))nativeCall('GIVE_WEAPON_COMPONENT_TO_PED',[ped,w,c]);C.comps=list;C.weapon=w;}}
   if(ci[1020]===1&&[cf[1021],cf[1022],cf[1023]].every(Number.isFinite)){const x=cf[1021],y=cf[1022],z=cf[1023],dm=self.__pavDrawMarkers;
    if(dm&&!dm.c210)self.__pavDrawMarkers=Object.assign(()=>{dm();try{const mf=new Float32Array(memory.buffer,base,16384);if(Math.hypot(x-mf[16],y-mf[17])<70)self.__ring127(x,y,z,255,140,60);}catch{}},{c210:true});}}
 }catch(error210){self.__c210Off=true;console.warn('PAV crime210 off',error210?.stack||error210);}
 /* 212: down means down. While the server counts the player as unconscious (cell 1001 of the 201 buffer, written by
  crime211.js from every sync) the engine stood the ped back up after a while. 211 killed it again every 3 s, which
  replayed the death fade and the engine's respawn (dark/light flashes, the ped dropping from above). Now a ped that
  is up again stays alive but lies in a ragdoll, cannot be hurt and has no controls until the server revives it. */
 if(!self.__c210Off)try{const N212=self.__npc201;if(N212&&N212.buf>0){const ci212=new Int32Array(memory.buffer,N212.buf,1024),H212=self.__hold212??={at:0,on:false};
  const hold=ci212[1001]===1&&e.pn_health(ped)>100;
  if(hold){if(!H212.on){H212.on=true;e.pn_invincible(ped,1);}e.pn_controls_disable(0);if(now-H212.at>4000||!e.pn_is_ragdoll(ped)&&now-H212.at>600){H212.at=now;e.pn_ragdoll_task(ped,9000,9000,0,0,0,0);}}
  else if(H212.on){H212.on=false;e.pn_invincible(ped,0);}}}catch{}
 lap213('c210');
 /* 197: street props broken by a car are shared. While our car moves, the props of a fixed list within 9 m are seen
  4 times a second; one that breaks (HAS_OBJECT_BEEN_BROKEN), tips over (> 25 deg) or leaves its place (> 1 m) is
  reported once with the pose it had when first seen: ring a[16340] (count) + 4 entries of 4 cells at 16341 (model,
  x, y, z). The page sends it to the game server, which hands the broken props near each player back; the page
  queues them in ring a[16360] (written) / a[16361] (applied by us) with 4 entries of 5 cells at 16362 (model, x, y,
  z, op: 1 hide, 2 restore), and we hide (CREATE_MODEL_HIDE, 1.5 m) or restore that prop here. */
 {const P197=self.__props197??={seen:new Map(),scanAt:0,hashes:null,common:['prop_streetlight_01','prop_streetlight_01b','prop_streetlight_02','prop_traffic_01a','prop_traffic_01b','prop_traffic_03a','prop_fire_hydrant_1','prop_fire_hydrant_2','prop_bollard_02a','prop_sign_road_01a','prop_sign_road_03a','prop_parknmeter_01'].map(n=>modelHash23(n)|0)};
  if(!P197.hashes)P197.hashes=['prop_streetlight_01','prop_streetlight_01b','prop_streetlight_02','prop_streetlight_03','prop_streetlight_03b','prop_streetlight_03c','prop_streetlight_03d','prop_streetlight_03e','prop_streetlight_04','prop_streetlight_05','prop_streetlight_05_b','prop_streetlight_06','prop_streetlight_07a','prop_streetlight_07b','prop_streetlight_08','prop_streetlight_09','prop_streetlight_10','prop_streetlight_11a','prop_streetlight_11b','prop_streetlight_11c','prop_streetlight_12a','prop_streetlight_12b','prop_streetlight_14a','prop_streetlight_15a','prop_streetlight_16a','prop_traffic_01a','prop_traffic_01b','prop_traffic_01d','prop_traffic_02a','prop_traffic_02b','prop_traffic_03a','prop_traffic_03b','prop_fire_hydrant_1','prop_fire_hydrant_2','prop_fire_hydrant_4','prop_bollard_02a','prop_bollard_02b','prop_bollard_02c','prop_bollard_03a','prop_bollard_04','prop_bollard_05','prop_sign_road_01a','prop_sign_road_02a','prop_sign_road_03a','prop_sign_road_04a','prop_sign_road_05a','prop_sign_road_06a','prop_parknmeter_01','prop_parknmeter_02','prop_postbox_01a','prop_phonebox_01a','prop_phonebox_04','prop_news_disp_02a','prop_news_disp_03a','prop_bin_01a','prop_bin_05a','prop_bin_07a','prop_bin_08a','prop_busstop_02','prop_busstop_04','prop_busstop_05','prop_elecbox_01a','prop_elecbox_02a'].map(n=>modelHash23(n)|0);
  if((self.__props197Off|0)<3)try{
   const car197=e.pn_vehicle(ped,0);
   if(car197){e.pn_velocity(ptr,car197);const sp197=Math.hypot(s[0],s[2],s[4]),prev214=P197.speed??sp197;P197.speed=sp197;if(prev214>5&&prev214-sp197>2.5){P197.hit=coords(car197);P197.queue=P197.common.slice();}/* 214: only after an impact */}else P197.speed=0;
   if(P197.queue&&P197.queue.length){const c197=P197.hit;
     for(const h197 of P197.queue.splice(0,3)){const o197=nativeCall('GET_CLOSEST_OBJECT_OF_TYPE',[...c197.map(bits),bits(8),h197,0,0,0]);if(!o197||!e.pn_exists(o197))continue;
      const pos197=coords(o197);e.pn_rotation(ptr,o197,2);const tilt197=Math.max(Math.abs(s[0]),Math.abs(s[1]));let k197=P197.seen.get(o197);
      if(k197&&k197.sent){k197.at=now;continue;}
      const broken197=tilt197>25||!!nativeCall('HAS_OBJECT_BEEN_BROKEN',[o197,0]);
      if(broken197&&pos197.every(Number.isFinite)){P197.seen.set(o197,{h:h197,pos:pos197,at:now,sent:true});const n197=a[16340]|0,o4=16341+(n197%4)*4;a[o4]=h197;f.set(pos197,o4+1);a[16340]=n197+1;}}}
   if(P197.seen.size>400)for(const[o,k]of P197.seen)if(now-k.at>60000)P197.seen.delete(o);
   for(let g197=0;g197<8&&(a[16361]|0)<(a[16360]|0);g197++){const r197=a[16361]|0,o5=16362+(r197%4)*5,h=a[o5],x=f[o5+1],y=f[o5+2],z=f[o5+3],op=a[o5+4];
    if(h&&[x,y,z].every(Number.isFinite))nativeCall(op===2?'REMOVE_MODEL_HIDE':'CREATE_MODEL_HIDE',[bits(x),bits(y),bits(z),bits(3),h,1]);a[16361]=r197+1;}
  }catch(error197){self.__props197Off=(self.__props197Off|0)+1;if(self.__props197Off===1)console.error('PAV props197',error197?.stack||error197);}}
 lap213('props');mark51(5);if(now-doorCheckAt>100){doorCheckAt=now;a[114]=0;a[115]=-2;let nearestDoor=2.8,count=0;const local=coords(ped);Atomics.add(a,7500,1);
 if(!a[48]&&!a[62]){const nearbyIds=new Set(carStates.filter(v=>Math.hypot(v.pos[0]-local[0],v.pos[1]-local[1],v.pos[2]-local[2])<16).map(v=>v.id));const candidates=[...vehicles].filter(([id])=>nearbyIds.has(id)).slice(0,8).map(([id,v])=>({id,v,c:coords(v.handle)})).map(r=>({...r,d:Math.hypot(...r.c.map((c,i)=>c-local[i]))})).filter(r=>r.d<7).sort((a,b)=>a.d-b.d).slice(0,2);
 for(const {id,v} of candidates){const names=v.boat88?['seat_dside_f','seat_pside_f','seat_dside_r','seat_pside_r']:['door_dside_f','door_pside_f','door_dside_r','door_pside_r','bonnet','boot'];for(let i=0;i<names.length;i++){if(i<4&&i>=e.pn_vehicle_seats(e.pn_model(v.handle)))continue;const bone=e.pn_bone_index(v.handle,cstring(names[i]));if(bone<0)continue;e.pn_bone_position(ptr,v.handle,bone);const d=Math.hypot(s[0]-local[0],s[2]-local[1],s[4]-local[2]);if(d>3.5)continue;const visible=e.pn_project(ptr,BigInt(base+25240),BigInt(base+25244));if(!visible)continue;const o=7510+count*8;a[o]=id;a[o+1]=i;f[o+2]=f[6310];f[o+3]=f[6311];f[o+4]=d;a[o+5]=1;count++;if(i<4&&d<nearestDoor){nearestDoor=d;a[114]=id;a[115]=i-1;}}}}
 a[7501]=count;Atomics.add(a,7500,1);}
 const desired=a[48],desiredSeat=a[49];let ownCar=e.pn_vehicle(ped,0);
 // Reserving a seat is not proof that the car is stable. Let a bouncing car
 // settle under its own physics; retry briefly instead of holding it in the air.
 if(!entryLocked&&seatVersion!==a[50]){
  seatVersion=a[50];seatStarted=now;seatWarped=false;seatTask62=false;a[56]=0;
  if(!desired){seatExit46=ownCar&&[...vehicles.values()].some(v=>v.handle===ownCar)?ownCar:0;if(ownCar)e.pn_leave_vehicle(ped,ownCar,e.pn_speed(ownCar)>4?4160:0);else e.pn_clear_tasks(ped);}
 }
 if(!entryLocked&&desired&&seatVersion===a[50]&&!seatWarped){
  const v=vehicles.get(desired),seated=v&&e.pn_vehicle_seat(v.handle,desiredSeat,0)===ped;
  if(seated){seatWarped=true;}
  else if(v&&v.grounded!==false){
   const pose=entryPose62(v.handle),snapshot=carStates.find(row=>row.id===desired);
   // Remote replicas are frozen locally, so their native speed reads zero.
   if(snapshot?.driver&&snapshot.driver!==a[51]){pose.speed=Math.max(pose.speed,Math.hypot(...snapshot.velocity));pose.safe=pose.safe&&Number.isFinite(pose.speed)&&pose.speed<3;}
   a[14120]=desired;f[14121]=pose.tilt;f[14122]=pose.speed;
   if(desiredSeat+2>e.pn_vehicle_seats(e.pn_model(v.handle))){a[56]=2;seatWarped=true;}
   else if(!pose.safe){
    if(seatTask62||now-seatStarted>=4000){if(seatTask62)e.pn_clear_tasks(ped);a[56]=3;seatWarped=true;}
   }else if(!seatTask62){e.pn_enter_vehicle(ped,v.handle,8000,desiredSeat,1,8,0n);seatTask62=true;seatStarted=now;}
   else if(now-seatStarted>8500){e.pn_clear_tasks(ped);a[56]=4;seatWarped=true;}
  }else if(now-seatStarted>20000){a[56]=5;seatWarped=true;}
 }
 ownCar=e.pn_vehicle(ped,0);
 if(!entryLocked&&!desired&&ownCar&&ownCar===seatExit46&&seatVersion===a[50]&&now-seatStarted>3000){e.pn_leave_vehicle(ped,ownCar,16);seatStarted=now;ownCar=e.pn_vehicle(ped,0);}
 const carPair=[...vehicles].find(([id,v])=>v.handle===ownCar);
 if(ownCar&&!carPair){a[56]=1;}else if(!ownCar&&(!desired||![2,3,4,5].includes(a[56])))a[56]=0;
 // Ambient discovery is bounded and sampled, not performed per rendered frame.
 if(now-trafficCheckAt>350&&!a[62]){trafficCheckAt=now;a[7602]=0;for(const v of carStates){if(v.owner!==0||Math.hypot(v.pos[0]-f[16],v.pos[1]-f[17],v.pos[2]-f[18])>7)continue;const h=vehicles.get(v.id)?.handle;if(!h)continue;const driver=e.pn_vehicle_seat(h,-1,0);if(driver&&driver!==ped&&!entities.size){a[7602]=v.id;a[7603]=e.pn_model(h);a[7604]=Math.min(8,e.pn_vehicle_seats(a[7603]));break;}if(driver&&driver!==ped&&![...entities.values()].some(e=>e.handle===driver)){a[7602]=v.id;a[7603]=e.pn_model(h);a[7604]=Math.min(8,e.pn_vehicle_seats(a[7603]));break;}}const local=coords(ped),managed=new Set([...vehicles.values()].map(v=>v.handle));
  const pool=new Int32Array(memory.buffer,base+49152,1026);pool.fill(0);pool[0]=512;const count=Math.max(0,Math.min(512,e.pn_all_vehicles(BigInt(base+49152))));
  vector(...local);const closest=e.pn_closest_vehicle?e.pn_closest_vehicle(ptr,7,0,127):0;let candidate=0,distance=7.01,pickCost=Infinity;const trying=e.pn_vehicle_trying(ped),inside=ownCar&&!carPair?ownCar:0;
  for(let i=-3;i<count;i++){const h=i===-3?closest:i===-2?inside:i===-1?trying:pool[2+i*2];if(!h||managed.has(h)||!e.pn_exists(h))continue;const cls=e.pn_vehicle_class(h);if(cls===14||cls===15||cls===16||cls===21)continue;const c=coords(h),d=Math.hypot(...c.map((v,n)=>v-local[n]));if(d>7||h!==inside&&e.pn_speed(h)>=5)continue;let score=d;if(a[6254]&&h!==inside){vector(c[0],c[1],c[2]+.5);if(!e.pn_project(ptr,BigInt(base+25240),BigInt(base+25244)))continue;score=Math.hypot(f[6310]-f[6252],f[6311]-f[6253]);if(score>.22)continue;}if(score<pickCost){candidate=h;distance=d;pickCost=score;}}
  Atomics.add(a,6208,1);a[6209]=candidate;a[6224]=candidate===inside?1:0;a[6225]=-2;if(candidate===inside&&inside)for(let seat=-1;seat<7;seat++)if(e.pn_vehicle_seat(candidate,seat,0)===ped){a[6225]=seat;break;}
  if(candidate){a[6210]=e.pn_model(candidate);const lock=e.pn_vehicle_lock_status(candidate);a[6211]=lock===0||lock===1?0:1;f.set(coords(candidate),6212);f[6215]=e.pn_heading(candidate);f[6216]=e.pn_vehicle_body(candidate);a[6217]=Math.min(8,e.pn_vehicle_seats(a[6210]));const driver=e.pn_vehicle_seat(candidate,-1,0);a[6226]=driver&&driver!==ped?1:0;f[6223]=distance;
   const paint72=readPaint43(candidate);a[6230]=paint72?1:0;if(paint72)a.set(paint72,6231);
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
  const pos=coords(ownCar);e.pn_rotation(ptr,ownCar,2);const rotation=[s[0],s[1],s[2]];e.pn_velocity(ptr,ownCar);carSample=[...pos,e.pn_heading(ownCar),...rotation,s[0],s[2],s[4],e.pn_vehicle_body(ownCar)];if(actualSeat===-1)self.__trail172={id:carPair[0],h:ownCar,at:now};
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
 const phoneAnim116=(p,d,c,flag,ms)=>{const dp=cstring(d,65120),cp=cstring(c,65160);nativeCall('pn_v19_anim_request',[dp]);if(!nativeCall('pn_v19_anim_loaded',[dp]))return false;nativeCall('pn_v19_anim',[p,dp,cp,bits(4),bits(-4),ms,flag,bits(0),0,0,0]);return true;},phonePlaying116=(p,d,c)=>!!nativeCall('IS_ENTITY_PLAYING_ANIM',[p,cstring(d,65120),cstring(c,65160),3]);const call116=!!a[13930],wantPhone=!entryLocked&&e.pn_health(ped)>100&&!a[7830]&&!a[7831]&&(!!a[116]||call116),inCar116=!!e.pn_vehicle(ped,0),dict116=inCar116?'anim@cellphone@in_car@ps':'cellphone@',clip116=call116?'cellphone_call_listen_base':'cellphone_text_read_base';if(wantPhone!==phoneState){if(!wantPhone){phoneAnim116(ped,self.__phoneDict116||dict116,'cellphone_text_out',48,800);e.pn_destroy_phone();}phoneState=wantPhone;self.__phoneClip116='';self.__pavPhoneAt42=0;}
 if(wantPhone&&(self.__phoneClip116!==dict116+clip116||now-(self.__pavPhoneAt42||0)>1500)){self.__pavPhoneAt42=now;if((self.__phoneClip116!==dict116+clip116||!phonePlaying116(ped,dict116,clip116))&&phoneAnim116(ped,dict116,clip116,49,-1)){self.__phoneClip116=dict116+clip116;self.__phoneDict116=dict116;}}
 const wantHands=!entryLocked&&!!a[117]&&e.pn_health(ped)>100&&!ownCar;if(wantHands!==handsState){if(wantHands){e.pn_clear_tasks(ped);e.pn_select_weapon(ped,0xA2719263|0,1);e.pn_hands_up(ped,-1,0,-1,0);}else if(handsState)e.pn_clear_tasks(ped);handsState=wantHands;}
 // 128: the wallet is mirrored into the Story cash stats (SP0..SP2_TOTAL_CASH) so native shops and
 // services see the player's money. A native spend or pickup changes the stat: the difference is
 // added to cells 13992 (spent) / 13993 (gained) for the server to settle, and the stat is put back to
 // the wallet value. 13990 wallet target, 13991 its version (UI), 13994 version applied here.
 self.__cash128??={applied:0,last:0,at:0};const cash128=self.__cash128;
 if(now-cash128.at>=1000&&!a[62]&&!a[7610]&&!a[71]&&!a[72]){cash128.at=now;const stats128=['sp0_total_cash','sp1_total_cash','sp2_total_cash','mp0_wallet_balance','mp1_wallet_balance','bank_balance'].map(hash),out128=new Int32Array(memory.buffer,base+65500,1);
  if(a[13991]!==cash128.applied){cash128.applied=a[13991];cash128.last=Math.max(0,Math.min(2000000000,a[13990]|0));for(const h of stats128)nativeCall('STAT_SET_INT',[h,cash128.last,0]);a[13994]=cash128.applied;}
  else if(cash128.applied>0){let changed=false;for(const h of stats128){out128[0]=cash128.last;if(!nativeCall('STAT_GET_INT',[h,BigInt(base+65500),-1]))continue;const v=out128[0];if(v!==cash128.last){const d=v-cash128.last;if(d<0)Atomics.add(a,13992,Math.min(1000000,-d));else Atomics.add(a,13993,Math.min(1000000,d));changed=true;break;}}if(changed)for(const h of stats128)nativeCall('STAT_SET_INT',[h,cash128.last,0]);}
 }
 // A physical phone prop is independent of the stock phone UI.
 self.__phone85??={handle:0,ped:0,next:0};const phone85=self.__phone85;
 if(phone85.handle&&(!wantPhone||phone85.ped!==ped||!e.pn_exists(phone85.handle))){drop101(phone85.handle);phone85.handle=0;phone85.ped=0;}
 if(wantPhone&&!phone85.handle&&now>=phone85.next){phone85.next=now+500;const model=hash('prop_npc_phone_02');if(loaded(model)){const pos=coords(ped),obj=nativeCall('CREATE_OBJECT_NO_OFFSET',[model,...pos.map(bits),0,0,0]);if(obj){e.pn_mission_entity(obj,1,1);e.pn_collision(obj,0,0);const bone=nativeCall('GET_PED_BONE_INDEX',[ped,28422]);vector(0,0,0);s[12]=0;s[14]=0;s[16]=0;e.pn_attach(obj,ped,Math.max(0,bone),ptr,BigInt(base+64048),0,0,0,0,2,1,0);phone85.handle=obj;phone85.ped=ped;}e.pn_model_release(model);}}
 // Walk-in rooms need a streaming pin too; transitions retain their own ownership.
 self.__releaseRoom85=()=>{if(self.__room85?.id)nativeCall('UNPIN_INTERIOR',[self.__room85.id]);self.__room85.id=0;};self.__room85??={id:0,at:0,refreshed:false};const room85=self.__room85;
 // 107: portal edges made GET_INTERIOR_FROM_ENTITY alternate between a room and 0, so the
 // pin was dropped and REFRESH_INTERIOR re-ran every second — a visible lighting flash that
 // the property "lights on" point lights hid. Switch only after two equal samples, keep the
 // pin 10 s across a 0, and refresh one interior at most every two minutes.
 room85.refreshAt??=new Map();
 if(now-room85.at>=1000){room85.at=now;const id=!a[62]&&!a[6500]&&!a[7701]?nativeCall('GET_INTERIOR_FROM_ENTITY',[ped]):0;
  if(id===room85.id){room85.pending=undefined;if(id)room85.seen=now;}
  else if(room85.pending!==id)room85.pending=id;
  else if(id||now-(room85.seen??0)>10000){room85.pending=undefined;if(room85.id)nativeCall('UNPIN_INTERIOR',[room85.id]);room85.id=0;room85.refreshed=false;if(id&&nativeCall('IS_VALID_INTERIOR',[id])){room85.id=id;room85.seen=now;nativeCall('PIN_INTERIOR_IN_MEMORY',[id]);}}
  if(room85.id&&!room85.refreshed&&nativeCall('IS_INTERIOR_READY',[room85.id])){if(now-(room85.refreshAt.get(room85.id)??-Infinity)>=120000){nativeCall('REFRESH_INTERIOR',[room85.id]);room85.refreshAt.set(room85.id,now);}room85.refreshed=true;}
 }
 // Render a local showroom object without changing ownership or player loadout.
 // World simulation and peer sampling continue after this block.
 if(a[6500]){
  const mode=a[6500],requested=a[6501],assetModel=mode===2?modelOf(0):requested;
  if(showroomHash!==requested||showroomMode!==mode){
   if(showroomHandle)drop101(showroomHandle,showroomMode===1);
   showroomHandle=0;showroomHash=requested;showroomMode=mode;a[6503]=0;
  }
  if(!showroomHandle&&loaded(assetModel)){
   const origin85=coords(ped),position=mode===1&&Math.hypot(origin85[0]+48,origin85[1]+1098)<100?[-49,-1098,26.4]:origin85;vector(position[0]+6,position[1],position[2]+3);e.pn_collision_request(ptr);a[16236]=0;
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
  if(showroomHandle)drop101(showroomHandle,showroomMode===1);
  showroomHandle=0;showroomHash=0;showroomMode=0;a[6503]=0;e.pn_focus_ped(ped);e.pn_follow_ped(ped);e.pn_follow_mode(1);e.pn_follow_heading(0);
 }


 // The workshop camera observes the real selected car and owns no vehicle pose.
 const cameraCar72=a[12800]&&!a[62]&&!a[6500]&&!preview&&vehicles.get(a[12801]);
 if(cameraCar72&&e.pn_exists(cameraCar72.handle)){
  if(!customCam72)customCam72=e.pn_cam_create(cstring('DEFAULT_SCRIPTED_CAMERA'),1);
  const p72=coords(cameraCar72.handle),angle72=(Number.isFinite(f[12802])?f[12802]:45)*Math.PI/180,dist72=Math.max(3,Math.min(9,f[12803]||5));
  vector(p72[0]+Math.sin(angle72)*dist72,p72[1]+Math.cos(angle72)*dist72,p72[2]+1.15);e.pn_cam_set(customCam72,ptr);vector(p72[0],p72[1],p72[2]+.45);e.pn_cam_point(customCam72,ptr);e.pn_cam_fov(customCam72,48);e.pn_cam_render(1,1,200,1,0,0);
 }else if(customCam72){e.pn_cam_render(0,1,200,1,0,0);e.pn_cam_destroy(customCam72,1);customCam72=0;a[12804]=0;for(const v of vehicles.values())v.mods=null;}
 // A capability probe must visibly change the getter before a kit can be sold.
 if(a[13250]&&a[13250]!==self.__airProbeSeq72){self.__airProbeSeq72=a[13250];const item=vehicles.get(a[13251]);a[13252]=0;
  if(item&&item.grounded!==false&&entryPose62(item.handle).safe){const h=item.handle,read=wheel=>{const raw=nativeCall('GET_HYDRAULIC_SUSPENSION_RAISE_FACTOR',[h,wheel]);return new Float32Array(new Int32Array([raw]).buffer)[0];};
   const old=[0,1,2,3].map(read);nativeCall('SET_CAN_USE_HYDRAULICS',[h,1]);nativeCall('SET_HYDRAULIC_SUSPENSION_RAISE_FACTOR',[h,0,bits(.55)]);airProbe72={h,read,old,at:now,seq:a[13250]};
  }else a[13252]=-1;
 }
 if(airProbe72&&now-airProbe72.at>400){const p72=airProbe72,exists72=e.pn_exists(p72.h),actual72=exists72?p72.read(0):NaN;if(a[13250]===p72.seq)a[13252]=Number.isFinite(actual72)&&Math.abs(actual72-.55)<.04&&Math.abs(actual72-p72.old[0])>.04?1:-1;if(exists72)for(let wheel=0;wheel<4;wheel++)nativeCall('SET_HYDRAULIC_SUSPENSION_RAISE_FACTOR',[p72.h,wheel,bits(Number.isFinite(p72.old[wheel])?p72.old[wheel]:0)]);airProbe72=null;}

 // Existing native GPS owns road routing. Sample only128points once/second.
 if(a[6650]!==self.__pavWaypointEpoch){self.__pavWaypointEpoch=a[6650];if(a[6651]){nativeCall('pn_v20_force_gps',[1]);nativeCall('pn_v19_waypoint',[bits(f[6652]),bits(f[6653])]);}else{nativeCall('pn_v19_waypoint_off');nativeCall('pn_v20_force_gps',[0]);}self.__pavRouteAt=0;}
 if(a[6651]&&now-(self.__pavRouteAt||0)>1000){self.__pavRouteAt=now;const origin=coords(ped),step=Math.max(20,Math.hypot(f[6652]-origin[0],f[6653]-origin[1])/80);let count=0,last=null;Atomics.add(a,6700,1);for(let n=0;n<128;n++){const out=BigInt(base+64704);new Float32Array(memory.buffer,Number(out),6).fill(0);if(!nativeCall('pn_v19_gps_point',[out,1,bits(n*step),0]))break;const reference=Array.from(new Float32Array(memory.buffer,base+60064,3)),point=new Float32Array(memory.buffer,Number(out),6),variants=[reference,[point[0],point[1],point[2]],[point[0],point[2],point[4]]];if(n===0){const viable=variants.map((v,i)=>({i,v,d:Math.hypot(...v.map((x,j)=>x-origin[j]))})).filter(o=>o.v.every(Number.isFinite)&&o.v.some(x=>Math.abs(x)>.0001));viable.sort((a,b)=>a.d-b.d);self.__pavGpsLayout=viable[0]?.i??0;}const xyz=variants[self.__pavGpsLayout??0];if(!xyz.every(Number.isFinite)||last&&Math.hypot(...xyz.map((x,i)=>x-last[i]))<.05)break;f.set(xyz,6702+count*3);count++;last=xyz;}a[6701]=count;Atomics.add(a,6700,1);}else if(!a[6651])a[6701]=0;
 // A finite, requested native animation. Clear only this task on completion.
 const kind=entryLocked?0:a[6600],actionSeq=a[6601];if(actionSeq!==self.__pavActionSeq){self.__pavActionSeq=actionSeq;self.__pavActionStarted=false;if(!kind&&self.__pavActionActive){e.pn_clear_tasks(ped);self.__pavActionActive=false;}}
 if(kind&&!self.__pavActionStarted){const extra72={6:['amb@world_human_picnic@male@base','base'],7:['amb@world_human_leaning@male@wall@back@hands_together@base','base'],8:['friends@frj@ig_1','wave_a'],9:['misslamar1dead_body','dead_idle']};const dict=extra72[kind]?.[0]||(kind===1?'mp_player_inteat@burger':kind===2?'mp_player_intdrink':kind===4?'weapons@pistol@combat_pistol':kind===5?'mini@repair':'clothingtie'),clip=extra72[kind]?.[1]||(kind===1?'mp_player_int_eat_burger':kind===2?'loop_bottle':kind===4?'reload_aim':kind===5?'fixing_a_ped':'try_tie_positive_a');const dp=cstring(dict,60800,96),cp=cstring(clip,60896,64);nativeCall('pn_v19_anim_request',[dp]);if(nativeCall('pn_v19_anim_loaded',[dp])){nativeCall('pn_v19_anim',[ped,dp,cp,bits(3),bits(-3),Math.max(500,a[6602]),kind>=6?1:49,bits(0),0,0,0]);self.__pavActionStarted=true;self.__pavActionActive=true;}}
 if(!entryLocked&&a[6604]!==self.__pavReloadSeq){self.__pavReloadSeq=a[6604];if(a[6604]){nativeCall('pn_v19_clip',[ped,a[103],Math.min(a[7120]||30,a[104])]);}}
 if(a[6660]!==self.__pavInteriorSeq){self.__pavInteriorSeq=a[6660];if(a[6661])nativeCall('pn_v19_ipl',[cstring('ex_dt1_02_office_02b',65200)]);}

 // Recon moves only a camera. Keep the actor at their saved position.
 const recon72=!!a[13300]&&!a[62]&&!preview&&!a[6500];
 if(recon72){
  reconActive72=true;reconReturn72=0;e.pn_freeze(ped,1);e.pn_invincible(ped,1);e.pn_collision(ped,0,0);nativeCall('SET_ENTITY_VISIBLE',[ped,0,0]);
  if(!reconCam72)reconCam72=e.pn_cam_create(cstring('DEFAULT_SCRIPTED_CAMERA'),1);
  const target72=[f[13304],f[13305],f[13306]],angle72=(f[13307]||0)*Math.PI/180;
  if(target72.every(Number.isFinite)){nativeCall('SET_FOCUS_POS_AND_VEL',[...target72.map(bits),bits(0),bits(0),bits(0)]);vector(...target72);e.pn_collision_request(ptr);vector(target72[0]+Math.sin(angle72)*5,target72[1]+Math.cos(angle72)*5,target72[2]+2);e.pn_cam_set(reconCam72,ptr);vector(target72[0],target72[1],target72[2]+.5);e.pn_cam_point(reconCam72,ptr);e.pn_cam_fov(reconCam72,55);e.pn_cam_render(1,0,0,1,0,0);}
 }else if(reconActive72||reconReturn72){
  if(reconActive72){reconActive72=false;reconReturn72=now;e.pn_focus_ped(ped);if(reconCam72){e.pn_cam_render(0,0,0,1,0,0);e.pn_cam_destroy(reconCam72,1);reconCam72=0;}}
  vector(...coords(ped));e.pn_collision_request(ptr);const returnReady72=now-reconReturn72>500&&e.pn_collision_ready(ped);
  e.pn_freeze(ped,returnReady72?0:1);e.pn_invincible(ped,returnReady72?(a[6400]?1:0):1);e.pn_collision(ped,1,1);nativeCall('SET_ENTITY_VISIBLE',[ped,1,0]);if(returnReady72)reconReturn72=0;
 }
 if(a[12849]&&a[12849]!==self.__rested72){self.__rested72=a[12849];nativeCall('RESTORE_PLAYER_STAMINA',[e.pn_player_id(),bits(1)]);}
 const xyz=coords(ped),heading=e.pn_heading(ped),speed=e.pn_speed(ped),health=e.pn_health(ped);
 e.pn_velocity(ptr,ped);const velocity=[s[0],s[2],s[4]];e.pn_cam_coord(ptr);const camera=[s[0],s[2],s[4]];e.pn_cam_rot(ptr,2);const pitch=s[0]*Math.PI/180,yaw=s[4]*Math.PI/180;
 const aim=[camera[0]-Math.sin(yaw)*Math.cos(pitch)*80,camera[1]+Math.cos(yaw)*Math.cos(pitch)*80,camera[2]+Math.sin(pitch)*80];
 if(!entryLocked&&e.pn_is_melee(ped))meleeUntil=now+250;{const n154=self.__shotN154|0,d154=(n154-(self.__shotSeen154|0))|0;if(d154>0&&!entryLocked){shootUntil=Math.max(shootUntil,now+180);self.__shotSend154=now+300;self.__shotSent154=((self.__shotSent154|0)+Math.min(d154,32))&0xffff;}self.__shotSeen154=n154;const m154=!entryLocked&&!!nativeCall('IS_PED_PERFORMING_MELEE_ACTION',[ped]);if(m154&&!self.__swingOn154)self.__swingN154=((self.__swingN154|0)+1)&0xffff;self.__swingOn154=m154;}if(!entryLocked&&e.pn_shooting(ped))shootUntil=now+180;const shooting=now<shootUntil,flags=entryLocked?0:(shooting||now<(self.__shotSend154||0)?1:0)|(e.pn_aiming(e.pn_player_id())?2:0)|(e.pn_jumping(ped)?4:0)|(e.pn_reloading(ped)?8:0)|(e.pn_is_ragdoll(ped)?16:0)|(now<meleeUntil?32:0)|(wantPhone?64:0)|(wantHands?128:0)|(()=>{/* 203: our radio station while we drive */try{const c=e.pn_vehicle(ped,0);if(!c||e.pn_vehicle_seat(c,-1,0)!==ped)return 0;return(((nativeCall('GET_PLAYER_RADIO_STATION_INDEX')|0)+1)&255)<<16;}catch{return 0;}})();
 const own=[...xyz,heading,speed,health,...velocity];if(!own.every(Number.isFinite))throw Error('Geçersiz motor konumu.');
 if(!entryLocked&&a[103]&&a[6608]===a[102]&&!a[62]&&!a[6600]&&!a[116]&&!a[117]&&e.pn_health(ped)>100&&now-(self.__pavEquipAt||0)>500&&(e.pn_weapon(ped)>>>0)!==(a[103]>>>0)){self.__pavEquipAt=now;e.pn_select_weapon(ped,a[103],1);}
 if(a[103]&&self.__pavTint!==ped+':'+a[103]+':'+a[7100]){nativeCall('pn_v20_tint',[ped,a[103],a[7100]]);self.__pavTint=ped+':'+a[103]+':'+a[7100];}const weapon=e.pn_weapon(ped);a[16020]=0;const clipOK=e.pn_clip(ped,weapon,BigInt(base+64080));const ammo=e.pn_ammo(ped,weapon),stamina=e.pn_stamina(e.pn_player_id()),safezone=e.pn_safezone();
 const projectHead=h=>{s[12]=0;s[14]=0;s[16]=0;const root=coords(h);e.pn_head(BigInt(base+64096),h,0x796e,BigInt(base+64048));const head=new Float32Array(memory.buffer,base+64096,6);self.__pavHeadHeights??=new Map();let height=self.__pavHeadHeights.get(h);if(height===undefined){height=Math.max(.6,Math.min(1.9,head[4]-root[2]));self.__pavHeadHeights.set(h,height);if(self.__pavHeadHeights.size>100)self.__pavHeadHeights.delete(self.__pavHeadHeights.keys().next().value);}const seated=!!e.pn_vehicle(h,0),bone=[head[0],head[2],head[4]],valid=bone.every(Number.isFinite)&&Math.hypot(bone[0]-root[0],bone[1]-root[1],bone[2]-root[2])<5;let tag164=seated&&valid?[bone[0],bone[1],bone[2]+.25]:[root[0],root[1],root[2]+height+.20];
  {const now164=performance.now(),mv164=self.__tagMv164??=new Map(),car164=seated?e.pn_vehicle(h,0):0,key164=car164||h,at164=car164?coords(car164):root,prev164=mv164.get(key164);
   if(self.__tagTick164!==tickStart51){self.__tagDt164=Math.min(.1,Math.max(.015,(tickStart51-(self.__tagTick164??tickStart51-33))/1000));self.__tagTick164=tickStart51;}
   if(!prev164||now164-prev164.t>250)mv164.set(key164,{p:at164,t:now164,v:[0,0,0]});
   else if(now164-prev164.t>=8){const dt=(now164-prev164.t)/1000,raw=at164.map((c,i)=>(c-prev164.p[i])/dt),ok=Math.hypot(...raw)<90;prev164.v=ok?prev164.v.map((x,i)=>x+(raw[i]-x)*.5):[0,0,0];prev164.p=at164;prev164.t=now164;}
   const v164=mv164.get(key164).v,lag164=0;tag164=tag164.map((c,i)=>c-v164[i]*lag164);
   if(mv164.size>120)mv164.delete(mv164.keys().next().value);}
  vector(tag164[0],tag164[1],tag164[2]);return e.pn_project(ptr,BigInt(base+64024),BigInt(base+64028));};
 const ownVisible=projectHead(ped),headXY=[s[6],s[7]];
 const info=new BigUint64Array(memory.buffer,base+64400,4),args=new BigUint64Array(memory.buffer,base+64432,4);info.fill(0n);info[2]=BigInt(base+64432);for(let i=0;i<4;i++)args[i]=BigInt(base+64320+i*4);e.pn_hud_minimap(BigInt(base+64400));const map=new Float32Array(memory.buffer,base+64320,4);
 if(!(map[2]>.02&&map[3]>.02)){e.pn_minimap_position(BigInt(base+64560));e.pn_minimap_size(BigInt(base+64576));const pos=new Float32Array(memory.buffer,base+64560,2),size=new Float32Array(memory.buffer,base+64576,2);if(size[0]>.02&&size[1]>.02)map.set([pos[0],pos[1],size[0],size[1]]);}
 a[67]=e.pn_armor(ped);
 Atomics.add(a,4,1);f.set(own,16);a[25]=weapon;a[26]=a[7612]?0:flags;const meleePed=e.pn_melee_target(ped),targetEntry=[...entities].find(([id,v])=>v.handle===meleePed);if(targetEntry)meleeTarget=targetEntry[0];a[106]=!a[7612]&&now<meleeUntil?meleeTarget:0;f.set(aim,27);a[30]=Math.max(0,ammo);a[31]=clipOK?Math.max(0,a[16020]):0;f[32]=Math.max(0,Math.min(100,100-stamina));f[33]=safezone;a[34]=ownVisible;f.set(headXY,35);f.set([map[0],map[1]],38);f.set([map[2],map[3]],52);a[54]=carPair?.[0]||0;a[55]=actualSeat;f.set(carSample,2880);{const t172=self.__trail172;let id172=0;if(t172&&t172.h!==ownCar&&now-t172.at<5000&&e.pn_exists(t172.h)){const p172=coords(t172.h);e.pn_rotation(ptr,t172.h,2);const r172=[s[0],s[1],s[2]];e.pn_velocity(ptr,t172.h);const v172=[s[0],s[2],s[4]];if(Math.hypot(...v172)>.3&&[...p172,...r172,...v172].every(Number.isFinite)){id172=t172.id;f.set([...p172,e.pn_heading(t172.h),...r172,...v172,e.pn_vehicle_body(t172.h)],16311);}else self.__trail172=null;}else if(t172&&t172.h!==ownCar)self.__trail172=null;a[16310]=id172;}a.fill(0,2891,2903);if(paintSample43){a[2891]=43;a[2892]=carPair[0];a.set(paintSample43,2893);}a[15900]=self.__shotSent154|0;a[15902]=self.__swingN154|0;Atomics.store(a,3,ped);Atomics.store(a,2,1);Atomics.add(a,4,1);

 mark51(6);// Only four nearby service attendants share one streamed model. Native ground
 // readiness precedes creation; no distant ped pool or per-frame pose reset.
 const nearServices=[];for(let i=0;i<Math.min(24,a[107]);i++){const o=6000+i*8,id=a[o];if(!id)continue;const d=Math.hypot(f[o+1]-f[16],f[o+2]-f[17],f[o+3]-f[18]);if(d<55)nearServices.push({id,x:f[o+1],y:f[o+2],z:f[o+3],d});}
for(let i=0;i<Math.min(24,a[107]);i++){const o=6000+i*8;if(!a[o]||a[o+4]!==361)continue;const d=Math.hypot(f[o+1]-f[16],f[o+2]-f[17],f[o+3]-f[18]);if(d<90)nativeCall('pn_v20_marker',[1,bits(f[o+1]),bits(f[o+2]),bits(f[o+3]-1),bits(0),bits(0),bits(0),bits(0),bits(0),bits(0),bits(14),bits(14),bits(.45),255,179,107,d<12?105:65,0,0,2,0,0n,0n,0]);}if(!a[62])for(const v of nearServices.filter(v=>v.d<18).slice(0,4))nativeCall('pn_v20_marker',[1,bits(v.x),bits(v.y),bits(v.z-.9),bits(0),bits(0),bits(0),bits(0),bits(0),bits(0),bits(.6),bits(.6),bits(.18),176,235,121,150,0,0,2,0,0n,0n,0]);
 // 107: the old pass scanned the object pool for 17 door models in one tick whenever a
 // service was within 35 m (field phase-6 peaks of 158 ms) and skipped shops missing from
 // the service list. Now one model is scanned per 150 ms, found doors are cached and only
 // doors within 18 m are re-asserted; every barber/shop door in the world qualifies and the
 // room behind it is enabled/uncapped if Story had closed it.
 self.__doors107??={i:0,at:-Infinity,assertAt:-Infinity,cache:new Map()};const doors107=self.__doors107;
 const doorModels107=['v_ilev_gunshopdoor','v_ilev_gunshopdoor_r','v_ilev_gc_door04','v_ilev_gc_door03','v_ilev_gc_door01','v_ilev_gc_door02','v_ilev_bs_door','v_ilev_bs_door01','v_ilev_hd_door_l','v_ilev_hd_door_r','v_ilev_ta_door','v_ilev_ss_door01','v_ilev_ss_door02','v_ilev_store_door','v_ilev_cs_door01','v_ilev_cs_door01r','v_ilev_clothmiddoor','v_ilev_clothmiddoor2','v_ilev_clothlowdoor','v_ilev_clothlowdoor2','v_ilev_ch_glassdoor','v_ilev_247door','v_ilev_247door_r','v_ilev_gasdoor','v_ilev_gasdoor_r','v_ilev_ml_door1'];
 if(!a[62]&&!a[6500]){
  if(now-doors107.at>=150){doors107.at=now;const model=modelHash23(doorModels107[doors107.i++%doorModels107.length]),h=nativeCall('GET_CLOSEST_OBJECT_OF_TYPE',[bits(f[16]),bits(f[17]),bits(f[18]),bits(25),model,0,0,0]);
   if(h&&e.pn_exists(h)&&!doors107.cache.has(h)&&doors107.cache.size<24)doors107.cache.set(h,{model,pos:coords(h),door:0,room:false});}
  if(now-doors107.assertAt>=400){doors107.assertAt=now;
   for(const [h,d] of doors107.cache){const dist=Math.hypot(...d.pos.map((x,i)=>x-f[16+i]));if(dist>45||!e.pn_exists(h)){doors107.cache.delete(h);continue;}if(dist>18)continue;const open=dist<3?1:0;
    e.pn_freeze(h,0);nativeCall('SET_STATE_OF_CLOSEST_DOOR_OF_TYPE',[d.model,...d.pos.map(bits),0,bits(open),0]);
    if(!d.door){a[16272]=0;if(nativeCall('DOOR_SYSTEM_FIND_EXISTING_DOOR',[...d.pos.map(bits),d.model,BigInt(base+65088)])){const inline=a[15016]>>>0;d.door=a[16272]>>>0||(inline!==((base+65088)>>>0)?inline:0);}}
    if(d.door){nativeCall('DOOR_SYSTEM_SET_DOOR_STATE',[d.door,0,0,1]);nativeCall('DOOR_SYSTEM_SET_OPEN_RATIO',[d.door,bits(open),0,1]);}
    if(!d.room){d.room=true;const room=nativeCall('GET_INTERIOR_AT_COORDS',d.pos.map(bits));if(room&&nativeCall('IS_VALID_INTERIOR',[room])){if(nativeCall('IS_INTERIOR_DISABLED',[room]))nativeCall('DISABLE_INTERIOR',[room,0]);if(nativeCall('IS_INTERIOR_CAPPED',[room]))nativeCall('CAP_INTERIOR',[room,0]);}}}
  }
  a[13912]=doors107.cache.size;
 }
 nearServices.sort((x,y)=>(x.d-(serviceNpcs.has(x.id)?8:0))-(y.d-(serviceNpcs.has(y.id)?8:0))||x.id-y.id);const wantedNpcs=[];for(const v of nearServices){if(wantedNpcs.length>=4)break;if(!wantedNpcs.some(n=>n.id===v.id||Math.hypot(n.x-v.x,n.y-v.y,n.z-v.z)<1.6))wantedNpcs.push(v);}const wantedIds=new Set(wantedNpcs.map(v=>v.id));
 for(const [id,npc] of serviceNpcs)if(!wantedIds.has(id)){drop101(npc.handle);serviceNpcs.delete(id);}
 let madeNpc=false;const npcModel=hash('a_m_m_business_01');Atomics.add(a,3001,1);let seenNpc=0;
 for(const v of wantedNpcs){let npc=serviceNpcs.get(v.id);if(npc&&!e.pn_exists(npc.handle)){serviceNpcs.delete(v.id);npc=null;}
  if(!npc&&!madeNpc&&now-(self.__npcAt107??-Infinity)>=400&&loaded(npcModel)){vector(v.x,v.y,v.z+.25);e.pn_collision_request(ptr);f[16236]=NaN;if(e.pn_ground(ptr,BigInt(base+64944),0,1)&&Number.isFinite(f[16236])&&Math.abs(f[16236]+1-v.z)<.8){const floor42=f[16236];vector(v.x,v.y,floor42+.05);const handle=e.pn_create_ped(4,npcModel,ptr,180,0,1);if(handle){vector(v.x,v.y,floor42+1);e.pn_set_coords(handle,ptr,1,1,1);npc={handle};serviceNpcs.set(v.id,npc);madeNpc=true;self.__npcAt107=now;e.pn_mission_entity(handle,1,1);e.pn_block_events(handle,1);e.pn_invincible(handle,1);e.pn_clear_tasks(handle);e.pn_freeze(handle,1);e.pn_collision(handle,0,0);e.pn_model_release(npcModel);}}}
  if(!npc){if(v.d<=18){vector(v.x,v.y,v.z+1.2);const visible=e.pn_project(ptr,BigInt(base+64024),BigInt(base+64028)),o=3010+seenNpc*8;a[o]=v.id;a[o+1]=visible;f[o+2]=s[6];f[o+3]=s[7];f[o+4]=v.d;seenNpc++;}continue;}const pos=coords(npc.handle),o=3010+seenNpc*8,visible=projectHead(npc.handle);a[o]=v.id;a[o+1]=visible;f[o+2]=s[6];f[o+3]=s[7];f[o+4]=Math.hypot(...pos.map((x,i)=>x-f[16+i]));seenNpc++;
 }Atomics.store(a,3000,seenNpc);Atomics.add(a,3001,1);
 if(!entryLocked&&!a[62]&&!a[6500]&&e.pn_health(ped)>100){restraint34(ped,!!a[7830],!!a[7831],self.__pavOwnRestraint34);if(a[7831])e.pn_freeze(ped,1);}
 const sequence=Atomics.load(a,6),peers=[];if(sequence&1)return;
 for(let i=0;i<Math.min(32,Atomics.load(a,5));i++){const o=128+i*64;peers.push({o,id:a[o],x:f[o+1],y:f[o+2],z:f[o+3],heading:f[o+4],speed:f[o+5],health:f[o+6],vx:f[o+7],vy:f[o+8],vz:f[o+9],weapon:a[o+10],flags:a[o+11],aim:[f[o+12],f[o+13],f[o+14]],vehicle:a[o+15],seat:a[o+16],version:a[o+17],damage:a[o+18],damageKind:a[o+19],tint:a[o+58],armor:a[o+60],meleeTarget:a[o+61],carriedBy:a[o+62],fly:!!a[o+63],cuffed:!(a[o+11]&256)&&a[7840+i*4]===a[o]&&!!a[7841+i*4],prone:!(a[o+11]&256)&&a[7840+i*4]===a[o]&&!!a[7842+i*4],ambient:!!(a[o+11]&256),model:(a[o+11]&256)?a[o+19]:modelOf(a[o+20])});}
 if(sequence!==Atomics.load(a,6))return;if(sequence!==peerSequence){peerSequence=sequence;receivedAt=now;}const prediction=Math.min(.35,Math.max(0,(now-receivedAt)/1000));
 const active=new Set(peers.map(p=>p.id));
 const remove=entity=>{
  if(entity.blip){a[16008]=entity.blip;e.pn_remove_blip(BigInt(base+64032));entity.blip=0;}
  if(!e.pn_exists(entity.handle))return true;
  entity.retiring38=true;if(now-(entity.deleteAt38??-Infinity)<500)return false;
  entity.deleteAt38=now;if(entity.phone130){drop101(entity.phone130);entity.phone130=0;}return drop101(entity.handle);
 };
 // Keep a briefly omitted ambient replica alive across ranking boundaries.
 // Real player departures remain immediate; retained ambient slots never exceed six.
 let retained86=0;
 for(const [id,entity] of entities)if(!active.has(id)){
  const keep86=entity.ambient86&&now-entity.lastSeen86<1600&&retained86<6&&active.size+retained86<32;
  if(keep86){retained86++;continue;}
  if(remove(entity)){entities.delete(id);attempts.delete(id);}
 }
 let created=false;Atomics.add(a,9,1);let observed=0;
 mark51(7);for(const p of peers){
  if(!p.id||![p.x,p.y,p.z,p.heading,p.health,...p.aim].every(Number.isFinite))continue;
  let entity=entities.get(p.id);if(entity&&entity.model!==p.model){if(!remove(entity))continue;entities.delete(p.id);entity=null;}
  if(!entity||!e.pn_exists(entity.handle)){
   if(created||!loaded(p.model)||now-(attempts.get(p.id)??-Infinity)<1000)continue;attempts.set(p.id,now);vector(p.x,p.y,p.z);const handle=e.pn_create_ped(4,p.model,ptr,p.heading,0,1);if(!handle)continue;
   created=true;entity={handle,model:p.model,version:-1,lastTask:0,weapon:0,mode:'',health:-1,damage:p.damage,vehicle:0,seat:-2,blip:p.ambient?0:e.pn_blip(handle),hitUntil:0};entities.set(p.id,entity);e.pn_mission_entity(handle,1,1);
   e.pn_block_events(handle,1);e.pn_combat_attr(handle,17,0);e.pn_combat_attr(handle,58,1);e.pn_flee_attr(handle,-1,0);e.pn_keep_task(handle,1);e.pn_ambient_anim(handle,0);e.pn_ambient_base(handle,0);e.pn_evasive_dive(handle,0);e.pn_critical_hits(handle,0);nativeCall('SET_PED_CAN_SWITCH_WEAPON',[handle,0]);e.pn_invincible(handle,p.ambient?1:0);e.pn_ragdoll(handle,p.ambient?0:1);if(remoteGroup)e.pn_group(handle,remoteGroup);e.pn_blip_colour(entity.blip,2);e.pn_blip_scale(entity.blip,.75);e.pn_clear_tasks(handle);e.pn_model_release(p.model);
  }
  if(entity.retiring38){entity.retiring38=false;entity.deleteAt38=-Infinity;entity.version=-1;entity.health=-1;entity.mode='';entity.vehicle=0;entity.seat=-2;entity.lastTask=0;e.pn_clear_tasks(entity.handle);if(!entity.blip&&!p.ambient){entity.blip=e.pn_blip(entity.handle);e.pn_blip_colour(entity.blip,2);e.pn_blip_scale(entity.blip,.75);}}
  entity.ambient86=p.ambient;entity.lastSeen86=now;const h=entity.handle;if(entity.phone130&&!(p.flags&64)){drop101(entity.phone130);entity.phone130=0;}if(entity.mode==='phone' &&!(p.flags&64)){const dp=cstring('cellphone@',65120),cp=cstring('cellphone_text_out',65160);if(nativeCall('pn_v19_anim_loaded',[dp]))nativeCall('pn_v19_anim',[h,dp,cp,bits(4),bits(-4),800,48,bits(0),0,0,0]);}if(entity.version!==p.version){if(!p.ambient)applyLook(h,p.o+20);entity.version=p.version;}
  if(e.pn_armor(h)!==p.armor)e.pn_set_armor(h,p.armor);
  const sep114=(g,q)=>{if(q.vehicle||q.carriedBy||q.cuffed||q.prone||q.fly||!ped||e.pn_vehicle(ped,0))return g;const m=coords(ped),dx=g[0]-m[0],dy=g[1]-m[1],d=Math.hypot(dx,dy);if(d>=.72||Math.abs(g[2]-m[2])>1.6)return g;const r=q.heading*Math.PI/180,ux=d>.01?dx/d:Math.sin(r),uy=d>.01?dy/d:-Math.cos(r);return[m[0]+ux*.72,m[1]+uy*.72,g[2]];};
  const current=coords(h),walking=p.speed>.35||Math.hypot(p.vx,p.vy)>.35,rest145=sep114([p.x,p.y,p.z],p),quietMotion42=!p.vehicle&&!walking&&Math.hypot(rest145[0]-current[0],rest145[1]-current[1])>.25,moving=walking||quietMotion42,lead146=(entity.key146!==p.x+','+p.y+','+p.z&&(entity.key146=p.x+','+p.y+','+p.z,entity.at146=now),Math.min(.35,Math.max(0,(now-entity.at146)/1000))),goal=walking?sep114([p.x+p.vx*lead146,p.y+p.vy*lead146,p.z],p):rest145,error=Math.hypot(...goal.map((v,i)=>v-current[i]));
  if(e.pn_damaged_by(h,ped,1)){if(entryLocked){e.pn_clear_damage(h);}else{const seq=Atomics.load(a,10)+1,o=2800+(seq%16)*4;a[o]=seq;a[o+1]=p.id;a[o+2]=shooting||(!(flags&32)&&(e.pn_weapon(ped)>>>0)!==0xA2719263)?1:0;Atomics.store(a,10,seq);if(!a[o+2]){meleeTarget=p.id;meleeUntil=now+250;if(now-(entity.localHit144??-Infinity)>1200)entity.hitUntil=Math.max(entity.hitUntil,now+450);entity.localHit144=now;}e.pn_clear_damage(h);}}
  const targetHealth=p.health<=100?0:Math.round(p.health),nativeHealth=e.pn_health(h);if(entity.health!==p.health||nativeHealth!==targetHealth){if(p.health>100&&nativeHealth<=100){e.pn_resurrect(h);/* 203: no T-pose after a revive */try{nativeCall('CLEAR_PED_TASKS_IMMEDIATELY',[h]);}catch{}entity.mode='';entity.lastTask=-Infinity;}e.pn_set_health(h,targetHealth,0);entity.health=p.health;}
  if(p.damage!==entity.damage){entity.damage=p.damage;if(p.damage&&p.health>100){const duration=p.damageKind===1?260:180,melee144=p.damageKind===1,o144=melee144?attacker144(p.id):-1;if(!(melee144&&(e.pn_is_ragdoll(h)||o144<0&&now-(entity.localHit144??-Infinity)<1500))){e.pn_ragdoll_task(h,duration,duration,0,0,0,0);entity.hitUntil=Math.max(entity.hitUntil,now+duration);}swing144(o144);}}

  const activity=a[p.o+59];if(entity.activity!==activity){entity.activity=activity;entity.actionStarted=false;if(!activity)e.pn_clear_tasks(h);}
  if(activity&&!entity.actionStarted){const d=activity===1?'mp_player_inteat@burger':activity===2?'mp_player_intdrink':activity===4?'weapons@pistol@combat_pistol':'clothingtie',c=activity===1?'mp_player_int_eat_burger':activity===2?'loop_bottle':activity===4?'reload_aim':'try_tie_positive_a';const dp=cstring(d,65120),cp=cstring(c,65160);nativeCall('pn_v19_anim_request',[dp]);if(nativeCall('pn_v19_anim_loaded',[dp])){nativeCall('pn_v19_anim',[h,dp,cp,bits(3),bits(-3),3000,49,bits(0),0,0,0]);entity.actionStarted=true;}}
  if(p.weapon){const w154=p.weapon>>>0;if(entity.weapon!==p.weapon){nativeCall('REMOVE_ALL_PED_WEAPONS',[h,1]);if(w154!==0xA2719263)e.pn_give_weapon(h,p.weapon,999,0,1);e.pn_select_weapon(h,p.weapon,1);entity.weapon=p.weapon;entity.tint='';entity.weaponAt154=now;}else if(now-(entity.weaponAt154||0)>400&&!p.cuffed&&!p.prone&&!e.pn_vehicle(h,0)&&!e.pn_is_ragdoll(h)&&(e.pn_weapon(h)>>>0)!==w154){entity.weaponAt154=now;if(w154!==0xA2719263&&!nativeCall('HAS_PED_GOT_WEAPON',[h,p.weapon,0]))e.pn_give_weapon(h,p.weapon,999,0,1);e.pn_select_weapon(h,p.weapon,1);Atomics.add(a,15903,1);}}if(p.weapon&&entity.tint!==p.weapon+':'+p.tint){nativeCall('pn_v20_tint',[h,p.weapon,p.tint]);entity.tint=p.weapon+':'+p.tint;}
  const car=vehicles.get(p.vehicle);const inCar=e.pn_vehicle(h,0);
  if(p.fly&&p.health>100&&!car){
   if(!entity.fly){e.pn_clear_tasks(h);e.pn_freeze(h,1);e.pn_collision(h,0,0);entity.fly=true;}
   vector(...goal.map((v,i)=>error>8?v:current[i]+(v-current[i])*.4));e.pn_set_coords(h,ptr,1,1,1);e.pn_set_heading(h,p.heading);entity.mode='fly';
  }else{
  if(entity.fly){e.pn_freeze(h,0);e.pn_collision(h,1,1);entity.fly=false;}

  if(car&&p.health>100){entity.waitAt143=undefined;const want146=p.seat>=-1&&p.seat+2<=e.pn_vehicle_seats(e.pn_model(car.handle)),occ146=want146?e.pn_vehicle_seat(car.handle,p.seat,0):0,blocked146=!!occ146&&occ146!==h&&(occ146===ped||peers.some(q=>q!==p&&q.vehicle===p.vehicle&&q.seat===p.seat&&entities.get(q.id)?.handle===occ146));const enter165=!inCar&&want146&&!blocked146&&(()=>{if(entity.enterCar165!==car.handle){const c1=coords(h),c2=coords(car.handle);if(!(Math.hypot(c1[0]-c2[0],c1[1]-c2[1],c1[2]-c2[2])<=8))return false;entity.enterCar165=car.handle;entity.enterAt165=now;e.pn_clear_tasks(h);e.pn_enter_vehicle(h,car.handle,4000,p.seat,1,1,0n);}return now-entity.enterAt165<4000;})();
  if(blocked146)entity.warpCar143=0;else if(enter165){entity.warpCar143=0;}else if(inCar!==car.handle||want146&&occ146!==h){if(entity.warpCar143!==car.handle||entity.warpSeat143!==p.seat){entity.warpCar143=car.handle;entity.warpSeat143=p.seat;entity.warpAt143=now;e.pn_warp_vehicle(h,car.handle,p.seat);}else if(now-entity.warpAt143>500){entity.warpAt143=now;nativeCall('SET_PED_INTO_VEHICLE',[h,car.handle,p.seat]);}}else entity.warpCar143=0;entity.vehicle=p.vehicle;entity.seat=p.seat;entity.mode='vehicle';}
  else if(p.vehicle&&!inCar&&p.health>100&&now-(entity.waitAt143??=now)<3000){entity.warpCar143=0;}
  else if(inCar){if(entity.mode!=='exit'){e.pn_leave_vehicle(h,inCar,e.pn_speed(inCar)>4?4160:0);entity.mode='exit';entity.exitAt42=now;entity.hitUntil=now+2000;}
   else if(!p.vehicle&&p.health>100&&now-(entity.exitAt42??now)>3000){e.pn_leave_vehicle(h,inCar,16);entity.exitAt42=now;if(!e.pn_vehicle(h,0)){vector(...goal);e.pn_set_coords(h,ptr,1,1,1);e.pn_set_heading(h,p.heading);entity.vehicle=0;entity.seat=-2;entity.mode='';entity.hitUntil=now;}}}
  else if(p.health>100&&!p.prone&&now>=entity.hitUntil&&(!activity||moving)){
   entity.vehicle=0;entity.seat=-2;entity.enterCar165=0;if(!p.vehicle)entity.waitAt143=undefined;let fallen145=!!(p.flags&16)||!!nativeCall('IS_PED_RAGDOLL',[h])||!!nativeCall('IS_PED_GETTING_UP',[h]);if(fallen145&&!(p.flags&16)){entity.rag174??=now;if(now-entity.rag174>1200){e.pn_clear_tasks(h);entity.rag174=undefined;fallen145=false;}}else entity.rag174=undefined;if(error>4){vector(goal[0],goal[1],goal[2]+(p.flags&16?.9:0));e.pn_set_coords(h,ptr,1,1,1);}else if(quietMotion42&&!fallen145){vector(...goal.map((v,i)=>i===2&&v<current[i]-.35?current[i]:current[i]+(v-current[i])*.35));e.pn_set_coords(h,ptr,1,1,1);}else if(moving&&error>1.2&&!fallen145){vector(...goal.map((v,i)=>i===2?current[i]:current[i]+(v-current[i])*.08));e.pn_set_coords(h,ptr,1,1,1);}
   const mode=p.cuffed?(walking?'walk':'idle'):p.flags&64?'phone':p.flags&128?'hands':p.flags&16?'ragdoll':p.flags&32&&p.meleeTarget?'melee':p.flags&8?'reload':p.flags&4?'jump':p.flags&1?(walking?'move-shoot':'shoot'):p.flags&2?(walking?'move-aim':'aim'):walking?'walk':'idle';
   if(mode==='idle'){const angle=((p.heading-e.pn_heading(h)+540)%360)-180;if(Math.abs(angle)>.5)e.pn_set_heading(h,p.heading);}
   {const want130=mode==='phone';if(want130&&!(entity.phone130&&e.pn_exists(entity.phone130))&&now>=(entity.phoneNext130||0)){entity.phoneNext130=now+600;const m130=hash('prop_npc_phone_02');if(e.pn_model_valid(m130)&&!e.pn_model_loaded(m130))e.pn_request_model(m130);if(e.pn_model_loaded(m130)){const pos130=coords(h),o130=nativeCall('CREATE_OBJECT_NO_OFFSET',[m130,...pos130.map(bits),0,0,0]);if(o130){e.pn_mission_entity(o130,1,1);e.pn_collision(o130,0,0);vector(0,0,0);s[12]=0;s[14]=0;s[16]=0;e.pn_attach(o130,h,Math.max(0,nativeCall('GET_PED_BONE_INDEX',[h,28422])),ptr,BigInt(base+64048),0,0,0,0,2,1,0);entity.phone130=o130;}}}else if(!want130&&entity.phone130){drop101(entity.phone130);entity.phone130=0;}}const previousMode=entity.mode,changed=mode!==previousMode;const interval=mode==='walk'?300:mode.startsWith('move-')?260:220;
   if((changed||now-entity.lastTask>interval)&&!(fallen145&&mode!=='ragdoll')){
    if(changed&&['hands','phone'].includes(previousMode)&&!['hands','phone'].includes(mode))e.pn_clear_tasks(h);

    if(mode==='phone'){const dp=cstring('cellphone@',65120),cp=cstring('cellphone_text_read_base',65160);nativeCall('pn_v19_anim_request',[dp]);if(nativeCall('pn_v19_anim_loaded',[dp])&&!nativeCall('IS_ENTITY_PLAYING_ANIM',[h,dp,cp,3]))nativeCall('pn_v19_anim',[h,dp,cp,bits(4),bits(-4),-1,49,bits(0),0,0,0]);}
    else if(mode==='hands'){if(entity.mode!=='hands')e.pn_hands_up(h,-1,0,-1,0);}
    else if(mode==='melee'){const target=p.meleeTarget===a[51]?ped:entities.get(p.meleeTarget)?.handle;if(changed&&previousMode&&previousMode!=='idle'&&now-(entity.swungAt144??-Infinity)>950)e.pn_clear_tasks(h);if(target&&e.pn_exists(target)){const tp154=coords(target),hp154=coords(h),dx154=tp154[0]-hp154[0],dy154=tp154[1]-hp154[1];if(Math.hypot(dx154,dy154)>.05)e.pn_set_heading(h,((Math.atan2(-dx154,dy154)*180/Math.PI)+360)%360);}entity.meleeTarget=p.meleeTarget;}
    else if(mode==='move-shoot'||mode==='move-aim'){vector(goal[0]+p.vx*.18,goal[1]+p.vy*.18,goal[2]);s[12]=p.aim[0];s[14]=p.aim[1];s[16]=p.aim[2];e.pn_move_aim(h,ptr,BigInt(base+64048),p.speed>4?3:p.speed>1.8?2:1,0,.12,0,0,0,1,0xC6EE6B4C|0);}
    else if(mode==='shoot'||mode==='aim'){vector(...p.aim);e.pn_aim(h,ptr,300,0,0);}
    else if(mode==='jump'){if(entity.mode!=='jump')e.pn_jump(h,0,0,0);}
    else if(mode==='reload'){if(entity.mode!=='reload')e.pn_reload(h,0);}
    else if(mode==='ragdoll'){if(entity.mode!=='ragdoll')e.pn_ragdoll_task(h,500,500,0,0,0,0);}
    else if(mode==='walk'){vector(goal[0]+p.vx*.8,goal[1]+p.vy*.8,goal[2]);e.pn_walk(h,ptr,Math.max(1,Math.min(3,p.speed>4?3:p.speed>1.8?2:1)),1000,p.heading,.15);}
    else if(entity.mode!=='idle'){if(now-(entity.swungAt144??-Infinity)>950)e.pn_clear_tasks(h);/* 203: keep the swing */e.pn_set_heading(h,p.heading);}
    entity.mode=mode;entity.lastTask=now;
   }
   if(entity.unstick175&&now>=entity.unstick175){entity.unstick175=0;if(entity.mode==='idle'&&!fallen145&&!p.vehicle&&!p.cuffed&&!p.prone){e.pn_clear_tasks(h);e.pn_set_heading(h,p.heading);}
   }
   {const w154=p.weapon>>>0,armed154=!!p.weapon&&w154!==0xA2719263&&!self.__melee103.has(w154),proto154=a[15901]===154;let due154=0;
    if(proto154){const q154=a[15904+((p.o-128)>>6)]&0xffff;if(entity.shotSeq154!==undefined){due154=(q154-entity.shotSeq154)&0xffff;if(due154>64)due154=0;}entity.shotSeq154=q154;}
    else{const on154=!!(p.flags&1);if(on154&&!entity.shotOn154){due154=1;entity.shotStart154=now;}else if(on154&&now-(entity.shotStart154||now)>350&&now-(entity.shotAt154||0)>=120)due154=1;entity.shotOn154=on154;}
    if(due154){entity.shotDue154=Math.min(6,(entity.shotDue154|0)+due154);entity.shotDueAt154=now;}
    if(!armed154||fallen145||p.cuffed||now-(entity.shotDueAt154||0)>500)entity.shotDue154=0;
    if(entity.shotDue154>0&&now-(entity.shotAt154||0)>=90&&(e.pn_weapon(h)>>>0)===w154&&p.aim.every(Number.isFinite)){nativeCall('SET_PED_SHOOTS_AT_COORD',[h,...p.aim.map(bits),1]);entity.shotDue154--;entity.shotAt154=now;Atomics.add(a,15970,1);}}
  }
  }
  if(now-(self.__meleePre171??0)>3000){self.__meleePre171=now;nativeCall('pn_v19_anim_request',[cstring('melee@unarmed@streamed_core',65120)]);nativeCall('pn_v19_anim_request',[cstring('melee@knife@streamed_core',65120)]);}
  {const melee144=!!(p.flags&32)&&!p.ambient;if(a[15901]===154){const sw154=a[15936+((p.o-128)>>6)]&0xffff;if(entity.swingSeq154!==undefined&&sw154!==entity.swingSeq154&&!p.ambient&&now-(entity.swungAt144??-Infinity)>250)entity.swing144=now;entity.swingSeq154=sw154;}else if(melee144&&!entity.melee144)swing144(p.o);entity.melee144=melee144;
   if(entity.swing144){const w144=p.weapon>>>0,knife=(self.__knife144??=new Set(['weapon_knife','weapon_dagger','weapon_switchblade','weapon_machete','weapon_bottle'].map(modelHash23))).has(w144),fist=!w144||w144===0xA2719263||w144===modelHash23('weapon_knuckle');
    if(now-entity.swing144>800||!(knife||fist)||p.health<=100||p.vehicle||p.cuffed||p.prone||p.fly||p.carriedBy||(p.flags&16)||e.pn_vehicle(h,0))entity.swing144=0;
    else{const dp=cstring(knife?'melee@knife@streamed_core':'melee@unarmed@streamed_core',65120),cp=cstring(knife?'knife_short_range_0':'short_0_punch',65160);nativeCall('pn_v19_anim_request',[dp]);if(nativeCall('pn_v19_anim_loaded',[dp])){nativeCall('pn_v19_anim',[h,dp,cp,bits(8),bits(-4),900,48,bits(0),0,0,0]);entity.swing144=0;entity.swungAt144=now;entity.unstick175=now+1200;}}}}
  restraint34(h,p.cuffed,p.prone,entity);if(p.prone){vector(...goal);e.pn_set_coords(h,ptr,1,1,1);e.pn_set_heading(h,p.heading);}
  const carrier=p.carriedBy===a[51]?ped:entities.get(p.carriedBy)?.handle;
  if(carrier&&entity.carriedBy!==p.carriedBy){const bone=e.pn_bone_index(carrier,cstring('SKEL_Spine2'));vector(0,-.25,.2);s[12]=0;s[14]=0;s[16]=180;e.pn_attach(h,carrier,Math.max(0,bone),ptr,BigInt(base+64048),0,0,0,1,2,1,0);entity.carriedBy=p.carriedBy;}
  else if(!carrier&&entity.carriedBy){e.pn_detach(h,1,1);entity.carriedBy=0;}
  const actual=coords(h),o=2304+observed*12,d183=Math.hypot(...actual.map((v,i)=>v-xyz[i]));let visible=projectHead(h);if(visible&&d183<=14){if(now-(entity.losAt183||0)>200){entity.losAt183=now;try{entity.los183=!!nativeCall('HAS_ENTITY_CLEAR_LOS_TO_ENTITY',[ped,h,17]);}catch{entity.los183=true;}}if(!entity.los183)visible=0;}a[o]=p.id;a[o+1]=visible;f[o+2]=s[6];f[o+3]=s[7];f[o+4]=Math.hypot(...actual.map((v,i)=>v-xyz[i]));f[o+5]=p.health;f.set(actual,o+6);const actualCar=e.pn_vehicle(h,0);a[o+9]=[...vehicles].find(([id,v])=>v.handle===actualCar)?.[0]||0;observed++;
 }
 const localCarrier=entities.get(a[118])?.handle;
 if(localCarrier&&self.__pavCarriedBy!==a[118]){const bone=e.pn_bone_index(localCarrier,cstring('SKEL_Spine2'));vector(0,-.25,.2);s[12]=0;s[14]=0;s[16]=180;e.pn_attach(ped,localCarrier,Math.max(0,bone),ptr,BigInt(base+64048),0,0,0,1,2,1,0);self.__pavCarriedBy=a[118];}
 else if(!localCarrier&&self.__pavCarriedBy){e.pn_detach(ped,1,1);self.__pavCarriedBy=0;}
 if(a[118]||entryLocked)e.pn_controls_disable(0);
 Atomics.store(a,11,observed);Atomics.add(a,9,1);
  self.__tagFrame187=()=>{if(Atomics.load(a,9)&1)return;const n187=Math.min(32,Atomics.load(a,11));Atomics.add(a,9,1);try{for(let i=0;i<n187;i++){const o=2304+i*12;if(!a[o+1])continue;const ent=entities.get(a[o]);if(!ent||!ent.handle||!e.pn_exists(ent.handle))continue;if(projectHead(ent.handle)){f[o+2]=s[6];f[o+3]=s[7];}}}finally{Atomics.add(a,9,1);}
   if(ped&&e.pn_exists(ped)){Atomics.add(a,4,1);try{a[34]=projectHead(ped)?1:0;f[35]=s[6];f[36]=s[7];}finally{Atomics.add(a,4,1);}}};Atomics.store(a,7,entities.size);
 }catch(error){failBridge(a,error);}
 finally{e.pn_bridge_control(1);busy=false;const elapsed51=performance.now()-tickStart51;f[14105]=elapsed51;f[14106]=Math.max(f[14106],elapsed51);if(elapsed51>33)Atomics.add(a,14107,1);mark51(a[2]===-1?99:0);}
}
};
})();
