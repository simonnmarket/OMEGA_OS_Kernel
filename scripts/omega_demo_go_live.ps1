# OMEGA — Pré-voo + validação DEMO (zero conflito P0 + Fase 1)
# Ref: governance/CEO_GO_LIVE_DEMO_ZERO_CONFLITO_20260525.md
#
# Uso:
#   cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
#   git checkout feat/execution-router-atr-20260523   # ou main após merge PRs
#   & .\scripts\omega_demo_go_live.ps1
#
# Fases: preflight -> smoke validação -> relatório audit/demo/

$ErrorActionPreference = "Stop"
$Root = if ($PSScriptRoot) { Split-Path -Parent $PSScriptRoot } else { Get-Location }
Set-Location $Root

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = Join-Path $Root "audit\demo_go_live"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Report = Join-Path $OutDir "GO_LIVE_REPORT_$ts.txt"

function Log($msg) {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content -Path $Report -Value $line
}

Log "=== OMEGA DEMO GO-LIVE PREFLIGHT ==="
Log "ROOT=$Root"

# --- Git ---
$branch = git branch --show-current 2>$null
$head = git log -1 --oneline 2>$null
Log "GIT branch=$branch HEAD=$head"

# --- Env alinhado run_omega_24x7.ps1 (DEMO) ---
$env:PYTHONPATH = $Root
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
$env:OMEGA_MAX_POSITIONS = "8"
$env:OMEGA_USE_V2 = "0"
$env:OMEGA_DISABLE_MOMENTUM_FALLBACK = "0"
$env:OMEGA_DECISION_TRACE = "1"
$env:OMEGA_PYTHONIOENCODING = "utf-8"
$env:PYTHONIOENCODING = "utf-8"
$env:OMEGA_EDGE_METAL_ATR = "0.0005"
$env:OMEGA_VOL_MIN_METAL = "0.10"
$env:OMEGA_VOL_MIN_FOREX = "0.10"
$env:OMEGA_M1_MIN_CONFIRMED = "1"
$env:OMEGA_MIN_CONFLUENCE = "35"
# NÃO definir OMEGA_24X7_ATIVOS — usa omega_asset_schedule.json (T-W1)

Log "ENV: magic=234001 max_pos_asset=1 use_v2=0 edge_metal_atr=0.0005"

# --- pytest ---
Log "pytest gate..."
$pytestOut = python -m pytest tests/test_p0_abc_20260522.py tests/test_runner_targets_v1_only.py tests/test_order_magic_propagation.py tests/test_router_atr_20260523.py -q --tb=no 2>&1
$pytestOut | ForEach-Object { Log $_ }
if ($LASTEXITCODE -ne 0) {
    Log "FAIL pytest — corrigir antes de DEMO"
    exit 1
}

# --- MT5 posições ---
Log "check_positions_now..."
python scripts/check_positions_now.py 2>&1 | Tee-Object -FilePath (Join-Path $OutDir "positions_pre.txt") | ForEach-Object { Log $_ }

# --- Smoke validação (um passo de cada vez) ---
function Invoke-PyStep($Name, [string[]]$PyArgs) {
    Log "=== $Name ==="
    $logFile = Join-Path $OutDir "${Name}_$ts.log"
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & python -u @PyArgs *>&1 | Tee-Object -FilePath $logFile
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prevEap
    }
    Log "$Name exit=$code"
    if ($code -ne 0) { Log "WARN $Name falhou — ver $logFile" }
    return $code
}

Invoke-PyStep "SM_EURUSD_H1_1" @(
    "core_engines/shadow_loop.py", "--mode", "paper",
    "--ativos", "EURUSD", "--timeframes", "H1", "--equity", "10000"
)
Invoke-PyStep "SM_EURUSD_H1_2" @(
    "core_engines/shadow_loop.py", "--mode", "paper",
    "--ativos", "EURUSD", "--timeframes", "H1", "--equity", "10000"
)
Invoke-PyStep "SM_XAUUSD_H4_SM-R" @(
    "core_engines/shadow_loop.py", "--mode", "paper",
    "--ativos", "XAUUSD", "--timeframes", "H4", "--equity", "10000"
)

$sinceDate = (Get-Date -Format "yyyy-MM-dd") + " 00:00:00"
Invoke-PyStep "RECONCILE" @(
    "scripts/psa_position_pnl_reconcile.py", "--since", $sinceDate
)

python scripts/check_positions_now.py 2>&1 | Tee-Object -FilePath (Join-Path $OutDir "positions_post.txt") | ForEach-Object { Log $_ }

Log "=== FIM PREVOO ==="
Log "Relatório: $Report"
Log "Logs: $OutDir"
Log ""
Log "Se todos os ciclos exit=0 e 0 posicoes orfas: pode arrancar:"
Log "  & .\scripts\run_omega_24x7.ps1"
Log "  ou & .\scripts\restart_full_portfolio.ps1 (delega run_omega_24x7 — pos-2517c8b)"

exit 0
