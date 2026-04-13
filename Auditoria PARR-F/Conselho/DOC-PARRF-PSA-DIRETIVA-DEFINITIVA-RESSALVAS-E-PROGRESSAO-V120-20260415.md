# DOC-PARRF-PSA-DIRETIVA-DEFINITIVA-RESSALVAS-E-PROGRESSAO-V120-20260415

| Campo | Valor |
|--------|--------|
| **ID oficial** | `DOC-PARRF-PSA-DIRETIVA-DEFINITIVA-RESSALVAS-E-PROGRESSAO-V120-20260415` |
| **Versão** | 1.0.0 |
| **Data** | 2026-04-15 |
| **Estado** | **DEFINITIVO** — substitui reaberturas informais sobre o mesmo facto já coberto |
| **Destinatário** | **PSA** (obrigatório), Tech Lead, Conselho, COO |
| **Leitura conjunta** | `DOC-PARRF-PSA-RUNBOOK-EXECUCAO-L04-L06-L07-FASE8-V120-20260415`, `DOC-PARRF-PSA-ADENDO-HOMOLOGACAO-RESSALVAS-V120-20260415` |
| **Classificação** | Uso interno — TIER-0 PARR-F |

---

## 1. Finalidade (encerramento de ciclo)

Este documento **encerra definitivamente** o ciclo de **micro-ressalvas** sobre o estado já documentado nas atas e adendos anteriores, **sem** invalidar exigências de evidência. A partir da sua entrada em vigor:

- O PSA **não** deve produzir novos memorandos que **repetem** o mesmo aviso técnico (ex.: “sem DSN não há `phase8_pass`”) **salvo** se houver **novo facto** (nova RUN, novo commit, nova falha, nova versão de schema).
- O tempo de equipa destina-se a **etapas seguintes** (ex.: DSN aprovado → spike Fase 8; alinhamento de clones se a política mudar), **não** a reescrever o que já está **PASS**, **PENDENTE** ou **EXCEPÇÃO** de forma clara na ata vinculada a este processo.

---

## 2. Estado congelado (não reabrir sem gatilho novo)

| Item | Estado oficial | Reabertura apenas se |
|------|----------------|----------------------|
| **L-04** | **FECHADO** com evidência (`pass_rate = 1.0` no lote validado, ficheiros em `00_PROVAS_AUDITORIA`). | Novo lote de audits ou bump de `AUDIT_JSON_SCHEMA_V1.0`. |
| **L-07** | **FECHADO** com evidência (10/10 smoke, summary JSON). | Mudança de orquestrador ou critério de aceite. |
| **L-06** | **EXCEPÇÃO APLICADA:** Desktop canónico; `nebular-kuiper` como espelho referencial com **lag de SHA aceite** até nova ordem. Drift **documentado** uma vez — **não** exige novo parecer semanal sobre o mesmo drift. | Decisão COO/Tech Lead de exigir **paridade estrita** ou após **merge/sync** explícito entre clones. |
| **Fase 8** | **PENDENTE (N/A — sem DSN)**. Ausência de DSN = **não** conclusão L3; **não** reclassificar como “falha de produto”. | DSN aprovado + `spike_phase8_*.json` com `phase8_pass: true`. |

---

## 3. Linguagem institucional (obrigatória em novos escritos)

- **Proibido** em atas PSA: superlativos absolutos (“100% blindado”, “silêncio total”) **sem** referência a ficheiro ou métrica.  
- **Obrigatório:** remeter a **path** ou **ID** de artefacto (`l07_smoke_summary_*.json`, `l04_validation_summary.json`, `ssot_parity_report_*.json`).  
- **Correcção permanente:** o travão sem DSN **não** se descreve como “aborto silencioso”; usar: *“execução não realizada: pré-requisito DSN em falta; sem `phase8_pass`.”*

---

## 4. Diretiva ao PSA — progressão imediata

1. **Arquivar** esta diretiva junto do runbook e do adendo de ressalvas.  
2. **Não** gerar novos documentos de “clarificação” sobre L-04/L-07/L-06 excepção/Fase 8 pendente **sem** versão bump (`1.0.1+`) e **sem** novo ID.  
3. **Próxima ação única obrigatória** no eixo dados: obter **DSN aprovado** (Conselho/COO) e executar **uma** RUN `postgres_spike_phase8.py`; anexar JSON com `phase8_pass: true` **ou** registrar falha técnica com log (uma vez).  
4. **Próxima ação única** no eixo SSOT (opcional até ordem): alinhar SHA entre clones **se** a política deixar de admitir lag.

---

## 5. Linha para rubrica COO (opcional, uma assinatura)

> Rubrico a excepção L-06 (Desktop canónico / espelho com lag documentado) e o encerramento de ressalvas repetitivas conforme `DOC-PARRF-PSA-DIRETIVA-DEFINITIVA-RESSALVAS-E-PROGRESSAO-V120-20260415`.

---

## 6. Registo de versões

| Versão | Data | Notas |
|--------|------|--------|
| 1.0.0 | 2026-04-15 | Diretiva definitiva de progressão e fim de ciclo de micro-ressalvas. |

---

**Fim do documento** — `DOC-PARRF-PSA-DIRETIVA-DEFINITIVA-RESSALVAS-E-PROGRESSAO-V120-20260415`
