# OMEGA - Madrugada pos-P0 - PORTFOLIO COMPLETO (CEO 2026-05-21)
# Pre-requisito: Gate G1-G5 PASS + commit P0 pushed
# Ref: PSA-EXEC-FINAL-MADRUGADA-20260521-v3
# P0-ABC 20260522: OMEGA_USE_V2=0 — PROIBIDO (runner usa shadow_loop.py v1 apenas)
$ErrorActionPreference = "Stop"
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_ROOT = (Get-Location).Path

$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_DECISION_TRACE = "1"
$env:OMEGA_LOOP_INTERVAL_SEC = "20"
$env:OMEGA_24X7_MODE = "paper"
$env:OMEGA_DISABLE_MOMENTUM_FALLBACK = "0"
$env:OMEGA_RUNNER_MAX_PARALLEL = "1"

# Risco madrugada: moderado (nao repetir stress 20/05)
$env:OMEGA_RISK_PER_TRADE = "0.003"
$env:OMEGA_DD_DAILY_MAX = "0.08"
$env:OMEGA_MAX_POSITIONS = "8"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
$env:OMEGA_LOT_MAX = "0.30"

# EDGE_GATE: usar relaxamento calibrado (nao esperar magic fix abrir gates)
$env:OMEGA_VOL_MIN_FOREX = "0.10"
$env:OMEGA_VOL_MIN_METAL = "0.10"
$env:OMEGA_VOL_MIN_INDEX = "0.10"
$env:OMEGA_VOL_MIN_CRYPTO = "0.12"
$env:OMEGA_VOL_MIN_CRYPTO_ALT = "0.08"
$env:OMEGA_EDGE_INDEX_ATR = "0.0005"
$env:OMEGA_EDGE_INDEX_ADX = "13.0"
$env:OMEGA_MIN_CONFLUENCE = "35"
$env:OMEGA_SPREAD_GUARD_MULT = "2.0"

# MTF weights
$env:OMEGA_MTF_W1_WEIGHT = "2"
$env:OMEGA_MTF_ALIGN_MIN = "0.20"

# PORTFOLIO COMPLETO
# P0-ABC 20260522 Fase 0b T-W1: REMOVIDO lista fixa — usa omega_asset_schedule.json
# $env:OMEGA_24X7_ATIVOS = "EURUSD GBPUSD USDJPY AUDUSD NZDUSD USDCAD USDCHF EURJPY GBPJPY AUDJPY CADJPY CHFJPY XAUUSD XAGUSD UKOIL+ USOIL+ GER40 UK100 US500 US30 BTCUSD ETHUSD SOLUSD BNBUSD LTCUSD XRPUSD ADAUSD AVAXUSD DOGUSD DOTUSD UNIUSD XLMUSD"

Write-Host "[OMEGA] MADRUGADA pos-P0 | magic=234001 | portfolio completo | $(Get-Date -Format 'HH:mm:ss')"
Write-Host "[OMEGA] Log: audit/paper/omega_24x7_runner.log"
Write-Host "[OMEGA] Risco: OMEGA_RISK_PER_TRADE=$env:OMEGA_RISK_PER_TRADE | DD_MAX=$env:OMEGA_DD_DAILY_MAX"
Write-Host "[OMEGA] Iniciando runner..."

python -u scripts/omega_paper_loop_24x7.py --timeframes H1 M15 H4 --pre-sync-ohlcv
