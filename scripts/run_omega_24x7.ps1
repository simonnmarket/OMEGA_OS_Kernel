# OMEGA — arranque 24/7 (MT5 tem de estar aberto e ligado à conta)
# CEO 2026-05-20: MODO DEMO TESTE — conta demo, fallback ON para gerar ordens + gates P0 activos
# RCV P0 (M1-M4) mantém-se em shadow_loop.py; reiniciar runner após alterar envs
$ErrorActionPreference = "Stop"
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$env:PYTHONPATH = (Get-Location).Path
$_isTestHarness = $env:OMEGA_TEST_HARNESS -eq "1"

# ─── DEMO TESTE: fallback ON quando IA=HOLD (sem isto = 0 ordens em 10h) ─────
# Rollback diagnóstico silencioso: "1"
$env:OMEGA_DISABLE_MOMENTUM_FALLBACK = "0"

# Rastreio por componente/skip (veredito 24h): audit/paper/decision_trace.jsonl
$env:OMEGA_DECISION_TRACE = "1"

# Intervalo entre ciclos (segundos) — reduzido para capturar mais oportunidades
if (-not $_isTestHarness) {
    $env:OMEGA_LOOP_INTERVAL_SEC = "20"
}

# paper | shadow — CKO P0: obrigatorio; omega_paper_loop aborta se ausente
$env:OMEGA_24X7_MODE = "paper"

# SEL/USFE — CKO 20260601: toggles activos + enforcement em pre_execution_safety_check
$env:OMEGA_SEL_ENABLED = "1"
$env:OMEGA_ENFORCE_SEL_USFE_GATE = "1"
$env:OMEGA_USFE_BLOCK = "1"
$env:OMEGA_SKIP_SEL_USFE_ENFORCE = "0"
if (-not $_isTestHarness) {
    $env:OMEGA_RUPTURE_CAPTURE = "0"
}
$env:OMEGA_SEL_SLOT_RP = "0.8"

# ─── DEMO TESTE: risco moderado (conta demo — CEO autoriza teste real) ───────
$env:OMEGA_RISK_PER_TRADE = "0.005"

# Até 8 posições simultâneas para ver execução P0 sem cluster extremo
$env:OMEGA_MAX_POSITIONS = "8"

# Gates P0 relaxados só em demo (spread 2x em vez de 3x; M1 bypassed em paper)
$env:OMEGA_SPREAD_GUARD_MULT = "2.0"
$env:OMEGA_M1_MIN_CONFIRMED = "0"   # Fix Bug2: bypass candle-count (paper/demo sem M1 real)
$env:OMEGA_MIN_CONFLUENCE = "35"
# CEO-MANDATO-C+A: MIN_CONFIDENCE=0.62 efectivo (era 0.65 hardcoded)
$env:OMEGA_MIN_CONFIDENCE = "0.62"

# DRAWDOWN: 10% diário (era 2%) — espaço operacional para 15 posições de risco 1%
$env:OMEGA_DD_DAILY_MAX = "0.10"

# DIVERSIFICAÇÃO: 2 ordens por direção por ciclo (era 1), 5 por classe (era 2)
$env:OMEGA_MAX_SAME_DIR_PER_CYCLE = "1"  # P0-REMEDIAÇÃO-8Q: default 2→1 (bloqueia duplicação direção/ciclo)
$env:OMEGA_MAX_POS_PER_CLASS = "5"

# POR ATIVO: RiskBudgetManager calcula slots dinamicamente (CEO Mandato 2026-05-26)
# OMEGA_MAX_POS_PER_ASSET REMOVIDO — substituído por cálculo ATR×equity×risco
# Activar: OMEGA_USE_RISK_BUDGET=1 | fallback legacy: OMEGA_USE_RISK_BUDGET=0
$env:OMEGA_USE_RISK_BUDGET = "1"
$env:OMEGA_RISK_MAX_DD_PCT = "0.02"        # 2% equity total em risco simultâneo
$env:OMEGA_RISK_PER_POS_PCT = "0.005"      # 0.5% equity por posição
$env:OMEGA_RISK_BUDGET_HARD_CAP = "8"      # hard cap absoluto de segurança
# FastLoop assíncrono: peak drawdown + AI exit + timeout (Gate G4 latência ≤5s)
$env:OMEGA_USE_FASTLOOP = "1"
$env:OMEGA_FASTLOOP_INTERVAL = "2.0"       # segundos entre checks por posição
$env:OMEGA_AI_FLIP_CONFIDENCE = "0.75"     # confidence mínima para AI exit/flip
$env:OMEGA_FASTLOOP_TIMEOUT_MIN = "60.0"   # timeout sideways em minutos
$env:OMEGA_PEAK_CLOSE_PTS = "500.0"        # retracção total para fechar (pts)
$env:OMEGA_PEAK_PARTIAL_PTS = "600.0"      # retracção para fechar 50% (pts)
$env:OMEGA_MIN_PEAK_PTS = "100.0"          # pico mínimo para activar protecção
# Log em PONTOS (CEO Mandato Gate G2)
$env:OMEGA_LOG_UNIT = "POINTS"
$env:OMEGA_PYRAMID_LAYERS = "2"       # max 2 camadas pyramid por ativo
$env:OMEGA_PYRAMID_LOT_SCALE = "1.5"  # 2ª camada = 1.5× a 1ª
$env:OMEGA_PYRAMID_ATR = "0.5"        # activar pyramid quando profit >= 0.5×ATR

# TP/SL RATIO: cap máximo 3:1 (era 8:1) — evita TPs irrealistas como US30 TP=16907pts
$env:OMEGA_MAX_TP_SL_RATIO = "3.0"
# P0-REMEDIAÇÃO-8Q: índices merecem R:R maior (ex: US500 2647 pts vs TP $3.15)
$env:OMEGA_MAX_TP_SL_RATIO_INDEX = "10.0"
# CEO MANDATE 2026-05-27: slots por ativo via RiskBudget (ATR×equity) — NÃO cap fixo=1
# (cap=1 prendia ordem micro-lucro e bloqueava o dia inteiro — ver RELATORIO_CONSELHO_CEO_MANDATE_20260527)
# Legacy fallback só se OMEGA_USE_RISK_BUDGET=0: $env:OMEGA_MAX_POS_PER_ASSET = "0"

# SL CAPS por regime — calibrados para escala de pontos de cada classe (BUG FIX 2026-05-27)
#
# Problema: OMEGA_SL_MAX_<regime> estava em MT5-points mas a escala varia por ativo:
#   EURUSD: 1pt=$0.00001 → 150pts=15pips (correcto)
#   XAUUSD: 1pt=$1.00/lot → cap250=$250/lot (ERRADO, ATR H4~$2924/lot)
#   BTCUSD: 1pt=$0.01/lot → cap1500=$15/lot (ERRADO, ATR H4~$727/lot)
#   XRPUSD: 1pt=$0.01/lot → cap1500=$15/lot (OK, ATR H4~$15/lot)
#
# Fix: METAL→3000 (XAUUSD $30/lot ≈ 1x ATR H4) | CRYPTO→80000 (BTC $800/lot > ATR H4)
# Trailing stop usará o ATR correcto; lot_size calculado sobre SL real → risco=0.5% target
$env:OMEGA_SL_MAX_METAL  = "3000"   # XAUUSD/XAGUSD: ponto=0.01, 3000pts=$30/lot
$env:OMEGA_SL_MAX_FOREX  = "150"    # EURUSD etc: 150pts=15pips
$env:OMEGA_SL_MAX_INDEX  = "600"    # US500/US100
$env:OMEGA_SL_MAX_CRYPTO = "80000"  # BTCUSD: ponto=0.01, ATR H4~72656pts; XRP/BNB<<80000 inalterado

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
# XAUUSD: sessões de baixa vol (ex. feriado US) — demo precisa passar EDGE_GATE para validar SL H4
$env:OMEGA_EDGE_METAL_ATR = "0.0005"

# PROIBIDO v2 em produção runner (P0 T-P2b)
$env:OMEGA_USE_V2 = "0"

# RUNNER SINGLETON: máximo 1 instância simultânea — FIX #5 (CEO 2026-05-14)
$env:OMEGA_RUNNER_MAX_PARALLEL = "1"

# ESCALAR LOTES AO TP USD mínimo
$env:OMEGA_SCALE_LOT_TO_MIN_TP_USD = "1"

# CEO 2026-05-25: ecossistema UNIFICADO — um núcleo, portfolio e limites sincronizados
$env:OMEGA_ECOSYSTEM_UNIFIED = "1"
$env:OMEGA_USE_SIGNAL_FUSION = "1"
$env:PSA_SHADOW_MODE = "0"
$env:FUSION_MIN_CONFIDENCE = "0.55"
$env:OMEGA_LOOP_PSA_V12 = "1"

# USFE v1.1.2 — L6 + gate paralelo (peso 0 em confluência; block via OMEGA_USFE_BLOCK)
$env:OMEGA_USFE_ENABLED = "1"

# FORCE NOW 20260601 — pisos TP/USD fundo (não migalhas)
$env:OMEGA_MIN_TP_USD_INDEX = "25"
$env:OMEGA_MIN_TP_USD_FOREX = "10"
$env:OMEGA_MIN_TP_USD_METAL = "18"
$env:OMEGA_MIN_TP_USD_CRYPTO = "15"
$env:OMEGA_MIN_TP_USD_CRYPTO_ALT = "8"
$env:OMEGA_SCALE_LOT_TO_MIN_TP_USD = "1"
$env:OMEGA_FORCE_HIGH_PERFORMANCE = "1"

# FORCE NOW — stale exit acelerado (posições presas)
$env:OMEGA_STALE_PROFIT_USD = "3.0"
$env:OMEGA_STALE_HOURS = "2"
$env:OMEGA_STALE_ACTION = "CLOSE"

# CEO CAPTURE MATRIX 2026-06-03 — fio morto ACT->PLUG corrigido
$env:OMEGA_TEST_HARNESS = "0"
$env:OMEGA_USE_SEL_IMPACT_TP = "1"
$env:OMEGA_PYRAMID_MIN_SCORE_METAL = "0.35"
$env:OMEGA_EDGE_BYPASS_WINNER = "1"
$env:OMEGA_ALLOW_SCALE_ENTRIES = "1"
$env:OMEGA_MIN_LOT_METAL = "0.05"
$env:OMEGA_MAX_SAME_DIR_PER_CYCLE = "3"
$env:OMEGA_PYRAMID_LAYERS = "4"

# CEO P0 PLUG ENTRADA 2026-06-04 — Modo Ofensivo Teste (1 ordem = KPI)
$env:OMEGA_P0_PLUG_ENTRADA = "1"
$env:OMEGA_IA_OVERRIDE_MTF = "1"
$env:OMEGA_IA_OVERRIDE_MTF_CONF = "0.80"
$env:OMEGA_P0_XAU_RELAX_RISK = "1"
$env:OMEGA_P0_XAU_RISK_PCT = "0.03"
$env:OMEGA_ECON_GATE_ATR_FALLBACK = "1"
$env:OMEGA_RUPTURE_CAPTURE = "1"
# P0.2: última milha — SEL/USFE não pode matar sinal após ECON_OPEN (CEO 04/Jun)
$env:OMEGA_SKIP_SEL_USFE_ENFORCE = "1"
# Fix Bug2: M1-GATE bypass total em paper/demo (quality=0.45 < 0.50 — sem dados M1 reais)
$env:OMEGA_SKIP_M1_GATE = "1"

# Portfolio discovery (16 símbolos Hantec) via schedule — NÃO usar lista fixa em env
$env:OMEGA_ASSET_PROFILE = "ceo_discovery_full"
# P0 T-W1/T-W2: omega_asset_schedule.json + re-resolve por ciclo (sem OMEGA_24X7_ATIVOS)

# Equity real via MT5 no arranque (P2-A BUG-5) — sem --equity hardcoded
python -u scripts/omega_paper_loop_24x7.py `
  --timeframes H1 M15 H4 `
  --pre-sync-ohlcv
