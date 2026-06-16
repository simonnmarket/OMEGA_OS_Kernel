# P0-ABC Smoke suite — CEO (um comando por passo, log agregado)
# Ref: governance/PSA_MANDATO_FECHO_P0_E_TRANSICAO_LEVEL_20260523.md Sec. 3.3
#
# Uso (a partir de SOURCE_CODE):
#   Set-Location C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
#   & .\scripts\run_p0_smoke_ceo.ps1
#
# Nota: usar & .\scripts\... evita aviso "command not found" do PowerShell.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$env:PYTHONPATH = $Root
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONNOUSERSITE = "1"

$LogDir = Join-Path $Root "audit\smoke"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "p0_smoke_ceo_$ts.log"

function Invoke-SmokeStep {
    param([string]$Name, [string[]]$PyArgs)
    $line = "`n========== $Name ==========`n"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line

    # Python escreve banner em stderr — com $ErrorActionPreference Stop isso abortava o script.
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & python -u @PyArgs *>&1 | Tee-Object -FilePath $LogFile -Append
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $prevEap
    }

    if ($exitCode -ne 0) {
        throw "FAIL: $Name (exit $exitCode). Ver $LogFile"
    }
    Write-Host "OK: $Name (exit 0)"
}

Write-Host "P0 smoke CEO -> $LogFile"
Add-Content -Path $LogFile -Value "P0 smoke CEO started $ts"

Invoke-SmokeStep "SM-1 EURUSD ciclo 1" @(
    "core_engines/shadow_loop.py", "--mode", "paper",
    "--ativos", "EURUSD", "--timeframes", "H1", "--equity", "10000"
)
Invoke-SmokeStep "SM-2/3 EURUSD ciclo 2" @(
    "core_engines/shadow_loop.py", "--mode", "paper",
    "--ativos", "EURUSD", "--timeframes", "H1", "--equity", "10000"
)
Invoke-SmokeStep "SM-6 XAUUSD ciclo 1" @(
    "core_engines/shadow_loop.py", "--mode", "paper",
    "--ativos", "XAUUSD", "--timeframes", "H1", "--equity", "10000"
)
Invoke-SmokeStep "P2a portfolio" @(
    "core_engines/shadow_loop.py", "--mode", "paper",
    "--ativos", "EURUSD", "GBPJPY", "XAUUSD", "--timeframes", "H1", "--equity", "10000"
)
$sinceDate = (Get-Date -Format "yyyy-MM-dd") + " 00:00:00"
Invoke-SmokeStep "Reconcile G3-G5 REG" @(
    "scripts/psa_position_pnl_reconcile.py", "--since", $sinceDate
)

Write-Host "`nP0 smoke CEO CONCLUIDO. Log: $LogFile"
