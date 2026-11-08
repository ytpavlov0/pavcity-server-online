# 201: replace the realtime relay with pavrt201 (shared population reports "n" + claims "k"). Backs up the running
# exe/source to backups\before-pavrt201, stops the running relay, starts pavrt201 through start_pavrt172.ps1 and checks
# /rt/status. Rollback: copy backups\before-pavrt201\pavrt.exe back over support\rt172\pavrt.exe and run this file's
# stop/start lines again. Players' realtime link reconnects by itself within ~1-2 minutes (HTTP sync keeps running).
$R='C:\PAVCITY';$D="$R\support\rt172";$B="$R\backups\before-pavrt201"
if(-not (Test-Path "$D\pavrt201.exe")){ 'pavrt201.exe missing'; exit 1 }
New-Item -ItemType Directory -Force $B | Out-Null
if(-not (Test-Path "$B\pavrt.exe")){ Copy-Item "$D\pavrt.exe" "$B\pavrt.exe"; Copy-Item "$D\pavrt.cs" "$B\pavrt.cs" }
$state=Get-Content "$R\backups\pavrt.json" -Raw | ConvertFrom-Json
$p=Get-Process -Id $state.pid -ErrorAction SilentlyContinue
if($p -and $p.ProcessName -like 'pavrt*'){ Stop-Process -Id $p.Id -Force -Confirm:$false; Start-Sleep -Milliseconds 800 }
Copy-Item "$D\pavrt201.exe" "$D\pavrt.exe" -Force; Copy-Item "$D\pavrt201.cs" "$D\pavrt.cs" -Force
& "$D\start_pavrt172.ps1"
try { $s=Invoke-RestMethod http://127.0.0.1:8090/rt/status -TimeoutSec 5; "pavrt201 running; connected: $($s.connected)" } catch { 'pavrt201 did not answer: ROLL BACK'; exit 1 }
