# RELATÓRIO FORCE NOW — 4H (CEO 20260601)

**Gerado:** 2026-05-31T22:20:55.948530+00:00 UTC
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
| F7 | USFE 1.1.2 | PASS (3161 linhas [USFE]) |

---

## ESTATÍSTICAS DO LOG

| Métrica | Valor |
|---------|-------|
| Total linhas | 26185 |
| [USFE] | 3161 |
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
| 192068976 | USDCAD | 0.01 | -0.49 | -0.08 |
| 192243746 | AUDUSD | 0.17 | -3.74 | 0.00 |
| 192243914 | USDJPY | 0.01 | 0.24 | 0.00 |
| 192244227 | USDJPY | 0.01 | 0.24 | 0.00 |


---

## F0 — Posições Legadas Fechadas

```json
{
  "closed_by_psa": [
    {
      "ticket": 192074499,
      "symbol": "US500",
      "retcode": 10009,
      "comment": "Request executed",
      "timestamp": "2026-06-01T00:22Z",
      "method": "position_param_V3"
    },
    {
      "ticket": 192105887,
      "symbol": "GER40",
      "retcode": 10009,
      "comment": "Request executed",
      "timestamp": "2026-06-01T00:22Z",
      "method": "position_param_V3"
    },
    {
      "ticket": 192250049,
      "symbol": "US500",
      "retcode": 10009,
      "comment": "Request executed",
      "timestamp": "2026-06-01T00:22Z",
      "method": "position_param_V3",
      "note": "ghost_position_from_V2_close"
    },
    {
      "ticket": 192250050,
      "symbol": "GER40",
      "retcode": 10009,
      "comment": "Request executed",
      "timestamp": "2026-06-01T00:22Z",
      "method": "position_param_V3",
      "note": "ghost_position_from_V2_close"
    }
  ],
  "pending_close": [
    {
      "ticket": 191908751,
      "symbol": "UKOIL+",
      "reason": "market_closed_retcode_10018",
      "retry": " quando mercado abrir"
    }
  ],
  "remaining_legacy": [
    {
      "ticket": 192068976,
      "symbol": "USDCAD",
      "note": "FASE2 CEO decide"
    },
    {
      "ticket": 192243746,
      "symbol": "AUDUSD",
      "note": "FASE2 CEO decide"
    },
    {
      "ticket": 192243914,
      "symbol": "USDJPY",
      "note": "FASE2 CEO decide"
    },
    {
      "ticket": 192244227,
      "symbol": "USDJPY",
      "note": "FASE2 CEO decide"
    }
  ]
}
```

**UKOIL+ fechamento:** UKOIL_CLOSE retcode=10018 comment=Market closed


---

## DECLARAÇÃO

**Não declaro "100% operacional".** O sistema opera com economia de fundo (pisos 25/10/18/15/8, gate NET_EDGE, USFE v1.1.2, stale exit). Resultados de PnL dependem de tempo de mercado e sinais direcionais.

---

*Relatório gerado automaticamente por PSA.*
