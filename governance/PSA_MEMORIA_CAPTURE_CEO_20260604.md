# PSA — MEMÓRIA COMPLETA (Capture Matrix + Batimento Cardíaco)

**ID:** `OMEGA-PSA-MEMORIA-CAPTURE-20260604`  
**Versão:** 2.0 (substitui v1.0 de 2026-06-03)  
**Autor:** PSA — Principal Solution Architect  
**Branch:** `hotfix/forensic-remediation-20260527`  
**Commits referência:** `a0f2352` (P0–P4) | `2ca77bd` (batimento pyramid)  
**Instruções operacionais:** `PSA_INSTRUCOES_EXECUCAO_CAPTURE_CEO_20260604.md`  
**Equity ref.:** USD 10,688.47 | **Modo:** paper MT5 demo

---

## 0. REGRA DE OURO PSA

| PSA deve | PSA não deve |
|----------|--------------|
| Manter **1 runner** paper 24/7 | Reiniciar em shadow silencioso |
| Push remote após cada fix P0 | Deixar código só local |
| Reportar **batimento** binário 08:00 | Entregar PnL USD como veredito |
| Escalar add=True + silêncio imediato | Esperar 72h passivas |
| Documentar cada sessão forensic | Perder evidência log |

---

## 1. NARRATIVA — O QUE ACONTECEU

### 1.1 Problema central (PLUG→ACT)

O motor SEL/USFE (**PLUG**) calculava energia (`sel_impact_tp_pts`, pyramid triggers). A camada MT5 (**ACT**) ignorava ou não recebia esses sinais.

**Metáfora CEO/CKO:** motor a gritar "compra/vende mais" — braço mecânico paralisado.

### 1.2 Caso forense #193126680 (prova empírica)

| Parâmetro | Valor |
|-----------|-------|
| Ticket | #193126680 |
| Símbolo | XAUUSD SELL @ 4475.71000 |
| Lote entrada | 0.02 |
| `sel_impact_tp_pts` (H4) | **42.48** |
| TP MT5 (wrong) | 4347.14 → **~12 857 pts** |
| TP correcto (impact) | ~4475.285 (~42 pts) |
| Partial broker | 0.01 @ 4461.92 → **USD 13.79** |
| Max excursion | ~**1 764 pts** favoráveis |
| `[PYRAMID_EVAL] add=True` | **158×** |
| `[PYRAMID] EXEC OK` | **0×** (pré-fix) |
| Fecho posição | ~15:03 UTC 03/Jun |

### 1.3 Causa raiz pyramid (descoberta forense completa 03/Jun sessão 2)

**FACTO log:** zero `[PYRAMID_DISPATCH]` e zero `[FastLoop EMIT]` em 640K+ linhas (todo runner PID 13144).

**Causa em camadas:**
1. Runner PID 13144 (iniciado 14:57:38 UTC) não tinha bloco `if _add:` em `_evaluate_position` — código antigo carregado em memória Python
2. Commit `2ca77bd` (21:29 UTC) adicionou o bloco mas o runner continuou com código antigo (Python não hot-reload)
3. Diagnóstico desta sessão: `.pyc` de 21:33 > `.py` de 21:29 → confirmou que o fix estava escrito mas o runner vivo nunca o viu
4. Fix: restart PID 9972 às 21:51 UTC via `psa_capture_session_go.ps1 -Background`

**Prova do restart correcto:**
```
[FastLoop STARTED — interval=2.0s | AI_flip_conf=0.75]     ← 21:52:26
[FASTLOOP] Iniciado — interval=2s | OMEGA_USE_FASTLOOP=1    ← novo código
[FastLoop asyncio loop iniciado]                             ← pyramid wire activo
MT5 State Sync: 0 posicoes OMEGA                            ← #193126680 já fechada
```

**Fix `2ca77bd`:** FastLoop emite `PYRAMID_ADD` + `[PYRAMID_DISPATCH]` → drain executa `dispatch_pyramid_broker()` na thread MT5.

---

## 2. MATRIZ P0–P4 + BATIMENTO (estado actual)

| ID | Descoberta | Acção | Evidência log | Status pós-2ca77bd |
|----|------------|-------|---------------|-------------------|
| **P0** | impact_tp ignorado | `OMEGA_USE_SEL_IMPACT_TP=1` | `[IMPACT_TP] SEL impact=` | **PARCIAL** — wiring OK |
| **P0r** | TP órfãs legacy | `resync_impact_tp_for_position()` | `[IMPACT_TP] [RESYNC]` | **NÃO PROVADO** (n=0) |
| **P0-U3** | Floor vs impact | CEO: floor económico | `FLOOR APPLIED` | **IMPLEMENTADO** |
| **P1** | Partial tardio metais | 0.3×ATR 1º nível | `[MT5_CLOSE_PARTIAL] ✅` | **PROVADO n=1** |
| **P2** | Pyramid gate 0.60 | Metal 0.35 + bypass profit | `[PYRAMID_EVAL] add=True` | **EVAL OK** |
| **P2b** | EVAL sem broker | `dispatch_pyramid_broker()` | DISPATCH→ORDERSEND→EXEC | **AGUARDA MERCADO** |
| **P3** | LOT1.00 / micro | `OMEGA_MIN_LOT_METAL=0.05` | sem LOT1.00 pós-fix | **CÓDIGO OK** |
| **P4** | EDGE bloqueia vencedor | BYPASS + scale entries | `[EDGE_GATE] BYPASS` | **NÃO PROVADO** (n=0) |
| **BAT** | Artéria cortada | PYRAMID_ADD queue | sequência §3 | **CÓDIGO OK** |

---

## 3. ARQUITECTURA BATIMENTO CARDÍACO (pós-2ca77bd)

```
FastLoop (2s, async)
  └─ check_pyramid_add()
       └─ add=True ?
            ├─ [PYRAMID_EVAL] log
            ├─ [PYRAMID_DISPATCH] log  ← NOVO (obrigatório)
            └─ FastLoopSignal(action=PYRAMID_ADD) → Queue

shadow_loop main thread (cada ciclo ~20s)
  └─ drain_fastloop_signals()
       └─ PYRAMID_ADD ?
            ├─ [PYRAMID_DISPATCH] (source=FASTLOOP_DRAIN)
            ├─ [MT5_ORDERSEND] pyramid
            └─ [PYRAMID] EXEC OK / EXEC FAIL

finally (fim ciclo shadow)
  └─ check_pyramid_add() + dispatch_pyramid_broker(source=FINALLY)
```

### Ficheiros alterados

| Ficheiro | Função / zona |
|----------|---------------|
| `async_position_orchestrator.py` | `FastLoopSignal` + emit `PYRAMID_ADD` L207–280 |
| `shadow_loop.py` | `dispatch_pyramid_broker()` L2595+ |
| `shadow_loop.py` | drain `PYRAMID_ADD` L3223+ |
| `shadow_loop.py` | `IMPACT_TP` + `FLOOR APPLIED` L4456+ |
| `shadow_loop.py` | finally pyramid L5533+ |
| `scripts/psa_capture_session_report.ps1` | Secção BATIMENTO CARDÍACO |

---

## 4. P0 — IMPACT_TP + U3 FLOOR

### Fórmula efectiva (código)

```python
eff_tp = max(_sel_impact_tp, float(_min_pts_pre))
# _min_pts_pre = max(cost_pts * 2, 8)
```

### Decisão CEO U3 (2026-06-04)

- **Regra:** floor económico — não sair por USD 0.85 em lote mínimo.
- **Log obrigatório quando floor activo:**

```
[XAUUSD H4] [IMPACT_TP] SEL impact=17.0pts -> FLOOR APPLIED -> eff_tp=60 (min_pts=...)
```

- **Quando impact >= min_pts:** log sem FLOOR APPLIED (ex.: BTC `873→873`).

### Resync órfãs

- Função: `resync_impact_tp_for_position()` — boot + cada ciclo `finally`.
- Log esperado: `[IMPACT_TP] [RESYNC] ticket=... new_tp=...`

---

## 5. P1 — PARTIAL 0.3×ATR METAIS

```python
_PARTIAL_CLOSE_LEVELS_METAL_CEO = [0.3, 1.5, 2.5, 4.0]
```

- Função: `partial_close_levels_for(symbol)`
- Prova #193126680: `[MT5_CLOSE_PARTIAL] ✅ 0.01 @ 4461.92` | move_atr=0.82

---

## 6. P2 — PYRAMID

### Regra metal (CEO prevalece sobre CQO)

```python
# CEO 2026-06-04: profit >= trigger → pyramid em metais SEM veto trend_score
_metal_profit_proven = symbol in _METAL_ASSETS and profit_pts >= trigger
```

### Envs

```
OMEGA_PYRAMID_MIN_SCORE_METAL = 0.35
OMEGA_PYRAMID_LAYERS          = 4
OMEGA_PYRAMID_ATR             = 0.5    # trigger = 0.5 × ATR_pts
OMEGA_PYRAMID_LOT_SCALE       = 1.5
```

### Contrafactual #193126680 (1 camada 0.05 @ 1500 pts)

```
PnL ≈ 1500 × 0.05 × 1.0 = USD 75.00  (oportunidade perdida pré-batimento)
```

---

## 7. P3 — LOTE

```python
def exec_min_lot_floor(asset, regime):
    if asset in _METAL_ASSETS:
        return OMEGA_MIN_LOT_METAL  # 0.05
    return min_lot_floor_for_regime(regime)
```

**PROIBIDO:** `OMEGA_MIN_LOT_EXEC=1.0` (revertido CEO 03/Jun).

---

## 8. P4 — EDGE + SCALE

```
OMEGA_EDGE_BYPASS_WINNER     = 1
OMEGA_ALLOW_SCALE_ENTRIES    = 1
OMEGA_MAX_SAME_DIR_PER_CYCLE = 3
```

**Risco cluster:** até 3 × R ≈ USD 160/ciclo — monitor DD diário.

---

## 9. SUPRESSORES DE FLUXO (PSA alertas)

| Gate | Contagem log (03/Jun acum.) | Efeito |
|------|----------------------------|--------|
| `[MTF_BIAS] BLOCK` | ~7 000+ | Reduz entradas contra macro |
| `[USFE] bias=BLOCK` | ~31 000+ | Veto paralelo SEL-USFE |
| Combinação | — | λ efectivo << 1.5 trades XAU/dia |

**Implicação:** batimento pode demorar até posição vencedor XAU abrir e atingir trigger.

---

## 10. TIMELINE CONSOLIDADA

| UTC | Evento |
|-----|--------|
| 03/Jun 01:04 | Entrada #193126680 |
| 03/Jun 14:52–15:03 | 158× pyramid EVAL; partial OK; 0 EXEC |
| 03/Jun 20:25 | Restart PID 13144 — capture matrix (código P0–P4 activo) |
| 03/Jun 21:28 | Fix batimento `2ca77bd` commit — PID 10416 (OLD code still in memory) |
| 03/Jun 21:51 | **Restart PID 9972** — novo código carregado (`PYRAMID_DISPATCH` activo) |
| 03/Jun ~15:03 | #193126680 fechada por SL breakeven 4476.28 |
| 04/Jun 08:00 | Relatório PSA batimento (obrigatório) |

---

## 11. ENVS COMPLETOS — `run_omega_24x7.ps1`

```powershell
# CEO CAPTURE MATRIX
$env:OMEGA_TEST_HARNESS             = "0"
$env:OMEGA_USE_SEL_IMPACT_TP        = "1"
$env:OMEGA_PYRAMID_MIN_SCORE_METAL  = "0.35"
$env:OMEGA_EDGE_BYPASS_WINNER       = "1"
$env:OMEGA_ALLOW_SCALE_ENTRIES      = "1"
$env:OMEGA_MIN_LOT_METAL            = "0.05"
$env:OMEGA_MAX_SAME_DIR_PER_CYCLE   = "3"
$env:OMEGA_PYRAMID_LAYERS           = "4"
$env:OMEGA_24X7_MODE                = "paper"
$env:OMEGA_MIN_TP_USD_METAL         = "18"
$env:OMEGA_LOOP_INTERVAL_SEC        = "20"
$env:OMEGA_USE_FASTLOOP             = "1"
$env:OMEGA_FASTLOOP_INTERVAL        = "2.0"
```

---

## 12. SCRIPTS PSA

### `psa_capture_session_go.ps1`

- FASE 0: stop duplicados + locks  
- FASE 1: py_compile + pytest  
- FASE 2: runner background  
- Forensic: `audit/forensic/capture_session_*/`

### `psa_capture_session_report.ps1`

**Métricas novas (v2):**

| Métrica | Pattern |
|---------|---------|
| `pyramid_dispatch` | `[PYRAMID_DISPATCH]` |
| `mt5_ordersend_pyramid` | `[MT5_ORDERSEND] pyramid` |
| `impact_tp_floor` | `FLOOR APPLIED` |

**Veredito batimento:** impresso automaticamente (secção BATIMENTO CARDIACO).

---

## 13. HEURÍSTICA VEREDITO — ETAPA 2A

| Prioridade | Critério | PASS |
|------------|----------|------|
| **P0** | Batimento DISPATCH→ORDERSEND | >=1 após add=True |
| P1 | IMPACT_TP activo | >=1 |
| P2 | Pyramid EXEC OK ou FAIL explicado | >=1 tentativa broker |
| P3 | Partial metal (anecdotal n=1 já existe) | >=0 nova |
| P4 | Sem LOT1.00 / MIN_LOT_EXEC | Zero |
| P5 | Runner + git remote | OK |

**Não declarar capture validada** até P0+P2 PASS.

---

## 14. COMMITS E REMOTE

```bash
git log --oneline -5
# 2ca77bd fix(capture): wire FastLoop pyramid to MT5 thread - batimento cardiaco
# a0f2352 feat(capture): CEO Capture Matrix 2026-06-03
git push origin hotfix/forensic-remediation-20260527
```

---

## 15. DOCUMENTAÇÃO CRUZADA

| Documento | Papel |
|-----------|-------|
| `PSA_INSTRUCOES_EXECUCAO_CAPTURE_CEO_20260604.md` | Handoff operacional |
| `PSA_MEMORIA_CAPTURE_CEO_20260604.md` | Este ficheiro |
| `PSA_ADDENDUM_CONSELHO_20260604.md` | Síntese Conselho + decisões |
| `CEO_MANDATO_BATIMENTO_PYRAMID_20260604.md` | Mandato CEO |
| `AIC_PARECER_CONSOLIDACAO_CONSELHO_PLUG_ACT_20260604.md` | Parecer AIC |
| `CONSELHO_CENARIO_PLUG_ACT_20260603.md` | Relatório forense Conselho |

---

## 16. LIMITAÇÕES

- Prova pyramid broker depende de mercado (posição vencedor + trigger).
- Contagens MTF/USFE/USFE BLOCK reduzem frequência de oportunidades.
- Partial n=1 = evidência anecdótica (governança Tier-2 pede n≥30).
- Este documento não autoriza GO live.

---

*PSA — memória v2.0 | AIC_TIER0 | 2026-06-04*
