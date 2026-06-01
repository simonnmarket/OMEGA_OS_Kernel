# PSA_MADRUGADA_GO — Preflight + arranque alta performance (CEO 2026-06-01)
# Uso: powershell -NoProfile -ExecutionPolicy Bypass -File scripts\psa_madrugada_go.ps1
$ErrorActionPreference = "Stop"
$Root = "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$LogDir = Join-Path $Root "audit\paper"
$Lock = Join-Path $Root "audit\.omega_system.lock"
$RunnerLog = Join-Path $LogDir "omega_24x7_runner.log"
$Trace = Join-Path $LogDir "decision_trace.jsonl"
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"
$Forensic = Join-Path $Root "audit\forensic\madrugada_$Ts"

Set-Location $Root
New-Item -ItemType Directory -Force -Path $Forensic | Out-Null
$env:PYTHONPATH = $Root

Write-Host "=== OMEGA PSA MADRUGADA GO ===" -ForegroundColor Cyan
Write-Host "ROOT: $Root"

# ─── FASE 0: Parar instâncias duplicadas ───────────────────────────────────
Write-Host "`n[FASE 0] Processos python OMEGA..."
Get-CimInstance Win32_Process -Filter "name='python.exe' OR name='python3.exe' OR name='python3.11.exe'" |
    Where-Object { $_.CommandLine -match "omega_paper_loop|shadow_loop" } |
    ForEach-Object {
        Write-Host "  STOP PID $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
Start-Sleep -Seconds 3

# ─── FASE 1: Mutex ───────────────────────────────────────────────────────────
Write-Host "`n[FASE 1] Mutex $Lock"
if (Test-Path $Lock) {
    $lockPid = (Get-Content $Lock -Raw).Trim()
    $alive = $false
    if ($lockPid -match '^\d+$') {
        $alive = $null -ne (Get-Process -Id ([int]$lockPid) -ErrorAction SilentlyContinue)
    }
    if (-not $alive) {
        Remove-Item $Lock -Force
        Write-Host "  REMOVED stale lock (PID $lockPid morto)" -ForegroundColor Yellow
    } else {
        Write-Host "  WARN: lock PID $lockPid ainda vivo — parar manualmente" -ForegroundColor Red
        exit 1
    }
}

# ─── FASE 2: Testes gate SEL/USFE ──────────────────────────────────────────
Write-Host "`n[FASE 2] pytest sel_usfe_gate..."
python -m pytest -q tests/test_sel_usfe_gate.py 2>&1 | Tee-Object (Join-Path $Forensic "pytest_sel_usfe.txt")
if ($LASTEXITCODE -ne 0) { throw "pytest FAIL" }

# ─── FASE 3: Evidência pré-arranque ────────────────────────────────────────
Write-Host "`n[FASE 3] Snapshot pré-arranque..."
git -C $Root rev-parse HEAD | Tee-Object (Join-Path $Forensic "git_head.txt")
git -C $Root status -sb | Tee-Object (Join-Path $Forensic "git_status.txt")
Get-Content (Join-Path $Root "config\live_flags.json") | Set-Content (Join-Path $Forensic "live_flags.json")
Select-String -Path $RunnerLog -Pattern "mode=paper|mode=shadow" | Select-Object -Last 5 |
    ForEach-Object { $_.Line } | Set-Content (Join-Path $Forensic "last_modes.txt")

# ─── FASE 4: Arranque runner madrugada ─────────────────────────────────────
Write-Host "`n[FASE 4] Arranque run_omega_24x7_madrugada.ps1 (foreground)..."
Write-Host "  Logs: $RunnerLog"
Write-Host "  Trace: $Trace"
Write-Host "  Rollback gate: `$env:OMEGA_SKIP_SEL_USFE_ENFORCE='1' + restart"
Write-Host ""

powershell -NoProfile -ExecutionPolicy Bypass -File "$Root\scripts\run_omega_24x7_madrugada.ps1" 2>&1 |
    Tee-Object (Join-Path $Forensic "runner_console.log")
