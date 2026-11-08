# PAVCITY tunnel watchdog: keeps the named Cloudflare tunnel (pavcity) running.
# Every 15 s: starts cloudflared if it is not running; restarts it if /ready has failed for ~60 s.
# Only one watchdog runs at a time (named mutex). Close the window to stop watching (the tunnel keeps running).
$ErrorActionPreference = 'Continue'
$root    = 'C:\PAVCITY'
$exe     = Join-Path $root 'cloudflared.exe'
$config  = 'C:\Users\USER\.cloudflared\config.yml'
$tunlog  = Join-Path $root 'backups\tunnel-named.log'
$wdlog   = Join-Path $root 'backups\tunnel-watchdog.log'
$metrics = '127.0.0.1:20241'
$cfArgs  = "tunnel --config $config --no-autoupdate --metrics $metrics --logfile $tunlog run pavcity"
$interval = 15
$maxFails = 4

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Global\PAVCITY-Tunnel-Watchdog', [ref]$created)
if (-not $created) {
    Write-Host 'Watchdog zaten calisiyor, bu pencere kapanabilir.' -ForegroundColor Yellow
    Start-Sleep 5
    exit
}
$Host.UI.RawUI.WindowTitle = 'PAVCITY Tunel Watchdog'

function Log([string]$msg, [string]$color = 'Gray') {
    $line = '{0:yyyy-MM-dd HH:mm:ss}  {1}' -f (Get-Date), $msg
    Write-Host $line -ForegroundColor $color
    Add-Content -Path $wdlog -Value $line -Encoding UTF8
}

function Get-Tunnel {
    Get-CimInstance Win32_Process -Filter "Name='cloudflared.exe'" |
        Where-Object { $_.CommandLine -like '*run pavcity*' }
}

function Test-Ready {
    try { (Invoke-WebRequest "http://$metrics/ready" -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 }
    catch { $false }
}

function Start-Tunnel([string]$why) {
    foreach ($p in Get-Tunnel) {
        try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch {}
    }
    Start-Sleep 2
    $p = Start-Process -FilePath $exe -ArgumentList $cfArgs -WindowStyle Hidden -PassThru
    Log "Tunel baslatildi ($why), pid $($p.Id)" 'Yellow'
    $script:fails = 0
    $script:startedAt = Get-Date
}

Log 'Watchdog basladi. Tunel her 15 sn kontrol ediliyor. Kapatmak icin pencereyi kapat.' 'Cyan'
$fails = 0
$startedAt = Get-Date
$wasReady = $null

while ($true) {
    $running = @(Get-Tunnel)
    if ($running.Count -eq 0) {
        Start-Tunnel 'calismiyordu'
        $wasReady = $null
    }
    elseif (Test-Ready) {
        if ($wasReady -ne $true) { Log 'Tunel hazir, site acik.' 'Green' }
        $fails = 0
        $wasReady = $true
    }
    elseif (((Get-Date) - $startedAt).TotalSeconds -gt 30) {
        $fails++
        Log "Tunel Cloudflare'e bagli degil ($fails/$maxFails)" 'Red'
        $wasReady = $false
        if ($fails -ge $maxFails) { Start-Tunnel 'baglanti koptu' }
    }
    Start-Sleep $interval
}
