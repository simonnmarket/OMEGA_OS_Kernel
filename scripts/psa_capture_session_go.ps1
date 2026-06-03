# PSA_CAPTURE_SESSION_GO - CEO Capture Matrix 2026-06-03 (producao, sem harness)
# Uso (MT5 aberto + demo ligada):
#   cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\psa_capture_session_go.ps1 -Background
#
# Relatorio intermedio / manha:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\psa_capture_session_report.ps1
param(
    [switch]$SkipPytest,
    [switch]$Background
)

$ErrorActionPreference = "Stop"
$Root = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$LogDir = Join-Path $Root "audit\paper"
$Lock = Join-Path $LogDir "omega_runner.lock"
$Mutex = Join-Path $Root "audit\.omega_system.lock"
$RunnerLog = Join-Path $LogDir "omega_24x7_runner.log"
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"
$Forensic = Join-Path $Root "audit\forensic\capture_session_$Ts"

Set-Location $Root
New-Item -ItemType Directory -Force -Path $Forensic | Out-Null
$env:PYTHONPATH = $Root

Write-Host "=== OMEGA PSA CAPTURE SESSION GO (CEO 2026-06-03) ===" -ForegroundColor Cyan
Write-Host "Modo: producao paper | SEM test harness | lote metal min 0.05"
Write-Host "Forensic: $Forensic"

Write-Host ""
Write-Host "[FASE 0] Parar runners OMEGA duplicados..."
Get-CimInstance Win32_Process -Filter "name='python.exe' OR name='python3.exe' OR name='python3.11.exe'" |
    Where-Object { $_.CommandLine -match "omega_paper_loop|shadow_loop" } |
    ForEach-Object {
        Write-Host "  STOP PID $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
Start-Sleep -Seconds 3
Remove-Item $Lock, $Mutex -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "[FASE 1] Preflight..."
python -m py_compile core_engines\shadow_loop.py 2>&1 | Tee-Object (Join-Path $Forensic "py_compile_shadow_loop.txt")
if ($LASTEXITCODE -ne 0) { throw "shadow_loop.py syntax FAIL" }

if (-not $SkipPytest) {
    python -m pytest -q tests/test_sel_usfe_gate.py 2>&1 | Tee-Object (Join-Path $Forensic "pytest_sel_usfe.txt")
    if ($LASTEXITCODE -ne 0) { throw "pytest FAIL" }
}

git -C $Root rev-parse HEAD 2>$null | Tee-Object (Join-Path $Forensic "git_head.txt")
Copy-Item (Join-Path $Root "governance\PSA_MEMORIA_CAPTURE_CEO_20260603.md") (Join-Path $Forensic "memoria_psa.txt") -ErrorAction SilentlyContinue

@{
    runner_lines = if (Test-Path $RunnerLog) { (Get-Content $RunnerLog).Count } else { 0 }
    started_utc  = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content (Join-Path $Forensic "pre_counters.json")

Write-Host ""
Write-Host "[FASE 2] Arranque run_omega_24x7.ps1 (capture matrix)..."
Write-Host "  Log: $RunnerLog"

if ($Background) {
    Start-Process powershell -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', (Join-Path $Root 'scripts\run_omega_24x7.ps1')
    ) -WindowStyle Hidden
    Start-Sleep -Seconds 8
    if (Test-Path $Lock) {
        Write-Host "  Runner PID: $(Get-Content $Lock)" -ForegroundColor Green
    } else {
        Write-Warning "  Lock ausente - verificar log"
    }
} else {
    Write-Host "  Foreground - Ctrl+C para parar."
    powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\run_omega_24x7.ps1" 2>&1 |
        Tee-Object (Join-Path $Forensic "runner_console.log")
}

Write-Host ""
Write-Host "=== CAPTURE SESSION ARRANCADA ===" -ForegroundColor Green
