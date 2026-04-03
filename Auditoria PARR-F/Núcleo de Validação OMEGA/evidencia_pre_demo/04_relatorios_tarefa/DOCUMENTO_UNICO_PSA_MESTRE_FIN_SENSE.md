# Documento único PSA — FIN-SENSE DATA MODULE, Tier-0 e roteiro completo

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-UNICO-PSA-MESTRE-20260403` |
| **Versão** | 1.0 |
| **Data** | 3 de abril de 2026 |
| **Para** | PSA (único executor; custódia de actualizações no repositório) |
| **Função** | **Um só ficheiro** com normas, script, instruções, métricas, IDs e estado de **execução** — envio oficial ao PSA |
| **Substitui para envio** | Leitura conjunta de `HANDOFF_*`, `SCRIPT_EXECUCAO_*`, `SCRIPT_PSA_FASE_PH-FS-01_*` (o conteúdo essencial está **aqui**; os outros permanecem como cópias de trabalho no disco) |

---

## Índice mestre

1. [Resumo dos documentos fusionados](#1-resumo-dos-documentos-fusionados)  
2. [Estado de execução (snapshot)](#2-estado-de-execução-snapshot)  
3. [Norte estratégico](#3-norte-estratégico)  
4. [Catálogo de identificadores](#4-catálogo-de-identificadores)  
5. [Parâmetros normativos (SLA)](#5-parâmetros-normativos-sla)  
6. [Métricas KPI-01 … KPI-07](#6-métricas-kpi-01--kpi-07)  
7. [FIN-SENSE DATA MODULE (resumo)](#7-fin-sense-data-module-resumo)  
8. [Anexos Conselho / lacunas / MVP](#8-anexos-conselho--lacunas--mvp)  
9. [Diretriz Complementar v2.0 (condensada)](#9-diretriz-complementar-v20-condensada)  
10. [Sequência Tier-0](#10-sequência-tier-0)  
11. [Script de execução — fases e gates](#11-script-de-execução--fases-e-gates)  
12. [Instruções operacionais PSA (persistência, RUN_LOG, anti-conflito)](#12-instruções-operacionais-psa-persistência-run_log-anti-conflito)  
13. [PH-FS-01 — passos numerados e métricas de fase](#13-ph-fs-01--passos-numerados-e-métricas-de-fase)  
14. [Reconciliação HEAD + linhas JSON (`PSA_RUN_LOG`)](#14-reconciliação-head--linhas-json-psa_run_log)  
15. [Layout OHLCV canónico (PH-FS-02)](#15-layout-ohlcv-canónico-ph-fs-02)  
16. [Artefactos, caminhos e kit Python](#16-artefactos-caminhos-e-kit-python)  
17. [Proibições e próximos passos](#17-proibições-e-próximos-passos)  

---

## 1. Resumo dos documentos fusionados

| Doc-ID original | Conteúdo absorvido neste mestre |
|-----------------|----------------------------------|
| `DOC-HANDOFF-PSA-20260403-UNIFIED` | Normas, IDs, parâmetros, KPIs, FIN-SENSE resumo, Conselho, Diretriz, lacunas, Tier-0, checklist de fases |
| `DOC-SCRIPT-EXEC-PSA-20260327` | Roteiro, mermaid, fases 0→PH-PS-01, registos Fase 0 e PH-FS-01 |
| `DOC-SCRIPT-OPS-PH-FS-01-20260403` | PSA único executor, pastas, esquema CSV, passos 6.1–6.9, anti-conflito |
| `STATUS-ANEXOS-CONSELHO-20260403` | Referência: anexos ausentes declarados |
| `CERTIFICADO-CONCLUSAO-PH-FS-01` | PH-FS-01 concluída (ver §2) |
| `DOC-OFC-PSA-PROVAS-AUD-20260403` | **Provas rastreáveis + checklist objectiva** (`DOCUMENTO_OFICIAL_PSA_PROVAS_E_AUDITORIA.md`) |
| `DOC-OFC-MODELO-TAR-20260403` | **Solicitação vs tarefa vs veredito** (`DOCUMENTO_OFICIAL_MODELO_SOLICITACAO_APROVACAO_TAREFA.md`) + `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` |

---

## 2. Estado de execução (snapshot)

| Fase | Estado | Evidência principal |
|------|--------|---------------------|
| **Fase 0** | **CONCLUÍDA** | `STATUS_ANEXOS_CONSELHO.md`; HEAD inicial de referência `593fe7938abe058af8779745bbb55f2209586391` |
| **PH-FS-01** | **CONCLUÍDA** | `INVENTARIO_FONTES_DADOS_v1.csv` (10 linhas); `PSA_RUN_LOG.jsonl`; `DECLARACAO_CONCLUSAO_PH_FS_01.md` |
| **HEAD canónico (pós gate)** | Alinhar relatórios e novos logs a | `2b906ec774a8fadca7fb3fc257ed3ef28746f1c5` (última passagem documentada em `PSA_GATE_CONSELHO_ULTIMO.txt` ao tempo do gate) |
| **PH-FS-02** | **AUTORIZADA** | Catálogo OHLCV unificado — iniciar conforme §11 e §15 |

---

## 3. Norte estratégico

**Objectivo de negócio:** profit sustentável e **mensurável com prova** (dados → sinais → execução → PnL / métricas), **sem** números sem custódia de dados.

**Tese FIN-SENSE:** toda informação que **trafega** no sistema para **decisão ou relatório** deve ser **identificável**, **catalogável** e, quando persistida, ligada a **`ingestion_id`** (e manifestos). O módulo **não** calcula VaR/PnL institucional completo — **habilita** a auditoria.

**Ciclo:** actualizar → testar → auditar (KPIs) → reavaliar.

**Diretriz tática (CEO):** o script de execução (`DOC-SCRIPT-EXEC-PSA-20260327`) é a **principal diretriz processual** para a camada de dados centrais.

---

## 4. Catálogo de identificadores

### 4.1 Prefixos `module_code`

| Código | Módulo | Uso |
|--------|--------|-----|
| `FS` | FIN-SENSE DATA MODULE | Ingestão, tabelas, proveniência, QC, catálogo OHLCV |
| `OM` | OMEGA | Sinais, `DEMO_LOG`, execução |
| `PS` | PSA | Pipelines, sync, gate, relatórios operacionais |
| `TR` | Tier-0 | `verify`, gate, hashes |
| `MD` | Metadados | `_INDEX.csv`, símbolo/timeframe |

### 4.2 Identificadores por tipo

| ID | Formato | Uso |
|----|---------|-----|
| `ingestion_id` | UUID v4 | Cada batch de ingestão |
| `schema_version` | `v<major>.<minor>` | Batches e relatórios |
| `run_id` | `PS-<YYYYMMDD>-<HHMMSS>-<git_sha_7>` | Execuções PSA |
| `correlation_id` | UUID v4 | Opcional, jobs encadeados |
| `manifest_id` | UUID ou SHA-256 do manifest | Alinhado a `TBL_DATA_PROVENANCE` |
| `operator_id` | string | Ex.: `service:psa_sync` |

### 4.3 Cabeçalho obrigatório de relatório ao Conselho

- `doc_id`  
- `ingestion_ids[]`  
- `git_head`  
- `kpi_catalog_coverage` (KPI-06)  

---

## 5. Parâmetros normativos (SLA)

| Parâmetro | Símbolo | Valor por defeito |
|-----------|---------|-------------------|
| Desvio temporal source vs recv | `Δ_skew` | **300** s |
| Meta PAR | `PAR_min` | **0,999** |
| Meta IC | `IC_min` | **0,99** |
| Meta TCR | `TCR_min` | **0,995** |
| Meta DRR | `DRR_max` | **1e-6** |
| Timestamps | — | **UTC ISO 8601** |
| Hash ficheiro (manifest) | — | **SHA-256** hex |

---

## 6. Métricas KPI-01 … KPI-07

**Referência de código:** `finsense_validation_kit.py` (PAR, IC, TCR, manifest mínimo, CC).

| ID | Nome | Definição resumida | Meta pós-MVP |
|----|------|-------------------|--------------|
| KPI-01 | PAR | linhas com `ingestion_id` / linhas | ≥ `PAR_min` |
| KPI-02 | IC | linhas com FIGI ou ISIN ou (symbol+exchange) / linhas | ≥ `IC_min` |
| KPI-03 | TCR | `source_ts ≤ recv_ts + Δ_skew` / linhas válidas | ≥ `TCR_min` |
| KPI-04 | MHM | manifests com hash verificado / manifests | **1,0** |
| KPI-05 | DRR | duplicados pós-ingest / linhas | ≤ `DRR_max` |
| KPI-06 | CC | \|S∩C\| / \|S\| (relatório vs catálogo) | **1,0** antes de publicar |
| KPI-07 | SVD | ingestões com `schema_version` válido / ingestões | **100%** |

**Auditoria:** anexar `KPI_REPORT_<ingestion_id>.json` por release de dados.

---

## 7. FIN-SENSE DATA MODULE (resumo)

1. **Escopo:** armazenar, versionar, expor dados + metadados; **sem** motor de métricas de negócio embutido.  
2. **Tabelas (nomes):** `TBL_MARKET_TICKS_RAW`, `TBL_ORDERBOOK_SNAPSHOT`, `TBL_ORDERS`, `TBL_EXECUTIONS`, `TBL_POSITIONS_HISTORY`, `TBL_SECURITIES_MASTER`, `TBL_BENCHMARKS`, `TBL_CORP_ACTIONS`, `TBL_DERIVATIVES_CHAIN`, `TBL_RATES_CURVES`, `TBL_MACRO_EVENTS`, `TBL_DATA_PROVENANCE`, `TBL_DATA_QUALITY_FLAGS`, `TBL_COUNTERPARTY_EXPOSURES`.  
3. **MVP prioritário:** `TBL_SECURITIES_MASTER` + `TBL_ORDERS` + `TBL_EXECUTIONS` + `TBL_DATA_PROVENANCE` + catálogo OHLCV; mapear `DEMO_LOG` → modelo normalizado.  
4. **Metadados por linha:** conforme `Auditoria Conselho/FIN‑SENSE DATA MODULE.txt`.

---

## 8. Anexos Conselho / lacunas / MVP

| Ficheiro | Estado típico |
|----------|----------------|
| `FIN‑SENSE DATA MODULE.txt` | **Presente** — norma activa |
| `Inventário Expandido...`, `DDL...`, `Scripts Spark...` | Frequentemente **ausentes** no repo — declarar `file_not_found` ou `PENDENTE-CTO` no inventário |

**MVP (prioridades):** ordens/execuções/fees; preço de referência por evento; manifest FIN-SENSE alinhado a `MANIFEST_RUN_*.json`. Spark/VaR/CVA: **após** MVP dados.

---

## 9. Diretriz Complementar v2.0 (condensada)

- Declarar **demo vs fundo**; métricas institucionais sem tabelas = **não validáveis**.  
- KPI-06 **obrigatório** antes de relatório técnico ao Conselho.  
- Dados e compute em **fases** (CQO vs CTO).

---

## 10. Sequência Tier-0

1. Raiz do repo + `$env:NEBULAR_KUIPER_ROOT`  
2. `git rev-parse HEAD` → registar em `run_id` / manifest  
3. `psa_gate_conselho_tier0.py` → `PSA_GATE_CONSELHO_ULTIMO.txt`  
4. `verify_tier0_psa.py` → **ESTADO OK**  
5. Demo / pós-demo conforme `PARAMETRO_PSA_INSTRUCOES_CONSELHO_ATUAL.md`  
7. `psa_sync_manifest_from_disk.py` quando artefactos mudarem  

---

## 11. Script de execução — fases e gates

**Ordem:** `0 → PH-FS-01 → PH-FS-02 → PH-FS-03 → PH-FS-04 → PH-TR-01 → PH-PS-01`

```mermaid
flowchart LR
  A[PH-FS-01 Inventário] --> B[PH-FS-02 Catálogo OHLCV]
  B --> C[PH-FS-03 Map DEMO_LOG TBL]
  C --> D[PH-FS-04 Job KPIs]
  D --> E[PH-TR-01 Gate + verify]
  E --> F[PH-PS-01 Relatório Conselho]
```

| Fase ID | Entregável | Gate |
|---------|------------|------|
| **0** | HEAD, leitura normativa, `STATUS_ANEXOS_CONSELHO.md` | OK |
| **PH-FS-01** | `INVENTARIO_FONTES_DADOS_v1.csv` + `PSA_RUN_LOG.jsonl` | Sem `dependency_status` vazio |
| **PH-FS-02** | `CATALOGO_OHLCV_PLANO_v1.md` + plano `_INDEX` | KPI-06 testável |
| **PH-FS-03** | `MAP-DEMO-TBL_v1.md` | Reprodutibilidade |
| **PH-FS-04** | `run_kpi_batch.py` + `KPI_REPORT_*.json` | Metas §5 ou justificativa |
| **PH-TR-01** | Gate + verify | OK |
| **PH-PS-01** | `RPT-PILOTO-*` | Cabeçalho §4.3; CC=1 |

**Falha:** relatório sem `ingestion_ids[]` ou KPI-06 &lt; 1 → **não enviar** (salvo excepção CEO).

### Registos concluídos (para auditoria)

- **Fase 0:** concluída; ver tabela §2.  
- **PH-FS-01:** concluída; certificado `DECLARACAO_CONCLUSAO_PH_FS_01.md`.  
- **Seguinte:** **PH-FS-02**.

---

## 12. Instruções operacionais PSA (persistência, RUN_LOG, anti-conflito)

- **Executor único:** PSA grava e versiona; evitar edições paralelas sem coordenação.  
- **Base de gravação:** `evidencia_pre_demo/04_relatorios_tarefa/` (+ `ph_fs01/` para rascunhos).  
- **`PSA_RUN_LOG.jsonl`:** append-only; **nunca** apagar linhas.  
- **Inventário v1:** lacrado; correções → `v2` ou `ERRATA_*.md`.  
- Antes de `commit`: `git status`; alinhar `git_head` no log com `git rev-parse HEAD`.  
- Actualizar `STATUS_ANEXOS_CONSELHO.md` só se anexos mudarem + entrada no RUN_LOG.

### Campos mínimos por linha JSONL

`ts_utc`, `run_id`, `phase`, `git_head`, `action`, `artifact`, `metrics`, `command` (ver exemplos §14).

### Esquema CSV inventário (colunas obrigatórias)

`row_id`, `module_code`, `asset_or_scope`, `source_type`, `path_relative`, `schema_version`, `consumes_reports_or_runs`, `last_known_git_head`, `dependency_status`, `notes`.

---

## 13. PH-FS-01 — passos numerados e métricas de fase

| Passo | Acção |
|-------|--------|
| 6.1 | `git rev-parse HEAD` → registo |
| 6.2 | Listar relatórios relevantes em `04_relatorios_tarefa/` |
| 6.3 | Rastrear relatório → ficheiros de dados |
| 6.4 | OHLCV `/_INDEX` e `inputs/OHLCV_DATA` se aplicável |
| 6.5 | Scripts gate/verify/finsense no inventário |
| 6.6 | Gravar `INVENTARIO_FONTES_DADOS_v1.csv` UTF-8 |
| 6.7 | (Opc.) `finsense_validation_kit.py` |
| 6.8 | verify / gate |
| 6.9 | `phase_complete` no RUN_LOG |

**Métricas de fase:** cobertura `dependency_status` = 1,0; rastreio HEAD 100%; KPI-06 prévia registável.

*(PH-FS-01 já executada; repetir padrão para revisões futuras ou v2.)*

---

## 14. Reconciliação HEAD + linhas JSON (`PSA_RUN_LOG`)

Quando o HEAD do inventário (fase inicial) difere do HEAD após commit + gate, acrescentar **sem apagar** linhas anteriores:

**1) `head_reconciled_post_commit`**

```json
{"ts_utc": "2026-04-03T16:46:00.000000Z", "run_id": "PS-20260403-RECON-2b906ec", "phase": "PH-FS-01", "git_head": "2b906ec774a8fadca7fb3fc257ed3ef28746f1c5", "action": "head_reconciled_post_commit", "artifact": "04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt", "metrics": {"prior_git_head_inventario": "593fe7938abe058af8779745bbb55f2209586391", "canonical_head": "2b906ec774a8fadca7fb3fc257ed3ef28746f1c5"}, "command": "git rev-parse HEAD"}
```

**2) `gate_pass`** (mesmo `git_head` que o verify/gate)

```json
{"ts_utc": "2026-04-03T16:46:00.000000Z", "run_id": "PS-20260403-RECON-2b906ec", "phase": "PH-FS-01", "git_head": "2b906ec774a8fadca7fb3fc257ed3ef28746f1c5", "action": "gate_pass", "artifact": "04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt", "metrics": {"verify_tier0_exit": 0, "gate_timestamp_utc": "2026-04-03T16:45:19Z", "manifest": "03_hashes_manifestos/MANIFEST_RUN_20260329.json"}, "command": "verify_tier0_psa.py"}
```

**Novas fases:** usar o **HEAD actual** de `git rev-parse HEAD` em todas as linhas novas após cada commit.

---

## 15. Layout OHLCV canónico (PH-FS-02)

Alvo (medalhão + Hive-style), extensível:

```text
FIN_SENSE_DATA/bronze/market_data/ohlcv/symbol=<ID>/timeframe=<TF>/year=<YYYY>/month=<MM>/
```

- Deprecar novas ingestões em `Auditoria PARR-F/inputs/OHLCV_DATA/grafico_*` sem `ingestion_id`.  
- Fonte actual até migração: `nebular-kuiper/OHLCV_DATA/_INDEX.csv`.  
- Detalhe arquitectural: `CONSELHO_FIN_SENSE_DATA_MODULE_FINAL_20260403.md` §3.1.

---

## 16. Artefactos, caminhos e kit Python

| Item | Caminho (relativo a `04_relatorios_tarefa/` salvo nota) |
|------|----------------------------------------------------------|
| Este mestre | `DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md` |
| PARAM | `../PARAMETRO_PSA_INSTRUCOES_CONSELHO_ATUAL.md` |
| FIN-SENSE (Conselho) | `../../../Auditoria Conselho/FIN‑SENSE DATA MODULE.txt` |
| Especificação OHLCV v1.1 | `CONSELHO_FIN_SENSE_DATA_MODULE_FINAL_20260403.md` |
| Kit KPI | `finsense_validation_kit.py` |
| Gate | `PSA_GATE_CONSELHO_ULTIMO.txt` |
| Inventário | `INVENTARIO_FONTES_DADOS_v1.csv` |
| Log runs | `PSA_RUN_LOG.jsonl` |
| Certificado PH-FS-01 | `DECLARACAO_CONCLUSAO_PH_FS_01.md` |
| Anexos | `STATUS_ANEXOS_CONSELHO.md` |
| Provas / auditoria | `DOCUMENTO_OFICIAL_PSA_PROVAS_E_AUDITORIA.md`, `templates_auditoria_psa/`, `psa_refutation_checklist.py` |
| Modelo SOL/TAR/DEC | `DOCUMENTO_OFICIAL_MODELO_SOLICITACAO_APROVACAO_TAREFA.md`, `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` |

---

## 17. Proibições e próximos passos

**Proibições:** não afirmar paridade **fundo** sem feeds; não enviar relatório sem KPI-06 quando aplicável; não apagar linhas do JSONL.

**Próximo passo imediato (PSA):** **PH-FS-02** — catálogo OHLCV unificado, plano de `_INDEX` com `ingestion_id` / `file_hash` planeada, documento `CATALOGO_OHLCV_PLANO_v1.md`.

---

**Fim do documento único — `DOC-UNICO-PSA-MESTRE-20260403` — qualquer revisão substancial deve bump de versão e entrada em `PSA_RUN_LOG.jsonl`.**
