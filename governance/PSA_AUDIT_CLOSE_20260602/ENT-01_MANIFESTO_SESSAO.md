# ENT-01 — MANIFESTO DA SESSÃO
**ID:** `OMEGA-PSA-AUDIT-CLOSE-20260602 / ENT-01`  
**Título:** Manifesto completo de todas as operações da sessão  
**Janela:** 2026-06-01 23:29:53 UTC → 2026-06-02 19:10 UTC  
**Branch:** `hotfix/forensic-remediation-20260527` | HEAD: `b805c2a`  
**Runner PID:** 30020 | mode: paper | SEL/USFE: ON

---

## 1. PARÂMETROS DA SESSÃO

| Parâmetro | Valor |
|-----------|-------|
| Equity T0 | $10,730.89 |
| KS anchor | $10,740.01 |
| Equity (17:58 UTC) | $10,731.42 (DD=0.08%) — quasi-recuperado |
| Kill switch | NUNCA disparado |
| DD máximo sessão | 1.29% @ 06:04 UTC |
| Threshold KS | 10% ($9,657.80) |
| Ciclos completos | 104+ (até 08:00 UTC) |
| Ativos avaliados | 19 × 3 TFs = 57 combinações/ciclo |

---

## 2. TODAS AS OPERAÇÕES (21 tickets únicos)

### 2A — OMEGA-managed (18 tickets)

| # | Ticket | Ativo | Dir | Lots | Open UTC | Close UTC | PnL | Resultado |
|---|--------|-------|-----|------|----------|-----------|-----|-----------|
| 1 | #192648431 | XAUUSD | SELL | — | pré-sess. | 2026-06-02T00:34 | −$15.22 | LOSS (legacy fechado) |
| 2 | #192695231 | US100 | BUY | 0.45 | T00:34 | T01:04 | −$21.17 | LOSS |
| 3 | #192702716 | USDJPY | BUY | 0.24 | T00:59 | T01:00 | −$1.35 | LOSS |
| 4 | #192710972 | XAUUSD | SELL | 0.0455 | T01:04 | T04:01 | −$68.60 | LOSS |
| 5 | #192746138 | BTCUSD | SELL | 0.07 | T02:08 | ~T04:36* | ~−$37.54* | LOSS (SL hit — ver ENT-03) |
| 6 | #192661613 | USDJPY | BUY | 0.25 | T01:31 | T~07:xx | +$9.55** | WIN (fechado pós-sessão) |
| 7 | #192807978 | GER40 | BUY | 0.50 | T06:07 | T06:07 | −$0.06 | LOSS |
| 8 | #192809456 | GER40 | BUY | 0.50 | T06:14 | T07:54 | +$74.54 | WIN |
| 9 | #192819339 | USDJPY | BUY | 0.10 | T06:43 | T08:02 | −$2.25 | LOSS |
| 10 | #192836895 | GER40 | BUY | 0.50 | T08:02 | T08:29 | −$25.39 | LOSS |
| 11 | #192842530 | GER40 | BUY | 0.42 | T08:29 | T09:37 | −$25.21 | LOSS |
| 12 | #192858349 | GER40 | BUY | 0.45 | T09:43 | T12:37 | −$33.33 | LOSS |
| 13 | #192911095 | UKOIL+ | BUY | 0.05 | T13:04 | **ABERTO** | +$6.00†  | OPEN |
| 14 | #192917489 | UKOIL+ | BUY | 0.05 | T13:13 | **ABERTO** | +$4.05†  | OPEN |
| 15 | #192924673 | US100 | BUY | 0.38 | T13:29 | T13:30 | +$1.44 | WIN |
| 16 | #192932327 | GER40 | BUY | 0.35 | T13:39 | **ABERTO** | −$9.58†  | OPEN |
| 17 | #192935713 | US100 | BUY | 0.48 | T13:44 | T15:55 | +$7.79 | WIN |
| 18 | #192940845 | US500 | BUY | 0.47→0.02 | T13:52 | **ABERTO** | +$0.47†  | OPEN |

> \* BTCUSD #192746138: SL hit estimado. Sem `position_closed` em `trade_feedback.jsonl` — ver ENT-03.  
> \** USDJPY #192661613: float +$9.55 às 07:47; fechado por trailing SL ou SL hit em momento não registado.  
> † Float em `positions_ledger.json` @ 17:03 UTC.

### 2B — Legacy não-OMEGA (3 tickets — P-04)

Posições visíveis em MT5, abertas em sessões anteriores, **sem mark OMEGA**, não geridas pelo runner actual:

| Ticket | Ativo | Estado |
|--------|-------|--------|
| #192653640 | EURUSD | Aberto — sem gestão OMEGA |
| #192470725 | UKOIL+ | Aberto — P-03 pendente CEO |
| #192253913 | US500 | Aberto — P-04 pendente CEO |

**Total tickets únicos documentados: 21 = 18 OMEGA + 3 legacy**

---

## 3. ESTATÍSTICAS DA SESSÃO

| Métrica | Valor |
|---------|-------|
| Operações abertas (OMEGA) | 18 |
| Fechadas com registo | 12 |
| Abertas sem close event | 6 (incl. 2 com gaps — ver ENT-03) |
| WIN (com registo) | 3 |
| LOSS (com registo) | 8 |
| Legacy fechada | 1 |
| Win rate (fechadas) | 3/11 = 27.3% |
| Maior perda individual | −$68.60 (XAUUSD #192710972) |
| Maior ganho individual | +$74.54 (GER40 #192809456) |
| PnL realizado total (feedback) | **−$108.81 USD** |

---

*Fonte: `audit/paper/trade_feedback.jsonl`, `audit/paper/omega_24x7_runner.log`, `audit/paper/positions_ledger.json`*  
*Gerado: 2026-06-02 19:10 UTC*
