# PSA — Relatório Comando Final DEMO Discovery

| Campo | Valor |
|-------|--------|
| **Data/hora** | 2026-05-25 ~21:54 UTC+2 |
| **Branch** | `feat/execution-router-atr-20260523` |
| **HEAD** | `5748758` |
| **Veredito AIC/CEO** | **APROVADO — operação DEMO discovery em curso** |

---

## 1. git log -1

```
5748758 docs: registo validacao PSA handover v2 + fix aviso go_live script
```

HEAD > mínimo `161be96`. Fix L110 `omega_demo_go_live.ps1` confirmado.

---

## 2. pytest

**34/34** — 5.33s — exit 0 ✅

---

## 3. Reinício runner

- PID anterior `21980` terminado (CEO autorizou)
- `omega_runner.lock` removido
- Singleton limpo ✅

---

## 4. Arranque `run_omega_24x7.ps1`

- 16 símbolos `ceo_discovery_full`
- Capital MT5: **$10,134.02**
- Sessão: OVERLAP
- ENV: `OMEGA_USE_V2=0`, `magic=234001`, sem `OMEGA_24X7_ATIVOS` ✅

---

## 5. Marcadores de saúde

| Marcador | Estado |
|----------|--------|
| `[SCHEDULE]` 16 ativos | ✅ |
| `legacy_magic=234001` | ✅ |
| `ciclo 1 OK` shadow_rc=0 export_rc=0 | ✅ |
| Invalid comment | 0 ✅ |
| `OMEGA_USE_V2=0` | ✅ |

---

## 6. Posições OMEGA (via log runner)

| Ticket | Símbolo | Lado | Lot | Estado |
|--------|---------|------|-----|--------|
| #190160589 | ETHUSD | BUY | 0.10 | trailing activo |
| #190160678 | XRPUSD | BUY | 0.10 | trailing activo |

**Total:** 2 posições, magic `234001`, float ~ -$0.43 (melhorando).

**Nota:** `check_positions_now.py` standalone falha com MT5 exclusivo do runner — esperado; usar log `[LEDGER]` ou consultar após parar runner.

---

## 7. Handover

Ficheiros protegidos **não alterados** nesta sessão PSA ✅

---

## Pendência CEO

| Item | Responsável |
|------|-------------|
| Merge PR #1, PR #2 | CEO |

---

## Mensagem CEO → PSA (registo)

> Relatório Comando Final DEMO Discovery **APROVADO**.  
> Operação 24×7 discovery confirmada. Manter runner; monitorizar P&L e `decision_trace.jsonl`.  
> Não alterar código até merge PRs ou novo mandato.

---

*Registo AIC — 2026-05-25*
