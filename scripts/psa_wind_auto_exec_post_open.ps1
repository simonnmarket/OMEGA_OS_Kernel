param(
    [string]$WorkDir = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE",
    [string]$Python = "python",
    [string]$Symbol = "XAUUSD",
    [int]$PollSeconds = 120,
    [int]$TimeoutMinutes = 360
)

$ErrorActionPreference = "Stop"
$StartedAt = Get-Date
Set-Location $WorkDir

if (-not (Test-Path ".\logs")) {
    New-Item -ItemType Directory -Path ".\logs" | Out-Null
}

$RunStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = ".\logs\psa_wind_auto_exec_$RunStamp.log"

function Write-RunLog {
    param([string]$Message)
    $line = "$(Get-Date -Format o) $Message"
    $line | Tee-Object -FilePath $LogPath -Append
}

function Initialize-Manifest {
    if (-not (Test-Path ".\logs\manifest.json")) {
        $manifest = [ordered]@{
            version = "1.0.0"
            bias_audits = @()
            created_at = (Get-Date -Format o)
        }
        $manifest | ConvertTo-Json -Depth 6 | Out-File ".\logs\manifest.json" -Encoding UTF8
        Write-RunLog "MANIFEST_CREATED logs/manifest.json"
    } else {
        Write-RunLog "MANIFEST_EXISTS logs/manifest.json"
    }
}

function Test-MarketOpen {
    $code = @"
import MetaTrader5 as mt5
symbol = "$Symbol"
ok = False
err = None
try:
    if mt5.initialize():
        sym = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        ok = bool(sym and tick and sym.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL)
    else:
        err = mt5.last_error()
finally:
    mt5.shutdown()
print("OPEN" if ok else "CLOSED")
if err:
    print(f"MT5_ERROR={err}")
"@
    $tmp = Join-Path $env:TEMP "omega_mt5_check_$RunStamp.py"
    Set-Content -Path $tmp -Value $code -Encoding UTF8
    try {
        $out = & $Python $tmp 2>&1
        Write-RunLog "MT5_CHECK symbol=$Symbol output=$($out -join ' | ')"
        return (($out -join "`n") -match "OPEN")
    } finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

function Wait-MarketOpen {
    Write-RunLog "WAIT_MARKET_START symbol=$Symbol poll=${PollSeconds}s timeout=${TimeoutMinutes}m"
    while ($true) {
        if (Test-MarketOpen) {
            Write-RunLog "MARKET_OPEN_DETECTED symbol=$Symbol"
            return
        }
        $elapsed = (New-TimeSpan -Start $StartedAt -End (Get-Date)).TotalMinutes
        if ($elapsed -ge $TimeoutMinutes) {
            throw "TIMEOUT_MARKET_NOT_OPEN after ${TimeoutMinutes}m"
        }
        Start-Sleep -Seconds $PollSeconds
    }
}

function Assert-MarketData {
    if (-not (Test-Path ".\config\market_data.json")) {
        throw "MISSING_MARKET_DATA config/market_data.json"
    }
    $mkt = Get-Content ".\config\market_data.json" -Raw | ConvertFrom-Json
    foreach ($field in @("DXY_change_pct", "XAU_change_pct", "Buffett_cash_B", "BlackRock_equities_change_pct", "_updated")) {
        if (-not ($mkt.PSObject.Properties.Name -contains $field)) {
            throw "INVALID_MARKET_DATA missing=$field"
        }
    }
    Write-RunLog "MARKET_DATA_OK updated=$($mkt._updated)"
}

function Write-FileSha3 {
    param([string]$Path)
    if (Test-Path $Path) {
        $code = @"
import hashlib, pathlib
p = pathlib.Path(r"$Path")
print(hashlib.sha3_256(p.read_bytes()).hexdigest())
"@
        $tmp = Join-Path $env:TEMP "omega_sha3_$RunStamp.py"
        Set-Content -Path $tmp -Value $code -Encoding UTF8
        try {
            $sha = (& $Python $tmp 2>&1 | Select-Object -First 1).ToString().Trim()
            Set-Content -Path "$Path.sha3" -Value $sha -Encoding UTF8
            Write-RunLog "SHA3 path=$Path sha3=$sha"
        } finally {
            Remove-Item $tmp -ErrorAction SilentlyContinue
        }
    } else {
        Write-RunLog "SHA3_SKIP missing=$Path"
    }
}

Write-RunLog "PSA_WIND_AUTO_EXEC_START workdir=$WorkDir"
Initialize-Manifest
Assert-MarketData
Wait-MarketOpen

Write-RunLog "BIAS_AUDIT_START"
& $Python ".\bias_audit.py" 2>&1 | Tee-Object -FilePath $LogPath -Append
if ($LASTEXITCODE -ne 0) { throw "BIAS_AUDIT_FAILED exit=$LASTEXITCODE" }
Write-RunLog "BIAS_AUDIT_DONE"

Write-RunLog "SHADOW_LOOP_START mode=paper ativos=XAUUSD,GBPUSD,USDJPY,AUDUSD timeframes=H1,H4"
& $Python ".\core_engines\shadow_loop.py" --mode paper --ativos XAUUSD GBPUSD USDJPY AUDUSD --timeframes H1 H4 --equity 10000 2>&1 | Tee-Object -FilePath $LogPath -Append
$shadowExit = $LASTEXITCODE
Write-RunLog "SHADOW_LOOP_DONE exit=$shadowExit"

Write-FileSha3 ".\audit\paper\paper_summary.json"

Write-RunLog "GIT_RECENT_COMMITS"
git log --oneline -10 2>&1 | Tee-Object -FilePath $LogPath -Append

Write-RunLog "PSA_WIND_AUTO_EXEC_COMPLETE"
exit $shadowExit
