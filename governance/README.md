# Governança OMEGA — Índice de documentos oficiais

**Versão do índice:** 1.7 — inclui **DOC-011** (**acta** de encerramento oficial — preencher **após** M1–M6); **congelamento** dos DOC-001–007 até rubrica PSA ou ordem CEO v2.

**Acta de encerramento (PSA — saída):** `DOC-OFC-ACTA-ENCERRAMENTO-OFICIAL-ETAPA-FINSENSE-HOMOLOGACAO-PSA-20260402-011` — documento para **assinar** e **arquivar** quando a etapa estiver **efectivamente** concluída (não substitui **DOC-009**).

**Notificação final ao PSA:** `DOC-OFC-NOTIFICACAO-FINAL-PSA-ENCERRAMENTO-CICLO-FINSENSE-20260401-010` — canal documental para este encerramento; execução via **DOC-009** (M1–M6).

**Ordem final de encerramento (definitiva):** `DOC-OFC-ORDEM-ENCERRAMENTO-DEFINITIVO-PSA-HOMOLOGACAO-FINSENSE-20260331-009` — mandato M1–M6, assinatura PSA, efeito de fecho do gap (DOC-006).

**Procedimento único para o PSA:** `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007` (rubrica, commit único pós-homologação, transição fase 2).

**Pacote de envio imediato (instruções consolidadas):** `DOC-OFC-ENVIO-IMEDIATO-PSA-PACOTE-HOMOLOGACAO-CICLO-FINSENSE-20260327-008` — checklist, PowerShell, Anexo A, commit.

**Estado do ciclo FIN-SENSE (técnico-documental):** **ENCERRADO** — ver `DOC-OFC-ENCERRAMENTO-DEFINITIVO-CICLO-FINSENSE-PSA-20260404-004`.

**Homologação PSA (obrigatória para fechar gap):** **PENDENTE** até o PSA validar e rubricar **`DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005`** (secção 5). **Sem esta validação existe GAP de governança** — ver **`DOC-OFC-REQUISITO-VALIDACAO-PSA-OBRIGATORIA-SEM-GAP-20260404-006`**.

**Estado operacional:** **Pronto para rubrica** — após assinatura, substituir o bloco acima pelo **Anexo A** do **DOC-007** (uma única vez).

**Tag Git:** `finsense-psa-cycle-20260404` (no `origin`).

| ID | Título |
|----|--------|
| `DOC-OFC-VIOLACAO-REGRA-CEO-INTEGRACAO-FINSENSE-PSA-20260327-001` | Violação de mandato (código sem ordem CEO) e encaminhamento PSA |
| `DOC-OFC-CONCLUSAO-INTEGRACAO-FINSENSE-PSA-20260404-001` | Conclusão de integração PSA (com addendum de caminho canónico) |
| `DOC-OFC-DESVIO-PADRAO-ESTRUTURAL-MODULES-FINSENSE-20260404-002` | Desvio: `modules` vs raiz; Auditoria Conselho; `FIN_SENSE_DATA` |
| `DOC-OFC-RESOLUCAO-REALINHAMENTO-FINSENSE-20260404-002` | Resolução + logs de validação e ingestão |
| `DOC-OFC-CIENCIA-ARQUICO-HISTORICO-PSA-FINSENSE-20260404-003` | Ciência PSA e arquivo histórico de todas as execuções (obrigatório continuidade) |
| `DOC-OFC-ENCERRAMENTO-DEFINITIVO-CICLO-FINSENSE-PSA-20260404-004` | **Encerramento técnico-documental** — checklists, logs, Git; **aviso restritivo**; homologação total via DOC-005/006 |
| `DOC-OFC-CONFIRMACAO-ENCERRAMENTO-OFICIAL-PSA-FINSENSE-20260404-005` | **Confirmação PSA** — diretórios canónicos + GitHub + **rubrica obrigatória** (secção 5) |
| `DOC-OFC-REQUISITO-VALIDACAO-PSA-OBRIGATORIA-SEM-GAP-20260404-006` | **Crítico:** validação PSA obrigatória — evitar **gap** se não houver homologação formal |
| `DOC-OFC-GUIA-UNICO-PSA-RUBRICA-TRANSICAO-FASE2-20260404-007` | **Guia único:** rubrica, README pós-homologação, commit único, **fase 2** (alta performance), **congelamento** |
| `DOC-OFC-ENVIO-IMEDIATO-PSA-PACOTE-HOMOLOGACAO-CICLO-FINSENSE-20260327-008` | **Envio imediato ao PSA:** pacote completo (verificação Git, DOC-005 §5, README Anexo A, commit único) |
| `DOC-OFC-ORDEM-ENCERRAMENTO-DEFINITIVO-PSA-HOMOLOGACAO-FINSENSE-20260331-009` | **Ordem definitiva PSA:** encerramento institucional (M1–M6), declaração e assinatura; **1.0 DEFINITIVA** |
| `DOC-OFC-NOTIFICACAO-FINAL-PSA-ENCERRAMENTO-CICLO-FINSENSE-20260401-010` | **Notificação final ao PSA:** canal documental encerrado; apenas executar **DOC-009** + **DOC-008** |
| `DOC-OFC-ACTA-ENCERRAMENTO-OFICIAL-ETAPA-FINSENSE-HOMOLOGACAO-PSA-20260402-011` | **Acta oficial PSA:** encerramento da **pendência/etapa** após M1–M6; checklist + assinatura (documento de **saída**) |

### Fase 2 — engenharia (nova iniciativa; não reabre DOC-001–007)

Contratos técnicos e roadmap pós-ciclo FIN-SENSE. Gate de engenharia e PSA **antes** do escalão Conselho (salvo excepções no próprio DOC).

| ID | Título |
|----|--------|
| `DOC-OFC-FASE2-FATIA1-PIPELINE-ZERO-LOSS-CSV-POSTGRES-20260412` | **Fatia 1:** pipeline zero-loss CSV → PostgreSQL (`scripts/ingest_pipeline.py`), A1–A5, métricas, prazo 12/04, auditoria 13/04 |
| *(futuro)* `DOC-OFC-FASE2-FATIA2-…` | Idempotência + reprocessamento |

**Evidências de teste (Fatia 1):** `DOC-TESTES-FASE2-FATIA1.md` (raiz do repositório; preencher após `stress_test_10k` / `validate_a1_a5`).

**Papéis (DOC Fatia 1 v1.1):** **Engenharia** executa e fecha o gate técnico; **COO** (Chief Operating Officer) dá **GO operacional**; **MACE-MAX** permanece **conselheiro** (não substitui execução nem COO); **PSA** assina §7 (governança processual).

---
**Observação:** Auditoria Conselho (apenas trânsito): `Auditoria PARR-F\Auditoria Conselho\LEIA-ME-AUDITORIA-CONSELHO.md`
