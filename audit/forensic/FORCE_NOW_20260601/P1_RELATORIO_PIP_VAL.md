# P1 - RELATORIO PIP_VAL BUG & FIX

**Data:** 2026-05-31T22:48:32.847090+00:00 UTC
**Commit fix:** `00c6c9b`
**Branch:** `hotfix/forensic-remediation-20260527`

---

## 1. Root Cause

Formula errada em calibracao e fallback shadow_loop:

```python
# ERRADO (pre-fix)
pip_val = profit / (100 * pt)  # divide por unidade de preco, nao por 100 pontos

# CORRECTO (pos-fix)
pip_val = profit / 100.0  # USD por ponto por lote
```

Exemplo EURUSD (pt=0.00001): order_calc_profit(+100pts, 1lot) = $100
- BUG: $100 / (100 x 0.00001) = 100,000 x/ponto/lote (errado)
- FIX: $100 / 100 = $1.00/ponto/lote (correcto)

---

## 2. Diff Cache Antes/Depois

| Simbolo | Antes (BUG) | Depois (FIX) | Ratio |
|---------|------------|-------------|-------|
| ADAUSD | 100.0 | 0.01 | x10000 |
| AUDUSD | 100000.0 | 1.0 | x100000 |
| AVAXUSD | 1.0 | 0.001 | x1000 |
| BNBUSD | 1.0 | 0.01 | x100 |
| BTCUSD | 1.0 | 0.01 | x100 |
| DOGUSD | 1000.0 | 0.01 | x100000 |
| ETHUSD | 1.0 | 0.001 | x1000 |
| EURUSD | 100000.0 | 1.0 | x100000 |
| GBPUSD | 100000.0 | 1.0 | x100000 |
| GER40 | 1.17 | 0.0117 | x100 |
| LTCUSD | 1.0 | 0.001 | x1000 |
| SOLUSD | 1.0 | 0.001 | x1000 |
| UKOIL+ | 100.0 | 1.0 | x100 |
| US100 | 1.0 | 0.01 | x100 |
| US30 | 1.0 | 0.01 | x100 |
| US500 | 1.0 | 0.01 | x100 |
| USDCAD | 72410.0 | 0.7241 | x100000 |
| USDJPY | 627.0 | 0.6268 | x1000 |
| XAGUSD | 5000.0 | 5.0 | x1000 |
| XAUUSD | 100.0 | 1.0 | x100 |
| XRPUSD | 1000.0 | 0.01 | x100000 |

---

## 3. Lot Sizing - Antes vs Depois

equity=$10917, risk=0.5%=$54.58, min_lot=0.01, max_lot=0.30

| Simbolo | Cat | SL_pts | pip_BUG | lot_BUG | pip_FIX | lot_FIX | TP_USD_FIX | Piso | Gate |
|---------|-----|--------|---------|---------|---------|---------|-----------|------|------|
| EURUSD | forex | 200 | 100000.0 | 0.01 | 1.0000 | 0.27 | $162.00 | $10 | PASS |
| USDJPY | forex | 50 | 627.0 | 0.01 | 0.6268 | 0.30 | $32.91 | $10 | PASS |
| AUDUSD | forex | 200 | 100000.0 | 0.01 | 1.0000 | 0.27 | $162.00 | $10 | PASS |
| XAUUSD | metal | 1500 | 100.0 | 0.01 | 1.0000 | 0.04 | $180.00 | $18 | PASS |
| UKOIL+ | energy | 60 | 100.0 | 0.01 | 1.0000 | 0.30 | $60.00 | $10 | PASS |
| US500 | index | 600 | 1.0 | 0.09 | 0.0100 | 0.30 | $13.34 | $25 | GATE-BLOQUEIA(<$25) |
| SOLUSD | crypto | 60 | 1.0 | 0.30 | 0.0010 | 0.30 | $0.06 | $15 | GATE-BLOQUEIA(<$15) |

---

## 4. Confirmacao MT5 History

Zero ordens absurdas. Verificado via history_deals_get(position=) para todas as posicoes:

| Ticket | Simbolo | Vol | Hora_UTC | Nota |
|--------|---------|-----|----------|------|
| #192243746 | AUDUSD | 0.17 | 2026-05-31 23:42 | Pre-restart (formula correcta) |
| #192243914 | USDJPY | 0.01 | 2026-06-01 00:43 | Pos-restart (min_lot BUG clamp) |
| #192244227 | USDJPY | 0.01 | 2026-06-01 00:46 | Pos-restart (min_lot BUG clamp) |
| #192253446 | SOLUSD | 0.10 | 2026-06-01 01:23 | max_lot cap OK |
| #192253913 | US500  | 0.06 | 2026-06-01 01:25 | Normal |
| #192254628 | USDJPY | 0.01 | 2026-06-01 01:30 | Pos-restart (min_lot BUG clamp) |

Conclusao: BUG causou lots DEMASIADO PEQUENOS (conservador). ZERO risco de over-sizing.

---

## 5. Fix Aplicado (commit 00c6c9b)

| Ficheiro | Alteracao |
|----------|-----------|
| scripts/psa_calibrate_pip_value_mt5.py | profit/100.0 (era /100*pt) |
| core_engines/shadow_loop.py | fallback corrigido (linha ~1074) com comentario P1-FIX |
| config/pip_value_cache.json | recalibrado 21 simbolos |

Activacao: IMEDIATA (leitura de disco em cada ciclo, sem restart).

---

## 6. Monitorizacao 2H Pos-Fix

Proximos [ECON_OPEN] esperados com valores plausíveis:

| Simbolo | pip_val esperado | Observavel no log |
|---------|-----------------|-------------------|
| EURUSD  | ~1.00 | pip_val=1.000000 |
| USDJPY  | ~0.63 | pip_val=0.626800 |
| US500   | ~0.01 | pip_val=0.010000 |
| XAUUSD  | ~1.00 | pip_val=1.000000 |
| SOLUSD  | ~0.001 | pip_val=0.001000 |

[ECON_GATE] volta a bloquear trades suboptimos: EURUSD TP_est=$2 < $10 -> SKIP.

---
*PSA — 2026-05-31 22:48 UTC*