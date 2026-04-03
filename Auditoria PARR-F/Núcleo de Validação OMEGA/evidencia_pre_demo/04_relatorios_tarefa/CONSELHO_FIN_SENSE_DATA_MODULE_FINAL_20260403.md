# FIN-SENSE DATA MODULE — Documento final de etapa (v1.1)

**Classificação:** encerramento de **módulo de dados** (escopo restringido) — **modelo de trabalho actual** para **centralização e catalogação**  
**Data:** 27 de março de 2026 (actualização de alinhamento OHLCV / pastas)  
**Fonte normativa Conselho:** `Auditoria PARR-F/Auditoria Conselho/FIN‑SENSE DATA MODULE.txt`  
**Para:** PSA, Engenharia de Dados, CQO/CTO (consumo)

---

## 0. Motivação de negócio (bússola recalibrada)

**Problema observado:** em várias ocasiões o **PSA** produziu **métricas e relatórios** (incluindo pedidos mais técnicos) **sem** conseguir provar ou repetir o resultado com **dados históricos catalogados** no sistema — porque **não existia** (ou não estava **registado** de forma única e rastreável) o **conjunto mínimo de dados** necessário à validação.

**Objectivo deste módulo (agora explícito):** criar **uma única camada** de **centralização dos dados** — **independentemente do ativo** — de modo que **qualquer teste ou relatório** solicitado ao sistema possa ser **validado** contra **informação persistida**, com **proveniência** e **catálogo** conhecidos. O documento **`FIN‑SENSE DATA MODULE.txt`** é o **modelo normativo** para esse trabalho; **não** substitui a necessidade de **preencher** o armazém com feeds reais — define **como** armazenar e **como** expor.

**Relação com “analytics”:** o módulo **não** embute cálculos de negócio; **fornece** os dados para que **PSA, research e CQO** deixem de depender de ficheiros soltos ou de memória operacional.

---

## 1. Declaração de âmbito (o que este módulo **é** e **não é**)

| | |
|--|--|
| **É** | Camada **persistente** que **armazena**, **versiona** e **expõe** dados numéricos e metadados — com **integridade**, **lineage**, **QC** e **contratos de ingestão**. |
| **Não é** | Motor de **cálculos de negócio**, agregações analíticas, modelos preditivos, regime detection, correlações estatísticas ou políticas de trading — isso permanece em **research / execution / outros módulos** que **consomem** estas tabelas. |

**Princípio reforçado no documento Conselho:** *“Não inclui funções de cálculo, agregação ou modelos: apenas armazenamento, integridade, lineage e exposição.”*

**Esta etapa considera-se concluída** quando a **especificação** acima estiver **aprovada** e **arquivada** como referência única para implementação — **sem** exigir, nesta fase, cluster Spark, Kafka ou REST em produção.

---

## 1.1 Estado actual OHLCV no repositório (diagnóstico)

Foram revistas as árvores indicadas pelo Conselho:

| Local | Padrão actual | Comentário |
|-------|----------------|------------|
| `nebular-kuiper/OHLCV_DATA/` | `{SYMBOL}/{SYMBOL}_{TF}.csv` + `_INDEX.csv` com colunas `symbol,timeframe,bars,from,to,file` | **Relativamente consistente** entre activos; o **`_INDEX.csv`** funciona como **mini‑catálogo** — alinhado ao espírito FIN-SENSE (saber *o que* existe e *onde*). |
| `Auditoria PARR-F/inputs/OHLCV_DATA/` | Subpastas `grafico_candle/` e `grafico_linha/` com ficheiros duplicados por símbolo/timeframe | **Risco de deriva:** o mesmo dado conceptual aparece em **dois sítios**; relatórios podem apontar para **cópias diferentes** sem **ingestion_id** único. |

**Conclusão:** a **padronização** exige **um único ramo canónico** dentro do módulo FIN-SENSE (ver secção 3.1), e **deprecação** do uso de `inputs/OHLCV_DATA` para **novas ingestões** — apenas **migração** ou **symlink** documentado até consolidar.

---

## 2. Análise completa do documento `FIN‑SENSE DATA MODULE.txt`

### 2.1 Coerência interna

- **Fronteira clara** entre “data plane” e “compute/analytics” — **reduz** risco de acoplamento e **facilita** auditoria.
- **Immutabilidade raw + Delta/Iceberg** para curated **upserts** — padrão de mercado para **reprodutibilidade** e **time travel**.
- **Metadados por linha** (`ingestion_id`, `source_ts`, `recv_ts`, `schema_version`, `qc_flags`, …) — **adequados** a rastreio e **replays** de experimentos.
- **Identificadores** (FIGI preferencial, ISIN, composite ticker+exchange) — **alinhados** a integração institucional.
- **Dedup / idempotência** por chaves explícitas — **essencial** para pipelines reais.
- **Joins documentados como contratos** (Exec↔Orders, tick↔snapshot, positions↔ticks) **sem** embutir fórmulas de PnL — **coerente** com o escopo.

### 2.2 Pontos de atenção (sem reabrir o módulo)

| Ponto | Nota |
|-------|------|
| **Plataforma** (Kafka, Spark, Glue, Trino) | **Recomendações** de arquitectura; a **especificação lógica** das tabelas **não depende** de um fornecedor cloud concreto. |
| **REST** | Contrato descrito; **implementação** é fase de **infra/API**. |
| **DDL exemplos** | Sintaxe **Delta**; validação final no **motor** escolhido (Databricks/Trino/outro). |
| **“Materialized views”** | Texto refere *precomputed partitions* **sem analytics dentro do módulo** — manter **disciplina**: só **projeções** de leitura, não métricas de negócio. |

### 2.3 Diretriz Complementar v2.0 — interdependências (resumo)

| Função | Ligação ao DATA MODULE |
|--------|-------------------------|
| **CIO** | **Dono natural** da proveniência, QC e schema registry. |
| **CQO / Research** | **Consumidor** — depende de **ingest_id** e tabelas limpas para **qualquer** métrica posterior. |
| **CTO** | **Infra** (storage, compute, catalog) — entrega **o contentor** onde o módulo vive. |
| **PSA** | **Orquestração** de pipelines de ingestão e **alinhamento** com custódia Tier-0 do repo (manifestos, hashes) onde aplicável. |
| **COO / Execução** | Consome **orders/executions** — **não** calcula PnL **dentro** do DATA MODULE. |

**Nenhuma interdependência crítica** invalida a **definição** do módulo; apenas **ordena** dependências de **implementação**.

---

## 3. Catálogo de tabelas (consolidado do documento fonte)

Tabelas nomeadas para cobertura:  
`TBL_MARKET_TICKS_RAW`, `TBL_ORDERBOOK_SNAPSHOT`, `TBL_ORDERS`, `TBL_EXECUTIONS`, `TBL_POSITIONS_HISTORY`, `TBL_SECURITIES_MASTER`, `TBL_BENCHMARKS`, `TBL_CORP_ACTIONS`, `TBL_DERIVATIVES_CHAIN`, `TBL_RATES_CURVES`, `TBL_MACRO_EVENTS`, `TBL_DATA_PROVENANCE`, `TBL_DATA_QUALITY_FLAGS`, `TBL_COUNTERPARTY_EXPOSURES`.

**Roadmap interno ao documento:** 0–3 meses foco em **securities master + ticks + orders + executions + provenance**; depois orderbook, positions, benchmarks, etc.

### 3.1 Padrão internacional de estrutura de pastas (object storage / data lake)

Não existe um **único** “ISO” para pastas de ficheiros de mercado; a prática **de facto** em **data lakes** combina:

- **Arquitectura em camadas (medalhão)** — *bronze* (raw imutável), *silver* (curated/validado), *gold* (consumo padronizado) — amplamente usada (p.ex. Databricks) e compatível com **Delta Lake / Iceberg** do teu documento fonte.
- **Particionamento estilo Hive** — `chave=valor` nos nomes de pastas — padrão **Apache Hive** / Spark, interoperável com **Glue/Metastore**.
- **Datas em UTC** — metadados e particionamento temporal alinhados a **ISO 8601** (como já previsto no `FIN‑SENSE DATA MODULE.txt` para timestamps).

**Proposta canónica (única árvore, qualquer ativo)** — raiz de exemplo `FIN_SENSE_DATA/` (ou `nebular-kuiper/FIN_SENSE_DATA/`):

```text
FIN_SENSE_DATA/
  bronze/
    market_data/
      ohlcv/
        symbol=<INSTRUMENT_ID>/          # ex.: XAUUSD, EURUSD — mesmo padrão para FX, índice, commodity
          timeframe=<TF>/                 # M1, M5, M15, H1, H4, D1, W1
            year=<YYYY>/month=<MM>/       # particionamento temporal quando os dados forem particionados por dia
              data.parquet                # preferível a CSV em fase madura; CSV permitido em migração com manifest
  silver/
    market_data/
      ohlcv/                              # schema alinhado a tabela curated (bar_open_ts UTC, OHLCV, ids)
        symbol=<INSTRUMENT_ID>/timeframe=<TF>/...
  gold/
    market_data/
      ohlcv/                              # vistas ou exports só leitura para PSA/UI — sem lógica de métricas no módulo
  manifests/
    ingestion_id=<UUID>/
      manifest.json                       # alinhado a TBL_DATA_PROVENANCE: hashes, contagem, operator_id
  catalog/
    _INDEX.csv                            # evolução do actual _INDEX: incluir ingestion_id, schema_version, file_hash
```

**Regras:**

1. **Não** separar por `grafico_candle` vs `grafico_linha` no armazenamento canónico — são **vistas** de apresentação, não **partições** de dados.  
2. **Um** `symbol` + `timeframe` + `intervalo temporal` → **um** sítio de verdade em **bronze** (append-only).  
3. Toda a ingestão gera **`ingestion_id`** + entrada em **manifest** + linha lógica em **proveniência** (quando a tabela existir).

Mapeamento para o modelo FIN-SENSE: barras OHLCV agregadas correspondem a **dados de mercado curados**; no roadmap completo podem viver como **tabela derivada** a partir de `TBL_MARKET_TICKS_RAW` ou como **dataset bronze/silver** explícito até existir tick — o importante é **não** duplicar árvores sem catálogo.

---

## 4. Critérios de aceitação desta **etapa de especificação** (módulo DATA)

- [x] Escopo **escrito** (armazenar + versionar + expor; **sem** analytics embutido).  
- [x] Lista de **tabelas** e **campos** essenciais, **PK/partição**, metadados mínimos.  
- [x] **Ingestão**: idempotência, dedup, exemplo JSON, checks de QC **sem** cálculo de negócio.  
- [x] **Lineage** e **manifests** diários descritos.  
- [x] **Joins** como contratos de leitura.  
- [x] **Roadmap** 0–3 / 3–9 / 9–18 meses.  
- [x] **Problema de negócio** (lacunas de dados nos relatórios PSA) **explicitado** e **ligado** a catalogação central.  
- [x] **Padrão único de pastas** (medalhão + Hive-style + UTC) **definido** para OHLCV e extensível a outros datasets.  

**Veredicto:** a especificação **FIN-SENSE DATA MODULE** (com este addendum v1.1) está **completa para arquivo** como **referência de implementação** da **camada de dados** e **modelo de trabalho** para **centralização**.

---

## 5. Pendências **explicitamente** adiadas para a **próxima etapa** (não fazem parte deste encerramento)

Estas linhas derivam de **discussões anteriores** e de **extensões** do ecossistema; **não** são entregáveis do **DATA MODULE** puro:

1. **Módulo sensorial “completo”** (classificação de padrões, taxonomia, match histórico ↔ live) — **camada cognitiva** acima dos dados brutos.  
2. **FIN-SENSE orquestração** (agent, priorização keep/scale/disable) — **política e decisão**.  
3. **Correlações multi-ativo completas** (Granger, copulas, regimes) — **research**, **não** storage.  
4. **Stack institucional completo** (CVA, Euler, multi‑provider obrigatório) — **fases** posteriores.  
5. **Integração profunda** com **OMEGA MT5** (mapeamento de `DEMO_LOG` → `TBL_*`) — **projeto de ingestão** concreto, **próximo sprint** após escolha de **MVP de tabelas**.  
6. **Documentos de handoff** anteriores no repo — **revisão** opcional para **alinhar** linguagem com este **encerramento** de âmbito.

*(Esta lista **fixa** o que fica **fora** do “concluído agora” para **não perder o foco** da bússola.)*

---

## 6. Instruções mínimas ao PSA (pós-arquivo)

1. Tratar **`FIN‑SENSE DATA MODULE.txt`** como **ESPECIFICAÇÃO** aprovada para **dados**.  
2. Qualquer código novo de **ingestão** deve **respeitar** metadados obrigatórios e **não** implementar **métricas de negócio** dentro do mesmo pacote **sem** quebrar a fronteira.  
3. **Antes** de publicar métricas ou relatórios técnicos: **verificar** que os **inputs** estão referenciados por **`ingestion_id`** (ou manifesto) no **catálogo** FIN-SENSE — **não** assumir que “o CSV existe” sem entrada no **índice/manifest**.  
4. **Consolidar OHLCV:** migrar consumo para a **árvore canónica** (secção 3.1); **parar** de alimentar relatórios a partir de `inputs/OHLCV_DATA/grafico_*` sem reconciliação.  
5. **Próximo passo operativo sugerido:** escolher **subconjunto MVP** (ex.: `SECURITIES_MASTER` + `ORDERS` + `EXECUTIONS` + `DATA_PROVENANCE`) e **mapear** para o que **já** existe no OMEGA (`DEMO_LOG`, manifestos); em paralelo, **elevar** `_INDEX.csv` a **catálogo** com hashes conforme `TBL_DATA_PROVENANCE`.  
6. **Tier-0 repo** (`verify`, `psa_gate`) **continua** a reger **artefactos** do projecto actual; o **lake** FIN-SENSE é **camada paralela** quando existir **infra**.

---

## 7. Assinatura de fim de etapa

**Módulo:** FIN-SENSE **DATA MODULE** (especificação v1.0 + addendum operacional v1.1)  
**Estado:** **modelo de trabalho** para **centralização e catalogação** — especificação **encerrada** para **implementação** por fases.  
**Próxima etapa:** **migração física** das pastas OHLCV para o layout canónico + **manifests**; integração OMEGA (fora do detalhe deste documento).

---

*Documento gerado para arquivo junto de `FIN‑SENSE DATA MODULE.txt` e comunicação ao PSA.*
