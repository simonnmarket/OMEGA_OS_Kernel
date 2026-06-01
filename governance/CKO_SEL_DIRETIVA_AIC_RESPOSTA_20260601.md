# Resposta AIC — Diretiva CKO SEL (2026-06-01)

**Status implementação (lab):** P0 + Grupo A draft + integração USFE + hooks shadow_loop  
**RUPTURE_CAPTURE:** `OMEGA_RUPTURE_CAPTURE=0` (SEL-1 logs) — activar dia 13+ com ordem CEO

## P0 — Feito

| Item | Ficheiro |
|------|----------|
| Fim default shadow | `scripts/omega_paper_loop_24x7.py` — `SystemExit` se `OMEGA_24X7_MODE` ausente |
| SEL gate paralelo (peso 0) | `core_engines/shadow_loop.py` — USFE removido da soma 0.05 |
| Slot overwrite RP>0.8 | `shadow_loop._try_sel_slot_overwrite` |
| RUPTURE_CAPTURE bypass | `OMEGA_RUPTURE_CAPTURE=1` — ignora pacing dir/class |
| `sel_core.py` Grupo A | `modules/sel_core.py` |
| L4/L5 offline only | `scripts/sel_research_offline.py` |
| USFE+SEL fusion | `modules/omega_usfe_engine.py` |

## Arranque obrigatório

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_24X7_MODE = "paper"
.\scripts\run_omega_24x7.ps1
```

**Não** executar `python scripts/omega_paper_loop_24x7.py` sem `$env:OMEGA_24X7_MODE`.

## Logs esperados

- `[SEL] RP=... ready=... leak=... impact_tp=... veto=...`
- `[RUPTURE_WATCH]` quando RP>0.75 e capture OFF
- `[SEL_SLOT_OVERWRITE]` quando RP>0.8 e MAX_POSITIONS cheio

## Próximo (PSA / dia 9–12)

- Correr 72h paper com `[SEL]` + correlacionar movimentos >1000 pts
- Relatório SEL-1 com hit rate RP>0.75 vs deslocamento real MT5
