# 194 backend swap (NPC ambulance call shared nearby, revive when it arrives): DB backup + state copy, stop current, start v193; roll back to v192 on failure.
$ErrorActionPreference='Stop'
$R='C:\PAVCITY';Set-Location $R
$py="$R\runtime\python.exe";$B="$R\backups\before-release194-backend"
if(Test-Path "$B\online.db"){throw 'backup already exists'}
New-Item -ItemType Directory -Force $B|Out-Null
& $py -X utf8 -c "import sqlite3,sys;s=sqlite3.connect('file:online.db?mode=ro',uri=True);d=sqlite3.connect(sys.argv[1]);s.backup(d);print('backup',d.execute('PRAGMA quick_check').fetchone()[0])" "$B\online.db"
Copy-Item backups\detached-server.json "$B\detached-server.json"
$old=(Get-Content backups\detached-server.json -Raw|ConvertFrom-Json).pid
"stopping $old";Stop-Process -Id $old -Force;Start-Sleep -Seconds 2
function Start-Runner($script){$r=Invoke-CimMethod Win32_Process -MethodName Create -Arguments @{CommandLine="`"$py`" -X utf8 support/dev-tools/$script";CurrentDirectory=$R};"started $script pid $($r.ProcessId) rc $($r.ReturnValue)"}
function Caps($v){for($i=0;$i -lt 60;$i++){try{$c=Invoke-RestMethod "http://127.0.0.1:8000/pn/server-capabilities-$v.json" -TimeoutSec 5;return $c}catch{Start-Sleep -Seconds 2}};return $null}
Start-Runner run_detached_gameplay_v194.py
$c=Caps 'v194'
if($c -and $c.backend_release -eq 'v194' -and $c.ems194){"v194 up"}
else{"v194 FAILED - rolling back";$p=(Get-Content backups\detached-server.json -Raw|ConvertFrom-Json).pid;try{Stop-Process -Id $p -Force}catch{};Start-Runner run_detached_gameplay_v193.py;$c=Caps 'v193';"rollback v193: "+[bool]$c;exit 1}

