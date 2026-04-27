# OMEGA INSTITUTIONAL ANALYSIS — v2.5
## Forense Completa | Gap Analysis | Plano Executivo para $1000/dia
**Emitente:** Arquiteto OMEGA (CRO/CTO/CQO)  
**Data:** 2026-04-28  
**Status:** PAPEL — IA_ON pendente autorização

---

## 1. ESTADO REAL DO ECOSSISTEMA (Auditoria Completa)

### 1.1 Módulos Implementados e Status

| Módulo | Arquivo | Status | Nota |
|--------|---------|--------|------|
| M1 — Strategy Catalog | `agent_ia/core/omega_strategy_catalog.py` | OPERACIONAL | 8 estratégias: TrendFollowing, MeanReversion, Breakout, Scalping, MarketMaking, Momentum, Arbitrage, Adaptive |
| M2 — Agent Ecosystem | `agent_ia/core/omega_agent_ecosystem.py` | OPERACIONAL | Competição multi-agente com Q-learning |
| M3 — Session Calibrator | `agent_ia/core/omega_session_calibrator.py` | OPERACIONAL | 5 sessões; priority_assets expandidos (F2) |
| M4 — Global Orchestrator | `agent_ia/core/omega_global_orchestrator.py` | OPERACIONAL | Integração M1–M3, filtros, Kelly sizing |
| M5 — Shadow Loop Integration | `agent_ia/integration/shadow_loop_integration.py` | OPERACIONAL | `OmegaAgentIntegration` com record_trade |
| Engine — Shadow Loop | `core_engines/shadow_loop.py` | OPERACIONAL | USE_AGENT_IA agora via env var (F3) |
| Wrapper — Fase 4 | `agent_ia/tools/fase4_wrapper.py` | OPERACIONAL | 11 símbolos + IA_ON automático (F4) |
| Detector — Spoof/Iceberg | `modules/detection/spoof_iceberg_detector.py` | **STUB** | `get_signature_scores()` adicionado (F1); scores retornam 0 — detecção real pendente |
| Detector — Gap/Wave/BigPlayer | N/A | **NÃO EXISTE** | Módulos planejados mas não implementados |
| Quantum Brain | `agent_ia/core/omega_quantum_brain.py` | EXISTE | Integração com IA Engine via M2 |

---

### 1.2 Gaps Identificados (Root Cause Analysis)

#### GAP-01 — CRÍTICO RESOLVIDO: `USE_AGENT_IA = False` hardcoded
- **Causa:** Flag de segurança hardcoded impedia IA de operar em qualquer run
- **Impacto:** 480/480 ciclos usavam fallback momentum MT5, IA nunca chamada
- **Fix F3:** `USE_AGENT_IA = os.getenv("OMEGA_USE_AGENT_IA", "0") == "1"` — IA ativa ao passar env var

#### GAP-02 — CRÍTICO RESOLVIDO: `get_signature_scores()` ausente no detector
- **Causa:** `SpoofIcebergDetector` era stub de 8 linhas sem o método
- **Impacto:** `hasattr(spoof_detector, "get_signature_scores")` retornava False → `sig_scores = {}` sempre → sem filtro de assinaturas
- **Fix F1:** Método adicionado com scores zerados; análise real a implementar

#### GAP-03 — RESOLVIDO: Wrapper cobria apenas 4 símbolos cripto
- **Causa:** `CRYPTO_SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD"]` codificado em `run_shadow_loop()`
- **Impacto:** Forex e índices nunca executados; sessões LONDON/NY com liquidez máxima inexploradas
- **Fix F4:** `ALL_SYMBOLS` = 11 símbolos; `--symbols` CLI para controle granular

#### GAP-04 — RESOLVIDO: Session calibrator sem USDJPY/AUDUSD em LONDON e NY
- **Causa:** Priority_assets incompleto para sessões de alta liquidez
- **Impacto:** IA retornaria HOLD para USDJPY/AUDUSD/USDCAD mesmo em sessão ideal
- **Fix F2:** USDJPY + AUDUSD adicionados a LONDON; USDJPY + AUDUSD + USDCAD adicionados a NY

#### GAP-05 — ESTRUTURAL: Edge gate bloqueava fallback momentum em baixa liquidez
- **Status:** CORRETO e DESEJADO — a sessão CLOSED tem spread/ADX baixo; fallback sem edge geraria bleed
- **Próximo passo:** Com IA_ON, o orchestrator gera sinais com confidence calibrado; edge gate aplica apenas ao fallback

#### GAP-06 — PENDENTE: Detectors reais (Spoof, Iceberg, Wave, BigPlayer)
- **Status:** Todos são stubs zeros — nenhum algoritmo de microestrutura real
- **Impacto atual:** Neutro (scores=0 → sem ajuste de confidence) mas sem proteção real
- **Prioridade:** MÉDIO — papel trading não requer proteção máxima; live trading SIM

#### GAP-07 — PENDENTE: `build_market_data()` chamado 2× por ciclo (shadow_loop + orchestrator)
- **Causa:** shadow_loop não passa `market_data` pré-construído para `agent_ia.get_signal()`; orchestrator chama MT5 internamente
- **Impacto:** Latência ~2× na chamada MT5; não afeta resultado, apenas performance
- **Fix:** Opcional — construir `market_data` em shadow_loop e passar via parâmetro

---

## 2. ARQUITETURA DE DECISÃO (Fluxo Institucional)

```
MT5 tick / OHLCV
       │
shadow_loop.py [por ativo × timeframe]
       │
       ├── [AGENT_IA=1] OmegaAgentIntegration.get_signal(asset, sig_scores)
       │       │
       │       └── OmegaGlobalOrchestrator.get_signal_for_asset()
       │               │
       │               ├── SessionCalibrator → sessão, priority_assets, min_confidence
       │               ├── EcosystemOrchestrator → melhor agente (Q-value × win_rate)
       │               ├── StrategyCatalog → BUY/SELL/HOLD + confidence + SL/TP ATR
       │               ├── KellyFraction → lot sizing
       │               └── SignatureFilter (SPOOFER_LAYER, ICEBERG) → ajuste confidence
       │
       ├── [action != HOLD] → execução MT5 (lot, SL, TP)
       │
       └── [action == HOLD] → EDGE GATE (ATR/spread/ADX) → fallback momentum ou SKIP
```

---

## 3. ANÁLISE DE SESSÕES E COBERTURA MULTI-ATIVO

### 3.1 Mapa Sessão × Ativos × Estratégias

| Sessão | UTC | Liquidez | Ativos Priority | Estratégias | max_lot | min_conf |
|--------|-----|----------|-----------------|-------------|---------|----------|
| ASIA | 00–08 | LOW | XAUUSD, AUDUSD, NZDUSD, USDJPY, BTCUSD, ETHUSD | SCALPING, MEAN_REVERSION, ARBITRAGE | 0.005 | 0.75 |
| LONDON | 08–13 | HIGH | EURUSD, GBPUSD, USDJPY, AUDUSD, XAUUSD, GER40, BTCUSD, ETHUSD | TREND_FOLLOWING, BREAKOUT, MOMENTUM, ADAPTIVE | 0.01 | 0.65 |
| NEW_YORK | 13–17 | MAXIMUM | XAUUSD, EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, US500, NAS100, BTCUSD, ETHUSD | MOMENTUM, MARKET_MAKING, TREND_FOLLOWING, BREAKOUT, ADAPTIVE | 0.01 | 0.65 |
| OVERLAP | 17–21 | MEDIUM | US500, NAS100, BTCUSD, ETHUSD, XAUUSD, SOLUSD, DOGUSD | ADAPTIVE, ARBITRAGE, MEAN_REVERSION, SCALPING, MARKET_MAKING | 0.01 | 0.70 |
| CLOSED | 21–00 | MINIMUM | BTCUSD, ETHUSD, SOLUSD, DOGUSD | MARKET_MAKING, ADAPTIVE, MEAN_REVERSION, SCALPING | 0.005 | 0.75 |

**Janela institucional recomendada para fase IA_ON:** LONDON + NEW_YORK (08:00–17:00 UTC) — liquidez máxima, 10 ativos cobertos, min_confidence=0.65.

---

## 4. P&L CRITERIA E GO/NO-GO

### 4.1 Critério GO/NO-GO (já implementado em `fase4_wrapper.py`)

| KPI | Threshold Mínimo | Env Var Override |
|-----|------------------|------------------|
| net_pnl | ≥ $0 | `OMEGA_GO_MIN_NET_PNL` |
| win_rate_$ | ≥ 45% | `OMEGA_GO_MIN_WIN_RATE` |
| profit_factor | ≥ 1.2 | `OMEGA_GO_MIN_PF` |
| expectancy | ≥ $0 | `OMEGA_GO_MIN_EXP` |
| closed_positions | ≥ 50 trades | `OMEGA_GO_MIN_TRADES` |

### 4.2 Caminho para $1000/dia

**Premissa base:** conta DEMO $10,000, max_lot 0.01, paper mode

| Cenário | Trades/dia | Expectancy | P&L/dia | Viabilidade |
|---------|-----------|-----------|---------|-------------|
| ATUAL (só CLOSED, 4 cripto) | ~0–5 | -$2 a +$2 | < $10 | INVIÁVEL |
| FASE 1 — IA_ON LONDON+NY, 10 ativos | 20–40 | +$3 a +$8 | $60–$320 | VALIDAR |
| FASE 2 — Lote escalado (0.05) | 20–40 | +$15 a +$40 | $300–$1600 | META |
| FASE 3 — Live, capital $50k, lote 0.1 | 30–50 | +$20 a +$50 | $600–$2500 | LIVE |

**Nota:** $1000/dia com $10k de capital = 10%/dia — exige lote escalado (Fase 2) ou capital maior (Fase 3). Paper trading com max_lot=0.01 tem expectancy máxima de ~$10–50/trade em XAUUSD/índices.

---

## 5. PLANO EXECUTIVO EM 3 FASES

### FASE 1 — VALIDAÇÃO IA_ON (Semana 1–2)
**Objetivo:** confirmar que IA emite sinais válidos em sessão LONDON/NY, win_rate_$ ≥ 45%, profit_factor ≥ 1.2

**Comando de execução:**
```bash
python agent_ia/tools/fase4_wrapper.py --label IA_ON --cycles 50 \
  --symbols EURUSD GBPUSD USDJPY XAUUSD US500 NAS100 BTCUSD ETHUSD \
  --sleep-after-run 3 --sleep-after-close 2
```
**Horário:** 08:00–17:00 UTC (LONDON + NY)  
**KPI de saída:** GO/NO-GO passe com 50 trades fechados  
**Guardrails:**
- Kill switch DD ≥ 5% (já ativo em shadow_loop)
- max_positions=3 (LONDON), max_positions=3 (NY)
- CLOSE_MODE=ttl, TTL=600s

### FASE 2 — ESCALA DE LOTE (Semana 3–4)
**Pré-requisito:** GO/NO-GO passou Fase 1 por 3 runs consecutivos  
**Mudanças:**
- `EQUITY=50000` (simular $50k)
- max_lot escalado para 0.05 via HUNTER regime (`config/regimes/hunter.json`)
- Adicionar XAGUSD, GER40 como ativos adicionais
- Target: P&L ≥ $500/dia em paper

### FASE 3 — LIVE READINESS (Semana 5–6)
**Pré-requisito:** Fase 2 com profit_factor ≥ 1.5 e expectancy ≥ $10/trade  
**Ações:**
- Implementar detectores reais (Spoof/Iceberg com book de ordens MT5)
- Migrar para conta live com capital real $10k
- Escalar lote gradualmente: 0.01 → 0.02 → 0.05
- Monitor P&L diário com alerta automático em -$200

---

## 6. GUARDRAILS INSTITUCIONAIS ATIVOS

| Guardrail | Implementação | Arquivo |
|-----------|---------------|---------|
| Kill Switch DD 5% | `DD_DAILY_MAX = 0.05` | `shadow_loop.py` |
| Kill Switch 3 falhas consecutivas | `MAX_CONSEC_FAIL = 3` | `shadow_loop.py` |
| Edge Gate (ATR/spread/ADX) | `has_edge_for_momentum()` | `shadow_loop.py:174+` |
| Concentração por ativo >40% → lote −50% | Linha ~882 | `shadow_loop.py` |
| TTL de fechamento (respeita SL/TP) | `CLOSE_TTL_SEC=600` | `fase4_wrapper.py` |
| max_positions por sessão | `SessionConfig.max_positions` | `omega_session_calibrator.py` |
| Correlation filter (exposição duplicada) | `CorrelationFilter` | `modules/portfolio` |
| max_spread_pips por sessão | `SessionConfig.max_spread_pips` | `omega_session_calibrator.py` |
| Dedup de tickets (idempotência) | `_processed_tickets` set | `shadow_loop.py` |
| GO/NO-GO (5 KPIs financeiros) | `evaluate_go_no_go()` | `fase4_wrapper.py` |

---

## 7. AÇÕES IMEDIATAS (hoje)

### Implementadas nesta sessão (Fixes F1–F4):
- [x] **F1** — `SpoofIcebergDetector.get_signature_scores()` implementado
- [x] **F2** — USDJPY, AUDUSD adicionados a LONDON; USDJPY, AUDUSD, USDCAD adicionados a NY
- [x] **F3** — `USE_AGENT_IA` controlado via `OMEGA_USE_AGENT_IA=1` (sem mudança de código para ativar)
- [x] **F4** — Wrapper expande para 11 símbolos; IA ativa automaticamente em `--label IA_ON`

### Próximas ações recomendadas (pendentes autorização):
- [ ] **Executar Fase 1**: `fase4_wrapper.py --label IA_ON --cycles 50` em sessão LONDON/NY
- [ ] **Verificar `build_market_data()`**: confirmar que ativos forex (EURUSD) retornam dados válidos via MT5 (`copy_rates_from_pos`)
- [ ] **Verificar nomes dos símbolos no broker**: US500, NAS100 podem ser `US500m`, `NAS100m` dependendo do broker — verificar antes de incluir
- [ ] **Implementar Fase 2 escalada** após GO/NO-GO confirmado

---

## 8. COMANDOS DE EXECUÇÃO RÁPIDA

```bash
# BASELINE (sem IA, sem escalada) — 10 ciclos, todos 11 ativos
python agent_ia/tools/fase4_wrapper.py --label BASELINE --cycles 10

# IA_ON full — 30 ciclos, 11 ativos, IA habilitada automaticamente
python agent_ia/tools/fase4_wrapper.py --label IA_ON --cycles 30

# IA_ON restrito a LONDON/NY assets — 50 ciclos
python agent_ia/tools/fase4_wrapper.py --label IA_ON --cycles 50 \
  --symbols EURUSD GBPUSD USDJPY XAUUSD US500 NAS100 BTCUSD ETHUSD

# Shadow sem IA (diagnóstico) — XAUUSD apenas
python core_engines/shadow_loop.py --mode paper --ativos XAUUSD --timeframes H1

# Shadow COM IA (diagnóstico) — XAUUSD e EURUSD
$env:OMEGA_USE_AGENT_IA="1"; python core_engines/shadow_loop.py --mode paper \
  --ativos XAUUSD EURUSD GBPUSD --timeframes H1

# Validar sintaxe
python -m py_compile core_engines/shadow_loop.py agent_ia/tools/fase4_wrapper.py \
  agent_ia/core/omega_session_calibrator.py modules/detection/spoof_iceberg_detector.py
```

---

## 9. DISCLAIMER TÉCNICO

O sistema está em **paper trading** com conta DEMO. Todas as operações são simuladas em ambiente real MT5. Nenhuma perda de capital real ocorre. O GO/NO-GO garante que a transição para live só ocorra com estatísticas comprovadas (≥50 trades, profit_factor ≥ 1.2, win_rate_$ ≥ 45%).

Os detectores de assinatura (Spoof, Iceberg, Wave, BigPlayer) são **stubs** que retornam scores zero. Isso é seguro para paper trading mas deve ser implementado antes do live.

---
*Documento gerado automaticamente pelo Arquiteto OMEGA — versão 2.5*
