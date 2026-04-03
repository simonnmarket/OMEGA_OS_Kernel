# HANDOFF PSA — Documento único de execução (FIN-SENSE DATA MODULE + Tier-0 + auditoria)

| Campo | Valor |
|-------|--------|
| **ID do documento** | `DOC-HANDOFF-PSA-20260403-UNIFIED` |
| **Versão** | 2.0 (substitui conteúdo monolítico v1.0 de 03/04/2026; absorve `CEO_DEFESA_FIN_SENSE_DATA_MODULE_CONSELHO_20260327` + `CONSELHO_FIN_SENSE_DATA_MODULE_FINAL_20260403`) |
| **Data** | 27 de março de 2026 |
| **Para** | PSA (execução operacional MACE-MAX / Antigravity) |
| **De** | Núcleo de Validação OMEGA + Consolidação Conselho |
| **Estado** | **EXECUTÁVEL** — instruções objectivas com parâmetros, métricas auditáveis e catálogo de IDs |
| **Envio** | Transmitir **integralmente** ao PSA; manter `DOC-ID` em todas as comunicações derivadas |

**Relacionado:** `HANDOFF_PSA_INSTRUCOES_FINAIS_20260401.md` (histórico apenas). **Roteiro só de tarefas (caminho):** `SCRIPT_EXECUCAO_PSA_CAMINHO_PROPOSTA.md` (`DOC-SCRIPT-EXEC-PSA-20260327`).  
**Documento único para envio ao PSA (tudo consolidado):** `DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md` (`DOC-UNICO-PSA-MESTRE-20260403`).

---

## Índice

1. [Norte estratégico](#1-norte-estratégico)  
2. [Catálogo de identificadores (obrigatório)](#2-catálogo-de-identificadores-obrigatório)  
3. [Parâmetros normativos (SLA de dados)](#3-parâmetros-normativos-sla-de-dados)  
4. [Métricas de auditoria (KPI-01 … KPI-07)](#4-métricas-de-auditoria-kpi-01--kpi-07)  
5. [Artefactos e caminhos no disco](#5-artefactos-e-caminhos-no-disco)  
6. [FIN-SENSE DATA MODULE — resumo executável](#6-fin-sense-data-module--resumo-executável)  
7. [Análise Conselho / Inventário / DDL / Scripts](#7-análise-conselho--inventário--ddl--scripts)  
8. [Diretriz Complementar v2.0 (condensada)](#8-diretriz-complementar-v20-condensada)  
9. [Lacunas vs OMEGA e MVP](#9-lacunas-vs-omega-e-mvp)  
10. [Sequência Tier-0 (inalterada)](#10-sequência-tier-0-inalterada)  
11. [Checklist de execução PSA (com IDs de fase)](#11-checklist-de-execução-psa-com-ids-de-fase)  
12. [Proibições e limitações](#12-proibições-e-limitações)  
13. [Próximos passos e arquivo](#13-próximos-passos-e-arquivo)  

---

## 1. Norte estratégico

**Objectivo de negócio:** profit sustentável e **mensurável com prova** (dados → sinais → execução → PnL / métricas), **sem** números sem custódia de dados.

**Tese FIN-SENSE:** toda informação que **trafega** no sistema para **decisão ou relatório** deve ser **identificável**, **catalogável** e, quando persistida, ligada a **`ingestion_id`** (e manifestos). O módulo **não** calcula VaR/PnL institucional completo — **habilita** a auditoria.

**Ciclo:** actualizar → testar → auditar (KPIs) → reavaliar.

---

## 2. Catálogo de identificadores (obrigatório)

### 2.1 Prefixos de módulo / componente (`module_code`)

Cada evento, ficheiro lógico ou registo de pipeline **deve** poder ser prefixado para auditoria cruzada.

| Código | Módulo / camada | Uso |
|--------|-----------------|-----|
| `FS` | **FIN-SENSE DATA MODULE** | Ingestão, tabelas, proveniência, QC, catálogo OHLCV |
| `OM` | **OMEGA** (motor, estratégia, demo) | Sinais, `DEMO_LOG`, execução |
| `PS` | **PSA** (pipelines, sync, gate) | Manifestos Tier-0, `psa_sync`, relatórios operacionais |
| `TR` | **Tier-0** (verificação) | `verify`, gate, hashes de artefactos |
| `MD` | **Metadados / catálogo** | `_INDEX.csv`, registo de símbolo/timeframe |

**Regra:** em logs estruturados (JSONL), incluir sempre **`module_code`** + **`ingestion_id`** quando aplicável.

### 2.2 Identificadores por tipo

| ID | Formato | Obrigatório em | Exemplo |
|----|---------|----------------|---------|
| **`ingestion_id`** | UUID v4 (RFC 4122), string minúscula | Cada **batch** de ingestão FIN-SENSE; propagar a linhas | `550e8400-e29b-41d4-a716-446655440000` |
| **`schema_version`** | `v<major>.<minor>` ou git tag | Todos os batches e relatórios que citam dados | `v1.0` |
| **`run_id`** | `PS-<YYYYMMDD>-<HHMMSS>-<git_sha_7>` | Cada execução PSA que produz artefactos rastreados | `PS-20260327-143052-a1b2c3d` |
| **`correlation_id`** | UUID v4 | Pedidos REST internos / jobs encadeados (opcional mas recomendado) | UUID |
| **`manifest_id`** | UUID v4 **ou** hash SHA-256 hex (64 chars) do manifest canónico | `MANIFEST_RUN_*.json` alinhado a `TBL_DATA_PROVENANCE` | ver gate |
| **`operator_id`** | string (utilizador ou `service:psa-gate`) | Manifestos e ingestões | `service:psa_sync` |
| **`component_instance`** | `<module_code>.<função>` | Logs de depuração | `FS.INGEST`, `PS.REPORT` |

### 2.3 Chaves de negócio (dedup / join — FIN-SENSE)

| Entidade | Chave mínima documentada |
|----------|---------------------------|
| Tick / trade raw | `(source, trade_id)` ou `(source, seq_no)` |
| Ordem | `order_id` |
| Execução | `exec_id` |
| Barra OHLCV (curated) | `(symbol, timeframe, bar_open_ts_utc)` + `ingestion_id` da última materialização |

### 2.4 Rastreio “relatório → dados”

Todo **relatório PSA** entregue ao Conselho **deve** declarar no cabeçalho (YAML ou tabela):

- `doc_id` (ex.: `DOC-RPT-<YYYYMMDD>-<seq>`)  
- `ingestion_ids[]` utilizados  
- `git_head`  
- `kpi_catalog_coverage` (KPI-06) — ver secção 4  

---

## 3. Parâmetros normativos (SLA de dados)

| Parâmetro | Símbolo | Valor por defeito | Unidade | Notas |
|-----------|---------|---------------------|---------|--------|
| Desvio temporal máximo source vs recv | `Δ_skew` | **300** | segundos | Alinhado a `finsense_validation_kit.TCR`; ajustar por feed |
| Meta KPI PAR | `PAR_min` | **0,999** | adimensional | Após MVP |
| Meta KPI IC | `IC_min` | **0,99** | adimensional | Por classe de ativo se necessário |
| Meta KPI TCR | `TCR_min` | **0,995** | adimensional | |
| Meta DRR | `DRR_max` | **1e-6** | adimensional | Duplicados pós-dedup |
| Formato temporal | — | **UTC ISO 8601** com `Z` ou offset explícito | — | FIN-SENSE |
| Hash de ficheiro (manifest) | — | **SHA-256** hex minúsculo | — | Compatível Tier-0 onde aplicável |

---

## 4. Métricas de auditoria (KPI-01 … KPI-07)

**Implementação de referência:** `finsense_validation_kit.py` (PAR, IC, TCR, manifest mínimo, CC).

| ID | Nome | Fórmula (resumo) | Meta pós-MVP | Evidência |
|----|------|------------------|--------------|-----------|
| **KPI-01** | Provenance Attach Rate (PAR) | linhas com `ingestion_id` / linhas | ≥ `PAR_min` | Query ou batch CSV |
| **KPI-02** | Identifier Completeness (IC) | linhas com FIGI ou ISIN ou (symbol+exchange) / linhas | ≥ `IC_min` | Idem |
| **KPI-03** | Time Consistency Rate (TCR) | linhas com `source_ts ≤ recv_ts + Δ_skew` / linhas válidas | ≥ `TCR_min` | Idem |
| **KPI-04** | Manifest Hash Match (MHM) | manifests com todos os hashes verificados / manifests | **1,0** oficiais | Recomputar SHA-256 |
| **KPI-05** | Dedup Residual Rate (DRR) | duplicados pós-ingest / linhas | ≤ `DRR_max` | Job QC |
| **KPI-06** | Catalog Coverage (CC) | \|S∩C\| / \|S\| (símbolos/TF do relatório ∩ catálogo) | **1,0** antes de publicar | `_INDEX` + manifest |
| **KPI-07** | Schema Version Discipline (SVD) | ingestões com `schema_version` válido / ingestões | **100%** | Manifest |

**Auditoria:** para cada release de dados, anexar ficheiro `KPI_REPORT_<ingestion_id>.json` com valores numéricos e `run_id`.

---

## 5. Artefactos e caminhos no disco

| Artefacto | Caminho relativo (base: `evidencia_pre_demo/04_relatorios_tarefa/`) |
|-----------|------------------------------------------------------------------------|
| Este handoff (único) | `HANDOFF_PSA_INSTRUCOES_FINAIS_20260403.md` |
| Especificação FIN-SENSE (Conselho) | `../../../Auditoria Conselho/FIN‑SENSE DATA MODULE.txt` (relativo a `04_relatorios_tarefa/`) |
| Documento de especificação v1.1 (OHLCV / medalhão) | `CONSELHO_FIN_SENSE_DATA_MODULE_FINAL_20260403.md` |
| Defesa CEO (conteúdo absorvido neste doc; manter como anexo histórico) | `CEO_DEFESA_FIN_SENSE_DATA_MODULE_CONSELHO_20260327.md` |
| Kit Python KPI / hash | `finsense_validation_kit.py` |
| Gate Conselho (último) | `PSA_GATE_CONSELHO_ULTIMO.txt` |
| PARAM Conselho | `../PARAMETRO_PSA_INSTRUCOES_CONSELHO_ATUAL.md` (relativo a esta pasta `04_relatorios_tarefa/`) |

**OHLCV canónico (evolução):** raiz lógica `FIN_SENSE_DATA/bronze/market_data/ohlcv/...` (detalhe em `CONSELHO_FIN_SENSE...` §3.1). Até migração: fonte operacional actual `nebular-kuiper/OHLCV_DATA/` com `_INDEX.csv`; **deprecar** novas ingestões em `Auditoria PARR-F/inputs/OHLCV_DATA/grafico_*` sem `ingestion_id`.

---

## 6. FIN-SENSE DATA MODULE — resumo executável

1. **Escopo:** armazenar, versionar, expor dados + metadados; **sem** motor de métricas de negócio embutido.  
2. **Tabelas núcleo (nomes):** `TBL_MARKET_TICKS_RAW`, `TBL_ORDERBOOK_SNAPSHOT`, `TBL_ORDERS`, `TBL_EXECUTIONS`, `TBL_POSITIONS_HISTORY`, `TBL_SECURITIES_MASTER`, `TBL_BENCHMARKS`, `TBL_CORP_ACTIONS`, `TBL_DERIVATIVES_CHAIN`, `TBL_RATES_CURVES`, `TBL_MACRO_EVENTS`, `TBL_DATA_PROVENANCE`, `TBL_DATA_QUALITY_FLAGS`, `TBL_COUNTERPARTY_EXPOSURES`.  
3. **MVP prioritário (PSA):** `TBL_SECURITIES_MASTER` (mínimo) + `TBL_ORDERS` + `TBL_EXECUTIONS` + `TBL_DATA_PROVENANCE` + catálogo OHLCV unificado; mapear `DEMO_LOG` → modelo normalizado.  
4. **Cada linha:** metadados mínimos conforme `FIN‑SENSE DATA MODULE.txt` (`ingestion_id`, `source`, `schema_version`, `recv_ts`, `source_ts`, `qc_flags`, …).

---

## 7. Análise Conselho / Inventário / DDL / Scripts

| Ficheiro (referência) | Papel |
|-----------------------|--------|
| `FIN‑SENSE DATA MODULE.txt` | **Presente** em `Auditoria Conselho/` — norma activa |
| `Inventário Expandido e Especificação de Dados.txt` | Roadmap de lacunas e métricas institucionais — **localizar ou anexar** |
| `DDL em estilo Parquet Delta.txt` | DDL alvo — **localizar ou anexar** |
| `Scripts Spark SQL Delta‑compatible.txt` | Receitas analíticas (esboço) — **localizar ou anexar** |

**Estado do workspace (auditoria):** os **três** últimos **não** foram encontrados no repositório com esses nomes. **Acção PSA:** (1) colocar cópias em `Auditoria Conselho/` **ou** (2) registar `file_not_found` + `substitute_path` + `sha256` no próximo `manifest` de configuração.

**Síntese:** Inventário/DDL/Scripts definem **alvo analítico**; FIN-SENSE define **substrato**; Tier-0 define **custódia actual** de ficheiros rastreados.

---

## 8. Diretriz Complementar v2.0 (condensada)

- **Não omissão:** declarar **demo vs fundo**; métricas institucionais **sem** tabelas = **não validáveis**.  
- **CQO vs CTO:** dados e compute devem ser planeados em **fases**.  
- **CIO vs CQO:** sem securities master + timestamps auditados, rastreio **incompleto**.  
- **PSA:** KPI-06 **obrigatório** antes de enviar relatório técnico ao Conselho.

---

## 9. Lacunas vs OMEGA e MVP

| Domínio | Prioridade | Acção PSA |
|---------|------------|-----------|
| Ordens + execuções + fees normalizadas | **Alta** | Modelo mínimo + IDs estáveis |
| Preço de referência por evento | **Alta** | Ligação barra/tick + `ingestion_id` |
| Manifest FIN-SENSE ↔ `MANIFEST_RUN_*.json` | **Alta** | Mesmo conceito de hash + lista de ficheiros |
| ISIN/FIGI | Média | Roadmap |
| Spark / VaR / CVA | Baixa curto prazo | Após MVP dados |

---

## 10. Sequência Tier-0 (inalterada)

1. Raiz do repo + `$env:NEBULAR_KUIPER_ROOT`  
2. `git rev-parse HEAD` → registar em manifest / `run_id`  
3. `psa_gate_conselho_tier0.py` → `PSA_GATE_CONSELHO_ULTIMO.txt`  
4. `verify_tier0_psa.py` → **ESTADO OK**  
5. Demo: `11_live_demo_cycle_1.py` `--smoke` → `--bars N`  
6. Pós-demo: `verificar_demo_apos_noturno.py --csv "<DEMO_LOG_*.csv>"`  
7. `psa_sync_manifest_from_disk.py` quando artefactos mudarem  

---

## 11. Checklist de execução PSA (com IDs de fase)

| Fase ID | Entregável | Critério de saída (pass/fail) |
|---------|------------|-------------------------------|
| **PH-FS-01** | Inventário de todas as fontes de dados usados em relatórios 2025–2026 | Lista com `module_code` + path + `schema_version` |
| **PH-FS-02** | Unificar catálogo OHLCV (`_INDEX` + colunas `ingestion_id`, `file_hash` planeado) | KPI-06 testável para novo relatório |
| **PH-FS-03** | Mapeamento `DEMO_LOG` → campos `TBL_ORDERS` / `TBL_EXECUTIONS` (MVP) | Documento `MAP-DEMO-TBL_v1.md` + `ingestion_id` por export |
| **PH-FS-04** | Job que calcula KPI-01…KPI-03 sobre export CSV/Parquet | `KPI_REPORT_<id>.json` gerado |
| **PH-TR-01** | Gate + verify verdes após alterações | `PSA_GATE` + log verify |
| **PH-PS-01** | Relatório ao Conselho com cabeçalho (secção 2.4) | `CC = 1` para datasets citados |

**Falha de fase:** qualquer relatório sem `ingestion_ids[]` ou com KPI-06 &lt; 1 → **não enviar** até correcção ou excepção documentada pelo CEO.

---

## 12. Proibições e limitações

- Não afirmar paridade com **fundo institucional** sem feeds e infra.  
- Inventário ≠ dados carregados; DDL ≠ cluster a correr.  
- SQL exemplo (VaR/CVA) nos anexos Spark pode ser **pseudo** — validar antes de produção.  
- `finsense_validation_kit.py` **não** substitui política de risco; apenas **integridade de dados**.

---

## 13. Próximos passos e arquivo

**Transmitir ao PSA:** este ficheiro (`DOC-HANDOFF-PSA-20260403-UNIFIED`) + `PARAMETRO_PSA_INSTRUCOES_CONSELHO_ATUAL.md` + `FIN‑SENSE DATA MODULE.txt` + `finsense_validation_kit.py` + último `PSA_GATE_CONSELHO_ULTIMO.txt` + `HEAD` git.

**Anexos recomendados:** `CONSELHO_FIN_SENSE_DATA_MODULE_FINAL_20260403.md`, `CEO_DEFESA_FIN_SENSE_DATA_MODULE_CONSELHO_20260327.md` (arquivo histórico).

**Tarefa imediata:** completar **PH-FS-01 … PH-FS-04**; localizar ou formalizar ausência dos três `.txt` do Inventário/DDL/Scripts com registo auditável.

---

**Fim do documento único — ID `DOC-HANDOFF-PSA-20260403-UNIFIED` — próxima revisão quando MVP dados (secção 9) estiver implementado ou quando `Auditoria Conselho/` receber novos ficheiros com hash registado.**
