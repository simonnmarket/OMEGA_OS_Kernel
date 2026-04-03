# Script de execução — caminho da proposta (PSA)

| Campo | Valor |
|-------|--------|
| **ID** | `DOC-SCRIPT-EXEC-PSA-20260327` |
| **Para** | PSA — desenvolvimento e execução |
| **Função** | Apresentar **só** o **roteiro sequencial** da proposta; normas completas, IDs e KPIs estão em `HANDOFF_PSA_INSTRUCOES_FINAIS_20260403.md` (`DOC-HANDOFF-PSA-20260403-UNIFIED`) |
| **Diretriz tática** | **Principal processual** para a nova camada de dados centrais (acto CEO — adopção oficial) |
| **Pacote único (envio PSA)** | `DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md` (`DOC-UNICO-PSA-MESTRE-20260403`) — normas + script + instruções + métricas |

---

## Registo de execução — Fase 0 (CONCLUÍDA)

**Data de encerramento:** 3 de abril de 2026  
**Run de referência (sugerido):** `PS-20260403-FASE0-593fe793`

| # | Tarefa | Evidência | Estado |
|---|--------|-----------|--------|
| **0.1** | `git rev-parse HEAD` + ambiente (`NEBULAR_KUIPER_ROOT` / RLS) | Selo **`593fe7938abe058af8779745bbb55f2209586391`** | OK |
| **0.2** | Leitura `HANDOFF_PSA_INSTRUCOES_FINAIS_20260403.md` + `FIN‑SENSE DATA MODULE.txt` | Checklist interno lido e assinado (PSA) | OK |
| **0.3** | Inventário de anexos Conselho (HANDOFF §7) | `STATUS_ANEXOS_CONSELHO.md` (`STATUS-ANEXOS-CONSELHO-20260403`) — ausências DDL/Inventário/Spark **declaradas** (`file_not_found` legalizado) | OK |

**Decisão:** Fase 0 **fecha com luz verde**. **Autorização imediata** para iniciar **PH-FS-01** (Inventário de fontes de dados).

**Nota de auditoria:** a ausência sistémica dos três espelhos textuais **não** bloqueia PH-FS-01; no `INVENTARIO_FONTES_DADOS_v1.*`, onde um relatório depender de especificação ainda não anexada, usar marcação `PENDENTE-CTO` ou `RISCO-AUDITORIA` conforme gate da fase (nunca omitir a dependência).

---

## Registo de execução — PH-FS-01 (CONCLUÍDA)

**Data de encerramento:** 3 de abril de 2026  
**Run de referência:** `PS-20260403-PH-FS-01-593fe79`  
**Certificado ao Conselho:** `DECLARACAO_CONCLUSAO_PH_FS_01.md` (`CERTIFICADO-CONCLUSAO-PH-FS-01`)

| # | Entrega | Evidência | Estado |
|---|---------|-----------|--------|
| **PH-FS-01.a** | Inventário v1 lacrado | `INVENTARIO_FONTES_DADOS_v1.csv` (10 linhas) | OK |
| **PH-FS-01.b** | Log append-only | `PSA_RUN_LOG.jsonl` (`start_phase`, `file_saved`, `phase_complete`) | OK |
| **PH-FS-01.c** | Declaração / custódia | `DECLARACAO_CONCLUSAO_PH_FS_01.md` | OK |
| **PH-FS-01.d** | Tier-0 | `PSA_GATE_CONSELHO_ULTIMO.txt` (última passagem) | OK (ver nota HEAD no certificado) |

**Decisão:** **Luz verde** para iniciar **PH-FS-02** (catálogo OHLCV unificado).

---

## Objetivo

Executar, de forma **ordenada e auditável**, a implementação do **FIN-SENSE DATA MODULE** (camada de dados central) e a sua ligação ao **OMEGA / Tier-0**, até um **MVP** com catálogo, proveniência e relatórios rastreáveis — **sem** saltar fases que invalidem auditoria posterior.

---

## Visão do caminho (uma página)

```mermaid
flowchart LR
  A[PH-FS-01 Inventário fontes] --> B[PH-FS-02 Catálogo OHLCV]
  B --> C[PH-FS-03 Map DEMO_LOG para TBL]
  C --> D[PH-FS-04 Job KPIs]
  D --> E[PH-TR-01 Gate + verify]
  E --> F[PH-PS-01 Relatório com cabeçalho auditável]
```

---

## Roteiro de execução (script)

Cada fase **só avança** se o critério de saída estiver **verde**. Registar `run_id` e `ingestion_id` conforme HANDOFF secção 2.

### Fase 0 — Pré-requisitos (antes de PH-FS-01)

| # | Tarefa | Saída |
|---|--------|--------|
| 0.1 | Confirmar `git rev-parse HEAD` e ambiente (`NEBULAR_KUIPER_ROOT`) | Registo no manifesto de run |
| 0.2 | Ler `HANDOFF_PSA_INSTRUCOES_FINAIS_20260403.md` + `FIN‑SENSE DATA MODULE.txt` | Checklist interno assinado |
| 0.3 | Localizar ou declarar ausência dos ficheiros Inventário / DDL / Scripts (HANDOFF §7) | `STATUS_ANEXOS_CONSELHO.md` ou entrada em manifest |

---

### Fase PH-FS-01 — Inventário de fontes de dados

| | |
|--|--|
| **Objetivo** | Saber **que** dados alimentaram **que** relatórios (2025–2026). |
| **Entradas** | Relatórios PSA, paths CSV, `DEMO_LOG`, OHLCV, notas de execução. |
| **Tarefas** | Listar cada fonte com `module_code`, path absoluto ou relativo, `schema_version` se existir. |
| **Saída** | `INVENTARIO_FONTES_DADOS_v1.csv` (ou `.md` tabelado). |
| **Gate** | Nenhuma linha “origem desconhecida” sem marcação `RISCO-AUDITORIA`. |

**Instruções operacionais (PSA: persistência, RUN_LOG, métricas, anti-conflito):**  
→ `SCRIPT_PSA_FASE_PH-FS-01_INSTRUCOES_OPERACIONAIS.md` (`DOC-SCRIPT-OPS-PH-FS-01-20260403`).

---

### Fase PH-FS-02 — Catálogo OHLCV unificado

| | |
|--|--|
| **Objetivo** | Uma **árvore canónica** + índice; eliminar deriva `grafico_candle` / `grafico_linha` sem reconciliação. |
| **Entradas** | `nebular-kuiper/OHLCV_DATA/_INDEX.csv`, especificação medalhão em `CONSELHO_FIN_SENSE_DATA_MODULE_FINAL_20260403.md` §3.1. |
| **Tarefas** | Planear colunas `ingestion_id`, `file_hash` no índice; definir path alvo `FIN_SENSE_DATA/bronze/...` (ou fase de migração documentada). |
| **Saída** | `CATALOGO_OHLCV_PLANO_v1.md` + `_INDEX` actualizado ou script de geração. |
| **Gate** | KPI-06 **testável** para um relatório piloto (conjunto S de símbolos/TF ⊆ catálogo C). |

---

### Fase PH-FS-03 — Mapeamento DEMO_LOG → TBL (MVP)

| | |
|--|--|
| **Objetivo** | Normalizar execução demo para o **modelo lógico** `TBL_ORDERS` / `TBL_EXECUTIONS` (mínimo de colunas). |
| **Entradas** | `DEMO_LOG_*.csv`, especificação FIN-SENSE. |
| **Tarefas** | Tabela de mapeamento coluna-a-coluna; regras de `order_id` / `exec_id`; export com `ingestion_id` por lote. |
| **Saída** | `MAP-DEMO-TBL_v1.md` + opcionalmente script `export_demo_to_tbl_mvp.py`. |
| **Gate** | Reprodutibilidade: mesmo CSV + mesmo script → mesmo output hash (ou diff vazio). |

---

### Fase PH-FS-04 — Job de KPIs (integridade de dados)

| | |
|--|--|
| **Objetivo** | Automatizar KPI-01, KPI-02, KPI-03 (e preparar MHM) sobre exports. |
| **Entradas** | `finsense_validation_kit.py`, CSV/Parquet de teste. |
| **Tarefas** | Integrar chamadas ao kit; gravar `KPI_REPORT_<ingestion_id>.json`. |
| **Saída** | Script `run_kpi_batch.py` (nome sugerido) + relatório JSON de exemplo. |
| **Gate** | Metas HANDOFF §3 para pelo menos um lote de referência (ou justificativa documentada). |

---

### Fase PH-TR-01 — Custódia Tier-0

| | |
|--|--|
| **Objetivo** | Garantir que alterações não quebram rastreio do repositório. |
| **Tarefas** | `psa_gate_conselho_tier0.py` → `PSA_GATE_CONSELHO_ULTIMO.txt`; `verify_tier0_psa.py` → OK; `psa_sync_manifest_from_disk.py` se aplicável. |
| **Gate** | ESTADO OK no verify; gate actualizado. |

---

### Fase PH-PS-01 — Relatório ao Conselho (piloto)

| | |
|--|--|
| **Objetivo** | Demonstrar **cadeia completa** dados → relatório com cabeçalho auditável. |
| **Tarefas** | Incluir `doc_id`, `ingestion_ids[]`, `git_head`, KPI-06 = 1 para datasets citados. |
| **Saída** | Um relatório piloto `RPT-PILOTO-<YYYYMMDD>.md` (ou PDF derivado). |
| **Gate** | Aprovação interna antes de envio formal ao Conselho. |

---

## Ordem estrita recomendada

`0 → PH-FS-01 → PH-FS-02 → PH-FS-03 → PH-FS-04 → PH-TR-01 → PH-PS-01`

**Paralelização permitida:** PH-TR-01 pode correr **após** cada conjunto de alterações em código; PH-FS-04 pode desenvolver-se em paralelo a PH-FS-03 **após** existir um export de teste.

---

## Documento de referência normativa

Todo o detalhe de **IDs, parâmetros numéricos, KPIs e proibições** permanece em:

`HANDOFF_PSA_INSTRUCOES_FINAIS_20260403.md`

---

*Fim do script de execução — `DOC-SCRIPT-EXEC-PSA-20260327` — rev. 2026-04-03 (registo Fase 0)*
