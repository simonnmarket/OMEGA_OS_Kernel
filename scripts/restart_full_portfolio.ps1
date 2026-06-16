# OMEGA — Reinício portfolio completo (delega para run_omega_24x7 — zero conflito T-W1/T-W2)
# CEO 2026-05-25: NÃO define OMEGA_24X7_ATIVOS fixo; usa config/omega_asset_schedule.json perfil ceo_discovery_full
#
# Uso:
#   cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
#   .\scripts\restart_full_portfolio.ps1

$ErrorActionPreference = "Stop"
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " OMEGA 24x7 — Portfolio Discovery (CEO)" -ForegroundColor Cyan
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host " Perfil: ceo_discovery_full (16 simbolos via schedule)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Delegando para run_omega_24x7.ps1 (T-W1 + T-W2 activos)..." -ForegroundColor Green
Write-Host ""

& "$PSScriptRoot\run_omega_24x7.ps1"
