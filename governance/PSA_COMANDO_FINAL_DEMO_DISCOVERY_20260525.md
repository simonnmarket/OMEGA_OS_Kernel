# PSA — COMANDO FINAL DEMO DISCOVERY (força máxima de medição)

**Objectivo CEO:** Portfolio completo (16), **todos os componentes activos** (sinais, execução, TP1/2/3, pyramid, lotes, **risk manager**), gerar comportamento real para medir o ecossistema.

**Não é:** desactivar kill-switch, DD, nem magic — risk manager **tem de estar ON** para medir.

---

## Comando final (copiar bloco inteiro)

```powershell
# === OMEGA DEMO DISCOVERY — ARRANQUE FINAL PSA ===
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE

git fetch origin
git checkout feat/execution-router-atr-20260523
git pull origin feat/execution-router-atr-20260523

# Gate rápido (opcional mas recomendado)
$env:PYTHONPATH = (Get-Location).Path
python -m pytest tests/test_p0_abc_20260522.py tests/test_runner_targets_v1_only.py tests/test_order_magic_propagation.py tests/test_router_atr_20260523.py -q --tb=no

# Pré-requisitos: MT5 aberto | conta DEMO | Algo Trading ON
# Se reiniciar runner: parar instância anterior (CTRL+C) antes de arrancar

& .\scripts\run_omega_24x7.ps1
```

**Comando único de arranque (se repo já sincronizado e pytest OK):**

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE; & .\scripts\run_omega_24x7.ps1
```

---

## O que este comando activa automaticamente

| Componente | Como |
|------------|------|
| Portfolio 16 símbolos | `OMEGA_ASSET_PROFILE=ceo_discovery_full` + `omega_asset_schedule.json` |
| Schedule por ciclo (T-W2) | `omega_paper_loop_24x7.py` |
| Sinais + fallback momentum | `OMEGA_DISABLE_MOMENTUM_FALLBACK=0` |
| Risk manager (KS, DD, circuit breaker) | `shadow_loop.py` — **não desactivar** |
| Pyramid (escalonamento) | `OMEGA_PYRAMID_LAYERS=2`, `LOT_SCALE=1.5` |
| TP1/TP2/TP3 parciais | `_PARTIAL_CLOSE_LEVELS_PSA` + `partial_taken` |
| Lotes + escala TP USD | `OMEGA_SCALE_LOT_TO_MIN_TP_USD=1` |
| Magic / tag | `234001` / `OV2\|` |
| Rastreio decisões | `OMEGA_DECISION_TRACE=1` |

---

## Monitorização (medir comportamento)

```powershell
# Log runner (SCHEDULE + ciclos + shadow)
Get-Content C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\paper\omega_24x7_runner.log -Tail 40 -Wait

# Posições OMEGA agora
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
python scripts/check_positions_now.py

# Decisões por componente (gates, skips)
Get-Content C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\audit\paper\decision_trace.jsonl -Tail 20
```

---

## PSA — NÃO fazer

- Não definir `OMEGA_24X7_ATIVOS` manualmente
- Não `OMEGA_USE_V2=1`
- Não desactivar risk (`OMEGA_DD_*`, kill-switch)
- Não segunda instância 24×7 em paralelo
- Não editar ficheiros do handover sem mandato CEO

---

## Resposta PSA ao CEO (após arranque)

1. `git log -1 --oneline`
2. Runner activo? (sim/não)
3. Última linha `[SCHEDULE]` com 16 ativos
4. Nº posições OMEGA abertas + símbolos
5. Qualquer `Invalid comment` no log? (sim/não)

---

*PSA_COMANDO_FINAL_DEMO_DISCOVERY_20260525.md*
