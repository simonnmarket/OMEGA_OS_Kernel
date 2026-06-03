# CEO MANDATO — Batimento Cardíaco Pyramid (2026-06-04)

**ID:** `CEO-MANDATO-BATIMENTO-20260604`  
**Autoridade:** CEO + CKO  
**Etapa:** 2A cirúrgica (24h, não 72h passivas)

---

## Decisões fechadas

| # | Decisão |
|---|---------|
| 1 | **U3:** Floor económico mantido — log `[IMPACT_TP] ... FLOOR APPLIED` |
| 2 | **P2 vs CQO:** Bypass metal prevalece — `profit_pts >= trigger` executa pyramid independente de `trend_score` |
| 3 | **Batimento:** `PYRAMID_EVAL add=True` → obrigatório `[PYRAMID_DISPATCH]` → `[MT5_ORDERSEND]` |
| 4 | **Relatório 08:00:** linha binária batimento — sem PnL USD |

---

## Implementação (código)

| Ficheiro | Alteração |
|----------|-----------|
| `async_position_orchestrator.py` | `PYRAMID_ADD` signal + `[PYRAMID_DISPATCH]` no FastLoop |
| `shadow_loop.py` | `dispatch_pyramid_broker()` + drain `PYRAMID_ADD` + `FLOOR APPLIED` |
| `psa_capture_session_report.ps1` | Secção BATIMENTO CARDIACO |

---

## Critério 08:00 UTC

```
✅ BATIMENTO DETETADO: [PYRAMID_DISPATCH] -> [MT5_ORDERSEND]
❌ SILENCIO CARDIACO: N EVALs, 0 Dispatch
```

---

*PSA: reiniciar runner após deploy. Git push obrigatório.*
