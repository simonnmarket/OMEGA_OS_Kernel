# CHECKLIST DE EXECUÇÃO — 2026-05-23

| Campo | Valor |
|-------|--------|
| **Documento** | CHECKLIST-EXECUCAO-20260523 |
| **Data** | 2026-05-23 |
| **Executor** | PSA (Devin) |
| **Branch** | `fix/cicc-remediation-p0-abc-20260522` |
| **Commits hoje** | 4a80b0c, 94bbc64, 860192e, 5865df9, 511e230, ae2fe03, ed6452e |
| **Mandato fecho** | `PSA_MANDATO_FECHO_P0_E_TRANSICAO_LEVEL_20260523.md` (Fase B em curso) |
| **Status global** | FASE 0 + 0b + Comment fix + Fase B (B1-B6) COMPLETAS | Smoke pendente (ação CEO) |

---

## 0. PRÉ-REQUISITO CEO — Pós-fecho USDJPY

| Item | Estado | Referência |
|------|--------|------------|
| Posição órfã USDJPY #189777509 | **FECHADA** (CEO confirmado) | `PSA_MANDATO_FECHO_P0_E_TRANSICAO_LEVEL_20260523.md` Sec. 0 |
| Conta MT5 limpa para smoke | Assumir SIM — CEO confirmar 0 posições `magic=234001` / `OV2\|` | Pre-check: `python scripts/check_positions_now.py` |
| Alinhamento AIC ↔ PSA | **CONFIRMADO** | `CEO_DECISAO_ROTEIRO_P0_20260523.md` |
| D1 `partial_taken` | **FECHADO** — Fase 1 (não bloqueia P0) | CEO Opção A |
| D2 T-W2 | **FECHADO** — Opcional; T-W3 suficiente | CEO aceite escrito |
| D3 Inventário 22/05 | **FECHADO** — B4 criou inventário 23/05 | `OMEGA_INVENTARIO_CONSOLIDADO_ABC_20260523.md` |
| D4 Commit final | **FECHADO** — HEAD `ed6452e` | Branch `fix/cicc-remediation-p0-abc-20260522` |

**Nota:** Fase E (Level 1 Router/ATR) PROIBIDA até AIC emitir `AIC_VALIDACAO_PSA_P0_ABC_20260523.md` com **APROVADO**.

---

## 1. DOCUMENTOS GERADOS/ATUALIZADOS HOJE

### 1.1 Documentos de Governança (SOURCE_CODE/governance/)

| Documento | Ação | Status |
|-----------|------|--------|
| `PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` | Atualizado (T-D4b + Fase 0b + commit final ed6452e) | ✅ FINAL |
| `AIC_PSA_RECONCILIACAO_ALINHAMENTO_20260523.md` | Criado pelo AIC; D1/D2/D3/D4 → FECHADO (B6) | ✅ FINAL |
| `INVENTARIO_ALINHAMENTO_20260523.md` | Criado pelo AIC | ✅ FINAL |
| `OMEGA_MANDATO_UNIFICADO_P0_ROUTER_WEEKEND_20260523.md` | Fornecido pelo CEO | ✅ FINAL |
| `PSA_MANDATO_FECHO_P0_E_TRANSICAO_LEVEL_20260523.md` | Fornecido pelo AIC | ✅ FINAL |
| `CEO_DECISAO_ROTEIRO_P0_20260523.md` | Fornecido pelo CEO | ✅ FINAL |
| `OMEGA_INVENTARIO_CONSOLIDADO_ABC_20260523.md` | Criado pelo CEO (B4) | ✅ FINAL |
| `AIC_VALIDACAO_PSA_P0_ABC_20260523_TEMPLATE.md` | Criado pelo CEO (B5) | ✅ FINAL |
| `run_p0_smoke_ceo.ps1` | Criado pelo CEO (B2) | ✅ FINAL |
| `CHECKLIST_EXECUCAO_20260523.md` | Este documento — atualizado (B6) | ✅ FINAL |

### 1.2 Documentos de Referência (Desktop/Auditoria)

| Documento | Ação | Status |
|-----------|------|--------|
| `PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` (cópia Desktop) | Sync automático | ✅ ATUALIZADO |
| `OMEGA_MANDATO_UNIFICADO_P0_ROUTER_WEEKEND_20260523.md` (cópia Desktop) | Sync automático | ✅ ATUALIZADO |

---

## 2. CÓDIGO MODIFICADO HOJE

### 2.1 Commits Realizados

| Commit | Hash | Conteúdo | Ficheiros |
|--------|------|----------|------------|
| **T-D4b** | `4a80b0c` | PositionManager wiring | `core_engines/shadow_loop.py`, `tests/test_p0_abc_20260522.py` |
| **Fase 0b** | `94bbc64` | Weekend 24×7 (T-W1, T-W3) | `core_engines/shadow_loop.py`, `scripts/run_omega_24x7.ps1`, `scripts/run_omega_madrugada_pos_p0.ps1` |
| **Relatório** | `860192e` | Atualizar relatório PSA | `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` |
| **Checklist** | `5865df9` | Adicionar CHECKLIST_EXECUCAO_20260523 | `governance/CHECKLIST_EXECUCAO_20260523.md` |
| **Comment fix** | `511e230` | MT5 comment <= 31 chars (CEO 20260523) | `core_engines/shadow_loop.py`, `tests/test_p0_abc_20260522.py` |

### 2.2 Ficheiros de Código Alterados

| Ficheiro | Linhas alteradas | Resumo |
|----------|------------------|--------|
| `core_engines/shadow_loop.py` | +431, -32 | Import PositionManager, instância, registro OPEN/PARTIAL/CLOSE, guards is_market_open |
| `tests/test_p0_abc_20260522.py` | +108, -25 | Adicionar UT-8 (PositionManager wiring) |
| `scripts/run_omega_24x7.ps1` | +1, -2 | Comentar OMEGA_24X7_ATIVOS fixo |
| `scripts/run_omega_madrugada_pos_p0.ps1` | +1, -2 | Comentar OMEGA_24X7_ATIVOS fixo |

---

## 3. TAREFAS IMPLEMENTADAS (FASE 0 + 0b)

### 3.1 Fase 0 — P0-ABC (12/12 PASS)

| ID | Tarefa | Status | Evidência |
|----|--------|--------|-----------|
| T-D1 | 1POS / state + mt5_position_tag fallback | ✅ PASS | UT-1 + shadow_loop.py L1437 + mt5_position_tag.py L144-221 |
| T-D2 | Breakeven buffer (1.5× spread) | ✅ PASS | UT-3 + shadow_loop.py L4362-4383 |
| T-D3 | Ghost orders (fill/ticket validation) | ✅ PASS | UT-2 + shadow_loop.py L1414-1421 + v2 L452-458 |
| T-D4 | Schema G5 (total_realized_pnl) | ✅ PASS | UT-4 + shadow_loop.py L3337 |
| **T-D4b** | **PositionManager wired** | ✅ PASS | **UT-8 + shadow_loop.py L39, L2435, L4162, L3216, L3276, L4370, L4409** |
| T-P1a | XAUUSD SL/TP floor 1500 pts | ✅ PASS | UT-5 + shadow_loop.py L571 |
| T-D5 | Partial TP 50% (ProgressivePartialCloseComplete) | ✅ PASS | UT-6 + engine pré-existente |
| T-P1b | Guardrail cache 60s | ✅ PASS | UT-7 + shadow_loop.py L1673-1696 |
| T-P1c | Anti-hedge qualquer posição MT5 | ✅ PASS | shadow_loop.py L3462-3479 |
| T-P2b | Runner só v1; v2 espelho D3 | ✅ PASS | test_runner_targets_v1_only + PS1 comment + v2 L452 |

### 3.2 Fase 0b — Weekend 24×7 (2/2 PASS)

| ID | Tarefa | Status | Evidência |
|----|--------|--------|-----------|
| T-W1 | Remover lista fixa OMEGA_24X7_ATIVOS dos PS1 | ✅ PASS | run_omega_24x7.ps1 L80 + run_omega_madrugada_pos_p0.ps1 L39 |
| T-W3 | Guard is_market_open em fechos automáticos | ✅ PASS | shadow_loop.py L1541, L1476, L3198, L3268 |
| Comment fix | MT5 comment <= 31 chars (PARTIAL, TS, ZAK) | ✅ PASS | shadow_loop.py L1589, L3226, L3291 + UT-9 |
| Comment fix | MT5 comment <= 31 chars (PARTIAL, TS, ZAK) | ✅ PASS | shadow_loop.py L1589, L3226, L3291 + UT-9 |

### 3.3 T-W2 (Opcional — NÃO implementado)

| ID | Tarefa | Status | Motivo |
|----|--------|--------|--------|
| T-W2 | Re-resolver ativos por ciclo | ⏸️ PENDENTE | Recomendado pelo AIC, não obrigatório no mandato |

---

## 4. TESTES UNITÁRIOS

### 4.1 Testes Executados

| Teste | Resultado | Detalhes |
|-------|-----------|----------|
| UT-1 | ✅ PASS | test_ut1_request_executed_with_ticket_in_state |
| UT-2 | ✅ PASS | test_ut2_fill_zero_not_success |
| UT-3 | ✅ PASS | test_ut3_breakeven_buffer_not_equal_entry |
| UT-4 | ✅ PASS | test_ut4_feedback_total_realized_pnl |
| UT-5 | ✅ PASS | test_ut5_xauUSD_sl_floor_1500 |
| UT-6 | ✅ PASS | test_ut6_partial_tp50_trigger |
| UT-7 | ✅ PASS | test_ut7_guardrail_cache_60s |
| UT-8 | ✅ PASS | test_ut8_position_manager_wiring |
| **UT-9** | ✅ PASS | **test_ut9_comment_length_31_chars (NOVO - CEO 20260523)** |
| runner test | ✅ PASS | test_runner_targets_v1_only |

**Total:** 10/10 PASS (9 P0 + 1 runner)

---

## 5. PENDÊNCIAS (BLOQUEIAM VEREDITO FINAL APROVADO)

### 5.1 Smoke MT5 (Ação CEO)

| ID | Critério | Status | Responsável |
|----|----------|--------|-------------|
| SM-1 | 1 ciclo EURUSD H1 exit 0 | ⏸️ PENDENTE | CEO |
| SM-2 | ≤1 posição EURUSD por direção | ⏸️ PENDENTE | CEO |
| SM-3 | 2º ciclo SKIP (1pos/MAX_POS/already) | ⏸️ PENDENTE | CEO |
| SM-4 | 0 PaperReport EXEC com fill=0 | ⏸️ PENDENTE | CEO |
| SM-5 | BE: SL ≠ entry (se aplicável) | ⏸️ PENDENTE | CEO |
| SM-6 | XAUUSD H1: SL ≥ floor | ⏸️ PENDENTE | CEO |
| SM-7 | anti_hedge bloqueia hedge | ⏸️ PENDENTE | CEO |

### 5.2 Smoke Portfolio (Ação CEO)

| ID | Critério | Status | Responsável |
|----|----------|--------|-------------|
| P2a-1 | EURUSD+GBPJPY+XAUUSD 1 ciclo H1 exit 0 | ⏸️ PENDENTE | CEO |
| P2a-2 | 0 hedges (BUY+SELL mesmo símbolo) | ⏸️ PENDENTE | CEO |
| P2a-3 | ≤1 pos/(ativo,direcção) | ⏸️ PENDENTE | CEO |

### 5.3 Reconcile (Ação CEO pós-smoke)

| Gate | Status | Responsável |
|------|--------|-------------|
| G3 magic OUT | ⏸️ PENDENTE | CEO |
| G4 UNKNOWN | ⏸️ PENDENTE | CEO |
| G5 PnL diff | ⏸️ PENDENTE | CEO |
| P0-8 R | ⏸️ PENDENTE | CEO |
| REG-1 order_send magic 234001 + OV2\| | ⏸️ PENDENTE | CEO |
| REG-2 deals OUT magic 234001 | ⏸️ PENDENTE | CEO |

### 5.4 Tabela PnL (Ação CEO pós-smoke)

| Métrica | Status | Responsável |
|---------|--------|-------------|
| Δ Equity | ⏸️ PENDENTE | CEO |
| Σ deals.profit (MT5) | ⏸️ PENDENTE | CEO |
| Σ feedback.pnl | ⏸️ PENDENTE | CEO |
| Σ feedback.total_realized_pnl | ⏸️ PENDENTE | CEO |
| Floating PnL (se aplicável) | ⏸️ PENDENTE | CEO |

### 5.5 Validação AIC (Ação AIC pós-smoke)

| Item | Status | Responsável |
|------|--------|-------------|
| AIC_VALIDACAO_PSA_P0_ABC_20260523.md | ⏸️ PENDENTE | AIC |
| Inventário ABC coluna Resolvido | ⏸️ PENDENTE | AIC |

---

## 6. PROBLEMAS IDENTIFICADOS E RESOLVIDOS

### 6.1 Problemas Resolvidos Hoje

| Problema | Solução | Status |
|----------|---------|--------|
| T-D4b DEFERRED (sem excepção CEO) | Implementado PositionManager wiring completo | ✅ RESOLVIDO |
| Lista fixa OMEGA_24X7_ATIVOS ignorava schedule FDS | Comentado nos PS1 | ✅ RESOLVIDO |
| Fechos automáticos sem guard mercado fechado | Adicionado is_market_open em 4 pontos | ✅ RESOLVIDO |
| MT5 comment > 31 chars (timestamp em PARTIAL) | Removido timestamp, abreviado TIME_STOP→TS, ZAK_TRAP→ZAK | ✅ RESOLVIDO |

### 6.2 Problemas Identificados (Não Resolvidos)

| Problema | Impacto | Responsável | Fase |
|----------|---------|-------------|------|
| Falha A: ATR M1 para sinal H4 (SL ~$2.50) | ALTO | PSA (Fase 1) | Router |
| Falha B: Cascata = entrada tardia | MÉDIO | PSA (Fase 2) | Router |
| Falha C: M1-GATE atraso | ALTO | PSA (Fase 2) | Router |
| Falha D: v2 hard-coded SL/TP | BAIXO (v2 inativo) | PSA (Fase 3) | Router |
| T-W2: Schedule só no arranque | BAIXO | PSA (opcional) | Weekend |

---

## 7. DESALINHAMENTOS DOCUMENTAIS IDENTIFICADOS PELO AIC

### 7.1 Desalinhamentos (todos FECHADOS por CEO 2026-05-23)

| ID | Descrição | Status | Resolução CEO |
|----|-----------|--------|---------------|
| D1 | T-D5 partial_taken no ledger | ✅ FECHADO | Opção A — flag → Fase 1 (não bloqueia P0) |
| D2 | T-W2 não implementado | ✅ FECHADO | Opcional; T-W3 suficiente |
| D3 | Inventário ABC 22/05 desactualizado | ✅ FECHADO | Inventário 23/05 criado (B4) |
| D4 | Commit final após smoke? | ✅ FECHADO | HEAD `ed6452e` é commit final |

Ref: `CEO_DECISAO_ROTEIRO_P0_20260523.md`

### 7.2 Desalinhamento Documental

| ID | Descrição | Ação necessária |
|----|-----------|-----------------|
| DOC-1 | OMEGA_INVENTARIO_CONSOLIDADO_ABC_20260522.md diz fixes NÃO | AIC atualizar coluna Resolvido |

---

## 8. O QUE NÃO DEVE SER REFEITO

### 8.1 Tarefas Completas (NÃO re-executar)

| Tarefa | Motivo |
|--------|--------|
| T-D1 (1POS/state) | Implementado e testado (UT-1 PASS) |
| T-D2 (Breakeven buffer) | Implementado e testado (UT-3 PASS) |
| T-D3 (Ghost orders) | Implementado e testado (UT-2 PASS) |
| T-D4 (Schema G5) | Implementado e testado (UT-4 PASS) |
| **T-D4b (PositionManager)** | **Implementado e testado (UT-8 PASS)** |
| T-P1a (XAUUSD 1500) | Implementado e testado (UT-5 PASS) |
| T-D5 (Partial TP) | Engine pré-existente, testado (UT-6 PASS) |
| T-P1b (Cache 60s) | Implementado e testado (UT-7 PASS) |
| T-P1c (Anti-hedge) | Implementado (shadow_loop.py L3462) |
| T-P2b (Runner v1) | Implementado e testado (runner test PASS) |
| T-W1 (PS1 sem lista fixa) | Implementado (PS1 comentados) |
| T-W3 (Guard is_market_open) | Implementado (4 pontos de fecho) |

### 8.2 Problemas Diagnosticados (NÃO re-investigar)

| Problema | Status | Próxima ação |
|----------|--------|--------------|
| Falha A ($2.50 SL) | Diagnosticado | Fase 1 Router (proibido até AIC P0) |
| Falha B (Cascata) | Diagnosticado | Fase 2 Router (proibido até AIC P0) |
| Falha C (M1-GATE) | Diagnosticado | Fase 2 Router (proibido até AIC P0) |
| Falha D (v2) | Diagnosticado | Fase 3 Router (proibido até AIC P0) |

---

## 9. PRÓXIMOS PASSOS (ORDEM OBRIGATÓRIA)

### 9.1 Imediato (Ação CEO)

1. **Executar smoke MT5** (Sec. 5.3 mandato unificado)
2. **Preencher Sec. 4-6** do relatório PSA
3. **Validar AIC** (criar AIC_VALIDACAO_PSA_P0_ABC_20260523.md)

### 9.2 Pós-AIC APROVADO (Ação PSA)

1. **Atualizar inventário ABC** (coluna Resolvido)
2. **Commit final** (se necessário)
3. **Merge para main** (após autorização CEO)

### 9.3 Fase 1 Router (Ação PSA — PROIBIDO até AIC P0)

1. **Patch ATR** (get_execution_tf_atr com signal_tf)
2. **Testes UT-R1, UT-R2**
3. **Smoke SM-R1, SM-R2, SM-R3**

---

## 10. VEREDITO FINAL

| Camada | Status |
|--------|--------|
| **Código Fase 0 + 0b** | ✅ COMPLETO (12/12 tarefas) |
| **Testes unitários** | ✅ PASS (9/9) |
| **Documentação governance** | ✅ ATUALIZADA |
| **Smoke MT5** | ⏸️ PENDENTE (ação CEO) |
| **Reconcile** | ⏸️ PENDENTE (ação CEO pós-smoke) |
| **Validação AIC** | ⏸️ PENDENTE (ação AIC pós-smoke) |
| **Veredito global** | **CÓDIGO P0 IMPLEMENTADO** — Aguardando smoke CEO |

---

## 11. REFERÊNCIAS

| Documento | Caminho |
|-----------|--------|
| Relatório PSA | `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` |
| Mandato Unificado | `governance/OMEGA_MANDATO_UNIFICADO_P0_ROUTER_WEEKEND_20260523.md` |
| **Mandato Fecho P0 + Level 1** | **`governance/PSA_MANDATO_FECHO_P0_E_TRANSICAO_LEVEL_20260523.md`** |
| Reconciliação AIC-PSA | `governance/AIC_PSA_RECONCILIACAO_ALINHAMENTO_20260523.md` |
| Inventário ABC 23/05 | `governance/OMEGA_INVENTARIO_CONSOLIDADO_ABC_20260523.md` |
| Inventário Alinhamento | `governance/INVENTARIO_ALINHAMENTO_20260523.md` |
| CEO Decisão Roteiro | `governance/CEO_DECISAO_ROTEIRO_P0_20260523.md` |
| Template AIC Validação | `governance/AIC_VALIDACAO_PSA_P0_ABC_20260523_TEMPLATE.md` |
| Mandato P0 v2.0 | `governance/PSA_MANDATO_EXECUCAO_P0_ABC_20260522.md` |

---

**Assinatura PSA:** Devin (Devin)  
**Data:** 2026-05-23  
**Status:** FASE 0 + 0b COMPLETAS | Smoke pendente (ação CEO)
