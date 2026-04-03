# Documento único — Auditoria de conclusão, provas e falhas de processo

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-AUD-CONCLUSAO-PROCESSO-20260403` |
| **Versão** | 1.1 |
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
| `PSA_RUN_LOG.jsonl` | **SIM** | ≥6 linhas JSON; inclui `audit_record` → `DOC-AUD-CONCLUSAO-PROCESSO-20260403` |
| `CATALOGO_OHLCV_PLANO_v1.md` | **SIM** | Ficheiro presente (PH-FS-02) |
| `prova_PRF-PHFS02-20260403-001.json` | **CORRIGIDO → PASS** | Inicialmente `REQ-PHFS02-001` era **inválido** para o regex do validador; após **`REQ-UNICO-030`**, `--validate` → **exit 0** |
| `_INDEX.csv` com colunas `ingestion_id`, `file_hash` | **NÃO VERIFICADO** | Plano **declara** obrigatoriedade; **não** há prova de ficheiro `_INDEX` já migrado neste audit |
| `PSA_GATE_CONSELHO_ULTIMO.txt` HEAD | **27a6d0b7fc515dedc1d4caab8c4b8bc4af3c3f8f** | Lido em 2026-04-03 (timestamp ficheiro `17:30:35Z`); **≠** vários `git_head` em PRFs/logs anteriores |
| `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` | **PARCIAL** | Linha PH-FS-02 com `proof_id` e `DEC-*`; **`req_id`** deve coincidir com a PRF (**`REQ-UNICO-030`**) |

**Conclusão imediata:** existe **prova escrita** de trabalho (inventário, log, plano); **F2** (formato `req_id`) foi **corrigido** — `--validate` na PRF **PASS**. Persistem **deriva de HEAD** entre artefactos e **KPI-06 não medido** (F4).

---

## 3. Mapa de fases (roteiro oficial) — estado

**Ordem:** `0 → PH-FS-01 → PH-FS-02 → PH-FS-03 → PH-FS-04 → PH-TR-01 → PH-PS-01`

| Fase | Estado global | Prova mínima exigida pelo roteiro | Situação |
|------|---------------|-----------------------------------|----------|
| **0** | **CONCLUÍDO_COM_PROVA** | `STATUS_ANEXOS_CONSELHO.md` | Presente |
| **PH-FS-01** | **CONCLUÍDO_COM_PROVA** | CSV inventário + `PSA_RUN_LOG` + certificado | Ficheiros presentes; **nota:** paths no inventário são **parciais** (ex. `01_raw_mt5/...`) — ficheiros existem sob `evidencia_pre_demo/01_raw_mt5/` mas **não** batem certo com path relativo único sem convenção explícita → **risco de rastreio** |
| **PH-FS-02** | **PARCIAL_COM_PROVA** | `CATALOGO_OHLCV_PLANO_v1.md` + gate KPI-06 **testável** | Plano **existe**; **KPI-06 = 1.0** no texto do plano é **afirmação**, não medição — **não** prova até existir `KPI_REPORT` ou script que calcule CC sobre conjunto S vs C; PRF JSON **`PASS`** em `--validate` (após `REQ-UNICO-030`) |
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
| CP-FS02-03 | KPI-06 medido (não só afirmado) | PENDENTE | Sem `KPI_REPORT` | **Falha de rigor** no texto do plano |

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
| **F3** | HEAD múltiplos | Commits entre geração de artefactos | Registar **sempre** `git rev-parse HEAD` no momento da prova; linha `head_reconciled` |
| **F4** | KPI-06 “1.0” no plano | Confundiu **desenho** com **medição** | Calcular CC ou marcar **PENDENTE** até haver `KPI_REPORT` |
| **F5** | Matriz SOL/TAR estagnada | `proof_id`/`dec_id` vazios | Preencher após PRF válido e decisão |

---

## 6. Instruções obrigatórias para o PSA (antes de prosseguir)

1. ~~**Corrigir** `req_id` na PRF~~ — **feito:** `REQ-UNICO-030`; `python psa_refutation_checklist.py --validate …` → **exit 0**.

2. **Opcional:** alargar o validador para aceitar `REQ-PHFS02-001` (mudança de código = novo commit + PRF a referir o commit).

3. **Não** declarar PH-FS-02 **fechada em todos os gates** até: (a) ~~PRF válido~~ **OK**; (b) `KPI_REPORT` com CC **ou** plano/matriz com **PENDENTE** explícito para KPI-06 nas `notas`.

4. ~~**Actualizar** matriz com `proof_id`~~ — **feito**; manter **`req_id`** idêntico ao JSON da PRF.

5. ~~**Registar** `audit_record` no `PSA_RUN_LOG.jsonl`~~ — ver linha acrescentada com `doc_id` **`DOC-AUD-CONCLUSAO-PROCESSO-20260403`**.

6. **Próxima fase executável:** completar **PH-FS-02** (provas) **ou** formalizar **PARCIAL** com **DEC-*** — só então **PH-FS-03**.

---

## 7. Tabela-resumo executiva (envio Conselho)

| Dimensão | Veredicto |
|----------|-----------|
| **Documentação normativa** | Gerada e presente — **PROVA OK** |
| **PH-FS-01** | **CONCLUÍDO_COM_PROVA** (com ressalva de paths) |
| **PH-FS-02** | **PARCIAL** — plano existe; **PRF válida** (`--validate` PASS); **KPI-06 não medido** |
| **Fases PH-FS-03+** | **NÃO_EXECUTADO** |
| **Processo SOL/TAR/DEC** | **PARCIAL** (linha PH-FS-02 preenchida; outras fases sem linhas) |
| **Risco global** | Avançar para PH-FS-03 **sem** fechar provas PH-FS-02 = **repetição do erro F1** |

---

## 8. Fecho

Este documento **não** “reprova” o trabalho global — **localiza** falhas **verificáveis** na cadeia **prova → validador → decisão**. **F2** está **fechado** com validação automática. Próximo passo **obrigatório:** **F4** (KPI-06 medido ou **PENDENTE** formal), reconciliação explícita de **HEAD** (F3), depois **PH-FS-03** com PRF própria.

---

*Fim — `DOC-AUD-CONCLUSAO-PROCESSO-20260403` — v1.1: PRF `--validate` PASS; matriz `req_id` alinhado; `audit_record` em `PSA_RUN_LOG.jsonl`.*
