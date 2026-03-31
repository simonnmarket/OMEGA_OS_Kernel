# PSA — Gate único Tier-0 (PowerShell)
# Executa: git HEAD + audit_trade_count + verify_tier0_psa + resumo PASS/FAIL

$ErrorActionPreference = "Stop"
$RepoRoot = "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
if ($env:NEBULAR_KUIPER_ROOT) { $RepoRoot = $env:NEBULAR_KUIPER_ROOT }

Set-Location -LiteralPath $RepoRoot
$env:NEBULAR_KUIPER_ROOT = $RepoRoot

$py = Join-Path $RepoRoot "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py"
Write-Host "Repo: $RepoRoot"
Write-Host "Script: $py"
python -u "$py" @args
exit $LASTEXITCODE
