# FIN-SENSE DATA MODULE — Defesa estratégica, alinhamento institucional e pacote de comprovação

**Para:** Conselho e CEO  
**De:** Consolidação técnica (Núcleo de Validação OMEGA + especificação Conselho)  
**Data:** 27 de março de 2026  
**Classificação:** decisão de investimento em **camada de dados central** — documento de apreciação conjunta  

**Nota de arquivo:** o documento **único** para **execução PSA** (IDs, KPIs, checklist, parâmetros) é `HANDOFF_PSA_INSTRUCOES_FINAIS_20260403.md` (`DOC-HANDOFF-PSA-20260403-UNIFIED`); este ficheiro mantém-se como **anexo de defesa** ao Conselho.

---

## 1. Resposta executiva à pergunta do CEO

**Pergunta:** *O modelo proposto (FIN-SENSE DATA MODULE + documentação derivada) segue o alto padrão descrito nos documentos de referência (Inventário expandido, DDL Parquet/Delta, Scripts Spark SQL Delta-compatible, Diretriz Complementar v2.0, HANDOFF PSA)?*

**Resposta (nível de confiança: alta para coerência lógica; média para verificação ficheiro-a-ficheiro):**

| Camada de referência | Relação com FIN-SENSE DATA MODULE |
|----------------------|-------------------------------------|
| **Inventário Expandido** (lacunas ISIN/FIGI, L2, fills, curvas, métricas institucionais) | **Alinhado como pré-requisito:** o inventário descreve **o que falta** para métricas “de fundo”; o FIN-SENSE DATA MODULE descreve **onde e como** persistir os dados que **tornam** essas métricas **auditáveis**. Sem o módulo de dados, o inventário permanece uma **lista de desejos** sem assento físico. |
| **DDL Parquet/Delta** | **Alinhado em esquema:** as tabelas núcleo (`TBL_MARKET_TICKS_RAW`, `TBL_ORDERS`, `TBL_EXECUTIONS`, `TBL_DATA_PROVENANCE`, …) no `FIN‑SENSE DATA MODULE.txt` são **coerentes** com o tipo de contrato que um DDL Delta formalizaria; o DDL detalhado é **camada seguinte** (DDL por coluna + tipos). |
| **Scripts Spark** (VaR, Euler, CVA, ledger) | **Compatível por separação de responsabilidades:** esses scripts são **consumidores** de tabelas; o DATA MODULE **não** substitui Spark — **fornece** dados versionados e manifests. O HANDOFF já nota que vários SQL são **esboço** e que álgebra pesada pode sair do SQL puro. |
| **Diretriz Complementar v2.0** (não-omissão, interdependências) | **Reforçada:** a fronteira “**armazenar sem calcular métricas de negócio dentro do módulo**” evita que CQO prometa VaR/CVA **sem** CIO ter proveniência; o documento `CONSELHO_FIN_SENSE_DATA_MODULE_FINAL_20260403.md` explicita conflitos **demo vs fundo** e encaminha MVP. |

**Conclusão:** o desenho **não contradiz** o alto padrão institucional; **estrutura-o em camadas**: **(1)** FIN-SENSE DATA MODULE = **substrato**; **(2)** Inventário/DDL/Scripts = **alvo analítico e receitas**; **(3)** OMEGA Tier-0 = **custódia actual** até migração.

**Limitação declarada:** na data desta revisão, a pasta `Auditoria Conselho/` no disco continha **apenas** `FIN‑SENSE DATA MODULE.txt`. Os ficheiros nomeados *Inventário Expandido…*, *DDL em estilo Parquet Delta…* e *Scripts Spark SQL…* **constam** do `HANDOFF_PSA_INSTRUCOES_FINAIS_20260403.md` como referência, mas **não foram encontrados** no workspace com esses nomes — a defesa baseia-se na **descrição** no HANDOFF e no texto integral do FIN-SENSE. **Recomendação:** colocar os três ficheiros na pasta Conselho ou anexar hashes para auditoria cruzada.

---

## 2. Auto-análise dos documentos gerados (rastreabilidade interna)

| Artefacto | Função | Avaliação crítica |
|-----------|--------|-------------------|
| `CONSELHO_FIN_SENSE_DATA_MODULE_FINAL_20260403.md` (v1.1) | Fecha **especificação** do módulo DATA; motivação PSA; layout bronze/silver/gold; pendências | **Forte** em âmbito e anti-deriva OHLCV; **não** substitui implementação nem prova de cluster. |
| `HANDOFF_PSA_INSTRUCOES_FINAIS_20260403.md` | Ponte **Tier-0 ↔ roadmap fundo**; Diretriz v2.0; lacunas vs OMEGA | **Forte** em honestidade (métricas institucionais sem dados = não validáveis); deve manter-se **sincronizado** com ficheiros reais em `Auditoria Conselho/`. |
| `FIN‑SENSE DATA MODULE.txt` | Norma de tabelas, ingestão, QC mínimo, APIs de leitura | **Forte** como **single source of truth** lógica; próximo passo é **DDL versionado** + **schema registry**. |

**Risco residual:** dispersão semântica se **FIN-SENSE sensorial** (classificação de padrões) for misturado com **FIN-SENSE DATA** — mitigado pela lista de pendências no documento v1.1.

---

## 3. Defesa da implementação (porquê agora, porquê desta forma)

### 3.1 Problema de negócio (sem dados catalogados não há prova)

Conforme alinhamento CEO: relatórios e métricas do PSA **perderam credibilidade** quando o **histórico exigido** não estava **persistido e catalogado** com **ingestion_id** e **manifesto**. Isso não é falha de “mais gráficos” — é falha de **cadeia de custódia de dados**.

### 3.2 Tese central

Implementar o **FIN-SENSE DATA MODULE** é **criar o direito de falar em validação**: qualquer número apresentado ao Conselho deve poder ser **ligado** a **linhas armazenadas**, **versão de esquema**, **origem** e **janela temporal** — condição **necessária** (não suficiente) para métricas institucionais do Inventário.

### 3.3 O que **não** resolve sozinho

- **VaR/CVA/attribution completos** — exigem **modelos** e **dados** além do MVP (o módulo **habilita**, não substitui CQO).  
- **Paridade com fundo** — exige **infra** e **feeds**; o módulo é **compatível** com essa evolução.  

---

## 4. Métricas de sucesso (KPIs) — definições operacionais

Objetivo: **comprovar** que o módulo cumpre **integridade**, **cobertura** e **reprodutibilidade**. Todas são **mensuráveis** sobre artefactos (ficheiros, tabelas, manifests).

| ID | Métrica | Definição | Meta sugerida (pós-MVP) |
|----|---------|-----------|-------------------------|
| **KPI-01** | **Provenance Attach Rate (PAR)** | \(\frac{\#\ \text{linhas com ingestion_id não nulo}}{\#\ \text{linhas}}\) em tabelas núcleo | \(\geq 0{,}999\) |
| **KPI-02** | **Identifier Completeness (IC)** | \(\frac{\#\ \text{linhas com (FIGI ou ISIN ou symbol+exchange)}}{\#\ \text{linhas}}\) | \(\geq 0{,}99\) (ativo por classe) |
| **KPI-03** | **Time Consistency Rate (TCR)** | \(\frac{\#\ \text{linhas onde } source\_ts \leq recv\_ts + \Delta}{\#\ \text{linhas}}\) | \(\geq 0{,}995\) com \(\Delta\) definido no SLA |
| **KPI-04** | **Manifest Hash Match (MHM)** | \(\frac{\#\ \text{manifests com hash verificado}}{\#\ \text{manifests}}\) | \(1{,}0\) em ingestões oficiais |
| **KPI-05** | **Dedup Residual Rate (DRR)** | \(\frac{\#\ \text{duplicados detectados post-ingest}}{\#\ \text{linhas}}\) | \(\leq 10^{-6}\) |
| **KPI-06** | **Catalog Coverage (CC)** | Para cada relatório PSA, fração de **símbolos/timeframes** referenciados que existem no **catálogo** com manifest | \(1{,}0\) antes de publicação |
| **KPI-07** | **Schema Version Discipline (SVD)** | Ingestões de produção **só** com `schema_version` registado e compatível | \(100\%\) |

**Nota:** KPI-06 endereça **directamente** o problema CEO (métricas sem dados subjacentes catalogados).

---

## 5. Especificação técnica das métricas (para auditoria)

### 5.1 PAR, IC, TCR

- **Entrada:** conjunto de linhas \(R\) após ingestão.  
- **Predicados:**  
  - `has_ingestion_id(r) := ingestion_id is not null`  
  - `has_id(r) := figi validado OU isin validado OU (symbol AND exchange)`  
  - `time_ok(r) := source_ts <= recv_ts + allowed_skew`  

\[
\text{PAR} = \frac{|\{r \in R : \text{has\_ingestion\_id}(r)\}|}{|R|}
\]

(análogo para IC e TCR).

### 5.2 MHM

- Para cada manifest \(m\), `expected_hash = m.file_hash` (ou Merkle root); recomputar a partir de ficheiros listados; **MHM = 1** sse todos coincidem.

### 5.3 DRR

- Após deduplicação por chave \((source, trade\_id)\) ou equivalente, contar colisões residuais em janela deslizante.

### 5.4 CC (relatório vs catálogo)

- Seja \(S\) o conjunto de pares `(symbol, timeframe)` citados no relatório; seja \(C\) o conjunto no `_INDEX` ou metadastore; **CC = |S ∩ C| / |S|**.

---

## 6. Código de referência (Python)

Foi criado o ficheiro:

`04_relatorios_tarefa/finsense_validation_kit.py`

Contém funções **determinísticas** para:

- cálculo de hash SHA-256 de ficheiros (alinhável a manifestos Tier-0);  
- avaliação de PAR, IC, TCR sobre `list[dict]` ou CSV simples;  
- validação estrutural mínima de manifest JSON;  
- relatório textual para anexar a auditorias.

**Fronteira:** este código **não** implementa VaR/CVA; **comprova** integridade e consistência do **módulo de dados** e dos **manifests**.

---

## 7. Fragmento C++ (opcional — verificação de integridade)

Para sistemas de baixa latência ou bibliotecas nativas, o mesmo contrato de integridade pode usar **SHA-256** sobre buffers de ingestão antes de persistir. O kit Python permanece a **referência canónica** no ecossigma OMEGA actual (Python + MT5); C++ é **opcional** e **não** foi adicionado ao repo sem decisão de build — a especificação do algoritmo é **SHA-256 (FIPS 180-4)** sobre o conteúdo canónico serializado (UTF-8, timestamps UTC ISO8601).

---

## 8. Diretriz Complementar v2.0 — registo de não omissão

| Tema | Declaração |
|------|------------|
| **Demo vs fundo** | O FIN-SENSE DATA MODULE **não** afirma paridade com fundo; **prepara** o caminho. |
| **CQO vs CTO** | Métricas pesadas **requerem** dados **e** compute; o módulo **remove** a desculpa “não temos onde persistir”. |
| **CIO vs CQO** | Sem **TBL_DATA_PROVENANCE** e **QC**, “rastreável” é **fraco**; o desenho **inclui** ambos. |
| **PSA** | Deve **ligar** cada relatório a **ingestion_id** / manifest — KPI-06. |

---

## 9. Próximos passos recomendados ao Conselho

1. **Aprovar** o FIN-SENSE DATA MODULE como **norma de dados** para novas ingestões.  
2. **Exigir** cópia física dos três documentos (Inventário, DDL, Scripts) em `Auditoria Conselho/` **ou** registo de versão + hash.  
3. **Mandatar** MVP: `SECURITIES_MASTER` (mínimo) + `ORDERS` + `EXECUTIONS` + `DATA_PROVENANCE` + catálogo OHLCV unificado.  
4. **Medir** KPI-01–KPI-07 trimestralmente até estabilização.

---

## 10. Assinatura técnica

Este documento foi elaborado para **apreciação conjunta** com o `FIN‑SENSE DATA MODULE.txt` e os artefactos listados na secção 2. **Não** substitui validação em ambiente de produção; **define** critérios e instrumentos para **comprovar** o objectivo de **dados centralizados, auditáveis e reprodutíveis**.

---

*Documento completo para o Conselho — 27/03/2026.*
