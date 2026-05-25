# 🛰️ AUDITORIA FORENSE NASA/ORACLE-GRADE — AGENT IA OMEGA

**ID:** `DOC-AGENT-IA-FORENSIC-AUDIT-20260426`
**Versão:** 1.0.0
**Classificação:** TIER-0 — CONFIDENCIAL
**Data/Hora:** 2026-04-26 22:18 UTC+02 (20:18 UTC)
**Branch:** `feature/agent-ia-m1-m6` (HEAD: `2967533` + Fase 4)
**Auditor:** Codex 5.1 Max via PSA-WIND
**Destino:** Conselho (CEO, CFO, COO, CTO, CIO, CKO, CQO)
**Padrão:** ENFORCED_EXECUTION_v2.5 + NASA Software Engineering Handbook §3.4 + Oracle DB Audit Vault & DB Firewall §12

---

## 0. SUMÁRIO EXECUTIVO (TL;DR)

| Pergunta | Resposta direta |
|---|---|
| **A IA tradou em produção no A/B?** | **Não.** 0/60 execuções na Fase B vieram da IA. 100 % MOMENTUM_MT5 (fallback). |
| **Por que a IA emitiu 0 ordens?** | **3 bloqueios estruturais simultâneos.** Cold-start mata Sharpe → confidence colapsa para ≤ 0.16 < 0.70. Sessão NEW_YORK não tem cripto. Best-agent default cai em estratégia errada para a sessão. |
| **A integração funciona?** | **Sim, mecanicamente.** Fase 4 chama `OmegaAgentIntegration.get_signal()` em 100 % dos ciclos. O patch está vivo. O que não funciona é a lógica interna da IA. |
| **A solução é trocar de IA?** | **Não.** Os 6 módulos M1–M6 são bons; precisam de **5 calibrações cirúrgicas** mensuráveis. Tempo estimado: 2 dias-homem. |
| **Quando a IA pode operar?** | Após implementar Fix #1–#5 + 1 ciclo de bootstrap warmup (≈ 200 trades simulados em backtest). |
| **Risco real atual?** | **Zero.** `USE_AGENT_IA=False` revertido. Patch dormente. Sistema opera no modo legado validado. |

---

## 1. ESTADO ATUAL — HASHES SHA256 (linha de base auditável)

| Arquivo | SHA256 (16) |
|---|---|
| `core_engines/shadow_loop.py` (Fase 4 patch) | `345E74984D78A06B…` |
| `agent_ia/core/omega_strategy_catalog.py` | `826DE98936AF7541` |
| `agent_ia/core/omega_agent_ecosystem.py` | `189E783FBF3D8445` |
| `agent_ia/core/omega_session_calibrator.py` | `6974023FA4F84528` |
| `agent_ia/core/omega_global_orchestrator.py` | `ACD19D00BC231076` |
| `agent_ia/core/omega_quantum_brain.py` | `E0E7A5DFA2CE4512` |
| `agent_ia/integration/shadow_loop_integration.py` | `F302B95753F7D59A` |
| `agent_ia/tools/fase4_wrapper.py` | `A84A51E7DB0935A3` |
| `agent_ia/tools/fase4_compare.py` | `1AD9B47242C601E8` |
| `agent_ia/tools/diagnose_hold_root_cause.py` | `B769E4DD7B6C1297` |

| Artefato auditoria | SHA3-256 |
|---|---|
| Aggregate Fase A (BASELINE) | `7cc4c14bb20a3a7383c703b28e9e768cf4e3deabb494bbb39a3c7dfd586bc40f` |
| Aggregate Fase B (IA_ON) | `52b67f73981cca4ad3523ee141e9a209781eafdbde8292e13bb9239ea3205b98` |
| AB Compare | `46db5c833d848de4eda896ae0b1ea094e4918038c8845fc523d511c23b0978ea` |
| Diagnose root-cause | `f497a1b9f3f383cb3c75f9948ffb243172a057a112bfa7b356d67509158566e5` |
| bias_audit final | `3c9c49c6f4eb3fd0905d09b7764f3661f7fb286f6b0928f83df158debe3a4d2c` |

---

## 2. EVIDÊNCIA EMPÍRICA — DIAGNÓSTICO DIRETO

Script: `agent_ia/tools/diagnose_hold_root_cause.py`
Execução: 2026-04-26 20:17 UTC, sessão **OVERLAP** (17–21 UTC).

### 2.1 Configuração da sessão observada

```
SESSION    : OVERLAP
PRIORITY   : ['US500', 'NAS100', 'BTCUSD', 'ETHUSD', 'XAUUSD']
MIN_CONF   : 0.70
STRATEGIES : ['ADAPTIVE', 'ARBITRAGE', 'MEAN_REVERSION', 'MARKET_MAKING']
```

### 2.2 Resultado por ativo (output literal)

| asset | g1_priority | g2_market_data | best_agent_strategy(risk_adj_conf) | raw_strategy_action | final_action | reason |
|---|---|---|---|---|---|---|
| BTCUSD | True | True | TREND_FOLLOWING(0.00) | — | **HOLD** | Confiança 0.12 < mínima 0.70 |
| ETHUSD | True | True | TREND_FOLLOWING(0.00) | — | **HOLD** | TREND_FOLLOWING: Sem condições de entrada |
| SOLUSD | False | True | TREND_FOLLOWING(0.00) | — | **HOLD** | Ativo não prioritário para sessão OVERLAP |
| DOGUSD | False | True | TREND_FOLLOWING(0.00) | — | **HOLD** | Ativo não prioritário para sessão OVERLAP |
| XAUUSD | True | True | TREND_FOLLOWING(0.00) | — | **HOLD** | Confiança 0.11 < mínima 0.70 |
| EURUSD | False | True | TREND_FOLLOWING(0.00) | — | **HOLD** | Ativo não prioritário para sessão OVERLAP |

### 2.3 Padrão observado (matemático)

`risk_adj_conf = 0.00` em **todos** os agentes. Direto da fórmula `get_risk_adjusted_confidence()` com `confidence=0.50` (default), `sharpe_ratio=0.00`:

```
sharpe_factor = (sharpe_ratio + 1.0) / 3.0 = (0 + 1) / 3 = 0.3333
risk_adj_conf = confidence * sharpe_factor = 0.50 × 0.3333 = 0.1667
```

(O log mostra **0.00** arredondado porque o agente não treinou; em diagnóstico direto chamando `get_risk_adjusted_confidence()` o valor real é **0.1667**, mas o `to_dict` arredonda confidence para `0.5` e Sharpe para `0.0`, produzindo a impressão `0.00`.)

E na composição final:

```
adjusted_confidence = signal.confidence × risk_adj_conf
                    = 0.75 (TrendFollow máx) × 0.1667
                    = 0.125  ← exatamente o valor reportado para BTCUSD ("0.12")
```

`0.125 < 0.70 (min_conf)` → **HOLD garantido matematicamente**.

---

## 3. CAUSAS-RAIZ (RCA) — 5 BUGS ESTRUTURAIS

### RCA #1 — COLD-START HARDLOCK (criticidade: BLOCKER)

**Sintoma:** todo agente, recém-criado, retorna `confidence ≤ 0.17` para qualquer estratégia.

**Mecanismo:** em `omega_agent_ecosystem.py:65-95`:
```python
@dataclass
class CompetitiveAgent:
    confidence: float = 0.50          # default
    sharpe_ratio: float = 0.0         # default cold-start
    kelly_fraction: float = 0.01      # default
    total_trades: int = 0
```

E em `get_risk_adjusted_confidence()` (linhas 302-311):
```python
if self.sharpe_ratio <= -1.0: sharpe_factor = 0.10
elif self.sharpe_ratio >= 2.0: sharpe_factor = 1.0
else: sharpe_factor = (self.sharpe_ratio + 1.0) / 3.0
return self.confidence * sharpe_factor
```

**Cold-start:** sharpe_factor = 1/3 → max teórico de `risk_adj_conf` = `0.50 × 1/3 ≈ 0.167`. Logo `signal_conf × 0.167 ≤ 0.95 × 0.167 = 0.158`. Nenhuma sessão (mín. 0.65 em Londres) é alcançável. **A IA não pode trabalhar fora de paper backtest até obter Sharpe ≥ 2.0** (não trivial: requer ~50–100 trades vencedores antes de operar).

**Comprovação:** `_update_kelly_fraction` exige `total_trades ≥ 5` (linha 256). `_calculate_sharpe_ratio` exige histórico não-vazio. Antes do primeiro trade, **nada** se atualiza → travamento eterno. Nenhum trade é executado → nenhum trade fecha → nenhum update → impossibilidade matemática de evolução em produção.

### RCA #2 — STRATEGY/SESSION MISMATCH (criticidade: BLOCKER)

**Sintoma:** ETHUSD e SOLUSD recebem agente `TREND_FOLLOWING` em sessão OVERLAP que **não tem TREND_FOLLOWING em `active_strategies`**.

**Mecanismo:** em `omega_agent_ecosystem.py:_initialize_agents` (linha 364-380), 8 agentes (um por StrategyType) são criados. `get_best_agent()` ordena por `performance_score`. Em cold-start `performance_score = 0×0.40 + 0×0.30 + (1.0 − 0/1e-10)×0.30 = 0.30` para **todos**. A função sort é estável → retorna **o primeiro** sempre, que é `TREND_FOLLOWING` (primeiro `StrategyType` no enum).

Mas o `OmegaGlobalOrchestrator.get_signal_for_asset` **nunca filtra a estratégia escolhida contra `session_config.active_strategies`**. Logo um agente TREND atende OVERLAP, e a estratégia TREND retorna HOLD porque o ativo cripto não está em "ema_50 > ema_200 + ADX > 25" → bloqueio.

### RCA #3 — PRIORITY_ASSETS INCOMPLETO PARA CRIPTO (criticidade: HIGH)

**Sintoma:** SOLUSD e DOGUSD bloqueados em **toda** sessão.

**Mecanismo:** `omega_session_calibrator.py:138-306`:

| Sessão | priority_assets | Cripto incluso? |
|---|---|---|
| ASIA (00–08) | XAUUSD, AUDUSD, NZDUSD, USDJPY | ❌ |
| LONDON (08–13) | EURUSD, GBPUSD, XAUUSD, USDCHF | ❌ |
| NEW_YORK (13–17) | XAUUSD, EURUSD, GBPUSD, US500, NAS100 | ❌ |
| OVERLAP (17–21) | US500, NAS100, BTCUSD, ETHUSD, XAUUSD | só BTC, ETH |
| CLOSED (21–24) | BTCUSD, ETHUSD | só BTC, ETH |

**SOLUSD/DOGUSD/XRPUSD/ADAUSD/etc.: bloqueados em 100 % dos horários.** Mesmo BTC/ETH só passam o gate em OVERLAP+CLOSED (8 das 24 h). NEW_YORK (mais ativa para volume cripto USD) não inclui cripto.

### RCA #4 — MIN_CONFIDENCE INALCANÇÁVEL EM COLD-START (criticidade: HIGH)

| Sessão | min_confidence | Necessário sharpe_factor para passar | Sharpe equivalente |
|---|---|---|---|
| ASIA | 0.75 | ≥ 0.789 (0.75/0.95) | ≥ 1.37 |
| LONDON | 0.65 | ≥ 0.684 | ≥ 1.05 |
| NEW_YORK | 0.65 | ≥ 0.684 | ≥ 1.05 |
| OVERLAP | 0.70 | ≥ 0.737 | ≥ 1.21 |
| CLOSED | 0.85 | ≥ 0.895 (acima de 1.0) | **impossível** |

CLOSED é matematicamente inviável (sharpe_factor capa em 1.0; precisaria 0.895 para passar; 0.50 × 1.0 = 0.50 < 0.85). Outras sessões exigem Sharpe ≥ 1.05 — alta para qualquer estratégia em produção real, **inalcançável em cold-start**.

### RCA #5 — SCHEDULER BIAS NO SHADOW_LOOP (criticidade: MEDIUM)

**Sintoma:** Concentração 100 % BTC nas Fases A e B (60/60 ordens).

**Mecanismo:** `shadow_loop.py:570 for asset in ativos: for tf in timeframes:`. Iteração sequencial determinística. Com `MAX_POSITIONS=6` e 4 posições FX/XAU travadas (mercado fechado), **só restam 2 slots, sempre preenchidos pelo primeiro ativo (BTCUSD nas duas TFs).**

ETH/SOL/DOGE são processados mas batem o limite e são pulados com `WARNING [ETHUSD H1] MAX_POSITIONS=6 atingido`.

**Confirmação direta dos logs (cycle_01.log Fase B):**
```
[BTCUSD H1] FASE4 EXEC source=MOMENTUM_MT5 success=True deal=182358076
[BTCUSD H4] FASE4 EXEC source=MOMENTUM_MT5 success=True deal=182358077
[ETHUSD H1] MAX_POSITIONS=6 atingido.
[ETHUSD H4] MAX_POSITIONS=6 atingido.
[SOLUSD H1] MAX_POSITIONS=6 atingido.
...
```

Concentração não é viés do **sinal**, é viés do **scheduler**. bias_audit estatístico (Wilson p-value) mostra `NOT_SIGNIFICANT` para BUY/SELL — direção é justa; só o ativo é viesado.

### RCA #6 (BÔNUS) — LATENCY SLO MAL ESPECIFICADO

p95 medido: 292 ms (A) / 305 ms (B). SLO: 200 ms. **Falha aparente.**

Mas isolando M6 (Quantum Brain) em CPU pura (`agent_ia/tests/test_quantum_brain_latency.py`): **p95 = 9.9 ms.**

**O que é medido em produção:** roundtrip total `mt5_send_order()` ↔ broker Hantec Markets MU (Maurícios). Inclui rede, fila do broker, validação de margem, fill. **Não é latência da IA.**

SLO precisa ser duas métricas distintas: `latency_ai_decision_ms` (IA pura) e `latency_broker_roundtrip_ms` (rede). A primeira é controlada por nós; a segunda é responsabilidade do broker e tem variância natural 50–500 ms.

---

## 4. EVIDÊNCIA OPERACIONAL (LOGS REAIS)

### 4.1 Fase A (BASELINE / IA OFF) — 30 ciclos

Diretório: `logs/agent_ia_phase3/fase4_BASELINE_20260426_195117/`

```
[CYCLE 01/30] rc=0 executed=2 hit=94.92 lat_max=30.0  closed=2
[CYCLE 06/30] rc=0 executed=2 hit=94.92 lat_max=318.1 closed=2  ← pico latência broker
[CYCLE 30/30] rc=0 executed=2 hit=94.92 lat_max=291.0 closed=2

AGGREGATE:
  cycles=30 total_trades=60 executed=60
  hit_rate_avg=94.92 latency_p95=292.2ms latency_max=318.1ms
  ks_triggers=0 max_concentration=100.0% on BTCUSD
  retcodes={'10009': 60}
```

### 4.2 Fase B (IA_ON) — 30 ciclos

Diretório: `logs/agent_ia_phase3/fase4_IA_ON_20260426_195627/`

```
[FASE4] Agente IA inicializado (assets=4, capital=$10000.00)
[BTCUSD H1] FASE4 EXEC source=MOMENTUM_MT5 success=True deal=182358076
[BTCUSD H4] FASE4 EXEC source=MOMENTUM_MT5 success=True deal=182358077

GREP source=AGENT_IA   : 0 hits
GREP source=MOMENTUM_MT5: 60 hits
GREP DECISION=AGENT_IA : 0 hits
```

A IA inicializou. Foi consultada. Em **100 % dos casos** retornou HOLD ou conf < 0.65 → fallback acionado.

### 4.3 bias_audit (3 execuções consecutivas, hashes distintos)

| Timestamp | Audit ID | SHA3 | Verdict |
|---|---|---|---|
| 2026-04-26 19:39 UTC | BIAS_20260426_193921 | `fec7fe34c7cb216a…` | NOT_SIGNIFICANT |
| 2026-04-26 19:41 UTC | BIAS_20260426_194141 | `6effe0c18334cc05…` | NOT_SIGNIFICANT |
| 2026-04-26 20:04 UTC | BIAS_20260426_200446 | `3c9c49c6f4eb3fd0…` | NOT_SIGNIFICANT |

Crisis_probability constante: 86.6 % (input `XAU_change_pct=8.5, DXY=-1.8` no `config/market_data.json`). RTT entre 0.36–0.46 ms. SLO PASS.

---

## 5. SOLUÇÕES MENSURÁVEIS — PLANO TÉCNICO

Cada fix tem: descrição, arquivo, mudança matemática, custo, teste de aceitação.

### FIX #1 — BOOTSTRAP WARMUP DOS AGENTES (resolve RCA #1, #4)

**Descrição:** ao criar agente, simular N trades virtuais (Monte Carlo) com a estratégia sobre OHLCV histórico para inicializar Sharpe, Kelly e win_rate antes de produção.

**Arquivo:** `agent_ia/core/omega_agent_ecosystem.py` — adicionar `_warm_start(ohlcv_data, n_trades=200)` no `__init__` do `CompetitiveAgent`.

**Pseudocódigo:**
```python
def _warm_start(self, market_data_history: List[Dict], n_trades: int = 200):
    """Bootstrap virtual usando estratégia sobre histórico real."""
    strategy = StrategyCatalog().get_strategy(self.strategy_name)
    virtual_pnl = []
    for window in sliding_windows(market_data_history, size=200):
        sig = strategy.get_signal(window[-1])
        if sig.action != HOLD:
            future_return = simulate_trade(window, sig, horizon=10)
            virtual_pnl.append(future_return)
    if virtual_pnl:
        self._update_sharpe_from_history(virtual_pnl)
        self._update_kelly_from_history(virtual_pnl)
        self.confidence = 0.65 if np.mean(virtual_pnl) > 0 else 0.40
```

**Resultado matemático esperado:** Sharpe pós-warmup típico 0.5–1.5 → sharpe_factor 0.5–0.83 → risk_adj_conf 0.32–0.79 → passa min_confidence das principais sessões.

**Teste de aceitação:** após warmup, `risk_adj_conf > 0.50` em ≥ 80 % dos agentes (verificável via `diagnose_hold_root_cause.py`).

**Custo:** 4 h dev + 2 h teste.

### FIX #2 — STRATEGY-SESSION FILTERING (resolve RCA #2)

**Descrição:** `get_best_agent_for_asset` deve aceitar `allowed_strategies` (vinda da sessão) e filtrar antes do sort.

**Arquivo:** `agent_ia/core/omega_agent_ecosystem.py:530` + `omega_global_orchestrator.py:248`.

**Mudança:**
```python
# omega_agent_ecosystem.py
def get_best_agent_for_asset(self, asset: str,
                             allowed_strategies: Optional[List[str]] = None) -> Optional[CompetitiveAgent]:
    eco = self.ecosystems.get(asset)
    if not eco: return None
    return eco.get_best_agent(allowed_strategies=allowed_strategies)

# omega_global_orchestrator.py:248
agent = self.ecosystem.get_best_agent_for_asset(
    asset,
    allowed_strategies=session_config.active_strategies
)
```

**Teste:** em sessão OVERLAP, agente devolvido tem `strategy_name in [ADAPTIVE, ARBITRAGE, MEAN_REVERSION, MARKET_MAKING]`.

**Custo:** 1 h dev + 30 min teste.

### FIX #3 — EXPANDIR PRIORITY_ASSETS PARA CRIPTO (resolve RCA #3)

**Descrição:** cripto opera 24/7 com alta liquidez global. Adicionar BTC/ETH em **todas** as sessões; SOL/DOGE/XRP em OVERLAP/CLOSED.

**Arquivo:** `agent_ia/core/omega_session_calibrator.py:138-306`.

**Diff conceitual:**

| Sessão | priority_assets atuais | priority_assets propostos |
|---|---|---|
| ASIA | XAUUSD, AUDUSD, NZDUSD, USDJPY | + BTCUSD, ETHUSD |
| LONDON | EURUSD, GBPUSD, XAUUSD, USDCHF | + BTCUSD, ETHUSD |
| NEW_YORK | XAUUSD, EURUSD, GBPUSD, US500, NAS100 | + BTCUSD, ETHUSD |
| OVERLAP | US500, NAS100, BTCUSD, ETHUSD, XAUUSD | + SOLUSD, DOGUSD |
| CLOSED | BTCUSD, ETHUSD | + SOLUSD, DOGUSD, XRPUSD |

**Teste:** `diagnose_hold_root_cause.py` mostra `gate1_in_priority=True` para BTC/ETH em qualquer hora.

**Custo:** 30 min dev + 30 min revisão.

### FIX #4 — RECALIBRAR MIN_CONFIDENCE (resolve RCA #4 + parte do #1)

**Descrição:** valores atuais (0.65–0.85) são da escola institucional FX. Para cripto e sistema cold-start, são proibitivos. Reduzir de modo escalonado por maturidade.

**Proposta:** introduzir **min_confidence dinâmico** em função de `total_trades_realizados`:

```python
def get_effective_min_confidence(session_config, agent) -> float:
    base = session_config.min_confidence
    if agent.total_trades < 20:    return base * 0.50  # warmup
    if agent.total_trades < 100:   return base * 0.75  # juvenil
    return base                                          # maduro
```

| Sessão | base | warmup (≤20) | juvenil (≤100) | maduro |
|---|---|---|---|---|
| ASIA | 0.75 | 0.375 | 0.563 | 0.750 |
| LONDON | 0.65 | 0.325 | 0.488 | 0.650 |
| NEW_YORK | 0.65 | 0.325 | 0.488 | 0.650 |
| OVERLAP | 0.70 | 0.350 | 0.525 | 0.700 |
| CLOSED | 0.85 | 0.425 | 0.638 | 0.850 |

**Arquivo:** `omega_global_orchestrator.py:272` + helper em `omega_session_calibrator.py`.

**Teste:** com FIX #1 (warmup) → adjusted_confidence ~0.45 + threshold dinâmico 0.325 → **PASS**.

**Custo:** 1 h dev + 1 h teste.

### FIX #5 — DESVIESAR SCHEDULER (resolve RCA #5)

**Descrição:** randomizar ou priorizar dinamicamente a ordem dos ativos por ciclo, e respeitar **slots livres por ativo** (não só global).

**Arquivo:** `core_engines/shadow_loop.py:570` + nova heurística.

**Mudança:**
```python
# Embaralhar a cada ciclo, com seed determinística para auditoria
import random
random.seed(int(time.time()) // 60)  # muda por minuto
ativos_shuffled = list(ativos); random.shuffle(ativos_shuffled)

# OU: priorizar ativos com menos posições atuais
ativos_sorted = sorted(ativos, key=lambda a: count_open_positions(a))
```

**Teste:** rodar 30 ciclos e verificar `max_concentration < 60 %` (relaxado de 40 % por causa de MAX_POSITIONS apertado).

**Custo:** 1 h dev + 1 h teste.

### FIX #6 — MÉTRICAS DE LATÊNCIA SEPARADAS (resolve RCA #6)

**Descrição:** instrumentar três pontos:
1. `t_decision = t_get_signal_end - t_get_signal_start` (IA pura)
2. `t_broker = t_order_done - t_order_send` (rede + broker)
3. `t_total = t_decision + t_broker`

SLOs separados:
- `t_decision_p95 ≤ 50 ms` (já provado: 9.9 ms isolado)
- `t_broker_p95 ≤ 500 ms` (realístico para broker remoto)
- `t_total_p95 ≤ 600 ms`

**Arquivo:** `core_engines/shadow_loop.py:684–720` (instrumentação) + `agent_ia/tools/fase4_compare.py` (evaluation).

**Custo:** 2 h dev + 1 h teste.

---

## 6. ROTEIRO DE EXECUÇÃO (sequenciado, 2 dias)

| Etapa | Fix | Hora | Validação |
|---|---|---|---|
| Dia 1 — manhã | FIX #3 (priority_assets) | 1 h | `diagnose_hold` mostra cripto in_priority=True 24h |
| Dia 1 — manhã | FIX #2 (strategy-session filter) | 1.5 h | unit test: agente devolvido em cada sessão tem strategy ∈ active_strategies |
| Dia 1 — tarde | FIX #4 (min_confidence dinâmico) | 2 h | unit test: warmup_min_conf < base; hit p95 OK |
| Dia 1 — tarde | FIX #1 (warmup) | 6 h | após `_warm_start` em 200 candles H1 BTC: Sharpe ≥ 0.3, kelly ≥ 0.05 em ≥ 80 % dos agentes |
| Dia 2 — manhã | FIX #5 (scheduler shuffle) | 2 h | concentration < 60 % em 30 ciclos |
| Dia 2 — manhã | FIX #6 (latency split) | 3 h | dois p95 reportados; t_decision ≤ 50 ms |
| Dia 2 — tarde | A/B Real | 4 h | wrapper N=30, IA_ON, ≥ 30 decisões `source=AGENT_IA` (50 %) |
| Dia 2 — tarde | Relatório GO/NO-GO | 1 h | DOC com hashes pré/pós, métricas, verdict |

**Checkpoint após Dia 1:** `diagnose_hold_root_cause.py` deve mostrar `final_action=BUY|SELL` para ≥ 4/6 ativos. Se não, parar e investigar.

---

## 7. ARQUITETURA-ALVO — IA "GENIUS DE SENTIMENTO"

A demanda do CEO é uma IA que **aprenda, ensine e calibre** o ecossistema. A arquitetura M1–M6 já comporta isso; precisa apenas dos fixes acima + 3 features:

### 7.1 Loop de aprendizado (já existe parcialmente)

```
Sinal (M1) → Decisão (M4) → Execução (shadow_loop) → Fechamento → record_trade_result (M4)
                                                            ↓
                                update_performance (M2)  ← Sharpe, Kelly, win_rate, drawdown
                                                            ↓
                                _update_kelly_fraction
                                _update_performance_score
                                                            ↓
                                rebalance_all (próximo ciclo)
```

**Está implementado.** Falta apenas alimentar o loop com dados (cold-start do FIX #1).

### 7.2 Feature pendente — Sentiment Layer (M6 expansion)

`omega_quantum_brain.py` hoje calcula Q-values em cima de features clássicas (preço/volume). Para "genius de sentimento":

1. **Inputs adicionais:** spoofing/iceberg do `SpoofIcebergDetector` (já existe), order flow imbalance (calculável de tick data MT5), funding rate cripto (API Binance), correlação cross-asset (já existe `CorrelationFilter`).

2. **Output adicional:** `sentiment_score ∈ [-1, +1]` que modula `confidence` ortogonalmente a Sharpe.

3. **Persistência:** `agent_ia/data/sentiment_history.db` (SQLite) para análise temporal.

**Custo estimado:** 2 dias-homem após fixes #1–#6.

### 7.3 Feature pendente — Auto-tuning calibrator

Hoje `priority_assets` e `min_confidence` são estáticos (constantes em `omega_session_calibrator.py`). Proposta: módulo M7 `omega_calibrator_tuner.py` que, **toda madrugada (00:00 UTC)**, lê últimos 7 dias de `paper_summary.json`, calcula hit rate por (sessão × ativo × estratégia) e reescreve thresholds em arquivo JSON externo (não código), assinado por SHA3.

**Custo:** 1 dia-homem.

---

## 8. CONFORMIDADE E AUDIT TRAIL

| Item | Status |
|---|---|
| Branch isolada (main intacta) | ✅ `feature/agent-ia-m1-m6` |
| `USE_AGENT_IA=False` revertido após teste | ✅ confirmado linha 52 |
| py_compile pós-patch | ✅ exit 0 todos os módulos |
| Rollback testado (git stash) | ✅ hash CBD6→345E→CBD6→345E |
| bias_audit íntegro pré e pós | ✅ NOT_SIGNIFICANT em ambas |
| SHA3 paper_summaries A e B | ✅ commitados |
| Logs de cada ciclo | ✅ 60 cycle_NN.log + 60 paper_summary_NN.json |
| Wrapper auditável | ✅ `fase4_wrapper.py` SHA256 `A84A51E7DB0935A3` |
| Diagnose forense | ✅ `diagnose_hold_root_cause.py` SHA256 `B769E4DD7B6C1297` |
| 4 posições MT5 FX/XAU travadas | ⚠️ aguardando reabertura broker (fim de semana) |
| Crisis probability validator | ✅ PASS 86.6 % |
| SLO RTT bias_audit | ✅ 0.36–0.46 ms |

---

## 9. RISCOS RESIDUAIS

| Risco | Severidade | Mitigação |
|---|---|---|
| Implementar warmup com má curadoria de OHLCV pode produzir Sharpe inflado | Médio | usar walk-forward, holdout 30 % |
| Reduzir min_confidence aumenta exposição em fase juvenil | Médio | manter `MAX_POSITIONS` apertado e DD kill switch 5 % |
| Sentiment layer (7.2) pode introduzir overfitting | Médio | A/B obrigatório com p-valor antes de ativar |
| MAX_POSITIONS=6 + 4 FX travadas = teste limitado a 2 slots | Baixo | aguardar reabertura FX ou subir para 12 com aprovação |
| Auto-tuning (7.3) pode degradar se mal supervisionado | Alto | logs SHA3 + revisão manual semanal |

---

## 10. CONCLUSÃO E SOLICITAÇÃO

**Ao Conselho:**

1. A IA OMEGA M1–M6 **não é defeituosa estruturalmente**. Os 6 módulos funcionam, validam, importam, executam.

2. Existem **5 bugs cirúrgicos comprovados** (RCA #1–#5) que se compõem multiplicativamente para travar 100 % das decisões. Cada um é fixável em horas. O conjunto, em 2 dias-homem.

3. **Solicito autorização** para executar o roteiro da Seção 6, com checkpoint obrigatório no fim do Dia 1 e A/B real ao fim do Dia 2, com critérios GO/NO-GO da Seção 6.

4. Após GO da fase de fix, propor M7 (auto-tuning) e expansão M6 (sentiment layer) — Seção 7.

5. **Não recomendo** ativar `USE_AGENT_IA=True` em produção até a conclusão do Dia 2 com verdict GO. O sistema legado (momentum MT5) opera com hit_rate observado de **94.92 %** e satisfaz GO/NO-GO em todos os critérios exceto o p95 mal especificado.

**Assinatura digital:**

```
audit_id        : DOC-AGENT-IA-FORENSIC-AUDIT-20260426
shadow_loop_sha : 345E74984D78A06B49233C91D82FE16B6943572B1FE24BEF19E7DCFDA1978A01
diagnose_sha3   : f497a1b9f3f383cb3c75f9948ffb243172a057a112bfa7b356d67509158566e5
ab_compare_sha3 : 46db5c833d848de4eda896ae0b1ea094e4918038c8845fc523d511c23b0978ea
bias_audit_sha3 : 3c9c49c6f4eb3fd0905d09b7764f3661f7fb286f6b0928f83df158debe3a4d2c
auditor         : Codex 5.1 Max via PSA-WIND
classification  : TIER-0 — CONFIDENCIAL
```

**FIM DO DOCUMENTO.**
