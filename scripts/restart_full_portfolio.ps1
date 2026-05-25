# OMEGA — Reinício com portfolio completo (todas as classes)
# AVISO P0-ABC 20260525: lista fixa 16 simbolos — NAO alinhado T-W1 / omega_asset_schedule.json
# Pos-P0 DEMO: usar scripts/run_omega_24x7.ps1 ou scripts/omega_demo_go_live.ps1
# DOC-OMEGA-ECOSISTEMA-AUDITORIA-2026-002 — C-01, C-02, C-03 aprovados
#
# QUANDO USAR:
#   1. Parar o processo 24x7 actual (CTRL+C na janela onde está a correr)
#   2. Executar este script a partir de C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
#
# USO:
#   cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
#   .\scripts\restart_full_portfolio.ps1
#
# JANELA DE EXECUÇÃO RECOMENDADA: esta noite ~23:45 Berlin (21:45 UTC)
# — Forex + Metais + Índices abrem 00:00 Berlin (22:00 UTC)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " OMEGA 24x7 — Reinicio Portfolio Completo" -ForegroundColor Cyan
Write-Host " $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') Berlin (UTC+2)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── Caminho raiz ─────────────────────────────────────────────────────────────
$ROOT = (Get-Location).Path
$env:PYTHONPATH = $ROOT

# ── C-01: Lista completa de símbolos (todos confirmados no broker Hantec) ────
# NAS100 = US100 no broker HantecMarkets
$env:OMEGA_24X7_ATIVOS = "EURUSD GBPUSD USDJPY AUDUSD USDCAD XAUUSD US500 US100 BTCUSD ETHUSD SOLUSD XRPUSD AVAXUSD ADAUSD LTCUSD BNBUSD"
$env:OMEGA_24X7_MODE   = "paper"

# ── C-02: Piso TP mínimo reduzido (1.25→0.80 USD) + escala de lote ──────────
$env:OMEGA_MIN_TP_USD_CRYPTO_ALT    = "0.80"
$env:OMEGA_SCALE_LOT_TO_MIN_TP_USD  = "1"

# ── C-03: Vol ratio crypto reduzido para trial paper (0.18→0.10) ────────────
# 0.10 desbloqueia ETH/SOL (estavam a ~0.15 ratio) sem entrar em ruído puro
# (0.05 foi proposto mas é demasiado agressivo — análise técnica independente)
$env:OMEGA_VOL_MIN_CRYPTO = "0.10"

# ── Guardrails: NÃO ALTERAR (excepção: MAX_POSITIONS definido aqui) ─────────
# DD_DAILY_MAX=0.01 e RISK_PER_TRADE=0.0025 permanecem no código
# MAX_POSITIONS=0 no código = ilimitado; para demo 16 símbolos usamos 6
# (permite diversificação mas contém exposição simultânea)
$env:OMEGA_MAX_POSITIONS = "6"
# OMEGA_NIGHT_PASS não definido (DEMO_WINDOW=0-24 já cobre 24/5)

Write-Host ""
Write-Host "Configuracao activa:" -ForegroundColor Yellow
Write-Host "  OMEGA_24X7_ATIVOS   = $env:OMEGA_24X7_ATIVOS"
Write-Host "  OMEGA_24X7_MODE     = $env:OMEGA_24X7_MODE"
Write-Host "  MIN_TP_USD_CRYPTOALT= $env:OMEGA_MIN_TP_USD_CRYPTO_ALT"
Write-Host "  SCALE_LOT_TO_MINTP  = $env:OMEGA_SCALE_LOT_TO_MIN_TP_USD"
Write-Host "  VOL_MIN_CRYPTO      = $env:OMEGA_VOL_MIN_CRYPTO"
Write-Host "  MAX_POSITIONS       = $env:OMEGA_MAX_POSITIONS"
Write-Host ""
Write-Host "Simbolos: 16 (5 Forex + 1 Metal + 2 Indices + 8 Crypto)" -ForegroundColor Green
Write-Host "Timeframes: H1 M15 H4" -ForegroundColor Green
Write-Host ""

# ── Verificação rápida de símbolos no MT5 antes de arrancar ──────────────────
Write-Host "Verificando simbolos no MT5..." -ForegroundColor Yellow
$checkResult = python -c "
import sys; sys.path.insert(0,'$ROOT'.replace('\\\\','\\'))
import MetaTrader5 as mt5
mt5.initialize()
symbols = '$env:OMEGA_24X7_ATIVOS'.split()
fail = [s for s in symbols if mt5.symbol_info(s) is None]
mt5.shutdown()
if fail: print('FAIL:', ' '.join(fail))
else: print('OK: todos os simbolos presentes no broker')
"
Write-Host $checkResult
if ($checkResult -like "*FAIL*") {
    Write-Host "[AVISO] Alguns simbolos nao encontrados. Remova-os antes de continuar." -ForegroundColor Red
    Write-Host "Premir ENTER para continuar mesmo assim, ou CTRL+C para abortar."
    Read-Host
}

Write-Host ""
Write-Host "A iniciar omega_paper_loop_24x7.py..." -ForegroundColor Green
python -u scripts/omega_paper_loop_24x7.py --timeframes H1 M15 H4
