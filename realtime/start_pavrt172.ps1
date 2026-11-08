# Starts the PAVCITY realtime server (pavrt172) in the background on 127.0.0.1:8090 unless it already answers.
# Detached through WMI so closing a console or editor does not stop it. PID recorded in backups/pavrt.json.
$R='C:\PAVCITY'
try { $s=Invoke-RestMethod http://127.0.0.1:8090/rt/status -TimeoutSec 3; "pavrt already running: $($s.connected) connected"; exit 0 } catch {}
$proc=Invoke-CimMethod Win32_Process -MethodName Create -Arguments @{CommandLine="`"$R\support\rt172\pavrt.exe`" `"$R`" --headless --port=8090";CurrentDirectory="$R\support\rt172"}
if($proc.ReturnValue -ne 0){ "start failed: $($proc.ReturnValue)"; exit 1 }
[IO.File]::WriteAllText("$R\backups\pavrt.json","{`"pid`": $($proc.ProcessId), `"port`": 8090}")
for($i=0;$i -lt 30;$i++){ try { $s=Invoke-RestMethod http://127.0.0.1:8090/rt/status -TimeoutSec 2; "pavrt started pid $($proc.ProcessId)"; exit 0 } catch { Start-Sleep -Milliseconds 300 } }
"pavrt did not answer"; exit 1
