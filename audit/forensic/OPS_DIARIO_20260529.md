# OPS DIÁRIO — 2026-05-29 (Sexta-feira)

## Snapshots do Dia

| Hora UTC | Path | Equity | Pos | PnL Float | Realized | Freeze | G4 | SYMBOLS_OPEN |
|----------|------|--------|-----|-----------|----------|--------|----|-------------|
| 09:54 | OPS_SNAPSHOT_20260529_0954.txt | 11038.80 | 8 | 15.68 | 0.0 | 0 | CHECK | — |
| 10:08 | OPS_SNAPSHOT_20260529_1000.txt | 11035.13 | 8 | 13.49 | 0.0 | 0 | PASS CONDICIONAL | — |
| 16:54 | OPS_SNAPSHOT_20260529_1654.txt | 11035.13 | 8 | 14.14 | 0.0 | 0 | PASS | AUDUSD, BNBUSD, ETHUSD, GER40, UKOIL+, US100, US500, USDCAD |

## Riscos (3 bullets)

1. **8 posições abertas em trailing** — requer monitorização contínua de SL/TP (especialmente GER40/UKOIL+ novos).
2. **FRIDAY_ROLLOVER weight=0.92** — sessão fraca, poucos sinais novos; validação forte segunda (Londres).
3. **REALIZED_PNL = 0.0** — nenhum fecho realizador no dia; todas as posições ainda flutuantes.

## Estado Runner

- MT5: terminal64.exe PID 25220 (ativo)
- Python: ciclo contínuo, shadow_rc=0
- DECISION_TRACE: =1 (mantido)
- Cache .pyc: limpo após reinício
- Último reinício: 12:03 UTC

## Checklist Fim de Turno PSA

- [x] Reinício via run_omega_24x7.ps1 feito
- [x] G4 PASS reportado (executed_gt0=24 post-reinício)
- [x] ≥3 OPS_SNAPSHOT no dia (meta ≥4)
- [x] SYMBOLS_OPEN + REALIZED_PNL em cada snapshot
- [x] Nenhum commit fora de hotfix/forensic
- [x] USFE: NÃO iniciado (AIC domingo/timebox)
- [x] Sem alertas (freeze=0, model_dump=0, pos≤12, runner alive)

---
*OPS_DIARIO gerado por PSA. Mandato: CEO-PSA-OPS-20260530.*
