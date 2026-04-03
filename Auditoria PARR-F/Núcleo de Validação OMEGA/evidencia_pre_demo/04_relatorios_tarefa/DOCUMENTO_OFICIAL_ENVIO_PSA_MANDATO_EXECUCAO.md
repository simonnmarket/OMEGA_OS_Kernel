# Documento oficial — Envio ao PSA (mandato de execução)

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-OFC-ENVIO-PSA-20260327` |
| **Versão** | 1.1 |
| **Tipo** | Instrução **oficial** ao executor **PSA** — sujeita a provas REQ/PRF e registo em `PSA_RUN_LOG.jsonl` |
| **Emitido por** | Núcleo de Validação OMEGA / Comando (cadeia `DOC-AUD-CONCLUSAO-PROCESSO-20260403` **v1.3**) |
| **Destinatário** | **PSA** — único executor de alterações in-repo neste programa |
| **Estado mandato §3 (PH-FS-03)** | **CUMPRIDO** — ver evidências em §6 |

---

## 1. Documentos normativos (obrigatoriamente em vigor)

| ID | Ficheiro (pasta base: `04_relatorios_tarefa/`) |
|----|-----------------------------------------------|
| MESTRE | `DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md` (`DOC-UNICO-PSA-MESTRE-20260403`) |
| PROVAS | `DOCUMENTO_OFICIAL_PSA_PROVAS_E_AUDITORIA.md` (`DOC-OFC-PSA-PROVAS-AUD-20260403`) |
| SOL/TAR/DEC | `DOCUMENTO_OFICIAL_MODELO_SOLICITACAO_APROVACAO_TAREFA.md` (`DOC-OFC-MODELO-TAR-20260403`) |
| AUDITORIA | `DOCUMENTO_UNICO_AUDITORIA_CONCLUSAO_E_FALHAS_PROCESSO.md` (`DOC-AUD-CONCLUSAO-PROCESSO-20260403` **v1.3**) |

**Regra:** nenhum “PASS” ou “concluído” sem **PRF** validada por `python psa_refutation_checklist.py --validate <ficheiro.json>` (exit 0), **`git_head` igual ao output de `git rev-parse HEAD` no momento do selo**, linha na matriz, e registo no `PSA_RUN_LOG.jsonl`.

---

## 2. Estado do programa (snapshot)

| Fase | Estado | Nota executiva |
|------|--------|----------------|
| **0**, **PH-FS-01** | CONCLUÍDO_COM_PROVA | Inventário + trilho em `PSA_RUN_LOG.jsonl` |
| **PH-FS-02** | **PARCIAL_COM_PROVA** | `CATALOGO_OHLCV_PLANO_v1.md` §4 **KPI-06 PENDENTE** até `KPI_REPORT_*.json`. |
| **PH-FS-03** | **CONCLUÍDO_COM_PROVA** | `MAP-DEMO-TBL_v1.md` (`DOC-MAP-DEMO-TBL-20260403`); PRF `PRF-PHFS03-20260403-001` / `REQ-UNICO-040`; `DEC-20260403-002`. |
| **PH-FS-04** | **NÃO_EXECUTADO** | Batch KPI / `KPI_REPORT_*.json` (próxima frente). |
| **Gate Tier-0** | **Alinhado (verificação)** | `PSA_GATE_CONSELHO_ULTIMO.txt` com HEAD **`fd64467f696362acf5cf519ecf94c59f38bf3fc9`** coerente com manifesto. |

---

## 3. Ordem de trabalho — **PH-FS-03** (encerrada)

Os passos do mandato v1.0 para PH-FS-03 encontram-se **executados** com artefactos no repositório e trilho em log. Não repetir salvo nova **SOL/TAR**.

---

## 4. Próxima ordem de trabalho — **PH-FS-04** (balizas)

1. **Emitir** **SOL-*** / **TAR-PHFS04-*** conforme modelo oficial.
2. **Executar** pipeline de métricas (ex.: `run_kpi_batch.py` ou roteiro equivalente no repo).
3. **Gerar** `KPI_REPORT_*.json` e **PRF** dedicada com `req_id` válido.
4. **`--validate`** na PRF → exit 0; **`git_head`** = `git rev-parse HEAD`.
5. **Actualizar** `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` e **`PSA_RUN_LOG.jsonl`** (`file_saved` / `prf_validated` / `phase_complete`).
6. **Manter** PH-FS-02 em **PARCIAL** até o **KPI_REPORT** fechar o indicador **KPI-06** (coerente com o catálogo).

---

## 5. Proibições (anti-F1 / anti-F6)

- Não confundir **validação de schema** PRF com **prova de commit**: o campo `git_head` tem de resolver com `git cat-file -t <sha>` = `commit`.
- Não declarar **PH-FS-02** fechada em métrica sem **`KPI_REPORT`**.

---

## 6. Evidências de cumprimento do mandato (PH-FS-03)

| ID | Evidência |
|----|-----------|
| Artefacto | `04_relatorios_tarefa/MAP-DEMO-TBL_v1.md` |
| PRF | `templates_auditoria_psa/prova_PRF-PHFS03-20260403-001.json` (`REQ-UNICO-040`) |
| Matriz | `templates_auditoria_psa/MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` — `SOL-20260403-002`, `TAR-PHFS03-001`, `DEC-20260403-002` |
| Log | `PSA_RUN_LOG.jsonl` — `run_id` `PS-20260403-PH-FS-03-fd64467` |
| Commit de referência | `fd64467f696362acf5cf519ecf94c59f38bf3fc9` |

**Nota auditoria v1.3:** uma versão anterior da PRF continha `git_head` **inválido**; o valor foi **corrigido** para o commit acima (**F6** em `DOC-AUD-CONCLUSAO-PROCESSO-20260403`).

---

## 7. Fecho

Mandato **DOC-OFC-ENVIO-PSA-20260327** relativo a **PH-FS-03** considerado **integralmente executado** ao nível de prova auditável. Próximo documento de envio recomendado: mandato ou anexo específico para **PH-FS-04** (a definir pelo Comando).

---

*Fim — `DOC-OFC-ENVIO-PSA-20260327` v1.1*
