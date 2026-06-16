# OMEGA — arranque 24/7 (MT5 tem de estar aberto e ligado à conta)
# CEO 2026-05-20: MODO DEMO TESTE — conta demo, fallback ON para gerar ordens + gates P0 activos
# RCV P0 (M1-M4) mantém-se em shadow_loop.py; reiniciar runner após alterar envs
$ErrorActionPreference = "Stop"
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$env:PYTHONPATH = (Get-Location).Path

# ─── DEMO TESTE: fallback ON quando IA=HOLD (sem isto = 0 ordens em 10h) ─────
# Rollback diagnóstico silencioso: "1"
$env:OMEGA_DISABLE_MOMENTUM_FALLBACK = "0"

# Rastreio por componente/skip (veredito 24h): audit/paper/decision_trace.jsonl
$env:OMEGA_DECISION_TRACE = "1"

# Intervalo entre ciclos (segundos) — reduzido para capturar mais oportunidades
$env:OMEGA_LOOP_INTERVAL_SEC = "20"

# paper | shadow
$env:OMEGA_24X7_MODE = "paper"

# ─── DEMO TESTE: risco moderado (conta demo — CEO autoriza teste real) ───────
$env:OMEGA_RISK_PER_TRADE = "0.005"

# Até 8 posições simultâneas para ver execução P0 sem cluster extremo
$env:OMEGA_MAX_POSITIONS = "8"

# Gates P0 relaxados só em demo (spread 2x em vez de 3x; M1 aceita 1/3 velas)
$env:OMEGA_SPREAD_GUARD_MULT = "2.0"
$env:OMEGA_M1_MIN_CONFIRMED = "1"
$env:OMEGA_MIN_CONFLUENCE = "35"

# DRAWDOWN: 10% diário (era 2%) — espaço operacional para 15 posições de risco 1%
$env:OMEGA_DD_DAILY_MAX = "0.10"

# DIVERSIFICAÇÃO: 2 ordens por direção por ciclo (era 1), 5 por classe (era 2)
$env:OMEGA_MAX_SAME_DIR_PER_CYCLE = "2"
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

# Portfolio discovery (16 símbolos Hantec) via schedule — NÃO usar lista fixa em env
$env:OMEGA_ASSET_PROFILE = "ceo_discovery_full"
# P0 T-W1/T-W2: omega_asset_schedule.json + re-resolve por ciclo (sem OMEGA_24X7_ATIVOS)

# Equity real via MT5 no arranque (P2-A BUG-5) — sem --equity hardcoded
python -u scripts/omega_paper_loop_24x7.py `
  --timeframes H1 M15 H4 `
  --pre-sync-ohlcv
