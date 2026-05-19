# OMEGA — arranque 24/7 (MT5 tem de estar aberto e ligado à conta)
# CKO 2026-05-20: MODO DIAGNÓSTICO CIRÚRGICO 24h (após RCV P0 mandatos em shadow_loop.py)
# RCV P0: não reiniciar sem validar logs [EQUITY] + [MOMENTUM_FALLBACK] DISABLED + gates activos
$ErrorActionPreference = "Stop"
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$env:PYTHONPATH = (Get-Location).Path

# ─── CEO 2026-05-20: corrida verificação 24h — fallback OFF (H1 / D2) ─────────
# OIS-DIAG-20260517: P0-A=1 desactiva fallback EMA8/21 quando IA não decide.
# Env tem precedência sobre config/live_flags.json. Rollback 24/7 antigo: "0".
$env:OMEGA_DISABLE_MOMENTUM_FALLBACK = "1"

# Rastreio por componente/skip (veredito 24h): audit/paper/decision_trace.jsonl
$env:OMEGA_DECISION_TRACE = "1"

# Intervalo entre ciclos (segundos) — reduzido para capturar mais oportunidades
$env:OMEGA_LOOP_INTERVAL_SEC = "20"

# paper | shadow
$env:OMEGA_24X7_MODE = "paper"

# ─── CKO OVERRIDE: MODO DIAGNÓSTICO CIRÚRGICO 24H ───────────────────────────
# 0.2% risco (~$2.5/trade em conta ~$1250) — sobreviver 24h para decision_trace
$env:OMEGA_RISK_PER_TRADE = "0.002"

# Exposição controlada (5 pos — evita cluster SL correlacionado)
$env:OMEGA_MAX_POSITIONS = "5"

# DRAWDOWN: 10% diário (era 2%) — espaço operacional para 15 posições de risco 1%
$env:OMEGA_DD_DAILY_MAX = "0.10"

# DIVERSIFICAÇÃO: 2 ordens por direção por ciclo (era 1), 5 por classe (era 2)
$env:OMEGA_MAX_SAME_DIR_PER_CYCLE = "2"
$env:OMEGA_MAX_POS_PER_CLASS = "5"

# POR ATIVO: 1 posição por ativo (CEO 2026-05-14 FIX — escalamento via pyramid progressivo)
# 2ª posição só via check_pyramid_add() com lot 1.5× maior (não mesmo volume)
$env:OMEGA_MAX_POS_PER_ASSET = "1"
$env:OMEGA_PYRAMID_LAYERS = "2"       # max 2 camadas pyramid por ativo
$env:OMEGA_PYRAMID_LOT_SCALE = "1.5"  # 2ª camada = 1.5× a 1ª
$env:OMEGA_PYRAMID_ATR = "0.5"        # activar pyramid quando profit >= 0.5×ATR

# TP/SL RATIO: cap máximo 3:1 (era 8:1) — evita TPs irrealistas como US30 TP=16907pts
$env:OMEGA_MAX_TP_SL_RATIO = "3.0"

# LOT CAP global: 0.50 lotes máximo por ordem (era 0.20)
$env:OMEGA_LOT_MAX = "0.50"

# ALINHAMENTO MTF: mínimo 20% — FIX #4-REV (CEO 2026-05-14)
$env:OMEGA_MTF_ALIGN_MIN = "0.20"

# ─── CEO 2026-05-15: alavanca única MTF — peso W1=2 (destrava sinais vs burocracia semanal) ──
$env:OMEGA_MTF_W1_WEIGHT = "2"

# ─── PSA/Conselho 2026-05-15 (CONGELADO 24h — não activar sem ordem CEO) ──
# Opcional — relaxar APENAS TFs listados para alinhamento mínimo mais baixo no intraday:
# $env:OMEGA_MTF_ALIGN_MIN_INTRADAY = "0.12"
# $env:OMEGA_MTF_RELAX_TFS = "M15,H1"

# ─── EDGE_GATE: vol_ratio reduzido — CEO 2026-05-14 ─────────────────────────
# Dados reais: vol_ratio tipico = 0.19-0.28. Threshold 0.30 bloqueava 291 sinais/sessao.
$env:OMEGA_VOL_MIN_FOREX = "0.10"
$env:OMEGA_VOL_MIN_METAL = "0.10"
$env:OMEGA_VOL_MIN_INDEX = "0.10"
$env:OMEGA_VOL_MIN_CRYPTO = "0.12"
$env:OMEGA_VOL_MIN_CRYPTO_ALT = "0.08"
# GER40/US30 ATR threshold reduzido (bloqueado a 0.076% < 0.080%)
$env:OMEGA_EDGE_INDEX_ATR = "0.0005"
$env:OMEGA_EDGE_INDEX_ADX = "13.0"

# RUNNER SINGLETON: máximo 1 instância simultânea — FIX #5 (CEO 2026-05-14)
$env:OMEGA_RUNNER_MAX_PARALLEL = "1"

# ESCALAR LOTES AO TP USD mínimo
$env:OMEGA_SCALE_LOT_TO_MIN_TP_USD = "1"

# Portfolio completo: Forex + Metals + Oils + Indices + Crypto
$env:OMEGA_24X7_ATIVOS = "EURUSD GBPUSD USDJPY AUDUSD NZDUSD USDCAD USDCHF EURJPY GBPJPY AUDJPY CADJPY CHFJPY XAUUSD XAGUSD UKOIL+ USOIL+ GER40 UK100 US500 US30 BTCUSD ETHUSD SOLUSD BNBUSD LTCUSD XRPUSD ADAUSD AVAXUSD DOGUSD DOTUSD UNIUSD XLMUSD"

# Equity real via MT5 no arranque (P2-A BUG-5) — sem --equity hardcoded
python -u scripts/omega_paper_loop_24x7.py `
  --timeframes H1 M15 H4 `
  --pre-sync-ohlcv
