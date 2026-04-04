# Documento Oficial — Ciência PSA e Arquivo Histórico de Execuções (FIN-SENSE)

| Campo | Valor |
|--------|--------|
| **ID do documento** | `DOC-OFC-CIENCIA-ARQUIVO-HISTORICO-PSA-FINSENSE-20260404-003` |
| **Versão** | 1.0 |
| **Data** | 4 de abril de 2026 |
| **Classificação** | Obrigatório — Arquivo institucional / Continuidade PSA |
| **Destinatário** | Principal Solution Architect (PSA) e sucessores designados |
| **Âmbito** | Todo o ciclo FIN-SENSE DATA MODULE: violação de mandato, integração, desvio estrutural, realinhamento, verificações |

---

## 1. Finalidade

Este documento existe para que o **PSA** (e qualquer sucessor) tenha **ciência formal** de **tudo o que foi executado** no workspace em relação ao **FIN-SENSE DATA MODULE**, de modo que:

1. As decisões e movimentações **façam parte do histórico** auditável do sistema.
2. **Não** haja lacunas que, no futuro, levem a **recriar duplicados**, **caminhos incorrectos** ou **políticas contraditórias** (por exemplo, código definitivo novamente em **Auditoria Conselho** ou na **raiz** em vez de `modules\`).
3. A **continuidade operacional** e a **integridade da informação** fiquem protegidas face a rotação de equipa ou revisões externas.

A ausência deste registo no arquivo de governança é considerada **risco de governança**: deve ser **indexada**, **versionada** no repositório remoto (GitHub ou equivalente) e **referenciada** em auditorias.

---

## 2. Inventário de documentos oficiais (cadeia completa)

Todos os ficheiros abaixo residem em:

`C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\governance\`

| Ordem | ID | Conteúdo essencial |
|-------|-----|-------------------|
| 1 | `DOC-OFC-VIOLACAO-REGRA-CEO-INTEGRACAO-FINSENSE-PSA-20260327-001` | Registo de criação de código sem ordem explícita do CEO; regras de recepção pelo PSA. |
| 2 | `DOC-OFC-CONCLUSAO-INTEGRACAO-FINSENSE-PSA-20260404-001` | Conclusão de integração PSA; **addendum (secção 7)** corrige caminho relativamente à raiz — ver par 002. |
| 3 | `DOC-OFC-DESVIO-PADRAO-ESTRUTURAL-MODULES-FINSENSE-20260404-002` | Divergência: código em raiz / Auditoria; dados dispersos; padrão `modules` + `FIN_SENSE_DATA`. |
| 4 | `DOC-OFC-RESOLUCAO-REALINHAMENTO-FINSENSE-20260404-002` | Resolução com **evidências em log** (GATE_GLOBAL, ingestão demo, `HUB_ROOT`). |
| 5 | **`DOC-OFC-CIENCIA-ARQUIVO-HISTORICO-PSA-FINSENSE-20260404-003`** | **Este ficheiro** — síntese para arquivo e ciência PSA. |

Índice auxiliar: `governance\README.md`.

---

## 3. Registo cronológico do que foi executado (factos)

*Nota: descrição factual das acções realizadas na sequência de trabalho; não substitui logs de CI/CD nem commits Git.*

### Fase A — Materialização inicial (contexto histórico)

- Foi criado um **pacote Python** `fin_sense_data_module` (schema v1.2, 23 tabelas, storage, ingestor, stubs por camada), inicialmente fora do padrão final de pastas.
- Foi gerado documento de **violação de mandato** (`...20260327-001`) por criação de código sem ordem explícita do CEO.

### Fase B — Integração declarada pelo processo PSA

- Foi produzida **conclusão de integração** (`...20260404-001`), posteriormente complementada por **addendum** quando se clarificou o caminho canónico.

### Fase C — Realinhamento estrutural

- **Consolidado** o código SSOT em:  
  `nebular-kuiper\modules\FIN_SENSE_DATA_MODULE\`
- **Removidas** duplicatas em:  
  `nebular-kuiper\FIN_SENSE_DATA_MODULE\` (raiz do workspace)  
  `nebular-kuiper\Auditoria PARR-F\Auditoria Conselho\FIN_SENSE_DATA_MODULE\`
- **Unificados** dados de hub sob:  
  `nebular-kuiper\FIN_SENSE_DATA\hub\`  
  (incluindo merge de conteúdo previamente sob `Auditoria Conselho\data\hub`, quando existia).
- **Reposicionados** os documentos `DOC-OFC-*.md` de **Auditoria Conselho** para **`governance\`**.
- **Eliminados** da pasta **Auditoria Conselho** os scripts duplicados (`validate_hub_integrity.py`, `ingest_demo_to_bronze.py`) em favor dos scripts canónicos no pacote.
- **Criados** scripts oficiais em:  
  `modules\FIN_SENSE_DATA_MODULE\scripts\validate_hub_integrity.py`  
  `modules\FIN_SENSE_DATA_MODULE\scripts\ingest_demo_to_bronze.py`  
  (ingestão apontando para `FIN_SENSE_DATA\hub`).
- **Definida** política escrita: `Auditoria PARR-F\Auditoria Conselho\LEIA-ME-AUDITORIA-CONSELHO.md` (apenas trânsito).

### Fase D — Verificação pós-realinhamento

- Execução de `pip install -e .` a partir de `modules\FIN_SENSE_DATA_MODULE`.
- `python scripts/validate_hub_integrity.py` → **GATE_GLOBAL: PASS** (23 tabelas).
- `python scripts/ingest_demo_to_bronze.py` → escrita demo em `FIN_SENSE_DATA\hub\...` com manifesto.

---

## 4. Tabela de localização canónica (referência única)

| Artefacto | Caminho canónico |
|-----------|------------------|
| Código-fonte do módulo (SSOT) | `...\nebular-kuiper\modules\FIN_SENSE_DATA_MODULE\` |
| Dados / lake local (hub Bronze demo, etc.) | `...\nebular-kuiper\FIN_SENSE_DATA\` |
| Governança e histórico documental | `...\nebular-kuiper\governance\` |
| Outros módulos Python do sistema | `...\nebular-kuiper\modules\` (ficheiros `.py` legados + pasta `FIN_SENSE_DATA_MODULE`) |
| Auditoria Conselho | **Apenas** documentação em trânsito — **não** SSOT |

---

## 5. Objectivo do módulo (registo imutável para arquivo)

O **FIN-SENSE DATA MODULE** existe para:

1. **Centralizar** formatos de dados num **contrato único** (schema **v1.2**, **23 tabelas**).
2. **Servir** research, execução e relatórios (incl. linha CEO) com **APIs e schema estáveis**.
3. Manter-se **expansível** e **independente** de um único conector ou motor de análise, com evolução por versão de schema.

Qualquer alteração futura que contradiga estes três pontos deve ser **deliberada**, **documentada** com novo `DOC-OFC-*` e **revisada** pelo PSA.

---

## 6. Obrigações do PSA (continuidade)

1. Garantir que este documento e os referidos no par. 2 estão **no repositório remoto** e **tagged** ou referenciados em release notes quando aplicável.
2. Em **onboarding** de novos arquitetos ou fornecedores, incluir **leitura obrigatória** deste ficheiro e do `README.md` em `governance\`.
3. Em **pull requests** que toquem em `FIN_SENSE` ou `modules`, validar que **não** se reintroduzem cópias na raiz ou em **Auditoria Conselho**.
4. Em **auditoria**, apresentar a cadeia **001 → 002 (desvio + resolução) → 003 (este arquivo)** como prova de trilho.

---

## 7. Risco de não arquivo

Se o PSA **não** mantiver este conjunto indexado:

- Pode haver **recriação de pastas duplicadas** e **deriva de versões**.
- Pode haver **confidencialidade** ou **dados** colocados em pastas de **trânsito** sem política.
- Pode haver **perda de contexto** legal ou operacional em litígio ou due diligence.

---

## 8. Declaração de encerramento

O presente documento **consolida** o conhecimento necessário para **ciência PSA** e **arquivo histórico** das execuções relacionadas ao FIN-SENSE DATA MODULE até a data indicada no cabeçalho. Deve ser **preservado** e **actualizado** apenas mediante novo `DOC-OFC-*` que referencie explicitamente este ID como predecessor.

**Fim do documento `DOC-OFC-CIENCIA-ARQUIVO-HISTORICO-PSA-FINSENSE-20260404-003`.**
