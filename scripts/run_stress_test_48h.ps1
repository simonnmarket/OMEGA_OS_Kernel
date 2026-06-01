# =============================================================================
# OMEGA STRESS TEST - 48 HORAS - PORTFOLIO COMPLETO
# =============================================================================

param(
    [int]$DurationHours = 48,
    [string]$Mode = "paper"
)

$ErrorActionPreference = "Continue"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = $RepoRoot
Push-Location $RepoRoot

$startTime = Get-Date
$endTime = $startTime.AddHours($DurationHours)

Write-Host "============================================================================" -ForegroundColor Red
Write-Host " OMEGA STRESS TEST - PORTFOLIO COMPLETO (14 ATIVOS)" -ForegroundColor Yellow
Write-Host " Inicio : $startTime" -ForegroundColor Yellow
Write-Host " Termino: $endTime" -ForegroundColor Yellow
Write-Host " Modo   : $Mode (TODOS OS MODULOS ATIVOS)" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Red

$cycleCount = 0
$successCount = 0
$failCount = 0
$tradesByAsset = @{}

while ((Get-Date) -lt $endTime) {
    $cycleCount++
    $cycleStart = Get-Date
    
    Write-Host "`n[CICLO $cycleCount] $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Magenta
    
    $env:OMEGA_REGIME = "HUNTER"
    $env:FIN_SENSE_DSN = "postgresql://finsense_user:staging_pass@localhost:5433/finsense_staging"
    
    $result = python core_engines/shadow_loop.py --mode $Mode 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        $successCount++
        Write-Host "[OK] Ciclo concluido" -ForegroundColor Green
    } else {
        $failCount++
        Write-Host "[WARN] Ciclo com exit code: $exitCode" -ForegroundColor Yellow
        Write-Host $result -ForegroundColor Gray
    }
    
    $cycleDuration = (Get-Date) - $cycleStart
    Write-Host "[INFO] Duracao: $([math]::Round($cycleDuration.TotalSeconds, 1))s" -ForegroundColor Gray
    
    $waitTime = 180
    for ($i = $waitTime; $i -gt 0; $i -= 30) {
        if ((Get-Date) -ge $endTime) { break }
        Start-Sleep -Seconds 30
    }
}

Write-Host "`n============================================================================" -ForegroundColor Red
Write-Host " STRESS TEST FINALIZADO" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Red
Write-Host " Duracao total : $([math]::Round(((Get-Date) - $startTime).TotalHours, 2)) horas" -ForegroundColor White
Write-Host " Total ciclos  : $cycleCount" -ForegroundColor White
Write-Host " Sucessos      : $successCount" -ForegroundColor Green
Write-Host " Falhas        : $failCount" -ForegroundColor $(if ($failCount -gt 0) { "Yellow" } else { "White" })
Write-Host "============================================================================" -ForegroundColor Red

Pop-Location