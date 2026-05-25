# Inventário Consolidado ABC — P0 (master 2026-05-23)

| Campo | Valor |
|-------|--------|
| **Substitui** | `OMEGA_INVENTARIO_CONSOLIDADO_ABC_20260522.md` (obsoleto — DOC-1) |
| **Branch** | fix/cicc-remediation-p0-abc-20260522 |
| **HEAD referência** | ed6452e (511e230 comment fix incluído) |

Legenda **Resolvido:** SIM = código + UT; smoke CEO pode estar pendente.

| ID | Descrição | Tarefa | Resolvido | Commit / UT |
|----|-----------|--------|-----------|-------------|
| A-01 | 1POS state file | T-D1 | SIM | UT-1 |
| A-02 | Request executed + ticket | T-D1 | SIM | UT-1 |
| A-03 | mt5_position_tag fallback | T-D1 | SIM | UT-1 |
| A-04 | MAX_POS per asset | T-D1 | SIM | smoke SM-2 |
| A-05 | Anti duplicate direction | T-D1 | SIM | smoke SM-3 |
| B-01 | Breakeven buffer | T-D2 | SIM | UT-3 |
| B-02 | BE ≠ entry | T-D2 | SIM | SM-5 |
| B-03 | Ghost fill=0 | T-D3 | SIM | UT-2, SM-4 |
| B-04 | Ghost ticket validation | T-D3 | SIM | UT-2 |
| B-05 | XAUUSD sl_pts_min 1500 | T-P1a | SIM | UT-5 (piso; Falha A → Fase 1) |
| B-09 | G5 total_realized_pnl | T-D4 | SIM | UT-4 |
| B-10 | Magic deals OUT | REG | SIM | smoke REG-2 |
| B-11 | PositionManager wired | T-D4b | SIM | UT-8, 4a80b0c |
| X-02 | Anti-hedge | T-P1c | SIM | SM-7 |
| X-03 | Guardrail cache 60s | T-P1b | SIM | UT-7 |
| W-01 | PS1 sem lista fixa 32 | T-W1 | SIM | 94bbc64 |
| W-03 | is_market_open fechos | T-W3 | SIM | 94bbc64 |
| W-COM | MT5 comment ≤31 | comment fix | SIM | UT-9, 511e230 |
| D-05 | Partial TP 50% engine | T-D5 | SIM | UT-6 |
| D-05b | partial_taken ledger flag | T-F1a | NÃO | Fase 1 (CEO Opção A) |
| F-A | ATR M1 vs signal H4 | T-R1 | NÃO | Fase 1 Router |
| F-B | Cascata MTF | T-R2 | NÃO | Fase 2 |
| F-C | M1-GATE delay | T-R2 | NÃO | Fase 2 |
| F-D | v2 hard-coded SL | T-R3 | NÃO | Fase 3 |
| W-02 | Schedule por ciclo | T-W2 | NÃO | Opcional CEO |

---

*PSA: actualizar coluna smoke após CEO preencher relatório. AIC valida em AIC_VALIDACAO_PSA_P0_ABC_20260523.md.*
