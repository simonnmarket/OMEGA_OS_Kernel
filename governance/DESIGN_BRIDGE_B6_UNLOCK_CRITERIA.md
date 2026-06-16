# DESIGN — Critérios de Desbloqueio B6 (Opção A: Bridge no shadow_loop)

| Campo | Valor |
|-------|-------|
| ID | GOV-BRIDGE-B6-UNLOCK-v1.0 |
| Data emissão | 2026-05-17 |
| Estado | 🔴 BLOQUEADO — pendente assinatura e critérios |
| Artefacto | `governance/DESIGN_BRIDGE_B6_UNLOCK_CRITERIA.md` |
| Decisão origem | Conselho OMEGA 17/05/2026 (Tech Lead + CKO + CIO) |
| Branch de referência | `feature/nebular-integration-phase1` |

---

## 1. Contexto

O `omega_bridge_runner.py` (Opção B) foi integrado e validado em dry-run (17/05/2026).
A **Opção A** — integração do `ComponentEngine.execute_signal()` directamente no
`shadow_loop.py` após decisão final — está **bloqueada** até este documento ser
preenchido, aprovado e assinado por todos os signatários obrigatórios.

O bloqueio **não é indefinido**: é levantado quando todos os critérios da Secção 3
estiverem satisfeitos e as assinaturas da Secção 5 estiverem preenchidas.

---

## 2. Risco que justifica o bloqueio

| Risco | Descrição |
|-------|-----------|
| **Dupla execução** | shadow_loop envia via `mt5_send_order` nativo E bridge escreve `AIRequest` — EA executa segunda vez o mesmo sinal |
| **Race condition** | Dois escritores para `AIRequest.SYMBOL.json` sem lock explícito |
| **Ambiguidade de auditoria** | "Quem abriu a posição — Python nativo ou EA via ficheiro?" |
| **Latência no hot path** | `execute_signal()` é bloqueante (I/O disco + poll timeout) — penaliza loop de 20s |

---

## 3. Critérios obrigatórios para desbloqueio

Todos os critérios abaixo devem estar satisfeitos **antes** de qualquer PR para
integrar o bridge no `shadow_loop.py`.

### 3.1 EA MQL5 operacional
- [ ] EA activo no terminal MT5 a ler `AIRequest.SYMBOL.json` em `Common\Files`
- [ ] EA escreve `AIResponse.SYMBOL.json` com schema documentado
- [ ] Confirmado que EA e Python usam **o mesmo terminal** (mesma `Common\Files`)
- [ ] Evidência: log de 1 ciclo completo `AIRequest → EA → AIResponse` capturado em `audit/bridge/bridge_runner.jsonl`

### 3.2 Regra anti-duplicação implementada e testada
- [ ] Definição formal de "dono de mt5_send_order": **um único caminho por ticket/ciclo**
- [ ] Flag `OMEGA_FILE_BRIDGE_AFTER_DECISION=1` implementada em `shadow_loop.py`
- [ ] Quando flag=1: `mt5_send_order` nativo é **inibido** para o mesmo sinal
- [ ] Teste paper comprovando 0 ordens duplicadas em N≥50 ciclos

### 3.3 Métricas de estabilidade (N dias com EA activo)
- [ ] Período mínimo: **5 dias em paper/demo** com EA activo e bridge runner a processar
- [ ] Latência de escrita atómica: p99 < 500 µs (registado em `bridge_runner.jsonl`)
- [ ] Falhas de ficheiro (`WRITE_SLOW` / `FEEDBACK_TIMEOUT`): < 5% dos ciclos
- [ ] Zero `AIRequest` órfãos (sem resposta EA) persistindo > `MAX_SIGNAL_AGE_S`
- [ ] Zero duplicações detectadas em `trade_feedback.jsonl`

### 3.4 Desenho técnico documentado
- [ ] Diagrama de sequência: `shadow_loop → ComponentEngine → AIRequest → EA → AIResponse → shadow_loop`
- [ ] Especificação do lock: ficheiro PID ou semáforo evita dois runners simultâneos
- [ ] Especificação do rollback: como reverter para Opção B sem downtime
- [ ] Documento versionado e guardado em `governance/` com ID `GOV-BRIDGE-OPC-A-DESIGN-v1.x`

---

## 4. Procedimento de desbloqueio

1. PSA Lead preenche todos os critérios da Secção 3 com evidências
2. Tech Lead valida critérios 3.1–3.4 e assina
3. CKO (Red Team) confirma critério 3.2 (anti-duplicação) e assina
4. CIO confirma critério 3.3 (métricas operacionais) e assina
5. **CEO emite ordem explícita** de desbloqueio referenciando este documento
6. PR criado para `shadow_loop.py` com B6 design implementado

---

## 5. Assinaturas (preencher na data de desbloqueio)

| Papel | Nome | Data | Aprovação |
|-------|------|------|-----------|
| **CEO** — Ordem de desbloqueio | | | ☐ |
| **PSA Lead** — Critérios preenchidos | | | ☐ |
| **Tech Lead** — Validação técnica | | | ☐ |
| **CKO / Red Team** — Anti-duplicação | | | ☐ |
| **CIO** — Métricas operacionais | | | ☐ |

---

## 6. Estado actual (17/05/2026)

| Item | Estado |
|------|--------|
| `omega_bridge_runner.py` v1.0.0 (Opção B) | ✅ Integrado e testado |
| Dry-run XAUUSD BUY conf=0.85 | ✅ `file_removed=True`, audit JSONL OK |
| EA MQL5 | 🔴 Pendente desenvolvimento |
| Anti-duplicação `OMEGA_FILE_BRIDGE_AFTER_DECISION` | 🔴 Pendente implementação |
| Métricas 5 dias | 🔴 Pendente dados |
| Desenho técnico Opção A | 🔴 Pendente |

**Enquanto este documento não estiver assinado, o B6 no `shadow_loop.py` não avança.**

---

*Emitido por: PSA — 2026-05-17 | Artefacto canónico: `governance/DESIGN_BRIDGE_B6_UNLOCK_CRITERIA.md`*
