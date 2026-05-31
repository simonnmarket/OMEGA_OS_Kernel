# RELATÓRIO FORCE NOW — 4H (CEO 20260601)

**Gerado:** 2026-05-31T22:20:08.487763+00:00 UTC
**Script:** `scripts/psa_force_now_4h_report.py`
**Log:** `audit/paper/omega_24x7_runner.log`

---

## CHECKLIST F0–F7 (4H)

| F | Item | Estado |
|---|------|--------|
| F0 | Posições legadas tratadas | UKOIL+ PENDENTE |
| F1 | Pip cache + ECON_OPEN + pisos | PASS (21 símbolos, pisos 25/10/18/15/8) |
| F2 | Runner reiniciado | PASS |
| F3 | Zero MAX_POS_PER_ASSET=1 pós-restart | FAIL |
| F4 | [ECON_OPEN] com TP ≥ piso | AGUARDAR (0 encontrados) |
| F5 | Zero índice TP < 25 | PASS (gate protege) |
| F6 | MT5 screenshots | CEO capturar manualmente |
| F7 | USFE 1.1.2 | PASS (3047 linhas [USFE]) |

---

## ESTATÍSTICAS DO LOG

| Métrica | Valor |
|---------|-------|
| Total linhas | 25454 |
| [USFE] | 3047 |
| [ECON_GATE] | 19 |
| [ECON_OPEN] | 0 |
| [STALE_EXIT] | 0 |
| MAX_POS_PER_ASSET=1 | 33 |
| UnboundLocalError | 1 |
| ImportError | 0 |

---

## POSIÇÕES MT5 ATUAIS

| Ticket | Símbolo | Volume | Profit | Swap |
|--------|---------|--------|--------|------|
| 191908751 | UKOIL+ | 0.06 | 6.36 | -3.69 |
| 192068976 | USDCAD | 0.01 | -0.50 | -0.08 |
| 192074499 | US500 | 0.06 | 0.24 | -0.31 |
| 192105887 | GER40 | 0.47 | 41.91 | -1.27 |
| 192243746 | AUDUSD | 0.17 | -3.57 | 0.00 |
| 192243914 | USDJPY | 0.01 | 0.23 | 0.00 |
| 192244227 | USDJPY | 0.01 | 0.24 | 0.00 |
| 192250049 | US500 | 0.06 | -0.28 | 0.00 |
| 192250050 | GER40 | 0.47 | 7.12 | 0.00 |


---

## F0 — Posições Legadas Fechadas

```json
{
  "tickets": [
    192068976,
    192243746,
    192243914,
    192244227,
    192248551,
    191908751
  ],
  "reason": "legado microlot / duplicado USDJPY / UKOIL swap negativo \u00e2\u20ac\u201d FASE2 ap\u00c3\u00b3s relat\u00c3\u00b3rio 4h",
  "approved_by": "CEO pendente \u00e2\u20ac\u201d responder APROVADO ou ajustar lista"
}
```

**UKOIL+ fechamento:** UKOIL_CLOSE retcode=10018 comment=Market closed


---

## DECLARAÇÃO

**Não declaro "100% operacional".** O sistema opera com economia de fundo (pisos 25/10/18/15/8, gate NET_EDGE, USFE v1.1.2, stale exit). Resultados de PnL dependem de tempo de mercado e sinais direcionais.

---

*Relatório gerado automaticamente por PSA.*
