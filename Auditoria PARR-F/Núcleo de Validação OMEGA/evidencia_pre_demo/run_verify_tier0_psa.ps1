# Verificação Tier-0 — executar na pasta do repositório ou definir NEBULAR_KUIPER_ROOT
$ErrorActionPreference = "Stop"
$RepoRoot = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
if ($env:NEBULAR_KUIPER_ROOT) { $RepoRoot = $env:NEBULAR_KUIPER_ROOT }

Set-Location -LiteralPath $RepoRoot
$env:NEBULAR_KUIPER_ROOT = $RepoRoot

$py = Join-Path $RepoRoot "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\verify_tier0_psa.py"
Write-Host "Repo: $RepoRoot"
Write-Host "Script: $py"
python -u "$py"
exit $LASTEXITCODE
