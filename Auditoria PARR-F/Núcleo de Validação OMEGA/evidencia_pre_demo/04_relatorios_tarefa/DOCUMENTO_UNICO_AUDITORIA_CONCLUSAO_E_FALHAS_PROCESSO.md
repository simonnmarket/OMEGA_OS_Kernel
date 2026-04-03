# Documento único — Auditoria de conclusão, provas e falhas de processo

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-AUD-CONCLUSAO-PROCESSO-20260403` |
| **Versão** | 1.3 |
| **Tipo** | Auditoria **objectiva** — distingue **prova** de **reconfirmação narrativa** |
| **Auditor** | Núcleo de Validação OMEGA (gerado com verificação de artefactos no disco) |
| **Para** | PSA — **executar** instruções §7 antes de avançar fases |
| **Normas** | `DOC-UNICO-PSA-MESTRE-20260403`, `DOC-OFC-PSA-PROVAS-AUD-20260403`, `DOC-OFC-MODELO-TAR-20260403` |

---

## 1. Regra de leitura (anti-subjectividade)

| Estado | Significado | Exige |
|--------|-------------|--------|
| **CONCLUÍDO_COM_PROVA** | Artefacto existe + identificador + rastreio reprodutível | Path, hash ou output de comando registado |
| **PARCIAL_COM_PROVA** | Parte entregue; gate da fase **não** fechado | Lista do que falta |
| **PENDENTE** | Solicitado, sem artefacto ou sem PRF válido | — |
| **NÃO_EXECUTADO** | Fase posterior não iniciada | — |
| **FALHA_DE_PROCESSO** | Narrativa ou “PASS” **sem** validação automática ou com **incoerência de IDs** | Ver §6 |

**Proibição:** tratar texto de conclusão (`DECLARACAO_*`) como prova **sem** cruzar com ficheiros e `--validate` em JSONs de prova.

---

## 2. Evidências materiais verificadas (snapshot do repositório)

| Verificação | Resultado | Evidência |
|-------------|-----------|-----------|
| `INVENTARIO_FONTES_DADOS_v1.csv` existe | **SIM** | ≥10 linhas de dados (INV-001…010) |
| `PSA_RUN_LOG.jsonl` | **SIM** | ≥11 linhas JSON; inclui `file_saved` / `prf_validated` / `phase_complete` **PH-FS-03** (`run_id` `PS-20260403-PH-FS-03-fd64467`) |
| `CATALOGO_OHLCV_PLANO_v1.md` | **SIM** | §4 declara **KPI-06 PENDENTE** (não afirma 1,0 medido) — **F4** formal no plano |
| `prova_PRF-PHFS02-20260403-001.json` | **CORRIGIDO → PASS** | Inicialmente `REQ-PHFS02-001` era **inválido** para o regex do validador; após **`REQ-UNICO-030`**, `--validate` → **exit 0** |
| `MAP-DEMO-TBL_v1.md` | **SIM** | `DOC-MAP-DEMO-TBL-20260403`; mapeamento `TBL_ORDERS` / `TBL_EXECUTIONS` |
| `prova_PRF-PHFS03-20260403-001.json` | **PASS** (após correcção **F6**) | `--validate` → **exit 0**; campo `git_head` **corrigido** para **`fd64467…`** (commit inválido `c3ea3be41…` não existia no repo) |
| `_INDEX.csv` com colunas `ingestion_id`, `file_hash` | **NÃO VERIFICADO** | Plano **declara** obrigatoriedade; **não** há prova de ficheiro `_INDEX` já migrado neste audit |
| `git rev-parse HEAD` (repo) | **`fd64467f696362acf5cf519ecf94c59f38bf3fc9`** | Commit mensagem: *DECISAO: Conclusao de TAR-PHFS03-001…*; alinhado a `MANIFEST_RUN_20260329.json` → `git_commit_sha` |
| `PSA_GATE_CONSELHO_ULTIMO.txt` HEAD (snapshot) | **`fd64467f696362acf5cf519ecf94c59f38bf3fc9`** | Lido em verificação: alinhado ao HEAD actual |
| `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` | **PARCIAL** | Linhas **PH-FS-02** e **PH-FS-03** (`SOL-20260403-002`, `DEC-20260403-002`); outras fases sem linha |

**Conclusão imediata:** **PH-FS-03** entregue: `MAP-DEMO-TBL_v1.md`, PRF **`REQ-UNICO-040`** com `--validate` PASS, matriz + DEC-002, manifesto com `git_commit_sha` = **fd64467…**, gate com mesmo HEAD. **F6:** PRF PH-FS-03 continha `git_head` **inexistente** no Git — **corrigido** para o commit real. **PH-FS-02** permanece **PARCIAL** (KPI-06 até `KPI_REPORT`).

---

## 3. Mapa de fases (roteiro oficial) — estado

**Ordem:** `0 → PH-FS-01 → PH-FS-02 → PH-FS-03 → PH-FS-04 → PH-TR-01 → PH-PS-01`

| Fase | Estado global | Prova mínima exigida pelo roteiro | Situação |
|------|---------------|-----------------------------------|----------|
| **0** | **CONCLUÍDO_COM_PROVA** | `STATUS_ANEXOS_CONSELHO.md` | Presente |
| **PH-FS-01** | **CONCLUÍDO_COM_PROVA** | CSV inventário + `PSA_RUN_LOG` + certificado | Ficheiros presentes; **nota:** paths no inventário são **parciais** (ex. `01_raw_mt5/...`) — ficheiros existem sob `evidencia_pre_demo/01_raw_mt5/` mas **não** batem certo com path relativo único sem convenção explícita → **risco de rastreio** |
| **PH-FS-02** | **PARCIAL_COM_PROVA** | `CATALOGO_OHLCV_PLANO_v1.md` + KPI-06 **testável** ou **PENDENTE** explícito | Plano **existe**; §4 **declara KPI-06 PENDENTE** (sem afirmação 1,0); **medição** continua **pendente** até `KPI_REPORT`; PRF JSON **`PASS`** (`REQ-UNICO-030`) |
| **PH-FS-03** | **CONCLUÍDO_COM_PROVA** | `MAP-DEMO-TBL_v1.md` + PRF + matriz + DEC | `prova_PRF-PHFS03-20260403-001.json` PASS; `DOC-MAP-DEMO-TBL-20260403` |
| **PH-FS-04** | **NÃO_EXECUTADO** | `run_kpi_batch.py` + `KPI_REPORT_*.json` | Script checklist existe; batch KPI **não** entregue |
| **PH-TR-01** | **PARCIAL** | Gate + verify OK **no âmbito** | `PSA_GATE` presente; reexecutar após cada alteração |
| **PH-PS-01** | **NÃO_EXECUTADO** | `RPT-PILOTO-*` com cabeçalho | Ausente |

---

## 4. Checklist por procedimento (binário onde possível)

### A. Documentação normativa (geração / fusão)

| ID | Procedimento | Estado | Prova | Falha se ausente |
|----|--------------|--------|-------|------------------|
| CP-DOC-01 | `DOCUMENTO_UNICO_PSA_MESTRE` existir | CONCLUÍDO_COM_PROVA | Ficheiro `.md` | — |
| CP-DOC-02 | `DOCUMENTO_OFICIAL_PSA_PROVAS` existir | CONCLUÍDO_COM_PROVA | Ficheiro | — |
| CP-DOC-03 | `DOCUMENTO_OFICIAL_MODELO_SOL_TAR_DEC` existir | CONCLUÍDO_COM_PROVA | Ficheiro | — |
| CP-DOC-04 | Matriz SOL/TAR preenchida até decisão | **PARCIAL** | Linhas PH-FS-02 e PH-FS-03 | Fecho total **após** PH-FS-04 / PH-TR / PH-PS |

### B. Dados e inventário (PH-FS-01)

| ID | Procedimento | Estado | Prova | Nota |
|----|--------------|--------|-------|------|
| CP-FS01-01 | 10 linhas inventário | CONCLUÍDO_COM_PROVA | CSV | — |
| CP-FS01-02 | Cada linha com `dependency_status` | CONCLUÍDO_COM_PROVA | CSV | — |
| CP-FS01-03 | Paths resolvíveis no repo | PARCIAL | Alguns paths são relativos sem raiz única documentada | **Falha leve de rastreio** |

### C. PH-FS-02 (catálogo)

| ID | Procedimento | Estado | Prova | Falha |
|----|--------------|--------|-------|-------|
| CP-FS02-01 | Plano MD existe | CONCLUÍDO_COM_PROVA | `CATALOGO_OHLCV_PLANO_v1.md` | — |
| CP-FS02-02 | PRF JSON válido pelo script | **CONCLUÍDO_COM_PROVA** (após correção) | `--validate` → **PASS** com `REQ-UNICO-030` | Alinhar `MATRIZ_*` ao mesmo `req_id` |
| CP-FS02-03 | KPI-06 medido **ou** PENDENTE formal | **PARCIAL_COM_PROVA** | Plano §4: **KPI-06 PENDENTE**; medição numérica **ainda** sem `KPI_REPORT` | — |

### D. Provas REQ/PRF (regime anti-subjetividade)

| ID | Procedimento | Estado | Prova |
|----|--------------|--------|-------|
| CP-PRF-01 | Toda PRF passa `--validate` | **PASS** | `prova_PRF-PHFS02-…` e `prova_PRF-PHFS03-20260403-001.json` |
| CP-PRF-02 | `DEC-*` emitido por tarefa | **PARCIAL** | `DEC-20260403-001` (PH-FS-02); `DEC-20260403-002` (PH-FS-03) |

### E. PH-FS-03 (mapa demo)

| ID | Procedimento | Estado | Prova |
|----|--------------|--------|-------|
| CP-FS03-01 | `MAP-DEMO-TBL_v1.md` existe | **CONCLUÍDO_COM_PROVA** | Ficheiro em `04_relatorios_tarefa/` |
| CP-FS03-02 | PRF PH-FS-03 + `git_head` resolvível | **CONCLUÍDO_COM_PROVA** (pós-F6) | `git cat-file -t fd64467…` = commit |

---

## 5. Onde o processo falhou (diagnóstico causal)

| # | Fenómeno | Causa provável | Acção corretiva (PSA) |
|---|----------|----------------|------------------------|
| **F1** | Reconfirmações em vez de provas | Documentos descrevem o que “deveria” estar feito | Exigir **PRF PASS** + artefacto antes de “concluído” |
| **F2** | `req_id` inválido no JSON | Formato `REQ-PHFS02-001` **não** compatível com regex `REQ-[A-Z]+-\\d{3}` (dígitos no meio) | **Aplicado:** `REQ-UNICO-030` — validador **PASS** |
| **F3** | HEAD múltiplos | Commits entre geração de artefactos | **Registo** `head_reconciled_post_commit` → **`c3ea3be…`** no `PSA_RUN_LOG.jsonl`; **reexecutar** `PSA_GATE` para alinhar ficheiro gate ao HEAD |
| **F4** | KPI-06 “1.0” no plano | Confundiu **desenho** com **medição** | **Mitigado:** §4 catálogo = **PENDENTE** até `KPI_REPORT` |
| **F5** | Matriz SOL/TAR estagnada | `proof_id`/`dec_id` vazios | Preencher após PRF válido e decisão |
| **F6** | `git_head` inválido na PRF PH-FS-03 | Hex **não** correspondia a commit no repo (`git cat-file` falhou) | **Corrigido** para **`fd64467…`**; validar sempre com `git rev-parse HEAD` antes de selar PRF |

---

## 6. Instruções obrigatórias para o PSA (antes de prosseguir)

1. ~~**Corrigir** `req_id` na PRF~~ — **feito:** `REQ-UNICO-030`; `python psa_refutation_checklist.py --validate …` → **exit 0**.

2. **Opcional:** alargar o validador para aceitar `REQ-PHFS02-001` (mudança de código = novo commit + PRF a referir o commit).

3. **Não** declarar PH-FS-02 **CONCLUÍDA** (100 %) até: ~~PRF válido~~ **OK**; ~~plano com KPI-06 explícito~~ **OK** (§4 **PENDENTE**); **ainda** falta **valor** de CC em `KPI_REPORT` para fecho métrico.

4. ~~**Actualizar** matriz com `proof_id`~~ — **feito**; notas actualizadas (F3/F4).

5. ~~**Registar** `audit_record` + **`head_reconciled_post_commit`**~~ — **feito** v1.2 (linhas com `c3ea3be…`).

6. ~~**PH-FS-03**~~ — **feito** (com correcção **F6** em `git_head`).

7. **Próxima fase executável:** **PH-FS-04** — `run_kpi_batch.py` (ou equivalente) + **`KPI_REPORT_*.json`**; nova PRF; linha na matriz; registo no `PSA_RUN_LOG.jsonl`.

---

## 7. Tabela-resumo executiva (envio Conselho)

| Dimensão | Veredicto |
|----------|-----------|
| **Documentação normativa** | Gerada e presente — **PROVA OK** |
| **PH-FS-01** | **CONCLUÍDO_COM_PROVA** (com ressalva de paths) |
| **PH-FS-02** | **PARCIAL** — §4 **KPI-06 PENDENTE** até `KPI_REPORT` |
| **PH-FS-03** | **CONCLUÍDO_COM_PROVA** — `MAP-DEMO-TBL_v1.md`, PRF PASS, `DEC-20260403-002` |
| **Fases PH-FS-04+** | **PH-FS-04 NÃO_EXECUTADO** (batch KPI / relatório) |
| **Processo SOL/TAR/DEC** | **PARCIAL** (duas linhas: PH-FS-02, PH-FS-03) |
| **Risco global** | Sempre cruzar **`git_head`** da PRF com `git rev-parse` (**F6**) |

---

## 8. Fecho

Este documento **não** “reprova” o trabalho global — **localiza** falhas **verificáveis** na cadeia **prova → validador → decisão**. **PH-FS-03** aceite com prova; **F6** documenta **obrigatoriedade** de `git_head` verificável. Próximo passo: **PH-FS-04** (métricas) mantendo **PH-FS-02** em **PARCIAL** até `KPI_REPORT`.

---

*Fim — `DOC-AUD-CONCLUSAO-PROCESSO-20260403` — v1.3: PH-FS-03 fechado; F6; `PSA_RUN_LOG` PH-FS-03; gate/manifesto alinhados a **fd64467…**.*
