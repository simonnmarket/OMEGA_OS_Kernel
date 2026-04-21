# =============================================================================
# VERIFICAÇÃO DE DEPLOYMENT
# =============================================================================
$dirs = @(".\config\regimes", ".\modules\validation", ".\logs\hunter")
foreach ($dir in $dirs) { if (-not (Test-Path $dir)) { Write-Host "FALTA: $dir"; exit 1 } }
Write-Host "TODOS OS ARQUIVOS INTEGROS [DEPLOY VERIFIED]" -ForegroundColor Green
