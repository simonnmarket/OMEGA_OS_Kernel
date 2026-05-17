# Memorando PSA — Fecho de secção (Governança Bridge + alinhamento Conselho)

| Campo | Valor |
|-------|--------|
| **ID** | GOV-MEMO-PSA-FECHO-BRIDGE-v1.0 |
| **Data** | 2026-05-17 |
| **Para** | PSA Lead |
| **Cc** | CEO, Tech Lead, CKO, CIO |
| **Assunto** | Encerramento da **secção de governança** Opção B / desbloqueio B6 — sem prejuízo de trabalho técnico pendente |

---

## 1. O que esta secção declara **fechada** (governança)

Com base nos artefactos versionados em `SOURCE_CODE/governance/`:

| Entrega | Estado | Artefacto |
|---------|--------|-------------|
| Opção B (runner dedicado) integrada e validável em dry-run | ✅ Encerrada para efeitos de **narrativa e critério CKO** | Evidências em `audit/` / logs acordados pelo projeto |
| Opção A (bridge no `shadow_loop`) | 🔴 Mantém-se **bloqueada** até critérios e assinaturas | `DESIGN_BRIDGE_B6_UNLOCK_CRITERIA.md` (GOV-BRIDGE-B6-UNLOCK-v1.0) |
| Critérios de desbloqueio B6 **não indefinidos** | ✅ Encerrada | Mesmo ficheiro — Secções 3–5 |
| Papéis (quem preenche vs quem assina anti-dup / métricas) | ✅ Explícito no doc | Secção 4–5 (PSA preenche; CKO confirma 3.2; CIO confirma 3.3; CEO ordem) |

**Nota de linguagem (evitar ambiguidade):** "Pendências fechadas" neste memorando significa **fecho da secção de definição e critérios auditáveis**, não conclusão de EA, flag `OMEGA_FILE_BRIDGE_AFTER_DECISION`, métricas de 5 dias ou PR de `shadow_loop.py` — estes itens permanecem listados na Secção 6 do GOV-B6 até evidência.

---

## 2. Trabalho técnico que **permanece aberto** (não bloqueia este fecho)

| Item | Dono típico |
|------|----------------|
| EA MQL5 (AIRequest / AIResponse, mesmo terminal `Common\Files`) | Equipa MQL5 |
| Implementação e teste da flag anti-duplicação | Engenharia + CKO |
| Janela de 5 dias + métricas (p99 escrita, timeouts, dups) | CIO / CQO (*alinhamento de papel*: se CQO ≠ CIO, referenciar no GOV-B6) |
| Desenho técnico Opção A versionado `GOV-BRIDGE-OPC-A-DESIGN-v1.x` | PSA Lead + Tech Lead |

---

## 3. Componente auxiliar (relógio / sessão) — referência externa

O PSA mínimo do **omega_session_clock** (anti-sobreposição de módulo) vive fora deste repositório até promoção:

`…\Pendente\componentes em desenvolvimento\omega_session_clock\PSA_MIN_OMEGA_SESSION_CLOCK_v1.md`

Não substitui o GOV-B6; evita conflito de **duas fontes** para o mesmo nome de módulo.

---

## 4. Pedido de acção ao PSA Lead (fecho formal)

1. **Arquivar** este memorando como registo de "secção de governança encerrada".
2. **Manter** o GOV-B6 como **única** porta de entrada para desbloqueio B6 (sem documentos paralelos com IDs conflituantes).
3. Quando critérios 3.1–3.4 estiverem com evidência, **preencher Secção 5** e solicitar ordem CEO conforme Secção 4.

---

## 5. Assinatura PSA (opcional — preencher na data)

| PSA Lead | Data | Assinatura / Aprovação |
|----------|------|-------------------------|
| | | ☐ Aceito fecho da secção de governança conforme memorando |

---

## 6. Rastreabilidade de artefactos relacionados

| Artefacto | Path | ID |
|-----------|------|----|
| Critérios desbloqueio B6 | `governance/DESIGN_BRIDGE_B6_UNLOCK_CRITERIA.md` | GOV-BRIDGE-B6-UNLOCK-v1.0 |
| Runner Opção B | `scripts/omega_bridge_runner.py` | BRIDGE-RUNNER-001 v1.0.0 |
| Componente Bridge | `modules/omega_execution_bridge_v2_2.py` | PSA-EXEC-BRIDGE-v2.2 |
| Evidência dry-run | `audit/bridge/bridge_runner.jsonl` | 2026-05-17T19:09 UTC |
| Catálogo módulos | `modules/__init__.py` | v2.5.1 |

---

*Emitido para suporte ao fecho de secção; não altera requisitos técnicos do GOV-B6.*
