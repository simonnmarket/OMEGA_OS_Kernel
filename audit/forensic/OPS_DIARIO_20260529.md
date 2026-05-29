# OPS DIÁRIO — 2026-05-29 (Sexta-feira)

## Snapshots do Dia

| Hora UTC | Path | Equity | Pos | PnL Float | Freeze | G4 |
|----------|------|--------|-----|-----------|--------|----|
| 09:54 | OPS_SNAPSHOT_20260529_0954.txt | 11038.80 | 8 | 15.68 | 0 | CHECK |
| 10:08 | OPS_SNAPSHOT_20260529_1000.txt | 11035.13 | 8 | 13.49 | 0 | PASS CONDICIONAL |

## Riscos (3 bullets)

1. **Threshold hit_rate=65% persiste em skip_table histórico** — zero sinais pós-reinício impede validação plena de G4.
2. **FRIDAY_ROLLOVER weight=0.92** — reduz confluência mínima, poucos sinais gerados.
3. **8 posições abertas em trailing** — requer monitorização contínua de SL/TP.

## Estado Runner

- MT5: terminal64.exe PID 25220 (ativo)
- Python: ciclo contínuo, shadow_rc=0
- DECISION_TRACE: =1 (mantido)
- Cache .pyc: limpo após reinício

## Checklist Fim de Turno PSA

- [x] Reinício via run_omega_24x7.ps1 feito
- [x] G4 PASS CONDICIONAL reportado
- [x] ≥2 OPS_SNAPSHOT no dia (meta ≥4)
- [ ] paper_summary incluído em cada snapshot
- [x] Nenhum commit fora de hotfix/forensic
- [x] USFE: NÃO iniciado (AIC domingo/timebox)

---
*OPS_DIARIO gerado por PSA. Mandato: CEO-PSA-OPS-20260530.*
