# Documento único oficial — Encerramento da auditoria (tranche FS) e próximos passos PSA

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-UNICO-ENCERRAMENTO-AUDITORIA-20260327` |
| **Versão** | 1.0 |
| **Tipo** | **Instrução única consolidada** para o **PSA** — encerramento formal da auditoria de processo **até PH-FS-03** e transição para **PH-FS-04** |
| **Emitido por** | Núcleo de Validação OMEGA / Comando |
| **Destinatário** | **PSA** (executor único in-repo) |
| **Documentos absorvidos** | `DOC-AUD-CONCLUSAO-PROCESSO-20260403` v1.3 · `DOC-OFC-ENVIO-PSA-20260327` v1.1 · normas MESTRE/PROVAS/SOL-TAR |
| **Base de pastas** | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/04_relatorios_tarefa/` |

---

## Parte A — O que aconteceu e porquê (leitura executiva)

Esta auditoria visou **eliminar a ambiguidade entre “procedimento descrito” e “prova verificável”** (erro **F1**). Ao longo do trackeamento surgiram falhas **nomeadas** e **corrigidas**:

| Código | O que foi | Porquê (causa) | Como se resolveu |
|--------|-----------|----------------|------------------|
| **F1** | Texto dizia que algo estava feito sem artefacto ou validador | Confundir narrativa com evidência | Exigir **PRF** + `--validate` exit 0 + ficheiros no repo |
| **F2** | PRF PH-FS-02 reprovada | `req_id` no formato errado para o regex do script | Uso de **`REQ-UNICO-030`** alinhado à matriz |
| **F3** | Vários **HEAD** em documentos diferentes | Commits sucessivos sem registo | Linhas **`head_reconciled_post_commit`** e **`audit_record`** em `PSA_RUN_LOG.jsonl` |
| **F4** | Catálogo sugeria KPI-06 = 1,0 sem medição | Confundir **desenho** com **medida** | §4 do catálogo: **KPI-06 PENDENTE** até existir **`KPI_REPORT`** |
| **F5** | Matriz incompleta | Tarefas sem linha SOL/TAR/PRF/DEC | Preenchimento progressivo por fase |
| **F6** | Campo `git_head` na PRF PH-FS-03 inválido | Hex que **não** correspondia a `commit` no Git (`git cat-file` falhou) | Correcção para **`fd64467f696362acf5cf519ecf94c59f38bf3fc9`** = HEAD/manifesto/gate verificados |

**Conclusão de causalidade:** os problemas não foram “falha de intenção”, e sim **lacunas de disciplina de prova**: IDs, validador, commit Git verificável e registo no **log JSONL**. Com **F2–F4–F6** tratados e **PH-FS-03** entregue, a tranche **FS-01 → FS-03** está **auditável**. O que **permanece aberto** por **design** é a **métrica KPI-06** (PH-FS-02 **PARCIAL**) até **PH-FS-04** produzir **`KPI_REPORT_*.json`**.

---

## Parte B — Estado do programa (snapshot único)

**Ordem de roteiro:** `0 → PH-FS-01 → PH-FS-02 → PH-FS-03 → PH-FS-04 → PH-TR-01 → PH-PS-01`

| Fase | Estado | Prova mínima | Situação |
|------|--------|--------------|----------|
| **0** | CONCLUÍDO_COM_PROVA | `STATUS_ANEXOS_CONSELHO.md` | OK |
| **PH-FS-01** | CONCLUÍDO_COM_PROVA | `INVENTARIO_FONTES_DADOS_v1.csv` + log | OK (ressalva: paths relativos — rastreio parcial) |
| **PH-FS-02** | **PARCIAL_COM_PROVA** | Catálogo + PRF + **KPI-06** | `CATALOGO_OHLCV_PLANO_v1.md` §4 **KPI-06 PENDENTE**; PRF **`REQ-UNICO-030`** PASS — **falta valor medido** em `KPI_REPORT` |
| **PH-FS-03** | **CONCLUÍDO_COM_PROVA** | Mapa demo + PRF + matriz + DEC | `MAP-DEMO-TBL_v1.md`; `PRF-PHFS03-20260403-001` / **`REQ-UNICO-040`**; **`DEC-20260403-002`** |
| **PH-FS-04** | **NÃO_EXECUTADO** | Batch + `KPI_REPORT_*.json` | **Próximo passo obrigatório** |
| **PH-TR-01** | PARCIAL | Gate | `PSA_GATE_CONSELHO_ULTIMO.txt` — reexecutar quando o manifesto mudar |
| **PH-PS-01** | NÃO_EXECUTADO | Relatório piloto | — |

**Commit de referência verificado (HEAD):** `fd64467f696362acf5cf519ecf94c59f38bf3fc9`  
**Alinhamento:** `MANIFEST_RUN_20260329.json` (`git_commit_sha`) · `PSA_GATE_CONSELHO_ULTIMO.txt` (GIT HEAD) — **coerentes** na última verificação.

---

## Parte C — Registo de identificadores (malha SOL/TAR/REQ/PRF/DEC)

| Fase | SOL | TAR | REQ | PRF | DEC |
|------|-----|-----|-----|-----|-----|
| PH-FS-02 | SOL-20260403-001 | TAR-PHFS02-001 | REQ-UNICO-030 | PRF-PHFS02-20260403-001 | DEC-20260403-001 |
| PH-FS-03 | SOL-20260403-002 | TAR-PHFS03-001 | REQ-UNICO-040 | PRF-PHFS03-20260403-001 | DEC-20260403-002 |
| PH-FS-04 | *(a emitir)* | *(a emitir)* | *(a atribuir)* | *(a gerar)* | *(a emitir)* |

Ficheiro-fonte: `templates_auditoria_psa/MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv`.

---

## Parte D — Checklist: “auditoria desta tranche está encerrada?”

Marque **SIM** apenas com prova no disco ou comando.

| # | Critério | SIM / NÃO |
|---|----------|-----------|
| D1 | Todas as PRFs em uso passam `psa_refutation_checklist.py --validate` (exit 0) | **SIM** (PH-FS-02 e PH-FS-03) |
| D2 | Cada PRF tem `git_head` = `git rev-parse HEAD` **no momento do selo** e `git cat-file -t <sha>` = `commit` | **SIM** (após correcção F6 na PH-FS-03) |
| D3 | `PSA_RUN_LOG.jsonl` contém trilho para fases entregues (ex.: `file_saved`, `prf_validated`, `phase_complete` PH-FS-03) | **SIM** |
| D4 | Matriz reflecte SOL/TAR/REQ/PRF/DEC para cada TAR fechada | **SIM** (FS-02 e FS-03) |
| D5 | Catálogo OHLCV não afirma KPI-06 medido sem `KPI_REPORT` | **SIM** (§4 PENDENTE) |
| D6 | **PH-FS-04** executada e `KPI_REPORT` produzido | **NÃO** — *isto define o “próximo passo”* |
| D7 | **PH-FS-02** fechada em **métrica** (KPI-06 com valor) | **NÃO** — depende de D6 |

**Interpretação:** a **auditoria de processo e integridade de provas até PH-FS-03** pode ser considerada **encerrada para envio ao Conselho** com a ressalva explícita: **métrica analítica global (FS-04 + KPI_REPORT)** ainda **não** concluída. Não há contradição — são **camadas diferentes** (processo vs. medição).

---

## Parte E — Instruções obrigatórias ao PSA (próximo passo: PH-FS-04)

1. **Emitir** **SOL-20260403-003** (ou próximo ID livre) e **TAR-PHFS04-001** segundo `DOCUMENTO_OFICIAL_MODELO_SOLICITACAO_APROVACAO_TAREFA.md`.
2. **Executar** o pipeline de métricas acordado no roteiro (ex.: `run_kpi_batch.py` ou script oficial no repo).
3. **Gerar** ficheiro **`KPI_REPORT_*.json`** com indicadores necessários para **fechar KPI-06** (e outros definidos no kit), com **rastreio** (timestamp, conjunto de dados, comando).
4. **Criar PRF** nova (ex.: `prova_PRF-PHFS04-YYYYMMDD-001.json`) com:
   - `req_id` válido para o validador (padrão `REQ-UNICO-0xx`);
   - `git_head` **copiado** de `git rev-parse HEAD` após commit;
   - referência ao artefacto `KPI_REPORT_*.json`.
5. **Validar:**  
   `python psa_refutation_checklist.py --validate templates_auditoria_psa/prova_PRF-PHFS04-….json` → **exit 0**.
6. **Actualizar** `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` com nova linha e **DEC-***.
7. **Registar** em `PSA_RUN_LOG.jsonl`: `file_saved` (KPI_REPORT), `prf_validated`, `phase_complete` para **PH-FS-04**.
8. **Actualizar** `MANIFEST_RUN_*.json` (ou processo oficial de sync) para incluir novos ficheiros e **`git_commit_sha`** correcto.
9. **Reexecutar** `psa_gate_conselho_tier0` / script de gate para renovar `PSA_GATE_CONSELHO_ULTIMO.txt` se o manifesto exigir.
10. **Actualizar** `CATALOGO_OHLCV_PLANO_v1.md` §4: quando existir medição, substituir **PENDENTE** por **valor + referência ao `KPI_REPORT`** (nunca número sem ficheiro).

---

## Parte F — Comandos de verificação (reproducibilidade)

...
*(Restringe-se conforme layout original)*

---

*Fim — `DOC-UNICO-ENCERRAMENTO-AUDITORIA-20260327` v1.0*
