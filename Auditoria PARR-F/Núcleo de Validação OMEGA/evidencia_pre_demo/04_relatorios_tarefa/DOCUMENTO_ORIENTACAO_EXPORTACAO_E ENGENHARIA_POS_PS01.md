# Orientação — Exportação remota e engenharia após PH-PS-01

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-ORIENT-POS-PS01-20260327` |
| **Versão** | 1.0 |
| **Tipo** | Directivas pós-relatório piloto (FIN-SENSE MVP) |
| **Pré-requisito** | `RPT-PILOTO-ADMINISTRACAO-20260403-001.md` · tag `fin-sense-mvp-audit-20260403` |

---

## 1. Exportação remota (repositório e pacote)

| Passo | Acção |
|-------|--------|
| E1 | **Push** do branch principal e da tag: `git push origin <branch> --tags` (ajustar `remote` / branch). |
| E2 | **Arquivo ZIP** da pasta `04_relatorios_tarefa` **ou** do pacote mínimo listado em `DOC-DIRETRIZ-POS-PH-TR01-20260327` §3 — excluir segredos (`.env`, chaves). |
| E3 | **Checksum** opcional: `Get-FileHash` (PowerShell) ou `sha256sum` sobre o ZIP para registo junto do Conselho. |
| E4 | **Backup** off-site (OneDrive, S3, artefacto CI) conforme política da organização. |

---

## 2. Coerência do gate antes de arquivo externo final

O ficheiro `PSA_GATE_CONSELHO_ULTIMO.txt` no disco deve estar **alinhado** com a narrativa “PASS”:

- Se `verify_tier0_psa` ainda apontar **ficheiro em falta** (ex.: `prova_TEMPLATE_PREENCHER.json`), **criar** o ficheiro esperado **ou** actualizar o manifesto com processo aprovado, e **reexecutar** `psa_gate_conselho_tier0.py` com `--out-relatorio` até `GATE_GLOBAL: PASS`.

Sem isso, o pacote administrativo contém **duas linguagens** (relatório vs. último gate gravado).

---

## 3. Engenharia do módulo principal OMEGA (blocos seguintes)

Sugestão de ordem (fora do escopo estrito FIN-SENSE DATA, mas coerente com o roteiro maior):

| Bloco | Foco |
|-------|------|
| **B1 — Orquestração** | Integração em tempo real / filas: contratos com `TBL_ORDERS` / `TBL_EXECUTIONS` definidos em `MAP-DEMO-TBL_v1.md`. |
| **B2 — Observabilidade** | Métricas runtime, alertas, dashboards; **novo** manifesto / gate se ficheiros de prova mudarem. |
| **B3 — Expansão de ativos** | Repetir **PH-FS-04**-style: `KPI_REPORT` sobre conjunto alargado; actualizar catálogo §4. |
| **B4 — PH-PS-02** (se adoptado) | Relatório de produção ou “go-live” com novo SOL/TAR/PRF conforme política. |

Cada bloco deve **repetir** o ciclo: artefacto → PRF (se aplicável) → matriz → `PSA_RUN_LOG` → gate quando o manifesto incluir novos paths.

---

## 4. O que não diluir

- **MVP estático** ≠ produção completa: manter limitações do `RPT-PILOTO` e do `KPI_REPORT` visíveis para o Conselho.
- **Não** apagar linhas de `PSA_RUN_LOG.jsonl`.

---

## 5. Fecho

**Exportação remota:** push + ZIP + hash opcional. **Engenharia OMEGA:** próximos blocos em orquestração, observabilidade e expansão de dados, sempre com trilho PSA quando o repositório exigir prova.

---

*Fim — `DOC-ORIENT-POS-PS01-20260327` v1.0*
