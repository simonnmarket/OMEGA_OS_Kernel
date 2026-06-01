# PSA — Relatório integração ecossistema

| Campo | Valor |
|-------|--------|
| **Estado** | **CONCLUÍDO — INTEGRAÇÃO PASS** |
| **Data/hora** | 2026-05-25 ~23:38 UTC local |
| **HEAD** | `f51b087` (gate script fix `d7fddc1`) |
| **Branch** | `feat/execution-router-atr-20260523` |
| **Comando** | `PSA_COMANDO_DEFINITIVO_ECOSISTEMA_20260525.md` |
| **Incidente** | `AIC_INCIDENTE_AUDITORIA_SCOPE_GAP_20260525.md` → **FECHADO** |

---

## Nota técnica (gate script)

Correcções PSA em `d7fddc1` em `omega_integration_gate.ps1`:

| Bug | Fix |
|-----|-----|
| Em-dash UTF-8 parse PS 5.1 | UTF-8 BOM + `--` |
| `script:failures` sem `$` | `$script:failures` |
| Needle A5 aspas | `'"ceo_discovery_full"'` |

---

## Gates

| Gate | Resultado | Evidência |
|------|-----------|-----------|
| pytest 34/34 | **PASS** | 34 passed in 4.99s |
| `omega_integration_gate.ps1` preflight | **PASS** | `INTEGRATION_GATE_preflight_20260525_233146.txt` |
| `omega_demo_go_live.ps1` | **PASS** | `GO_LIVE_REPORT_20260525_204139.txt` |
| `omega_integration_gate.ps1` runtime | **PASS** | `INTEGRATION_GATE_runtime_20260525_233824.txt` |
| `omega_integration_gate.ps1` kpi | **PASS** | `INTEGRATION_GATE_kpi_20260525_233848.txt` |

---

## Git / runner

| Campo | Valor |
|-------|--------|
| HEAD | `f51b087` |
| Runner reiniciado | **Sim** (~23:32) |
| `omega_ecosystem_unified.py` | **Sim** |
| Log unified | `[ECOSYSTEM_UNIFIED] manifesto=...` @ 23:33:30 |
| Ciclos | ciclo 1–2 OK, 16 ativos `[SCHEDULE]` |

---

## Manifesto (`audit/paper/ecosystem_unified_manifest.json`)

| Campo | Valor |
|-------|--------|
| unified | **true** |
| portfolio count | **16** |
| max_positions | **8** |
| decision_env | ECOSYSTEM_UNIFIED=1, FUSION=1, PSA_SHADOW=0, FUSION_MIN=0.55 |

---

## KPI (~últimas 3000 linhas)

| Métrica | Valor |
|---------|-------|
| PSA_FEED | 232 |
| AGENT_IA / Sinal aprovado | **46** |
| MOMENTUM_MT5 | 60 |
| EDGE_GATE | 106 |
| HOLD/rejeitado | 231 |
| Invalid comment | **0** |

**Interpretação AIC:** IA passou a ser via activa de decisão (46 linhas `AGENT_IA` / aprovado); momentum permanece como **fallback** (60), não como único motor — mudança material vs sessão pré-unified (0 AGENT_IA).

---

## Posições MT5

- **Abertas:** ETHUSD + XRPUSD (trailing activo)  
- **Magic:** 234001  

---

## Veredito

- [x] **INTEGRAÇÃO PASS** — incidente **INC-AUDIT-20260525-001 FECHADO**  
- [ ] INTEGRAÇÃO FAIL  

---

## Pendências (não bloqueiam integração)

| ID | Item | Quem |
|----|------|------|
| OP-1 | Merge PR #1 P0 | CEO |
| OP-2 | Merge PR #2 Router | CEO |
| OP-3 | TRE | Novo mandato CEO |
| OP-4 | Fase 2 Router | Novo mandato |

---

## Anexos

- [x] `audit/paper/ecosystem_unified_manifest.json`  
- [x] `audit/paper/omega_24x7_runner.log` (linhas 2026-05-25 23:33+)  
- [x] `audit/integration_gate/KPI_20260525_233848.json`  

---

*PSA + validação AIC local — 2026-05-25*
