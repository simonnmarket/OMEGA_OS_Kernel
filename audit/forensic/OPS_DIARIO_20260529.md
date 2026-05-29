# OPS DIÁRIO — 2026-05-29 (Sexta-feira)

## Snapshots do Dia

| Hora UTC | Path | Equity | Pos | PnL Float | Realized | Freeze | G4 | SYMBOLS_OPEN |
|----------|------|--------|-----|-----------|----------|--------|----|-------------|
| 09:54 | OPS_SNAPSHOT_20260529_0954.txt | 11038.80 | 8 | 15.68 | 0.0 | 0 | CHECK | — |
| 10:08 | OPS_SNAPSHOT_20260529_1000.txt | 11035.13 | 8 | 13.49 | 0.0 | 0 | PASS CONDICIONAL | — |
| 16:54 | OPS_SNAPSHOT_20260529_1654.txt | 11035.13 | 8 | 14.14 | 0.0 | 0 | PASS | 8 símbolos |
| 17:01 | OPS_SNAPSHOT_20260529_1701.txt | 11035.13 | 8 | 15.69 | 0.0 | 0 | PASS | 8 símbolos |

## PnL REALIZED (trade_feedback.jsonl)

| Período | Valor (USD) | Fonte |
|---------|-------------|-------|
| **HOJE (2026-05-29)** | **-46.99** | trade_feedback.jsonl |
| **7D (23-29 May)** | **-223.81** | trade_feedback.jsonl |
| **CUMULATIVO** | **-977.67** | trade_feedback.jsonl |

## TOP3 PERDAS HOJE

| # | Ativo | Ticket | PnL (USD) |
|---|-------|--------|-----------|
| 1 | **XAGUSD** | #192064150 | **-57.40** |
| 2 | US500 | #192026692 | -0.68 |
| 3 | XRPUSD | #192009009 | -0.63 |

## Todas Fechadas Hoje (2026-05-29)

| Ativo | Ticket | PnL (USD) |
|-------|--------|-----------|
| XAGUSD | #192064150 | -57.40 |
| US500 | #192026692 | -0.68 |
| XRPUSD | #192009009 | -0.63 |
| XRPUSD | #192075495 | -0.63 |
| BNBUSD | #192084259 | -0.27 |
| US100 | #192087104 | -0.21 |
| SOLUSD | #192078775 | -0.05 |
| SOLUSD | #192099309 | -0.05 |
| US100 | #192067598 | +0.01 |
| US100 | #192083807 | +0.20 |
| US100 | #192078911 | +0.92 |
| AUDUSD | #191997524 | +2.05 |
| US100 | #192006939 | +9.75 |

## Riscos (3 bullets)

1. **XAGUSD -57.40 é a maior perda isolada do dia** — representa 122% do PnL negativo total (-46.99). CEO avalia freeze entradas novas até segunda.
2. **8 posições abertas em trailing** — requer monitorização contínua de SL/TP (especialmente GER40/UKOIL+ novos).
3. **PnL cumulativo -977.67** — tendência negativa persistente; CEO proíbe alterar thresholds para "recuperar".

## Estado Runner

- MT5: terminal64.exe PID 25220 (ativo)
- Python: ciclo contínuo, shadow_rc=0
- DECISION_TRACE: =1 (mantido)
- Cache .pyc: limpo após reinício
- Último reinício: 12:03 UTC

## Decisões CEO Pendentes

| # | Decisão | Status |
|---|---------|--------|
| B1 | FREEZE entradas novas até segunda? | **Aguardar ordem CEO** |
| B2 | Alterar thresholds? | **PROIBIDO** (mandato CEO) |
| B3 | Ação sobre XAGUSD -57.40? | **Aguardar ordem CEO** |

## Checklist Fim de Turno PSA

- [x] Reinício via run_omega_24x7.ps1 feito
- [x] G4 PASS reportado (executed_gt0=24 post-reinício)
- [x] ≥4 OPS_SNAPSHOT no dia (meta ≥4)
- [x] SYMBOLS_OPEN + REALIZED_PNL em cada snapshot
- [x] PnL REALIZED_HOJE/7D/CUMUL do trade_feedback.jsonl incluído
- [x] TOP3 perdas de hoje listadas
- [x] Nenhum commit fora de hotfix/forensic
- [x] USFE: NÃO iniciado (AIC domingo/timebox)
- [x] Sem alertas (freeze=0, model_dump=0, pos≤12, runner alive)
- [x] PROIBIDO alterar thresholds para "recuperar" perdas

---
*OPS_DIARIO gerado por PSA. Mandato: CEO-PSA-OPS-20260530 + CEO-ORDEM-PnL-20260529.*
