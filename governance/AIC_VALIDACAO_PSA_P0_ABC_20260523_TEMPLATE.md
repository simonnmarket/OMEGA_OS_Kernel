# AIC — Validação P0-ABC (template — preencher após smoke CEO)

| Campo | Valor |
|-------|--------|
| **Documento** | AIC-VALID-P0-ABC-20260523 |
| **Data validação** | _PREENCHER_ |
| **Branch** | fix/cicc-remediation-p0-abc-20260522 |
| **Commit validado** | _PREENCHER_ |
| **Relatório PSA** | PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md Sec. 4–7 |

---

## 1. Evidências recebidas

| Evidência | Recebido (SIM/NÃO) | Caminho / nota |
|-----------|-------------------|----------------|
| Log smoke agregado | | audit/smoke/p0_smoke_ceo_*.log |
| Relatório PSA Sec. 4–6 | | |
| Tabela PnL 7.8 | | |
| Reconcile output | | |
| Conta sem posições órfãs | | CEO confirmou USDJPY fechada |

---

## 2. Tabela de gates

| ID | Critério | PASS/FAIL/NA | Nota AIC |
|----|----------|--------------|----------|
| SM-1..7 | | | |
| P2a-1..3 | | | |
| G3 | magic OUT | | |
| G4 | UNKNOWN | | |
| G5 | PnL diff | | |
| REG-1 | magic 234001 + OV2\| | | |
| REG-2 | deals OUT | | |
| UT-1..9 (reprodução) | | pytest local | |

---

## 3. Veredito

| Veredito | ☐ APROVADO ☐ REPROVADO ☐ CONDICIONAL |
|----------|--------------------------------------|
| Motivo | |
| Autoriza Fase 1 Router? | ☐ SIM ☐ NÃO |
| Autoriza merge main? | ☐ SIM ☐ NÃO (CEO final) |

---

## 4. Fixes obrigatórios se REPROVADO

| # | Item | Responsável | Prazo |
|---|------|-------------|-------|
| 1 | | | |

---

*AIC preenche e grava como `AIC_VALIDACAO_PSA_P0_ABC_20260523.md` (sem _TEMPLATE).*
