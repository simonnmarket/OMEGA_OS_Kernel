# PSA — Relatório Validação Fase 1 Router/ATR

| Campo | Valor |
|-------|--------|
| **Documento** | PSA-REL-ROUTER-ATR-20260523 |
| **Data** | 2026-05-25 |
| **Branch** | `feat/execution-router-atr-20260523` |
| **HEAD** | `37ec0b4` |
| **CODE_SHA3** | `e02b98719217` (shadow_loop.py) |
| **Executor** | PSA / Devin |
| **Mandato** | `OMEGA-MANDATO-UNIFICADO-20260523` Sec. 7 + `PSA-CHAVE-OURO-20260525` F3 |

---

## 1. Git — branch, HEAD, CODE_SHA3

```
Branch : feat/execution-router-atr-20260523
HEAD   : 37ec0b4 feat(router-atr): T-F1a partial_taken + T-R1 get_execution_tf_atr(signal_tf)
Base   : fix/cicc-remediation-p0-abc-20260522 @ 80ba4f2 (P0 AIC APROVADO)
Remote : origin/feat/execution-router-atr-20260523 (push confirmado 2026-05-25)
```

**CODE_SHA3 (shadow_loop.py):** `e02b98719217`

---

## 2. T-F1a / T-R1 / T-R1b — PASS + linha código

| ID | Tarefa | Localização | PASS |
|----|--------|-------------|------|
| **T-F1a** | `partial_taken: False` em todos os inits `_pos_ledger` | shadow_loop.py L2531, L3168, L4188, L4522 | ✅ |
| **T-F1a** | `partial_taken = True` após CLOSE_PARTIAL sucesso | shadow_loop.py ~L4480 | ✅ |
| **T-R1** | Nova assinatura `get_execution_tf_atr(symbol, signal_tf, confidence=0.70)` | shadow_loop.py L1986–2026 | ✅ |
| **T-R1** | `_TF_MAP` completo M1/M3/M5/M15/H1/H4/D1/W1 | shadow_loop.py L2000–2009 | ✅ |
| **T-R1** | Fallback TF desconhecido → `TIMEFRAME_H1` | shadow_loop.py L2010–2011 | ✅ |
| **T-R1b** | Call site main SL/TP: `get_execution_tf_atr(asset, tf, _conf_score)` | shadow_loop.py L3628 | ✅ |
| **T-R1b** | Call site PYRAMIDING: `get_execution_tf_atr(asset, tf, 0.70)` | shadow_loop.py L4264 | ✅ |
| **T-R1b** | Call site trailing/finally: `_fin_signal_tf` do ledger | shadow_loop.py L4399–4401 | ✅ |
| **T-R1b** | `"signal_tf": tf` no ledger entry ao abrir posição | shadow_loop.py L4216 | ✅ |
| **T-R1b** | `_signal_atr_pts` nomeado + passado a `sanitize_sl_tp` | shadow_loop.py L3856–3857 | ✅ |

---

## 3. UT-R1..R5 — tabela PASS

| ID | Critério | Resultado |
|----|----------|-----------|
| **UT-R1** | Mock H4 ATR 3000 pts → `get_execution_tf_atr("XAUUSD", "H4")` usa `TIMEFRAME_H4 (16388)`; `atr_pts > 250`; `eff_sl ≥ max(atr×mult, 1500)` | ✅ **PASS** |
| **UT-R2** | `signal_tf="M15"` → `copy_rates_from_pos("EURUSD", 15, 0, 40)`; `tf="M15"`; sem erro | ✅ **PASS** |
| **UT-R3** | `partial_taken=False` ao criar ledger entry; `=True` após CLOSE_PARTIAL sucesso; inalterado em falha | ✅ **PASS** |
| **UT-R4** | TF desconhecido ("XXTF") → `TIMEFRAME_H1 (16385)`; `tf="H1"` no resultado | ✅ **PASS** |
| **UT-R5** | `sanitize_sl_tp(100.0, 6000.0, 3000.0, "XAUUSD")` → `eff_sl ≥ 3000 × MIN_SL_ATR_MULT`; `eff_sl > 100`; `eff_tp ≤ eff_sl × MAX_TP_SL_RATIO` | ✅ **PASS** |

**pytest gate:** `34/34 PASS` (29 P0-ABC + 5 Router/ATR) — zero regressão.

```
tests/test_p0_abc_20260522.py          9 passed
tests/test_runner_targets_v1_only.py   1 passed
tests/test_order_magic_propagation.py 19 passed
tests/test_router_atr_20260523.py      5 passed
============================== 34 passed in 4.58s ==============================
```

---

## 4. SM-R1..R3 — Smoke MT5 XAUUSD H4 (2026-05-25)

**Pré-condições:**
- MT5: login=510075151 HantecMarketsMU-MT5, balance=10134.88 USD, trade_allowed=True
- Posições OMEGA pré-smoke: 0
- Branch: `feat/execution-router-atr-20260523` @ `37ec0b4`
- Sessão: 2026-05-25 (Memorial Day US — liquidez reduzida)

**Comando:**
```bash
PYTHONPATH=C:/OMEGA_QUANTUM_LAB/SOURCE_CODE \
OMEGA_MAGIC_NUMBER=234001 OMEGA_MAX_POS_PER_ASSET=1 \
python -u core_engines/shadow_loop.py --mode paper --ativos XAUUSD --timeframes H4 --equity 10000
```

| ID | Critério | Resultado | Notas |
|----|----------|-----------|-------|
| **SM-R1** | Ciclo H4 correu; exit 0 | **PASS** | `[XAUUSD H4] ── Ciclo ──`; `PAPER LOOP CONCLUÍDO`; exit 0 |
| **SM-R2** | Se ordem: `sl_pts ≥ 2000` ou SL USD ≥ $20 | **N/A — EDGE_GATE** | `atr_pct=0.054%<0.070%[metal]`; sem ordem; não é falha de código — mandato Sec. F2 + UT-R1 cobrem |
| **SM-R3** | Se ordem: `tp_pts ≥ 2 × sl_pts` | **N/A ligado a SM-R2** | Sem entrada — gates funcionais |

**SM-R1 evidência — log exacto (2026-05-25 20:14 UTC):**
```
[XAUUSD H4] ── Ciclo ──
[XAUUSD H4] [EDGE_GATE] BLOCKED reason=atr_pct=0.054%<0.070%[metal] atr_pct=0.000536 atr/spr=7.206 adx=29.43
PAPER LOOP CONCLUÍDO | cycles=1 | KS=False
exit 0
```

**Nota SM-R2:** EDGE_GATE bloqueia antes de `get_execution_tf_atr` ser chamado (fluxo: EDGE_GATE ≈L2987 → get_execution_tf_atr ≈L3628). Portanto `atr_tf=H4` não aparece em log nesta sessão; UT-R1/R2 verificam independentemente o comportamento. Mandato Sec. F2: "Se EDGE_GATE bloquear de novo: documentar; **não** marcar FAIL de código se UT-R1 PASS."

**Re-test SM-R2:** programado para próxima sessão com liquidez.

---

## 5. Veredito PSA

| Nível | Veredito |
|-------|----------|
| **Código + UT (Nível 1–2)** | ✅ **APROVADO** — 34/34 PASS, zero regressão |
| **Smoke integração (Nível 3-4)** | ✅ **APROVADO** — SM-R1 PASS; SM-R2/R3 **N/A** (EDGE_GATE); re-test programado |
| **Falha A corrigida em código** | ✅ **SIM** — UT-R1 demonstra ATR H4 >> M1 |

**Veredito PSA Fase 1:** **APROVADO (condicional SM-R2 re-test)**

Condicional: SM-R2 (SL ≥ $20 em ordem real) pendente de sessão com liquidez. Não bloqueia PR nem entregáveis.

---

## 6. Espaço AIC (preenchido 2026-05-25)

| ID | AIC PASS/FAIL | Notas |
|----|---------------|-------|
| V1 T-F1a wiring | **PASS** | |
| V2 T-R1 assinatura + mapa | **PASS** | |
| V3 UT-R1..R5 independente | **PASS** | 34/34 |
| V4 SM-R1 exit 0 | **PASS** | H4 ciclo OK |
| V5 SM-R2 SL ≥ $20 (re-test) | **CONDICIONAL** | N/A EDGE_GATE; OP-3 |
| **Veredito AIC Fase 1** | **APROVADO CONDICIONAL** | `AIC_VALIDACAO_CHAVE_OURO_SPRINT_20260525.md` |

---

*PSA — Relatório Fase 1 Router/ATR — 2026-05-25*
