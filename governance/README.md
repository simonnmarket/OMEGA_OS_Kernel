# Governança OMEGA — Índice de documentos oficiais

**Versão do índice:** 2.4 — **SOP Validação** (DOC-018 + `verify_governance_refs.py`); canal documental auditado automaticamente.

**Correções e Validação SOP (CEO/PSA):** `DOC-OFC-COMUNICACAO-PSA-CORRECOES-PROCEDIMENTO-VALIDACAO-GOV-CEO-20260327-018` (**018**) — documenta correções 008, 013, 014, 017; estabelece o script de auditoria automática.

**Único documento a anexar ao PSA (CEO):** `DOC-OFC-FINALIZACAO-UNICA-PSA-FINSENSE-TRANSICAO-CEO-20260327-017` (**017**) — mandato de finalização + transição + regra §8.

**Trilha Git (histórico):** **`9e884ff`** (v2.0) → **`f0e9373`** (consolidado) → **`078107c`** (pinado).

**Registo de falha e prevenção (PSA):** `DOC-OFC-REGISTO-FALHA-INDICE-DOC003-CORRECAO-PREVENTIVA-PSA-20260403-012` (012).

**Acta de encerramento (PSA — saída):** `DOC-OFC-ACTA-ENCERRAMENTO-OFICIAL-ETAPA-FINSENSE-HOMOLOGACAO-PSA-20260402-011` (011).

**Notificação final ao PSA:** `DOC-OFC-NOTIFICACAO-FINAL-PSA-ENCERRAMENTO-CICLO-FINSENSE-20260401-010` (010).

**Ordem final de encerramento (definitiva):** `DOC-OFC-ORDEM-ENCERRAMENTO-DEFINITIVO-PSA-HOMOLOGACAO-FINSENSE-20260331-009` (009).

**Procedimento único para o PSA:** `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007` (007).

**Pacote de envio imediato (instruções consolidadas):** `DOC-OFC-ENVIO-IMEDIATO-PSA-PACOTE-HOMOLOGACAO-CICLO-FINSENSE-20260327-008` (008) — **IMEDIATO**.

**Estado operacional:** **Pronto para rubrica** (ciclo FIN-SENSE) **|** **Transição Fase 2** (activa) — após rubrica PSA, substituir o bloco de homologação pelo **Anexo A** do **DOC-007** (uma única vez).

**Auditoria Automática:** `python scripts/verify_governance_refs.py` | Manifesto: `governance/MANIFESTO_DOCUMENTOS.json`.

**Tag Git:** `finsense-psa-cycle-20260404` (no `origin`).

| ID | Título |
|----|--------|
| `DOC-OFC-VIOLACAO-REGRA-CEO-INTEGRACAO-FINSENSE-PSA-20260327-001` | Violação de mandato (código sem ordem CEO) |
| `DOC-OFC-CONCLUSAO-INTEGRACAO-FINSENSE-PSA-20260404-001` | Conclusão de integração PSA |
| `DOC-OFC-DESVIO-PADRAO-ESTRUTURAL-MODULES-FINSENSE-20260404-002` | Desvio: `modules` vs raiz |
| `DOC-OFC-RESOLUCAO-REALINHAMENTO-FINSENSE-20260404-002` | Resolução + logs de validação |
| `DOC-OFC-CIENCIA-ARQUIVO-HISTORICO-PSA-FINSENSE-20260404-003` | Ciência PSA e arquivo histórico |
| `DOC-OFC-ENCERRAMENTO-DEFINITIVO-CICLO-FINSENSE-PSA-20260404-004` | **Encerramento técnico-documental** |
| `DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005` | **Confirmação PSA** (secção 5) |
| `DOC-OFC-REQUISITO-VALIDACAO-PSA-OBRIGATORIA-SEM-GAP-20260404-006` | **Crítico:** validação PSA obrigatória |
| `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007` | **Guia único:** Anexo A + fase 2 |
| `DOC-OFC-ENVIO-IMEDIATO-PSA-PACOTE-HOMOLOGACAO-CICLO-FINSENSE-20260327-008` | **Envio imediato ao PSA:** pacote completo |
| `DOC-OFC-ORDEM-ENCERRAMENTO-DEFINITIVO-PSA-HOMOLOGACAO-FINSENSE-20260331-009` | **Ordem definitiva PSA:** encerramento (M1–M6) |
| `DOC-OFC-NOTIFICACAO-FINAL-PSA-ENCERRAMENTO-CICLO-FINSENSE-20260401-010` | Notificação final ao PSA |
| `DOC-OFC-ACTA-ENCERRAMENTO-OFICIAL-ETAPA-FINSENSE-HOMOLOGACAO-PSA-20260402-011` | **Acta oficial PSA:** encerramento etapa (saída) |
| `DOC-OFC-REGISTO-FALHA-INDICE-DOC003-CORRECAO-PREVENTIVA-PSA-20260403-012` | Registo de falha (ARQUIVO) |
| `DOC-OFC-SOLICITACAO-EXECUCAO-PSA-ENCERRAMENTO-GAP-FINSENSE-CEO-20260404-013` | **[Arquivo]** redireciona para **017** |
| `DOC-OFC-CERTIFICADO-CONCLUSAO-ETAPA-FINSENSE-LACUNAS-RESOLVIDAS-CEO-20260404-014` | **[Arquivo]** redireciona para **017** |
| `DOC-OFC-ENVIO-UNICO-PSA-ENCERRAMENTO-FINSENSE-CEO-20260327-015` | **[Arquivo]** redireciona para **017** |
| `DOC-OFC-REGISTO-PSA-TRANSICAO-MODULO-METRICAS-RELATORIOS-CEO-20260327-016` | **[Arquivo]** redireciona para **017** |
| `DOC-OFC-FINALIZACAO-UNICA-PSA-FINSENSE-TRANSICAO-CEO-20260327-017` | **Finalização única PSA:** 015+016+regra §8 |
| `DOC-OFC-COMUNICACAO-PSA-CORRECOES-PROCEDIMENTO-VALIDACAO-GOV-CEO-20260327-018` | **Correções e Validação SOP:** auditoria automática (P1–P4) |

### Fase 2 — engenharia (nova iniciativa; não reabre DOC-001–007)

| ID | Título |
|----|--------|
| `DOC-OFC-FASE2-FATIA1-PIPELINE-ZERO-LOSS-CSV-POSTGRES-20260412` | **Fatia 1:** pipeline zero-loss CSV → PostgreSQL |
| *(futuro)* `DOC-OFC-FASE2-FATIA2-…` | Idempotência + reprocessamento |

**Evidências de teste (Fatia 1):** `DOC-TESTES-FASE2-FATIA1.md` (raiz; estado `FECHADO_CODIGO`).

**Papéis (DOC Fatia 1 v1.1):** **Engenharia** (execução); **COO** (GO operacional); **MACE-MAX** (conselheiro); **PSA** (governança §7).

---
**Observação:** Auditoria Conselho: `Auditoria PARR-F\Auditoria Conselho\LEIA-ME-AUDITORIA-CONSELHO.md`
