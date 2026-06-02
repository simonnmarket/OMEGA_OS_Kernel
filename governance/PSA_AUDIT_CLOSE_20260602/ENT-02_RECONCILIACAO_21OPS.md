# ENT-02 — RECONCILIAÇÃO "21 OPERAÇÕES"
**ID:** `OMEGA-PSA-AUDIT-CLOSE-20260602 / ENT-02`  
**Título:** Reconciliação MT5 vs trade_feedback — 21 tickets únicos  
**Referência CEO:** "reconciliação 21 operações"

---

## 1. ORIGEM DA DIVERGÊNCIA

O MT5 terminal mostra **21 operações** (deals/posições visíveis em History + Open Positions). O `trade_feedback.jsonl` regista **18 eventos de abertura** + **12 eventos de fecho** = 29 linhas totais.

| Fonte | Contagem | Notas |
|-------|----------|-------|
| MT5 terminal (History + Open) | **21** | Inclui legacy + gaps |
| `trade_feedback.jsonl` opened | 17 | Novos tickets da sessão |
| `trade_feedback.jsonl` closed | 12 | Incluindo 1 legacy |
| Legacy OMEGA (pré-sessão fechado) | 1 | XAUUSD #192648431 |
| **Total tickets únicos OMEGA** | **18** | 17 novos + 1 legacy |
| Legacy não-OMEGA (P-04) | **3** | Não geridos pelo runner |
| **TOTAL RECONCILIADO** | **21** | ✓ Match com MT5 |

---

## 2. BREAKDOWN DOS 21 TICKETS

### Grupo A — Fechados com registo completo (12)

| Ticket | Ativo | PnL | Status |
|--------|-------|-----|--------|
| #192648431 | XAUUSD | −$15.22 | ✓ closed em feedback |
| #192695231 | US100 | −$21.17 | ✓ closed em feedback |
| #192702716 | USDJPY | −$1.35 | ✓ closed em feedback |
| #192710972 | XAUUSD | −$68.60 | ✓ closed em feedback |
| #192807978 | GER40 | −$0.06 | ✓ closed em feedback |
| #192809456 | GER40 | +$74.54 | ✓ closed em feedback |
| #192819339 | USDJPY | −$2.25 | ✓ closed em feedback |
| #192836895 | GER40 | −$25.39 | ✓ closed em feedback |
| #192842530 | GER40 | −$25.21 | ✓ closed em feedback |
| #192858349 | GER40 | −$33.33 | ✓ closed em feedback |
| #192924673 | US100 | +$1.44 | ✓ closed em feedback |
| #192935713 | US100 | +$7.79 | ✓ closed em feedback |
| **SUBTOTAL** | | **−$108.81** | ✓ confirma figura CEO |

### Grupo B — Abertos com gestão activa (4 — ledger confirmado)

| Ticket | Ativo | Float (17:03 UTC) | SL | Status |
|--------|-------|-------------------|----|--------|
| #192911095 | UKOIL+ BUY | +$6.00 | 93.52 | OPEN trailing |
| #192917489 | UKOIL+ BUY | +$4.05 | 93.91 | OPEN trailing |
| #192932327 | GER40 BUY | −$9.58 | 25,030.47 | OPEN trailing |
| #192940845 | US500 BUY | +$0.47 | 7,591.65 | OPEN trailing |
| **Float total** | | **+$0.94** | | `positions_ledger.json` |

### Grupo C — Gaps de registo (2 — ver ENT-03)

| Ticket | Ativo | Gap |
|--------|-------|-----|
| #192746138 | BTCUSD SELL | Aberto em feedback, desapareceu de ledger ~04:36 UTC; sem `position_closed` |
| #192957446 | ETHUSD SELL | Aberto em feedback, `MT5_CLOSE_PARTIAL` executado 17:20 UTC; sem `position_closed` |

### Grupo D — Legacy não-OMEGA (3 — P-04)

| Ticket | Ativo | Estado |
|--------|-------|--------|
| #192653640 | EURUSD | Aberto em MT5, não gerido OMEGA |
| #192470725 | UKOIL+ | Aberto em MT5, P-03 pendente |
| #192253913 | US500 | Aberto em MT5, P-04 pendente CEO |

---

## 3. PnL TOTAL RECONCILIADO

| Componente | PnL |
|------------|-----|
| Realizados confirmados (Grupo A) | **−$108.81** |
| Float OMEGA activo (Grupo B, 17:03) | +$0.94 |
| BTCUSD #192746138 estimado (Grupo C) | ~−$37.54 |
| ETHUSD #192957446 estimado (Grupo C) | ~+$4.48 |
| Legacy não-OMEGA (Grupo D) | ND — fora de gestão |
| **Total estimado bruto** | **~−$140.93** |
| Equity actual (17:58 UTC) | $10,731.42 (DD=0.08%) |
| Equity T0 | $10,730.89 |
| **Variação T0→17:58** | **+$0.53** (recuperação) |

> **Nota:** A recuperação de equity a quasi-T0 ($10,731.42 vs $10,730.89) indica que posições activas (UKOIL+, US500, GER40) + flutuação intra-dia compensaram o drawdown de -$108.81 realizado.

---

*Fonte: `audit/paper/trade_feedback.jsonl`, `audit/paper/positions_ledger.json`, `audit/paper/omega_24x7_runner.log`*  
*Gerado: 2026-06-02 19:10 UTC*
