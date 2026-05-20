# OMEGA — modo diagnóstico pós-remediação CICC (CEO 2026-05-20)
# 3 pares forex + gate portfolio (XAU/BTC mínimos) + fallback OFF
$ErrorActionPreference = "Stop"
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_ROOT = (Get-Location).Path

$env:OMEGA_DIAGNOSTIC_MODE = "1"
$env:OMEGA_DISABLE_MOMENTUM_FALLBACK = "1"
$env:OMEGA_RISK_PER_TRADE = "0.002"
$env:OMEGA_DD_DAILY_MAX = "0.05"
$env:OMEGA_MAX_POSITIONS = "3"
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_DECISION_TRACE = "1"
$env:OMEGA_LOOP_INTERVAL_SEC = "30"
$env:OMEGA_24X7_MODE = "paper"
# Portfolio gate do runner exige XAU+BTC; forex foco + obrigatórios
$env:OMEGA_24X7_ATIVOS = "EURUSD GBPUSD USDJPY XAUUSD BTCUSD"

Write-Host "[OMEGA] Modo diagnostico CICC — madrugada. Log: audit/paper/omega_24x7_runner.log"
python -u scripts/omega_paper_loop_24x7.py --timeframes H1 M15 --pre-sync-ohlcv
