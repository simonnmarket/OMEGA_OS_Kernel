# RELATÓRIO FORCE NOW — 4H (CEO 20260601)

**Gerado:** 2026-05-31T22:25:08.404488+00:00 UTC
**Script:** `scripts/psa_force_now_4h_report.py`
**Log:** `audit/paper/omega_24x7_runner.log`

---

## CHECKLIST F0–F7 (4H)

| F | Item | Estado |
|---|------|--------|
| F0 | Posições legadas tratadas | PENDENTE (market closed) |
| F1 | Pip cache + ECON_OPEN + pisos | PASS (21 símbolos, pisos 25/10/18/15/8) |
| F2 | Runner reiniciado | PASS |
| F3 | Zero MAX_POS_PER_ASSET=1 pós-restart | FAIL |
| F4 | [ECON_OPEN] com TP ≥ piso | PASS (18 encontrados) |
| F5 | Zero índice TP < 25 | PASS (gate protege) |
| F6 | MT5 screenshots | CEO capturar manualmente (impedimento headless documentado) |
| F7 | USFE 1.1.2 | PASS (3217 linhas [USFE]) |

---

## ESTATÍSTICAS DO LOG

| Métrica | Valor |
|---------|-------|
| Total linhas | 27821 |
| [USFE] | 3217 |
| [ECON_GATE] | 19 |
| [ECON_OPEN] | 18 |
| [STALE_EXIT] | 0 |
| MAX_POS_PER_ASSET=1 | 33 |
| UnboundLocalError | 1 |
| ImportError | 0 |

---

## POSIÇÕES MT5 ATUAIS

| Ticket | Símbolo | Volume | Profit | Swap |
|--------|---------|--------|--------|------|
| 191908751 | UKOIL+ | 0.06 | 6.36 | -3.69 |
| 192068976 | USDCAD | 0.01 | -0.54 | -0.08 |
| 192243746 | AUDUSD | 0.17 | -2.72 | 0.00 |
| 192243914 | USDJPY | 0.01 | 0.25 | 0.00 |
| 192244227 | USDJPY | 0.01 | 0.26 | 0.00 |
| 192253446 | SOLUSD | 0.10 | -0.00 | 0.00 |


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

## F6 — Snapshot Textual MT5 (impedimento GUI)

**Ambiente:** Terminal/bash headless (sem GUI)
**MT5 GUI:** Disponível no Windows desktop do CEO
**Ação:** CEO captura 3 screenshots manualmente quando voltar:
1. Tab Trade — lista posições após 4h
2. Ordem índice com TP >= $25 em USD
3. History — últimos 10 deals com profit column

**Estado:** NÃO BLOQUEIA PASS se F4/F5 + snapshot textual OK

Snapshot gerado em: `audit/forensic/FORCE_NOW_20260601/mt5_snapshot_4h.txt`

---

## DECLARAÇÃO

**Não declaro "100% operacional".** O sistema opera com economia de fundo (pisos 25/10/18/15/8, gate NET_EDGE, USFE v1.1.2, stale exit). Resultados de PnL dependem de tempo de mercado e sinais direcionais.

---

*Relatório gerado automaticamente por PSA.*
