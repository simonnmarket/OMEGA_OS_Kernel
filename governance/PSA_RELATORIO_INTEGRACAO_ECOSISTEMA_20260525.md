# PSA — Relatório integração ecossistema (preencher após execução)

| Campo | Valor |
|-------|--------|
| **Estado** | **PENDENTE — PSA preencher** |
| **Comando** | `PSA_COMANDO_DEFINITIVO_ECOSISTEMA_20260525.md` |
| **Incidente** | `AIC_INCIDENTE_AUDITORIA_SCOPE_GAP_20260525.md` |

---

## Gates

| Gate | Resultado | Evidência |
|------|-----------|-----------|
| pytest 34/34 | | |
| `omega_integration_gate.ps1` preflight | | `audit/integration_gate/` |
| `omega_demo_go_live.ps1` | | `audit/demo_go_live/` |
| `omega_integration_gate.ps1` runtime | | |
| `omega_integration_gate.ps1` kpi 1h | | |

---

## Git / runner

| Campo | Valor |
|-------|--------|
| HEAD (`git log -1 --oneline`) | |
| Runner reiniciado (Sim/Não) | |
| Hora reinício | |
| `omega_ecosystem_unified.py` presente | |

---

## Manifesto (`audit/paper/ecosystem_unified_manifest.json`)

| Campo | Valor |
|-------|--------|
| unified | |
| portfolio count | |
| max_positions | |

---

## KPI ~1h

| Métrica | Valor |
|---------|-------|
| PSA_FEED (linhas) | |
| AGENT_IA / Sinal aprovado | |
| MOMENTUM_MT5 | |
| EDGE_GATE | |
| Invalid comment | **0 obrigatório** |

---

## Posições MT5

- Abertas:  
- Magic 234001:  

---

## Veredito (marcar um)

- [ ] **INTEGRAÇÃO PASS** — incidente INC-AUDIT-20260525-001 pode fechar  
- [ ] **INTEGRAÇÃO FAIL** — motivo:  

---

## Anexos

- [ ] `ecosystem_unified_manifest.json`  
- [ ] Trecho `omega_24x7_runner.log` com `[ECOSYSTEM_UNIFIED]`  
- [ ] Relatório gate em `audit/integration_gate/`  

---

*Template — PSA preencher e notificar CEO.*
