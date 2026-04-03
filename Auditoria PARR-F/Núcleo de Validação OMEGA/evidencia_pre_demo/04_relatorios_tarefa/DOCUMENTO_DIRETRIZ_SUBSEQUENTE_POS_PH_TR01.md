Diretriz subsequente — Após PH-TR-01 (roteiro FIN-SENSE / PSA)

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-DIRETRIZ-POS-PH-TR01-20260327` |
| **Versão** | 1.0 |
| **Tipo** | Ordem de continuidade pós-transição Tier-0 |
| **Precedência** | Complementa `DOC-UNICO-ENCERRAMENTO-AUDITORIA-20260327` v2.0 e `DOC-FINAL-EXEC-PH-TR01-20260327` |

---

## 1. Situação actual (trincheira FS + TR)

| Roteiro | Estado esperado |
|---------|-----------------|
| **PH-FS-01 … PH-FS-04** | Concluídos com PRF, KPI_REPORT, catálogo |
| **PH-TR-01** | Gate + critérios C1–C4 cumpridos (ver log `PSA_RUN_LOG.jsonl`) |

**Próximo nó oficial do roteiro:** **PH-PS-01** — relatório piloto / entrega narrativa-controlada para **administração / Conselho** (não substitui PRF).

---

## 2. Diretriz 1 — **PH-PS-01** (obrigatória antes de “v1 produção narrativa”)

1. **Emitir** **SOL-20260403-004** (ou próximo ID) e **TAR-PHPS01-001** (rótulo sugerido) alinhados ao modelo SOL/TAR/DEC.
2. **Produzir** documento **`RPT-PILOTO-*` ou equivalente** com:
   - Resumo executivo (1 página) referenciando **Doc-IDs** (`DOC-UNICO-ENCERRAMENTO…`, `KPI_REPORT_20260403-001`, `PSA_GATE_*`).
   - Tabela de **IDs** (SOL/TAR/REQ/PRF/DEC) e **HEAD** do commit de referência da entrega.
   - **Limitações** explícitas (escopo MVP estático, conjuntos de dados no KPI_REPORT, etc.).
3. **Opcional:** PRF de “encerramento narrativo” **se** o regime interno exigir prova para o relatório piloto; caso contrário, **DEC-*** na matriz com `notas` a citar apenas artefactos já validados.
4. **Registar** em `PSA_RUN_LOG.jsonl`: `phase_complete` para **PH-PS-01** ou `audit_record` com `doc_id` do relatório piloto.

---

## 3. Diretriz 2 — **Pacote ao Conselho / administração externa**

Entregar pasta **`04_relatorios_tarefa`** (ou ZIP) com **mínimo**:

| # | Artefacto |
|---|-----------|
| 1 | `DOCUMENTO_UNICO_OFICIAL_PSA_ENCERRAMENTO_AUDITORIA_E_PROXIMOS_PASSOS.md` v2.0 |
| 2 | `DOCUMENTO_UNICO_AUDITORIA_CONCLUSAO_E_FALHAS_PROCESSO.md` (última versão) |
| 3 | `KPI_REPORT_20260403-001.json` |
| 4 | `MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` |
| 5 | `PSA_GATE_CONSELHO_ULTIMO.txt` **com** `GATE_GLOBAL: PASS` **e** `verify_tier0_psa exit: 0` |
| 6 | `PSA_RUN_LOG.jsonl` (completo) |
| 7 | PRFs `prova_PRF-PHFS02/03/04-*.json` |

**Verificação de coerência:** se o ficheiro `PSA_GATE_CONSELHO_ULTIMO.txt` ainda indicar **FALHA** por ficheiro em falta no manifesto, **corrigir** (criar `prova_TEMPLATE_PREENCHER.json` vazio ou sincronizar manifesto) e **voltar a correr** `psa_gate_conselho_tier0.py` até o relatório bater certo com a narrativa “PASS”.

---

## 4. Diretriz 3 — **Cadência operacional (pós-freeze)**

| Evento | Acção |
|--------|--------|
| Novo commit que toque em ficheiros do manifesto | Actualizar `MANIFEST_RUN_*.json` e **reexecutar** gate |
| Nova alteração em PRF | `--validate` + alinhar `git_head` ao commit de selo |
| Auditoria externa | Reproduzir comandos em `DOC-FINAL-EXEC-PH-TR01-20260327` §4 |

---

## 5. Diretriz 4 — **Git e etiquetas (opcional)**

- Criar **tag** anotada no commit de conclusão (ex.: `fin-sense-mvp-audit-20260403`) para referência institucional.
- Manter **CHANGELOG** ou nota no commit apontando para `DOC-DIRETRIZ-POS-PH-TR01-20260327`.

---

## 6. O que **não** fazer

- Não declarar “inviolável” ou “sem gaps” **sem** `GATE_GLOBAL: PASS` no último `PSA_GATE_*` **e** `verify_tier0` exit 0 **coerentes** com o manifesto.
- Não apagar linhas antigas de `PSA_RUN_LOG.jsonl` (trilho de custódia).

---

## 7. Fecho

A **diretriz subsequente** imediata é: **executar PH-PS-01** + **pacote Conselho** + **garantir coerência gate/manifesto**; depois, **cadência** de gate em cada alteração relevante.

---

*Fim — `DOC-DIRETRIZ-POS-PH-TR01-20260327` v1.0*
