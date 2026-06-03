# AIC — Log de Correção CEO Capture Matrix
**Data:** 2026-06-03  
**Mandato:** CEO — fio morto PLUG→ACT; caso forense XAUUSD #193126680  
**Escopo:** Nível 1–2 (código). Validação runtime depende do runner MT5 activo.

---

## Resumo executivo

O motor de energia (SEL/USFE) calculava `impact_tp_pts` mas a camada ACT ignorava-o, aplicava partial tardio (2.5×ATR), bloqueava pyramid por `trend_score≥0.60`, micro-lotes (0.02) e EDGE_GATE em posições já vencedoras. Quatro correcções estruturais + reinício do runner 24/7.

---

## P0 — `impact_tp_pts` → TP real

| Antes | Depois |
|-------|--------|
| TP = `_pre_tp` = ATR × mult (ex. 12857 pts XAU) | TP = `sel_impact_tp_pts` quando > 0 |
| `impact_tp=42` ignorado na ordem | Log `[IMPACT_TP] SEL impact=42pts → eff_tp=42` |

**Ficheiro:** `core_engines/shadow_loop.py` (~4270–4575)  
**Env:** `OMEGA_USE_SEL_IMPACT_TP=1`  
**Nota:** TP de impacto não passa por `sanitize_sl_tp` R:R cap; SL continua capado por regime.

---

## P1 — Partial close metais 0.3×ATR

| Antes | Depois |
|-------|--------|
| 1º nível PSA: 2.5×ATR (~1000+ pts) | XAU/XAG: 0.3×ATR (~430 pts) |
| Log enganoso `[0.7/1.5/2.5/4.0]ATR` | Log dinâmico `levels=[0.3/1.5/2.5/4.0]ATR` |

**Função:** `partial_close_levels_for(symbol)`  
**Resync:** posições órfãs (#193126680) recebem níveis metal no boot `[PARTIAL_CLOSE] [RESYNC]`

---

## P2 — Pyramid gate metais 0.35

| Antes | Depois |
|-------|--------|
| `OMEGA_PYRAMID_MIN_SCORE=0.60` global | XAU/XAG: 0.35 quando `profit_pts ≥ trigger` |
| Bloqueio: `trend_score=0.20<min` com +753 pts | Metais: bypass trend se `profit_pts ≥ trigger`; senão min=0.35 |

**Função:** `pyramid_min_score_for()`  
**Env:** `OMEGA_PYRAMID_MIN_SCORE_METAL=0.35`, `OMEGA_PYRAMID_LAYERS=4`

---

## P3 — Piso de lote + escala

| Regra | Implementação |
|-------|----------------|
| CEO: min 0.05 metais | `OMEGA_MIN_LOT_METAL=0.05` — **sem** `OMEGA_MIN_LOT_EXEC` global |
| Mesa (revertido 2026-06-03): | Removido `OMEGA_MIN_LOT_EXEC=1.0` — risco ~30%/trade inaceitável |
| Regra efectiva | XAU/XAG: `max(LotCalc, 0.05)`; restantes: LotCalc puro |

**Função:** `exec_min_lot_floor(asset, regime)` — só metais

---

## P0 retroativo — posição #193126680

| Pergunta CEO | Resposta (evidência) |
|--------------|----------------------|
| TP impact aplicado à posição aberta? | **Não** — TP MT5 permaneceu **4347.14** (~12857 pts) até fecho |
| Código novo | `resync_impact_tp_for_position()` no boot — liga TP SEL a órfãs **a partir deste deploy** |
| Estado actual | Posição **fechada** (~15:03 UTC); partial 0.3×ATR **executou** (0.01 lot @ 4461.92) |

Entrada H4: `sel_impact_tp_pts=42.48` (decision_trace) — TP correcto seria ~4475.29, não 4347.14.

---

## Pyramid — broker vs FastLoop

| Camada | Estado antes | Estado agora |
|--------|--------------|--------------|
| FastLoop | `[PYRAMID_EVAL] add=True` (só log) | Mantido como avaliação |
| Broker | **Zero** `[PYRAMID] EXEC OK` no log | Execução em `finally` (thread MT5 principal), 1× por layer |
| Lote pyramid corrigido | `LOT1.00` (bug P3) | `LOT0.05` mínimo metal, escala desde volume âncora |

**#193126680:** pyramid nunca executou no broker — posição encerrou antes do wiring broker.

---

## P4 — EDGE_GATE bypass vencedores + multi-entrada

| Antes | Depois |
|-------|--------|
| EDGE bloqueava novas entradas XAU com vol baixo | BYPASS se posição OMEGA lucrativa no activo |
| 1 ordem/activo/ciclo | `OMEGA_ALLOW_SCALE_ENTRIES=1` + bypass `[DEDUP]` mesma dir vencedora |
| RiskBudget slots ignorados por legacy | Mantido bypass legado quando slots > 0 |

**Env:** `OMEGA_EDGE_BYPASS_WINNER=1`, `OMEGA_ALLOW_SCALE_ENTRIES=1`, `OMEGA_MAX_SAME_DIR_PER_CYCLE=3`

---

## Eliminados (CEO)

- Test Harness USFE+RUPTURE BTC como modelo XAU — `OMEGA_TEST_HARNESS=0`
- Filosofia "entrar 1× e esperar" — scale-entry activo

---

## Arranque runner

```powershell
Remove-Item -Force audit\paper\omega_runner.lock -ErrorAction SilentlyContinue
powershell -ExecutionPolicy Bypass -File scripts\run_omega_24x7.ps1
```

**Marcadores de sucesso no log:**
- `[FIX1] Engines re-sincronizados` com ticket #193126680
- `[PARTIAL_CLOSE] [RESYNC] XAUUSD #193126680`
- `[TRAILING] [RESYNC] XAUUSD #193126680`
- Novas entradas: `[IMPACT_TP]`, `[EDGE_GATE] BYPASS`, `[DEDUP] BYPASS scale-entry`

---

## Limitações declaradas

- Piso 0.05 só em XAU/XAG — outros activos seguem LotCalc (sem `OMEGA_MIN_LOT_EXEC=1.0`).
- TP por impacto depende de SEL activo e `sel_impact_tp_pts > 0` no ciclo de entrada.
- Validação PnL real só após sessão com logs MT5 — este documento cobre wiring Nível 1–2.

---

*AIC — conforme AIC_TIER0_RULES_v4 | estado runtime: verificar `audit/paper/omega_24x7_runner.log`*
