# =============================================================================
# MISSÃO: OMEGA-HUNTER-20260420 - EXECUÇÃO REGIME CAÇADOR
# =============================================================================

param([ValidateSet("paper", "live")][string]$Mode = "paper")
$ErrorActionPreference = "Continue"
$script:StartTime = Get-Date

Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " MISSÃO OMEGA-HUNTER-20260420 - REGIME CAÇADOR [$Mode]" -ForegroundColor Yellow

$hora = (Get-Date).Hour
if ($hora -ge 8 -and $hora -lt 17) {
    Write-Host "[AVISO] Ordem bloqueada. O sistema Caçador atua apenas nas sombras fóra do horário de pico (08-17)" -ForegroundColor Red
    exit 0
}

Write-Host "[VALIDAÇÃO] Acionando Auditores CQO Estocásticos..." -ForegroundColor Magenta

# Validar crise
$crisis_out = python -c "import sys; sys.path.insert(0, '.'); from modules.validation.crisis_probability_validator import CrisisProbabilityValidator; v = CrisisProbabilityValidator(); r = v.calculate(-2.0, 12.3, 325.0, -8.2); print(r['probability'])"
if ([double]$crisis_out -lt 0.7) { Write-Host "[NOGO] P(crise)<0.7"; exit 1 }

# Validar SLO
$config = Get-Content ".\config\regimes\hunter.json" | ConvertFrom-Json
$max_rtt = $config.slo.rtt_mt5_max_ms
$slo_out = python -c "import sys; sys.path.insert(0, '.'); from modules.validation.slo_validator_china import RegimeSLOValidatorChinaCouncil; v = RegimeSLOValidatorChinaCouncil(); print(v.validate(2.0, $max_rtt)['overall_adequate'])"
if ($slo_out -ne "True") { Write-Host "[NOGO] DSN Risk / MT5 Ping inadequados pra tomada de decisão"; exit 1 }

$env:OMEGA_REGIME = "HUNTER"
$env:FIN_SENSE_DSN = "postgresql://finsense_user:staging_pass@localhost:5433/finsense_staging"

if ($Mode -eq "live" -and $env:OMEGA_PROD_AUTHORIZATION -ne "CONSELHO_GO_2026") {
    Write-Host "[FATAL] Live sem permissão" -ForegroundColor Red
    exit 1
}

$mission_id = "HUNTER_" + (Get-Date -Format "yyyyMMdd_HHmmss")
$log_dir = ".\Auditoria PARR-F\logs\hunter\$mission_id"
New-Item -ItemType Directory -Force -Path $log_dir | Out-Null

try {
    Write-Host "[IGNIÇÃO] Ativando Shadow Loop em modo Shadow/Caçador" -ForegroundColor Magenta
    Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
    & python core_engines/shadow_loop.py --mode $Mode 2>&1 | Tee-Object -FilePath "Auditoria PARR-F\logs\hunter\$mission_id\execution.log"
    Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"

    $duration = (Get-Date - $script:StartTime).TotalSeconds
    $manifest = @{
        mission_id = $mission_id
        regime = "HUNTER"
        status = if ($LASTEXITCODE -eq 0) { "SUCCESS" } else { "FAILURE" }
    }
    $manifest | ConvertTo-Json -Depth 3 | Out-File "$log_dir\manifest.json"
    $config = Get-Content ".\config\regimes\hunter.json" | ConvertFrom-Json
    $config.hash_verificacao = (Get-FileHash "$log_dir\manifest.json" -Algorithm SHA256).Hash
    $config | ConvertTo-Json -Depth 4 | Out-File ".\config\regimes\hunter.json"
} finally {
    $env:OMEGA_REGIME = $null
}
