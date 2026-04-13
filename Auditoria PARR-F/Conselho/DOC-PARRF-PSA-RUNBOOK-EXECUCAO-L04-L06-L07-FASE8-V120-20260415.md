# DOC-PARRF-PSA-RUNBOOK-EXECUCAO-L04-L06-L07-FASE8-V120-20260415

| Campo | Valor |
|--------|--------|
| **ID oficial** | `DOC-PARRF-PSA-RUNBOOK-EXECUCAO-L04-L06-L07-FASE8-V120-20260415` |
| **Versão** | 1.0.0 |
| **Data** | 2026-04-15 |
| **Estado** | **VIGENTE** — instruções executáveis para PSA |
| **Destinatário primário** | **PSA** (execução, evidências, arquivo) |
| **Cópia** | Tech Lead, COO, Conselho |
| **Classificação** | Uso interno — TIER-0 PARR-F |
| **Relaciona com** | `DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414.md`, `SPEC_PSA_COMPLETION_PROOF.md`, `PACOTE_PSA_ENVIO_MINIMO.md` |

---

## 1. Finalidade e âmbito

Este documento define **onde**, **como**, **porquê** e **em que ordem** o PSA deve executar os procedimentos **L-06**, **L-04**, **L-07** e **spike Fase 8 (Postgres)** até **conclusão com evidência**, gravando tudo na **estrutura oficial** da árvore de auditoria e preparando **commit no GitHub**.

**Inclui:** comandos, ficheiros gerados, critérios de aceite, códigos de saída, regras de não-gravação de segredos.

**Não inclui:** aprovação de trading live, homologação de PnL, nem substituição de ata COO/CFO para risco financeiro.

---

## 2. Estrutura oficial do projeto (SSOT de ficheiros)

**Raiz da árvore de auditoria PARR-F** (`PARRF_AUDIT_TREE_ROOT`):

- Exemplo clone secundário: `...\nebular-kuiper\Auditoria PARR-F\`
- Exemplo clone canónico (quando aplicável): `...\Desktop\OMEGA_OS_Kernel\Auditoria PARR-F\`

**Pastas normativas (leitura / contrato):**

| Caminho | Conteúdo | Política |
|---------|-----------|----------|
| `Conselho\` | Documentos aprovados, `GATES_NUMERICOS_V1.yaml`, `ARBITRO_MULTITF_V1.py`, `AUDIT_JSON_SCHEMA_V1.0.json` | **Não** apagar nem sobrescrever durante runs; PSA só **lê** ou copia para `mirror\` no fluxo PSA_PROTOCOL_DEPLOY. |
| `protocol\PSA\` | Scripts: `PSA_PROTOCOL_DEPLOY.ps1`, `validate_audit_batch.py`, `git_parity_check.py`, `smoke_orchestrator_l07.py`, `postgres_spike_phase8.py`, `SPEC_PSA_COMPLETION_PROOF.md` | Versionar no Git; executar a partir da raiz `Auditoria PARR-F`. |

**Zona oficial de provas (escrita — efémera mas auditável):**

| Caminho | O quê gravar | Porquê |
|---------|----------------|--------|
| `00_PROVAS_AUDITORIA\` | **Todas** as saídas deste runbook (relatórios, CSV, JSON de paridade, smoke, spike) | Única área acordada para evidências geradas por scripts; não misturar com `src`/`lib` de aplicação. |
| `00_PROVAS_AUDITORIA\orchestrator_runs\` | Audits `omega_audit_PARRF_*.json`, logs L-07, `l07_smoke_summary_*.json` | Contrato L-04 + comportamento L-07. |
| `00_PROVAS_AUDITORIA\PSA\<DOC_ID>\<RUN_ID>\` | Quando usar `PSA_PROTOCOL_DEPLOY.ps1` — `MANIFEST.json`, `COMPLETION_PROOF.*`, `mirror\` | Prova de pacote PSA conforme SPEC. |

**Proibições:**

- **Não** gravar DSN, passwords ou tokens em ficheiros versionados sem redação.
- **Não** usar `evidence\PSA\` para novas execuções (legado); preferir `00_PROVAS_AUDITORIA\` conforme `00_PROVAS_AUDITORIA\README.md`.

---

## 3. Pré-requisitos (antes de qualquer etapa)

1. **Python** 3.10+ no PATH.  
2. Na raiz `Auditoria PARR-F`:

   ```powershell
   pip install -r requirements-psa.txt
   ```

3. **Git** instalado e acessível (`git` no PATH).  
4. Definir **repos** para L-06 (se diferentes dos defaults do script):

   - `OMEGA_GIT_REPO_DESKTOP` — raiz do repositório com `.git` (ex.: `...\OMEGA_OS_Kernel`)  
   - `OMEGA_GIT_REPO_KUIPER` — raiz do repositório com `.git` (ex.: `...\nebular-kuiper`)  

5. **Spike Postgres:** só após gate interno; variável `OMEGA_PG_DSN` ou `FIN_SENSE_DSN` (nunca commitar o valor).

---

## 4. Ordem obrigatória de execução (até conclusão)

Ordem: **L-06 → L-04 → L-07 → Fase 8 (Postgres)**.  
Motivo: evitar smoke e validação em clone desalinhado (L-06 primeiro); validar contrato JSON antes de massificar evidências (L-04); depois integração dry-run (L-07); por último dependência externa L3 (Postgres).

---

## 5. Procedimento L-06 — Paridade Git

**Objetivo:** Dois `HEAD` iguais **ou** política explícita de divergência documentada numa linha na ata.

**Comando (raiz `Auditoria PARR-F`):**

```powershell
python protocol/PSA/git_parity_check.py --label-a desktop --label-b kuiper
```

(opcional: `--repo-a` e `--repo-b` com paths absolutos.)

**Onde grava:**

- `00_PROVAS_AUDITORIA\ssot_HEAD_desktop.txt`
- `00_PROVAS_AUDITORIA\ssot_HEAD_kuiper.txt`
- `00_PROVAS_AUDITORIA\ssot_parity_report_<UTC>.json`

**Porquê:** prova objectiva de alinhamento entre clones antes de L-04/L-07.

**Bloqueio opcional:** `set OMEGA_REQUIRE_GIT_PARITY=1` — exit **1** se houver erro Git ou divergência de `HEAD`.

**Aceite:** `parity_match: true` no JSON **ou** ata com excepção aprovada.

---

## 6. Procedimento L-04 — Validação em lote (jsonschema)

**Objetivo:** Cada audit gerado cumpre `Conselho\AUDIT_JSON_SCHEMA_V1.0.json` (não basta JSON sintacticamente válido).

**Comando:**

```powershell
python protocol/PSA/validate_audit_batch.py `
  --schema "Conselho\AUDIT_JSON_SCHEMA_V1.0.json" `
  --glob "00_PROVAS_AUDITORIA\orchestrator_runs\omega_audit_PARRF_*.json" `
  --max 200 `
  --csv-out "00_PROVAS_AUDITORIA\l04_validation_report.csv" `
  --json-summary "00_PROVAS_AUDITORIA\l04_validation_summary.json"
```

**Onde grava:** paths indicados em `--csv-out` e `--json-summary` (sempre sob `00_PROVAS_AUDITORIA\`).

**Aceite:** exit code **0** e `pass_rate = 1.0` no summary.

**Se não existirem audits ainda:** usar primeiro L-07 (secção 7) **ou** `--allow-empty` apenas com **ata** que explique ausência temporária.

**Risco:** audits antigos fora do schema — política: corrigir orquestrador / arquivar JSONs antigos fora do glob, **documentado** numa linha na ata.

---

## 7. Procedimento L-07 — Smoke do orquestrador

**Objetivo:** N execuções (padrão **10**) com exit 0 e `status != "ERROR"` no audit associado.

**Comando:**

```powershell
python protocol/PSA/smoke_orchestrator_l07.py --runs 10
```

**Onde grava:**

- Logs e cópias de audit: `00_PROVAS_AUDITORIA\orchestrator_runs\l07_smoke_*`
- Resumo: `00_PROVAS_AUDITORIA\orchestrator_runs\l07_smoke_summary_<UTC>.json`

**Aceite:** script exit **0**; taxa de sucesso 100% no summary.

**Nota:** `OMEGA_USE_FIN_SENSE_L1=1` só se o módulo e dependências estiverem disponíveis; caso contrário omitir variável (stub L1).

---

## 8. Procedimento Fase 8 — Spike Postgres (read-only)

**Pré-condição:** aprovação interna (CFO/COO) + DSN apenas em ambiente seguro.

**Comando:**

```powershell
set OMEGA_PG_DSN=postgresql://user:***@host:5432/dbname
python protocol/PSA/postgres_spike_phase8.py
```

**Onde grava:**

- `00_PROVAS_AUDITORIA\spike_phase8_<trace_id>.json`
- `00_PROVAS_AUDITORIA\spike_phase8_<trace_id>.txt`

**Aceite:** exit **0** e `phase8_pass: true` no JSON.

**Porquê:** prova L3 de conectividade sem confundir com GO live.

---

## 9. PSA — Pacote `PSA_PROTOCOL_DEPLOY` (quando aplicável)

Se a ordem de trabalho exigir prova de **pacote espelhado** (golden points):

1. Executar `protocol\PSA\PSA_PROTOCOL_DEPLOY.ps1` conforme `SPEC_PSA_COMPLETION_PROOF.md` (parâmetro `-ParrfRoot` = raiz `Auditoria PARR-F`).  
2. Evidências **apenas** em `00_PROVAS_AUDITORIA\PSA\<DOC_ID>\<RUN_ID>\`.

Este runbook **não substitui** a SPEC; **complementa** as etapas L-04/L-06/L-07/Fase 8 executadas fora do mirror PSA.

---

## 10. GitHub — O que versionar e como concluir no repositório

**Incluir no commit (após runs bem-sucedidos):**

- Alterações em `protocol\PSA\*.py`, `requirements-psa.txt`, `Conselho\` (documentos normativos), `PACOTE_PSA_ENVIO_MINIMO.md` se alterado.  
- Evidências em `00_PROVAS_AUDITORIA\` **desde que** não contenham segredos (DSN completo, passwords). Os scripts de spike e relatórios já devem usar DSN sanitizado nos `.txt`/`.json` gerados — **revisar** antes do `git add`.

**Não commitar:**

- Ficheiros com DSN/password em claro.  
- Artefactos pessoais fora da árvore PARR-F.

**Procedimento Git sugerido (na raiz do repo que contém `.git`):**

```powershell
git status
git add protocol/PSA/*.py requirements-psa.txt Conselho/DOC-PARRF-PSA-RUNBOOK-EXECUCAO-L04-L06-L07-FASE8-V120-20260415.md
git add 00_PROVAS_AUDITORIA/*.json 00_PROVAS_AUDITORIA/*.csv 00_PROVAS_AUDITORIA/orchestrator_runs/l07_* 00_PROVAS_AUDITORIA/ssot_* 00_PROVAS_AUDITORIA/spike_phase8_* 
# ajustar lista: só ficheiros sem segredos
git commit -m "docs(psa): runbook L-06 L-04 L-07 Fase8 + evidências"
git push origin main
```

(Ajustar branch remota conforme política do projeto.)

---

## 11. Critério de conclusão global (checklist PSA)

| # | Gate | Evidência mínima |
|---|------|-------------------|
| 1 | L-06 | `ssot_parity_report_*.json` com `parity_match: true` **ou** ata de excepção |
| 2 | L-04 | `l04_validation_summary.json` com `exit_ok: true` e `pass_rate: 1` |
| 3 | L-07 | `l07_smoke_summary_*.json` com `l07_accepted: true` |
| 4 | Fase 8 | `spike_phase8_*.json` com `phase8_pass: true` (quando DSN disponível) |
| 5 | GitHub | Commit pushed com os artefactos acima (sem segredos) |

Quando **1–3** estiverem verdes, o trilho **core** deste runbook está **concluído** para ambientes sem Postgres; **4** fecha L3 de base de dados quando autorizado.

---

## 12. Como o PSA deve prosseguir até ao fim (resumo operacional)

1. Abrir este documento na pasta `Conselho\` e fixar o `PARRF_AUDIT_TREE_ROOT` em uso.  
2. Executar secções **5 → 6 → 7** em sequência; gravar **todos** os outputs sob `00_PROVAS_AUDITORIA\`.  
3. Se política exigir, correr **secção 9** (`PSA_PROTOCOL_DEPLOY.ps1`).  
4. Após gate CFO/COO, executar **secção 8** e arquivar JSON/TXT gerados.  
5. Revisar ficheiros para **zero segredos**; executar **secção 10** (Git).  
6. Preencher **secção 11** checklist e anexar a ata de fecho (1 página) com IDs e timestamps UTC.

---

## 13. Registo de alterações

| Versão | Data | Notas |
|--------|------|--------|
| 1.0.0 | 2026-04-15 | Versão inicial: runbook completo L-06, L-04, L-07, Fase 8, GitHub. |

---

**Fim do documento** — `DOC-PARRF-PSA-RUNBOOK-EXECUCAO-L04-L06-L07-FASE8-V120-20260415`
