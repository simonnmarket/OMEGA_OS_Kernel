# Documento único oficial — Encerramento da auditoria (tranche FS) e próximos passos PSA

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-UNICO-ENCERRAMENTO-AUDITORIA-20260327` |
| **Versão** | **2.0** |
| **Tipo** | **Instrução única consolidada** para o **PSA** — tranche **PH-FS-01 → PH-FS-04** **concluída com prova**; transição para **PH-TR-01** / relatório ao Conselho |
| **Emitido por** | Núcleo de Validação OMEGA / Comando |
| **Destinatário** | **PSA** (executor único in-repo) |
| **Documentos absorvidos** | `DOC-AUD-CONCLUSAO-PROCESSO-20260403` v1.3 · `DOC-OFC-ENVIO-PSA-20260327` v1.1 · normas MESTRE/PROVAS/SOL-TAR |
| **Base de pastas** | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/` |
| **HEAD de referência (última verificação)** | `f2fa72da5a3a610b667441071dfb80c58d4e406a` (= `MANIFEST_RUN_20260329.json` → `git_commit_sha`) |

---

## Parte A — O que aconteceu e porquê (leitura executiva)

Esta auditoria visou **eliminar a ambiguidade entre “procedimento descrito” e “prova verificável”** (erro **F1**). Falhas **nomeadas** e **corrigidas**:

| Código | O que foi | Porquê (causa) | Como se resolveu |
|--------|-----------|----------------|------------------|
| **F1** | Texto dizia que algo estava feito sem artefacto ou validador | Confundir narrativa com evidência | **PRF** + `--validate` exit 0 + ficheiros no repo |
| **F2** | PRF PH-FS-02 reprovada | `req_id` no formato errado para o regex | **`REQ-UNICO-030`** |
| **F3** | Vários **HEAD** em documentos diferentes | Commits sucessivos sem registo | **`PSA_RUN_LOG.jsonl`** (`head_reconciled`, `audit_record`, fases) |
| **F4** | Catálogo sugeria KPI-06 = 1,0 sem medição | Desenho vs. medida | §4 **PENDENTE** até **`KPI_REPORT`** → **agora PROVADO** (v2.0) |
| **F5** | Matriz incompleta | Tarefas sem linha SOL/TAR/PRF/DEC | Preenchimento até **FS-04** |
| **F6** | `git_head` na PRF **não** resolvia para `commit` | Hex errado ou desatualizado | **Sempre** `git rev-parse HEAD` + `git cat-file -t`; PRF PH-FS-04 ajustada a **`f2fa72…`** |

**Conclusão de causalidade:** com **`KPI_REPORT_20260403-001.json`**, **PRF PH-FS-04** (`REQ-UNICO-050`) e **§4 do catálogo** alinhados, **F4** no domínio KPI-06 está **fechado**. A malha **FS-01 a FS-04** está **integralmente documentada e validável**.

---

## Parte B — Estado do programa (snapshot único)

**Ordem de roteiro:** `0 → PH-FS-01 → PH-FS-02 → PH-FS-03 → PH-FS-04 → PH-TR-01 → PH-PS-01`

| Fase | Estado | Prova mínima | Situação |
|------|--------|--------------|----------|
| **0** | CONCLUÍDO_COM_PROVA | `STATUS_ANEXOS_CONSELHO.md` | OK |
| **PH-FS-01** | CONCLUÍDO_COM_PROVA | Inventário + log | OK |
| **PH-FS-02** | **CONCLUÍDO_COM_PROVA** (métrica) | Catálogo + PRF + **KPI-06 medido** | §4 **KPI-06 = 1.0 (PROVADO)** → `KPI_REPORT_20260403-001.json` (`KPI-06_CC`: 1.0) |
| **PH-FS-03** | CONCLUÍDO_COM_PROVA | Mapa demo + PRF + DEC | `MAP-DEMO-TBL_v1.md`; `PRF-PHFS03-20260403-001` / **`REQ-UNICO-040`**; **`DEC-20260403-002`** |
| **PH-FS-04** | **CONCLUÍDO_COM_PROVA** | `KPI_REPORT_*.json` + PRF + matriz + DEC | `KPI_REPORT_20260403-001.json`; `PRF-PHFS04-20260403-001` / **`REQ-UNICO-050`**; **`DEC-20260403-003`** |
| **PH-TR-01** | PARCIAL | Gate / transição | **Próximo foco** — renovar gate após alterações ao manifesto |
| **PH-PS-01** | NÃO_EXECUTADO | Relatório piloto | — |

**Limitação de escopo:** o `KPI_REPORT` reflecte **métricas declaradas no JSON** (incl. `catalogs_scanned`: XAUUSD, XAGUSD). Auditorias futuras podem exigir **reexecução** do pipeline sobre outros conjuntos.

---

## Parte C — Registo de identificadores (malha SOL/TAR/REQ/PRF/DEC)

| Fase | SOL | TAR | REQ | PRF | DEC |
|------|-----|-----|-----|-----|-----|
| PH-FS-02 | SOL-20260403-001 | TAR-PHFS02-001 | REQ-UNICO-030 | PRF-PHFS02-20260403-001 | DEC-20260403-001 |
| PH-FS-03 | SOL-20260403-002 | TAR-PHFS03-001 | REQ-UNICO-040 | PRF-PHFS03-20260403-001 | DEC-20260403-002 |
| PH-FS-04 | SOL-20260403-003 | TAR-PHFS04-001 | REQ-UNICO-050 | PRF-PHFS04-20260403-001 | DEC-20260403-003 |

Ficheiro-fonte: `templates_auditoria_psa/MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv`.

---

## Parte D — Checklist: auditoria da tranche FS encerrada?

| # | Critério | SIM / NÃO |
|---|----------|-----------|
| D1 | Todas as PRFs FS passam `psa_refutation_checklist.py --validate` (exit 0) | **SIM** (FS-02, FS-03, FS-04) |
| D2 | `git_head` em cada PRF resolvível com `git cat-file -t <sha>` = `commit` (último selo **f2fa72…**) | **SIM** (após alinhamento PRF PH-FS-04) |
| D3 | `PSA_RUN_LOG.jsonl` com trilho **FS-04** (`file_saved`, `prf_validated`, `phase_complete`) | **SIM** |
| D4 | Matriz com linhas para FS-02, FS-03, FS-04 | **SIM** |
| D5 | Catálogo §4 com KPI-06 **e** referência ao `KPI_REPORT` | **SIM** |
| D6 | `KPI_REPORT_20260403-001.json` presente e referenciado | **SIM** |
| D7 | Manifesto lista `KPI_REPORT` e `git_commit_sha` coerente com HEAD | **SIM** (`MANIFEST_RUN_20260329.json`) |

**Interpretação:** a **tranche FS (FS-01 a FS-04)** está **encerrada ao nível de prova** definido neste programa. Segue-se **PH-TR-01** (transição / gate) e, se aplicável, **relatório ao Conselho**.

---

## Parte E — Instruções ~~PH-FS-04~~ **CUMPRIDAS** — próximo passo: **PH-TR-01** / Conselho

~~(Lista de 10 itens para FS-04 — **executada**.)~~

1. **Emitir** documento ou **SOL/TAR** para **PH-TR-01** segundo o roteiro (ex.: verificação de gate, stress, manifesto).
2. **Reexecutar** `psa_gate_conselho_tier0` (ou script oficial) e **actualizar** `PSA_GATE_CONSELHO_ULTIMO.txt` se o Conselho exigir snapshot fresco.
3. **Preparar** pacote ao Conselho: este **DOC-UNICO v2.0**, `DOC-AUD-CONCLUSAO-PROCESSO-20260403`, matriz, amostra de `PSA_RUN_LOG.jsonl`, `KPI_REPORT_20260403-001.json`.
4. **PH-PS-01** (relatório piloto): emitir **SOL/TAR** quando o Comando autorizar.

---

## Parte F — Comandos de verificação (reproducibilidade)

Na raiz do repositório `nebular-kuiper`:

```bash
git rev-parse HEAD
git cat-file -t "$(git rev-parse HEAD)"
```

Validação das PRFs (ajustar caminho se necessário):

```bash
python "Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/psa_refutation_checklist.py" --validate "Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/templates_auditoria_psa/prova_PRF-PHFS02-20260403-001.json"
python "Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/psa_refutation_checklist.py" --validate "Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/templates_auditoria_psa/prova_PRF-PHFS03-20260403-001.json"
python "Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/psa_refutation_checklist.py" --validate "Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/templates_auditoria_psa/prova_PRF-PHFS04-20260403-001.json"
```

**Esperado:** `git cat-file` → `commit`; três validações → `PASS` / exit 0.

---

## Parte G — Documentos normativos

| ID | Ficheiro |
|----|----------|
| MESTRE | `DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md` |
| PROVAS | `DOCUMENTO_OFICIAL_PSA_PROVAS_E_AUDITORIA.md` |
| SOL/TAR | `DOCUMENTO_OFICIAL_MODELO_SOLICITACAO_APROVACAO_TAREFA.md` |
| Auditoria detalhada | `DOCUMENTO_UNICO_AUDITORIA_CONCLUSAO_E_FALHAS_PROCESSO.md` (v1.3) |

---

## Parte H — Proibições (resumo)

- **Anti-F1:** não substituir prova por narrativa.
- **Anti-F6:** todo `git_head` em PRF deve coincidir com commit real no momento do selo (verificar com Git).

---

## Parte I — Fecho

| Tranche | Estado |
|---------|--------|
| **PH-FS-01 a PH-FS-04** | **CONCLUÍDA COM PROVA** (v2.0) |
| **PH-TR-01 / Conselho** | **Próximo passo operacional** |

---

*Fim — `DOC-UNICO-ENCERRAMENTO-AUDITORIA-20260327` **v2.0** — FS-04 fechada; KPI-06 provado via `KPI_REPORT_20260403-001.json`; HEAD **f2fa72…**.*
