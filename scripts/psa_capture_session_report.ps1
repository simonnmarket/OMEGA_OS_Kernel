# PSA_CAPTURE_SESSION_REPORT — validacao CEO capture matrix
param(
    [int]$TailLines = 5000
)

$Root = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$Log = Join-Path $Root "audit\paper\omega_24x7_runner.log"
$Trace = Join-Path $Root "audit\paper\decision_trace.jsonl"
$Feedback = Join-Path $Root "audit\paper\trade_feedback.jsonl"
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = Join-Path $Root "audit\forensic\capture_report_$Ts"

Set-Location $Root
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "=== OMEGA CAPTURE SESSION REPORT ===" -ForegroundColor Cyan
Write-Host "Output: $OutDir"

function Count-Pattern($path, $pattern) {
    if (-not (Test-Path $path)) { return 0 }
    return (Select-String -Path $path -Pattern $pattern | Measure-Object).Count
}

$metrics = [ordered]@{
    generated_utc        = (Get-Date).ToUniversalTime().ToString("o")
    runner_log_lines     = if (Test-Path $Log) { (Get-Content $Log).Count } else { 0 }
    impact_tp_new        = Count-Pattern $Log '\[IMPACT_TP\] SEL impact='
    impact_tp_resync     = Count-Pattern $Log '\[IMPACT_TP\] \[RESYNC\]'
    partial_03atr        = Count-Pattern $Log 'TP1-0\.3ATR|0\.3x ATR'
    partial_broker_ok    = Count-Pattern $Log '\[MT5_CLOSE_PARTIAL\].*✅'
    pyramid_eval_add     = Count-Pattern $Log '\[PYRAMID_EVAL\].*add=True'
    pyramid_broker_ok    = Count-Pattern $Log '\[PYRAMID\].*EXEC OK'
    pyramid_broker_fail  = Count-Pattern $Log '\[PYRAMID\].*EXEC FAIL'
    edge_bypass          = Count-Pattern $Log '\[EDGE_GATE\] BYPASS'
    dedup_scale_bypass   = Count-Pattern $Log '\[DEDUP\] BYPASS scale-entry'
    lot_metal_floor      = Count-Pattern $Log 'LOT0\.05|min_lot.*0\.05'
    trace_executes       = Count-Pattern $Trace 'MT5_PAPER_EXECUTE'
    feedback_opens       = Count-Pattern $Feedback 'position_opened'
    feedback_closes      = Count-Pattern $Feedback 'position_closed'
}

$metrics | ConvertTo-Json -Depth 3 | Set-Content (Join-Path $OutDir "metrics.json")
$metrics.GetEnumerator() | ForEach-Object { Write-Host ("  {0,-22} {1}" -f $_.Key, $_.Value) }

$patterns = @(
    'IMPACT_TP.*RESYNC',
    'IMPACT_TP\] SEL impact=',
    'PYRAMID.*EXEC OK',
    'PYRAMID.*EXEC FAIL',
    'PYRAMID_EVAL.*add=True',
    'PARTIAL_CLOSE.*0\.3',
    'MT5_CLOSE_PARTIAL',
    'EDGE_GATE\] BYPASS',
    'DEDUP.*BYPASS scale-entry',
    'LOT1\.00|MIN_LOT_EXEC',
    'FATAL|CRITICAL'
)
foreach ($p in $patterns) {
    $hits = Select-String -Path $Log -Pattern $p -ErrorAction SilentlyContinue | Select-Object -Last 15
    if ($hits) {
        $hits | ForEach-Object { $_.Line } | Set-Content (Join-Path $OutDir ("sample_" + ($p -replace '[^\w]','_') + ".txt"))
    }
}

Write-Host "`nVERDITO automatico sessao capture:" -ForegroundColor Yellow

$checks = [ordered]@{
    "IMPACT_TP SEL >=1"          = ($metrics.impact_tp_new -ge 1)
    "IMPACT_TP RESYNC >=1"       = ($metrics.impact_tp_resync -ge 1)
    "PYRAMID EXEC OK >=1"        = ($metrics.pyramid_broker_ok -ge 1)
    "Partial 0.3xATR broker >=1" = ($metrics.partial_broker_ok -ge 1)
    "Sem LOT1.00 forbidden"      = ($metrics.lot_metal_floor -eq 0 -or $metrics.lot_metal_floor -gt 0) -and
                                   (Count-Pattern $Log 'LOT1\.00.*pyramid|OMEGA_MIN_LOT_EXEC') -eq 0
    "Runner lock activo"         = (Test-Path (Join-Path $Root "audit\paper\omega_runner.lock"))
    "Zero FATAL/CRITICAL"        = ($metrics | Where-Object { $_.Key -eq "FATAL" }).Value -eq 0 -or
                                   (Count-Pattern $Log 'FATAL|CRITICAL') -eq 0
}

$pass = 0; $total = $checks.Count
foreach ($k in $checks.Keys) {
    $ok = $checks[$k]
    $symbol = if ($ok) { "[OK]" } else { "[!!]" }
    $color  = if ($ok) { "Green" } else { "Red" }
    Write-Host ("  {0} {1}" -f $symbol, $k) -ForegroundColor $color
    if ($ok) { $pass++ }
}

Write-Host ""
if ($pass -eq $total) {
    Write-Host "RESULTADO: PASS ($pass/$total) — sessao capture SAUDAVEL" -ForegroundColor Green
} elseif ($pass -ge 4) {
    Write-Host "RESULTADO: PARCIAL ($pass/$total) — verificar criterios em falta" -ForegroundColor Yellow
} else {
    Write-Host "RESULTADO: FAIL ($pass/$total) — investigar antes do veredito CEO" -ForegroundColor Red
}

if (Test-Path (Join-Path $Root "audit\paper\omega_runner.lock")) {
    Write-Host "`nRunner lock PID: $(Get-Content (Join-Path $Root 'audit\paper\omega_runner.lock'))" -ForegroundColor Green
} else {
    Write-Warning "Runner lock AUSENTE — runner pode ter parado"
}

Write-Host "`nReport saved: $OutDir"
