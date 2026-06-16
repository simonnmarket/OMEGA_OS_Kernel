# Gate de integração ecossistema — OBRIGATÓRIO (pós-P0, pré-“DEMO OK”)

| Campo | Valor |
|-------|--------|
| **Versão** | 1.0 |
| **Data** | 2026-05-25 |
| **Substitui** | “Runner OK” como único critério de go-live |
| **Script** | `scripts/omega_integration_gate.ps1` |
| **Relacionado** | `AIC_INCIDENTE_AUDITORIA_SCOPE_GAP_20260525.md` |

---

## 1. Regra de ouro

> **Sprint P0 FECHADO** ≠ **Ecossistema integrado FECHADO**

Nenhum relatório PSA ou AIC pode usar **“DEMO operacional / integrado”** sem este gate **PASS** (ou FAIL documentado com bloqueio explícito).

---

## 2. Pré-requisitos

| # | Item |
|---|------|
| P1 | MT5 aberto, DEMO, Algo Trading ON |
| P2 | `cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE` |
| P3 | Branch `feat/execution-router-atr-20260523` |
| P4 | Ficheiro existe: `modules/omega_ecosystem_unified.py` |
| P5 | pytest 34/34 (mesmo conjunto do go-live) |

---

## 3. Gate A — Código e env (antes de reiniciar runner)

| ID | Verificação | Comando / critério | PASS |
|----|-------------|-------------------|------|
| A1 | Módulo unified | `Test-Path modules\omega_ecosystem_unified.py` | Existe |
| A2 | Runner define unified | `Select-String OMEGA_ECOSYSTEM_UNIFIED scripts\run_omega_24x7.ps1` | Valor `1` |
| A3 | Fusão live | `OMEGA_USE_SIGNAL_FUSION=1` no runner | Sim |
| A4 | Shadow OFF | `PSA_SHADOW_MODE=0` no runner | Sim |
| A5 | Portfolio profile | `OMEGA_ASSET_PROFILE=ceo_discovery_full` | Sim |
| A6 | pytest | `python -m pytest tests/...` (4 ficheiros go-live) | 34 passed |

**Script:** `& .\scripts\omega_integration_gate.ps1 -Phase preflight`

---

## 4. Gate B — Runtime (após ≥3 ciclos do runner reiniciado)

| ID | Verificação | Critério PASS |
|----|-------------|---------------|
| B1 | Manifesto escrito | `audit/paper/ecosystem_unified_manifest.json` existe |
| B2 | Unified flag | JSON `"unified": true` |
| B3 | Portfolio | JSON `portfolio` length = **16** |
| B4 | Max positions | JSON `max_positions` = **8** (ou valor `OMEGA_MAX_POSITIONS`) |
| B5 | Log manifesto | `omega_24x7_runner.log` contém `[ECOSYSTEM_UNIFIED] manifesto=` |
| B6 | Schedule | Log contém `[SCHEDULE]` com 16 símbolos |
| B7 | Sem regressão P0 | 0× `Invalid comment` nas últimas 500 linhas do log |
| B8 | Magic | Ordens OMEGA com magic `234001` (amostra reconcile) |

**Script:** `& .\scripts\omega_integration_gate.ps1 -Phase runtime`

---

## 5. Gate C — KPI decisão (amostra 1h — não bloqueia arranque, bloqueia “integrado OK”)

Após **60 minutos** de runner com unified:

| ID | Métrica | Como medir | Nota |
|----|---------|------------|------|
| C1 | Linhas `PSA_FEED` com BUY/SELL | `Select-String PSA_FEED` no log 1h | Baseline |
| C2 | Linhas `[IA] Sinal aprovado` | grep log | **Desejável > 0** se mercado activo |
| C3 | `DECISION=AGENT_IA` ou `source=AGENT_IA` | grep log | Prova bússola IA |
| C4 | `MOMENTUM_MT5` execuções | grep `FASE4 EXEC` | Documentar %; fallback esperado se HOLD |
| C5 | HOLD com motivo | `[IA] Sinal rejeitado` com `reason=` | Prova patch log |
| C6 | Bloqueios risk | EDGE_GATE, CORR, ECON | **Esperado** — não é bug |

**Interpretação honesta:**

- C2/C3 = 0 na 1ª hora **pode** ser mercado/gates — **não** é FAIL automático.  
- C2/C3 = 0 **e** C4 = 100% das execuções **após** unified **sem** nenhum `fusion=` no log → **FAIL integração** (investigar env).

**Script:** `& .\scripts\omega_integration_gate.ps1 -Phase kpi -LogHours 1`

---

## 6. Vereditos permitidos

| Veredito | Significado |
|----------|-------------|
| **INTEGRAÇÃO PASS** | A+B PASS; C documentado |
| **INTEGRAÇÃO CONDICIONAL** | A+B PASS; C pendente (<1h) |
| **INTEGRAÇÃO FAIL** | Qualquer A ou B FAIL — **não** dizer “resolvido” ao CEO |
| **P0 PASS** | pytest/smoke — independente deste gate |

---

## 7. Proibições (checklist negativa)

- [ ] Não remover `OMEGA_ECOSYSTEM_UNIFIED`
- [ ] Não repor `priority_assets` com 7 símbolos no calibrador
- [ ] Não definir `PSA_SHADOW_MODE=1` em discovery CEO
- [ ] Não usar só `PSA_HANDOVER` antigo com HEAD `161be96` sem unified
- [ ] Não fechar incidente INC-AUDIT-20260525-001 sem relatório PSA §7 da acta

---

## 8. Integração com scripts existentes

| Script | Papel |
|--------|-------|
| `omega_demo_go_live.ps1` | P0 + smoke **unitário** (mantém) |
| `omega_integration_gate.ps1` | **Novo** — integração ecossistema |
| `run_omega_24x7.ps1` | Arranque com envs unified |

**Ordem recomendada:**

1. `omega_demo_go_live.ps1`  
2. Parar runner antigo  
3. `run_omega_24x7.ps1`  
4. Aguardar ≥3 ciclos (~12–15 min)  
5. `omega_integration_gate.ps1 -Phase runtime`  
6. Após 1h: `omega_integration_gate.ps1 -Phase kpi`

---

*Gate v1.0 — AIC — obrigatório em todos os go-lives DEMO discovery.*
