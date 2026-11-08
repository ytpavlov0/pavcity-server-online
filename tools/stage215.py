"""215 (frontend): loader214 -> loader215 (bridge v215: NPC ambulance scene), crime215 replaces crime211 (ambulance on the death panel). Pairs with backend v194.
214 (frontend): loader213 -> loader214 (bridge v214: ATM looked up only when standing still, street props only after an impact).
213 (frontend): loader212 -> loader213 (bridge v213: phase-4 timing by parts, lighter props scan, host sample 3/s).
212 (frontend): loader211 -> loader212 (bridge v212: unconscious hold by ragdoll, no respawn loop).
211 (frontend): loader210 -> loader211 (bridge v211: unconscious ped held down), crime211 replaces crime210. Pairs with backend v193.
210 (frontend): loader207 -> loader210 (bridge v210: crime/rescue block), crime210.js after perf207.js, about210 replaces about208, gfx210 replaces gfx206. Pairs with backend v192.
209 (frontend): tag209.css (no dark bar for a nametag without armor), linked last in the head.
208 (frontend): about208.js replaces video205.js (video on all auth screens, ESC HAKKIMIZDA tab, F1). Loader unchanged.
207 (frontend): loader206 -> loader207 (GPU worker v60: draws and busy % with the FPS), perf207.js after gfx206.js.
206 (frontend): loader205 -> loader206 (bridge v206: NPC/traffic density budgets), gfx206.js after video205.js.
205 (frontend): loader204 -> loader205 (bridge v205: hunger/thirst damage), needs205.js + video205.js after npc201.js.
204 (frontend): loader203 -> loader204 (bridge v204: home lights on a fixed grid, faded).
203 (frontend): loader201 -> loader203 (bridge v203: radio station to passengers, full remote punch, no T-pose after a revive).
202 (frontend): client201 -> client202 (boarding announced over realtime while getting in). Rest as 201.
201 (frontend): shared street population. loader200 -> loader201 (bridge v201: host report / follower copies),
client197 -> client201 (realtime hooks), npc201.js after iodiag200, and the engine worker's pnNpc201 message is handed
to window.__npc201.host. Needs the realtime relay pavrt201 for the reports to travel; with the old relay nothing is
relayed and every player keeps its own population (as before)."""
from pathlib import Path
import re,json,hashlib,shutil
R=Path(__file__).resolve().parents[2];W=R/'mirror/playgta5.com';S=R/'support/fixes215';O=R/'backups/release215-checks';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((R/'gameplay-validation-v214.json').read_text(encoding='utf-8-sig'));assert not(R/'gameplay-validation-v215.json').exists()
O.mkdir(exist_ok=True,parents=True);assets=dict(prior['assets'])
for p in sorted(S.iterdir()):
 if p.suffix not in('.js','.css'):continue
 name=('b/8b0b5899ed/' if p.name.startswith(('loader-pn-','pn_native_bridge','wgpu_worker-','io-worker')) else 'pn/fixes215/')+p.name
 dest=W/name;assert not dest.exists() or sha(dest)==sha(p),('published asset would change',name);dest.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(p,dest);assets[name]=sha(dest)
for name,h in prior['assets'].items():assert sha(W/name)==h,name
entry=(W/'index.html').read_text(encoding='utf8');base_sha=sha(W/'index.html');assert base_sha==prior['index_sha256']
assert 'gameplay-v215' not in entry and 'gameplay-v214.js' in entry and 'crime215' not in entry
entry,n=re.subn(re.escape('/loader-pn-online-v16-gameplay-v214.js')+r'\?build=[a-f0-9]+','/loader-pn-online-v16-gameplay-v215.js?build='+(assets['b/8b0b5899ed/loader-pn-online-v16-gameplay-v215.js'][:6]+assets['b/8b0b5899ed/pn_native_bridge-v215.js'][:6]),entry);assert n==1
entry,n=re.subn(re.escape('/pn/fixes211/crime211.js')+r'\?build=[a-f0-9]+','/pn/fixes215/crime215.js?build='+assets['pn/fixes215/crime215.js'][:12],entry);assert n==1
(O/'index215.html').write_text(entry,encoding='utf8');(O/'assets.json').write_text(json.dumps(assets,indent=2));(O/'baseline.json').write_text(json.dumps(dict(index_sha256=base_sha)))
print('215 staged; loader215 (bridge v215), crime215')
