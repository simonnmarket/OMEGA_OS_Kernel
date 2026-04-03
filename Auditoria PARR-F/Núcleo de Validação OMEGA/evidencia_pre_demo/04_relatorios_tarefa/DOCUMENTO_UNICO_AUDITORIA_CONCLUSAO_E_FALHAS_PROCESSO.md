# Documento único — Auditoria de conclusão, provas e falhas de processo

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-AUD-CONCLUSAO-PROCESSO-20260403` |
| **Versão** | 1.2 |
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
| `PSA_RUN_LOG.jsonl` | **SIM** | ≥8 linhas JSON; inclui `audit_record` v1.1/v1.2 e **`head_reconciled_post_commit`** com `canonical_head` **`c3ea3be…`** |
| `CATALOGO_OHLCV_PLANO_v1.md` | **SIM** | §4 declara **KPI-06 PENDENTE** (não afirma 1,0 medido) — **F4** formal no plano |
| `prova_PRF-PHFS02-20260403-001.json` | **CORRIGIDO → PASS** | Inicialmente `REQ-PHFS02-001` era **inválido** para o regex do validador; após **`REQ-UNICO-030`**, `--validate` → **exit 0** |
| `_INDEX.csv` com colunas `ingestion_id`, `file_hash` | **NÃO VERIFICADO** | Plano **declara** obrigatoriedade; **não** há prova de ficheiro `_INDEX` já migrado neste audit |
| `git rev-parse HEAD` (repo) | **`c3ea3befa954b6ca41b1422317e4e277a0f533d1`** | Verificado por comando; alinhado a linha `head_reconciled_post_commit` no `PSA_RUN_LOG.jsonl` |
| `PSA_GATE_CONSELHO_ULTIMO.txt` HEAD (snapshot ficheiro) | **6a746b53b62e4d366ed741c9ec4dc27930327359** | **Desalinhado** do HEAD actual — **reexecutar** gate após commits para actualizar o ficheiro; `verify_tier0` pode falhar por artefactos em falta (ex.: `prova_TEMPLATE_PREENCHER.json`) |
| `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` | **PARCIAL** | Linha PH-FS-02 com `proof_id` e `DEC-*`; **`req_id`** deve coincidir com a PRF (**`REQ-UNICO-030`**) |

**Conclusão imediata:** **F2** fechado (PRF `--validate` PASS). **F4** (narrativa 1,0) **neutralizado no plano:** §4 do catálogo fixa **KPI-06 PENDENTE** até `KPI_REPORT`. **F3:** linha **`head_reconciled_post_commit`** registada no log com **`c3ea3be…`** (prova objectiva acrescentada na v1.2 onde faltava). **Risco residual:** `PSA_GATE_ULTIMO.txt` e HEAD de PRFs antigas **não** coincidem todos com o HEAD actual — esperado até novo gate limpo; não confundir “HEAD no log” com “gate PASS”.

---

## 3. Mapa de fases (roteiro oficial) — estado

**Ordem:** `0 → PH-FS-01 → PH-FS-02 → PH-FS-03 → PH-FS-04 → PH-TR-01 → PH-PS-01`

| Fase | Estado global | Prova mínima exigida pelo roteiro | Situação |
|------|---------------|-----------------------------------|----------|
| **0** | **CONCLUÍDO_COM_PROVA** | `STATUS_ANEXOS_CONSELHO.md` | Presente |
| **PH-FS-01** | **CONCLUÍDO_COM_PROVA** | CSV inventário + `PSA_RUN_LOG` + certificado | Ficheiros presentes; **nota:** paths no inventário são **parciais** (ex. `01_raw_mt5/...`) — ficheiros existem sob `evidencia_pre_demo/01_raw_mt5/` mas **não** batem certo com path relativo único sem convenção explícita → **risco de rastreio** |
| **PH-FS-02** | **PARCIAL_COM_PROVA** | `CATALOGO_OHLCV_PLANO_v1.md` + KPI-06 **testável** ou **PENDENTE** explícito | Plano **existe**; §4 **declara KPI-06 PENDENTE** (sem afirmação 1,0); **medição** continua **pendente** até `KPI_REPORT`; PRF JSON **`PASS`** (`REQ-UNICO-030`) |
| **PH-FS-03** | **NÃO_EXECUTADO** | `MAP-DEMO-TBL_v1.md` | Ausente (não encontrado) |
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
| CP-DOC-04 | Matriz SOL/TAR preenchida até decisão | **PARCIAL** | Linha PH-FS-02 com `proof_id`/`dec_id`; `req_id` alinhado a PRF | Fecho total **após** todas as fases com linhas por TAR |

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
| CP-PRF-01 | Toda PRF passa `--validate` | **PASS** (pós-correcão F2) | `prova_PRF-PHFS02-20260403-001.json` |
| CP-PRF-02 | `DEC-*` emitido por tarefa | **PARCIAL** | `DEC-20260403-001` na linha PH-FS-02; outras TARs sem linha |

---

## 5. Onde o processo falhou (diagnóstico causal)

| # | Fenómeno | Causa provável | Acção corretiva (PSA) |
|---|----------|----------------|------------------------|
| **F1** | Reconfirmações em vez de provas | Documentos descrevem o que “deveria” estar feito | Exigir **PRF PASS** + artefacto antes de “concluído” |
| **F2** | `req_id` inválido no JSON | Formato `REQ-PHFS02-001` **não** compatível com regex `REQ-[A-Z]+-\\d{3}` (dígitos no meio) | **Aplicado:** `REQ-UNICO-030` — validador **PASS** |
| **F3** | HEAD múltiplos | Commits entre geração de artefactos | **Registo** `head_reconciled_post_commit` → **`c3ea3be…`** no `PSA_RUN_LOG.jsonl`; **reexecutar** `PSA_GATE` para alinhar ficheiro gate ao HEAD |
| **F4** | KPI-06 “1.0” no plano | Confundiu **desenho** com **medição** | **Mitigado:** §4 catálogo = **PENDENTE** até `KPI_REPORT` |
| **F5** | Matriz SOL/TAR estagnada | `proof_id`/`dec_id` vazios | Preencher após PRF válido e decisão |

---

## 6. Instruções obrigatórias para o PSA (antes de prosseguir)

1. ~~**Corrigir** `req_id` na PRF~~ — **feito:** `REQ-UNICO-030`; `python psa_refutation_checklist.py --validate …` → **exit 0**.

2. **Opcional:** alargar o validador para aceitar `REQ-PHFS02-001` (mudança de código = novo commit + PRF a referir o commit).

3. **Não** declarar PH-FS-02 **CONCLUÍDA** (100 %) até: ~~PRF válido~~ **OK**; ~~plano com KPI-06 explícito~~ **OK** (§4 **PENDENTE**); **ainda** falta **valor** de CC em `KPI_REPORT` para fecho métrico.

4. ~~**Actualizar** matriz com `proof_id`~~ — **feito**; notas actualizadas (F3/F4).

5. ~~**Registar** `audit_record` + **`head_reconciled_post_commit`**~~ — **feito** v1.2 (linhas com `c3ea3be…`).

6. **Próxima fase executável:** emitir **SOL/TAR** para **PH-FS-03** (`MAP-DEMO-TBL_v1.md`) + **PRF** nova + `--validate`; **opcional:** corrigir ficheiros em falta no manifesto e **reexecutar** gate para alinhar `PSA_GATE_CONSELHO_ULTIMO.txt` ao HEAD.

---

## 7. Tabela-resumo executiva (envio Conselho)

| Dimensão | Veredicto |
|----------|-----------|
| **Documentação normativa** | Gerada e presente — **PROVA OK** |
| **PH-FS-01** | **CONCLUÍDO_COM_PROVA** (com ressalva de paths) |
| **PH-FS-02** | **PARCIAL** — plano + §4 **KPI-06 PENDENTE**; **PRF válida**; **KPI_REPORT** ainda não protocolado |
| **Fases PH-FS-03+** | **NÃO_EXECUTADO** |
| **Processo SOL/TAR/DEC** | **PARCIAL** (linha PH-FS-02 preenchida; outras fases sem linhas) |
| **Risco global** | PH-FS-03 exige **nova PRF** + entrada na matriz; não avançar só com narrativa |

---

## 8. Fecho

Este documento **não** “reprova” o trabalho global — **localiza** falhas **verificáveis** na cadeia **prova → validador → decisão**. **F2** fechado; **F4** mitigado no **texto** do plano (§4); **F3** com linha de log **`c3ea3be…`**. Próximo passo: **PH-FS-03** com **TAR + PRF**; **opcional** alinhar **PSA_GATE** ao HEAD e corrigir lacunas do manifesto.

---

*Fim — `DOC-AUD-CONCLUSAO-PROCESSO-20260403` — v1.2: catálogo §4 KPI-06 PENDENTE; `PSA_RUN_LOG` com `head_reconciled_post_commit` + `audit_record` v1.2; notas matriz.*
