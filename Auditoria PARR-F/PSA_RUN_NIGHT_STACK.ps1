param(
    [switch]$SkipManifestVerify,
    [switch]$SkipLiveDemo
)

$ErrorActionPreference = "Stop"

$env:NEBULAR_KUIPER_ROOT="C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:PSA_AUDIT_BASE="$env:NEBULAR_KUIPER_ROOT\Auditoria PARR-F"

Write-Host "[*] Inicializando PSA NIGHT STACK"
Write-Host "NEBULAR_KUIPER_ROOT: $env:NEBULAR_KUIPER_ROOT"
Write-Host "PSA_AUDIT_BASE: $env:PSA_AUDIT_BASE"

# Ativando Camadas Avancadas do Orquestrador Tier-0
$env:OMEGA_USE_FIN_SENSE_L1="1"
$env:OMEGA_AUDIT_DIR="$env:PSA_AUDIT_BASE\00_PROVAS_AUDITORIA\tier0_night_runs"
$env:OMEGA_MOMENTUM_THRESHOLD="0.001"

if (-not (Test-Path $env:OMEGA_AUDIT_DIR)) {
    New-Item -ItemType Directory -Force -Path $env:OMEGA_AUDIT_DIR | Out-Null
}

Write-Host "[*] Executando KernelDecisionLayer Tier-0 Completo (Multi-TF + Física Lote via Env)..."
for ($i=1; $i -le 3; $i++) {
    python "$env:PSA_AUDIT_BASE\omega_orquestador_tier0_v120.py"
    Start-Sleep -Seconds 2
}

Write-Host "[OK] Stack Noturno Base Finalizado"
