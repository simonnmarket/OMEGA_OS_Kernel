# PSA — RELATÓRIO PROFIT / CKO v2 — 08:00 UTC
**Ficheiro:** `governance/PSA_RELATORIO_PROFIT_20260602_0800UTC.md`  
**Gerado:** 2026-06-02 07:55 UTC (AIC — pré-08:00, pedido urgente CEO)  
**Janela de análise:** 2026-06-01 23:29:53 UTC → 2026-06-02 07:55 UTC  
**Branch:** `hotfix/forensic-remediation-20260527` | HEAD: `e295c44`  
**Runner PID:** 30020 | **mode:** paper | **ciclos completos:** 104+

---

## BLOCO 1 — PnL PAPER

### Equity

| Momento | Valor | Fonte |
|---------|-------|-------|
| T0 arranque (23:29:53 UTC) | **$10,730.89** | log `mode=paper` startup |
| KS anchor (primeira leitura) | $10,740.01 | log `KS OK` 00:04 UTC |
| Equity mínimo sessão | $10,601.48 | log `KS OK` 06:04 UTC (DD=1.29%) |
| Equity actual (07:52 UTC) | **$10,610.98** | log `KS OK` 07:52 UTC |
| **Variação T0 → actual** | **−$119.91 (−1.12%)** | calculado |
| DD máximo observado | **1.29%** | 06:04 UTC |
| Threshold DD kill switch | 10% ($9,657.80) | `OMEGA_DD_DAILY_MAX` |
| **Kill switch disparado** | **NÃO** | `kill_switch: False` |

### Trades Realizados (OMEGA-managed)

| # | Ticket | Ativo | Dir | Lots | Entrada | Saída/Estado | PnL | Dur | Notas |
|---|--------|-------|-----|------|---------|-------------|-----|-----|-------|
| 1 | #192648431 | XAUUSD | SELL | — | — | Fechado 00:34 UTC | **−$15.22** | 88.6 min | Legacy pré-sessão, fechado pelo runner |
| 2 | #192695231 | US100 | BUY | 0.45 | — | Fechado 01:04 UTC | **−$21.17** | ~30 min | Stop |
| 3 | #192702716 | USDJPY | BUY | 0.24 | — | Fechado 01:00 UTC | **−$1.35** | 0 min | Stop imediato |
| 4 | #192710972 | XAUUSD | SELL | 0.046 | — | Fechado 04:01 UTC | **−$68.60** | ~3h | Maior perda sessão |
| 5 | #192746138 | BTCUSD | SELL | 0.07 | 70,236.50 | SL hit ~04:36 UTC* | ~−$37* | — | SL=70,772.74; último log 04:36 |
| 6 | #192661613 | USDJPY | BUY | 0.25 | 159.662 | **ABERTO** | **+$9.55** | activo | Trailing SL=159.669; breakeven activo |

> \* BTCUSD #192746138: sem `position_closed` em `trade_feedback.jsonl`, mas posição desapareceu do ledger entre 04:36 e 07:38. SL 70,772 provavelmente atingido quando preço subiu de 70,236 → 70,761 às 04:36.

### Resumo PnL

| Métrica | Valor |
|---------|-------|
| Trades fechados (sessão) | 5 (incl. 1 legacy) |
| Trades LOSS | 5 |
| Trades WIN | 0 |
| **PnL realizado total** | **−$106.34** (confirmado `trade_feedback.jsonl`) |
| PnL estimado BTCUSD (#192746138) | ~−$37 (não registado) |
| Float USDJPY #192661613 | +$9.55 |
| Posições OMEGA abertas (07:55) | **1** (USDJPY #192661613) |

### Nota sobre "6 posições com prejuízo" (CEO)
O runner OMEGA só gere posições marcadas com comment OMEGA em MT5. O log confirma **1 posição OMEGA detectada** às 07:48 UTC (`MT5 State Sync: 1 posicoes OMEGA`). As restantes posições visíveis no MT5 são **legadas de sessões anteriores** (abertas antes do arranque desta sessão) e **não estão sob gestão do runner actual**. O DD de 1.12% reflecte o efeito combinado de todas as posições da conta MT5. Recomendação: fechar posições legacy conforme `tickets_to_close.json` (P-04 pendente aprovação CEO).

---

## BLOCO 2 — ACURÁCIA VETO SEL

### Resumo quantitativo

| Métrica | Valor |
|---------|-------|
| Total avaliações em `decision_trace.jsonl` (sessão) | 1,272 |
| `SKIP_SEL_AUDIT_VETO` (gate SEL) | **109** (8.6%) |
| `SKIP_USFE_BIAS_BLOCK` (gate USFE) | **75** (5.9%) |
| Total bloqueios SEL+USFE | **184** (14.5%) |
| `SKIP_EDGE_GATE` (upstream) | 1,086 (85.4%) |
| Entradas executadas | 5 (via `trade_feedback.jsonl`) |

### SEL veto por ativo (109 eventos)

| Ativo | Bloqueios SEL | TFs principais |
|-------|---------------|----------------|
| BTCUSD | 36 | M15, H4 |
| US100 | 26 | H4, H1 |
| GER40 | 26 | H4, H1 |
| ETHUSD | 20 | H4, H1 |
| XAUUSD | 1 | — |

### USFE veto por ativo (75 eventos)

| Ativo | Bloqueios USFE |
|-------|---------------|
| GBPUSD | 20 |
| USDJPY | 15 |
| BTCUSD | 10 |
| US100 | 7 |
| XRPUSD | 5 |
| XAUUSD | 4 |
| ETHUSD | 4 |
| UKOIL+ | 3 |
| AUDUSD | 3 |
| EURUSD | 2 |
| GER40 | 2 |

### Avaliação qualitativa veto SEL (amostra)

O gate SEL disparou principalmente em **BTCUSD, US100, GER40** (activos que efectivamente tiveram movimento adverso nesta sessão — BTCUSD subiu de 70,236 para 70,760 após runner abrir SELL; o SEL já bloqueava entradas nestas direcções antes). US100 foi bloqueado repetidamente (26×) às 23:59–02:00 UTC e o US100 aberto (#192695231 BUY 00:34) foi fechado com −$21.17 — sugerindo que o SEL estava correcto em vetar sinais subsequentes.

**Classificação preliminar:** sem preços de retorno completos para cada veto, mas a correlação entre as perdas realizadas e os activos mais vetados indica postura **defensiva correcta**. Análise detalhada requere dados MT5 OHLC pós-veto (disponível nos HDF5/OHLCV de cada ativo).

---

## BLOCO 3 — FRICTION RATE

### Pipeline de filtragem (pós-IA)

| Gate | Bloqueios (log) | % de sinais IA |
|------|----------------|----------------|
| Sinais IA aprovados (`Sinal aprovado`) | **2,485** | 100% baseline |
| MTF_BIAS BLOCK | 1,323 | 53.2% |
| SEL_AUDIT_VETO | 242 | 9.7% |
| USFE_BIAS_BLOCK | 200 | 8.1% |
| SPIKE_BLOCK | 4 | 0.2% |
| **Entradas executadas** | **5** | **0.2%** |

> Nota: os contadores MTF/SEL/USFE somam mais que 100% porque um sinal pode ser bloqueado sequencialmente em múltiplos TFs do mesmo ciclo. Counts directos do log (grep).

### Friction por fase (decision_trace — upstream)

| Fase | Contagem sessão |
|------|----------------|
| SKIP_EDGE_GATE (pré-IA) | 1,086 |
| SKIP_SEL_AUDIT_VETO (pré-execução) | 109 |
| SKIP_USFE_BIAS_BLOCK (pré-execução) | 75 |

### Interpretação

- **85.4%** dos sinais são eliminados logo no EDGE_GATE (ATR/ADX/vol insuficiente) — comportamento esperado, mercado nocturno/madrugada com baixa volatilidade.
- **14.5%** dos que passam o edge gate são bloqueados pela camada SEL+USFE — gate a funcionar.
- Taxa de execução efectiva: **~0.2%** dos sinais IA → confirmando que o sistema está em modo altamente selectivo.
- **0 ENTRY por SEL gate** — nenhuma entrada foi permitida pela SEL gate nesta sessão; todas as 5 entradas foram por path que não atingiu a gate SEL (passaram USFE/SEL veto=False com confluência variável).

---

## STATUS RUNNER (07:55 UTC)

| Item | Estado |
|------|--------|
| PID 30020 | **ACTIVO** |
| Último ciclo | 104 (07:47 UTC) |
| mode | **paper** |
| mode=shadow após arranque | **NÃO** — zero ocorrências |
| FATAL mutex >3 ciclos | **NÃO** |
| Kill switch | **False** |
| DD actual | **1.20%** (threshold 10%) |
| Posições OMEGA abertas | 1 (USDJPY +$9.55) |
| Commit HEAD | e295c44 |

---

## PENDÊNCIAS (PSA §12 — não alteradas)

| ID | Item | Estado |
|----|------|--------|
| P-03 | Fechar UKOIL+ #192470725 na abertura de mercado | **Aguarda CEO** |
| P-04 | Fase 2 fecho legacy (`tickets_to_close.json`) | **Aguarda CEO APROVADO** |
| P-05 | SEL-1 report RP>0.75 vs movimento MT5 | Dias 9-12 CKO |
| P-07 | `OMEGA_RUPTURE_CAPTURE=1` | Aguarda CEO dia 13+ |

---

*Relatório gerado por AIC — CKO v2 — 2026-06-02 07:55 UTC*  
*Fonte de dados: `audit/paper/omega_24x7_runner.log`, `audit/paper/positions_ledger.json`, `audit/paper/trade_feedback.jsonl`, `audit/paper/decision_trace.jsonl`*
