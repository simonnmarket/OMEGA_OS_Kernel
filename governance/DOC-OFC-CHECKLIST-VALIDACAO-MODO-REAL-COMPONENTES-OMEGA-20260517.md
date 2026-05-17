# Checklist única — Validação de componentes para modo real (OMEGA)

| Campo | Valor |
|-------|--------|
| **ID documento** | DOC-OFC-CHECKLIST-MODO-REAL-v1.0 |
| **Data emissão** | 2026-05-17 |
| **Para** | PSA Lead |
| **Cc** | CEO, Tech Lead, CKO, CIO |
| **Assunto** | Trilho único de testes e validações até **operação real com lucro** — ordem de dependências e critérios de evidência |
| **Relaciona com** | `DESIGN_BRIDGE_B6_UNLOCK_CRITERIA.md` (GOV-BRIDGE-B6-UNLOCK-v1.0); `GOV-MEMO-PSA-FECHO-BRIDGE-v1.0.md` |

---

## 1. Objectivo (CEO)

- Gerar **profit** com **risco controlado**.
- Executar **todos os testes** e **validações** necessários por componente.
- Só declarar **modo real** quando os critérios abaixo estiverem com **evidência** (logs, `jsonl`, hashes ou relatório PSA assinável).

Este documento **não** substitui o GOV-B6 para Opção A no `shadow_loop`; **complementa** o trilho até modo real com **ordem de dependência** explícita.

---

## 2. Regra anti-conflito (governação documental)

Antes de criar **novo** ficheiro em `governance/` com o mesmo assunto:

1. Listar `governance/*.md` e procurar ID ou título equivalente.
2. Se já existir documento com o mesmo **ID** ou propósito: **actualizar** o existente; **não** criar segundo ficheiro.

*(Registo de correcção de duplicado: ver secção 6.1 de `GOV-MEMO-PSA-FECHO-BRIDGE-v1.0.md`.)*

---

## 3. Ordem de dependência (o que bloqueia o quê)

| # | Bloco | Depende de | Bloqueia |
|---|--------|------------|----------|
| D1 | **EA MQL5** (ler `AIRequest.*.json`, escrever `AIResponse.*.json`, mesmo `Common\Files` que o runner) | — | Ciclo completo bridge ↔ MT5 |
| D2 | **`omega_bridge_runner.py`** (Opção B) + evidência `audit/bridge/bridge_runner.jsonl` | D1 para *feedback* real; dry-run sem D1 | Confiança em I/O bridge |
| D3 | **`omega_execution_bridge_v2_2.py`** (contrato de sinal / serialização) | D2 | Consistência de payloads |
| D4 | **Risco e caps** (`OMEGA_MAX_POSITIONS`, DD, risco por trade, confluência — o que estiver em vigor no lab) | Política CEO/PSA escrita | Modo real seguro |
| D5 | **`omega_session_clock`** (relógio / sessão — integração em curso) | `OMEGA_*` env + raiz para `config/omega_session_clock.json` se aplicável | Auditoria temporal coerente em JSONL |
| D6 | **Opção A / B6** (`shadow_loop` + bridge após decisão) | GOV-B6 assinado + flag `OMEGA_FILE_BRIDGE_AFTER_DECISION` testada | Um só caminho de execução MT5 |

**Ordem recomendada de trabalho paralelo ao EA:** D4 e D5 podem avançar **em paralelo** com D1; D6 **só** após GOV-B6.

---

## 4. Checklist por fase (PSA / Eng preenchem evidência)

### Fase A — Código e unidade (sem MT5)

| # | Critério | Evidência mínima | ☐ |
|---|-----------|------------------|---|
| A1 | Self-tests do bridge runner (T01–T03 ou equivalente) | Saída: `All self-tests PASSED — BridgeRunner v1.0.0` • commit `5fc18c0` | ☑ |
| A2 | Self-tests / smoke do `omega_execution_bridge_v2_2.py` | Saída: `All self-tests PASSED — v2.2` • commit `dcdd949` | ☑ |
| A3 | Dry-run runner (`--dry-run`) com sinal de teste | `audit_record: {event: dry_run, symbol: XAUUSD, action: BUY, confidence: 0.85}` • `file_removed: True` • commit `8d07809` | ☑ |
| A4 | `omega_session_clock.py` self-test após integração no lab | `[OK] omega_session_clock self-test passed` • commit `d321006` | ☑ |

### Fase B — Integração ficheiro (com MT5, paper/demo)

| # | Critério | Evidência mínima | ☐ |
|---|-----------|------------------|---|
| B1 | EA activo no terminal correcto | Log ou captura 1 ciclo | ☐ |
| B2 | Ciclo `AIRequest → EA → AIResponse` | Entrada em `audit/bridge/bridge_runner.jsonl` ou ficheiro citado no GOV-B6 §3.1 | ☐ |
| B3 | Zero duplicação de ordem em janela acordada (N ciclos) | Tabela PSA + `trade_feedback.jsonl` ou equivalente | ☐ |
| B4 | Métricas de estabilidade (ex.: 5 dias paper) conforme GOV-B6 §3.3 | Relatório CIO/CQO com números | ☐ |

### Fase C — Modo real (go-live trading)

| # | Critério | Evidência mínima | ☐ |
|---|-----------|------------------|---|
| C1 | Limites de risco activos e verificados no arranque | Env + log de arranque | ☐ |
| C2 | Rollback documentado (voltar a Opção B só runner) | Secção em `GOV-BRIDGE-OPC-A-DESIGN-v1.x` ou acto CEO | ☐ |
| C3 | Ordem escrita CEO para modo real (conta, símbolos, caps) | DOC-OFC / e-mail arquivado | ☐ |
| C4 | PSA Lead assina checklist Fase B completa | Secção 6 deste documento | ☐ |

---

## 5. Declaração de limitações

- **Modo real** não é inferido só por testes unitários; exige **Fase B** mínima com EA.
- Latências e p99 dependem de **definição de medição** acordada (ver GOV-B6 §3.3).
- Lucro **não** é garantido por checklist; o checklist garante **processo e redução de erro operacional**.

---

## 6. Assinaturas PSA (preencher quando Fases A–B estiverem fechadas para avanço a C)

| Papel | Nome | Data | Aprovação Fase A | Aprovação Fase B |
|-------|------|------|------------------|------------------|
| PSA Lead | | | ☐ | ☐ |
| CKO (anti-dup / bridge) | | | — | ☐ |
| CIO / CQO (métricas operacionais) | | | — | ☐ |
| Tech Lead (coerência técnica) | | | ☐ | ☐ |

**CEO — ordem modo real (Fase C):** _________________________ **Data:** __________

---

## 7. Path canónico deste documento

`SOURCE_CODE/governance/DOC-OFC-CHECKLIST-VALIDACAO-MODO-REAL-COMPONENTES-OMEGA-20260517.md`

**ID lógico:** `DOC-OFC-CHECKLIST-MODO-REAL-v1.0` — qualquer revisão futura deve **substituir** este ficheiro ou acrescentar sufixo de versão no corpo (v1.1), evitando segundo ficheiro com o mesmo ID.

---

*Documento gerado para envio único ao PSA. Não duplicar sem actualizar o ID e o path acima.*

---

## 8. Registo de actualizações

| Versão | Data | Autor | Alteração |
|--------|------|-------|-----------|
| v1.0 | 2026-05-17 | Conselho OMEGA | Emissão inicial |
| v1.0.1 | 2026-05-17 | PSA Lead | A1–A3 preenchidas com evidência (commits `dcdd949`, `5fc18c0`, `8d07809`) |
| v1.0.2 | 2026-05-17 | PSA Lead | A4 concluída — `omega_session_clock` self-test passed • commit `d321006` — **Fase A 4/4** |
