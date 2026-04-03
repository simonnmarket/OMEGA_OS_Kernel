| **ID** | `CONCL-OMEGA-TIER0-SELO-20260403-001` |
|--------|----------------------------------------|
| **Versão** | 1.0 FINAL |
| **Data** | 2026-04-03 |
| **Efeito** | Encerramento e **selo** do processo: lista de verificação **única** para **zero pendências** documentais e operacionais, alinhada a `INSTR-PSA-DEF-20260403-001` e `RUNBOOK-OMEGA-PEND-20260403-001`. |

---

## 1. Documentos de referência (não substituir; apenas concluir)

| ID | Ficheiro |
|----|----------|
| `INSTR-PSA-DEF-20260403-001` | `INSTR_PSA_DEFINITIVA_EXECUCAO_TIER0_20260403_001.md` |
| `RUNBOOK-OMEGA-PEND-20260403-001` | `DOC_RUNBOOK_FECHO_PENDENCIAS_OPERACIONAIS_OMEGA_20260403_001.md` |
| Mandato / fecho CEO | `DOCUMENTO_OFICIAL_PSA_MANDATO_EXECUCAO_PERMANENTE_E_ENCERRAMENTO_CEO.md`, `DOCUMENTO_OFC_CEO_FECHO_AUDITORIA_PSA.md` (se aplicável) |

---

## 2. Selo binário — condições para “processo concluído”

Todas as linhas seguintes devem estar **verdadeiras** no momento da homologação pelo Conselho:

| ID | Condição | Comando / prova |
|----|----------|-----------------|
| **S1** | `verify_tier0_psa.py` → exit **0** | `python verify_tier0_psa.py` (CWD = `evidencia_pre_demo`) |
| **S2** | Sem AVISO de `HEAD` vs manifesto **ou** AVISO aceite por acta | Preferível: `psa_sync` + verify **sem** AVISO |
| **S3** | `GATE_GLOBAL: PASS` na última execução do gate | `python psa_gate_conselho_tier0.py` |
| **S4** | PRFs Fin Sense → **PASS** | `psa_refutation_checklist.py --validate` por ficheiro |
| **S5** | Manifesto gravado **commitado** após último `psa_sync` | `git status` sem `M` em `MANIFEST_RUN_20260329.json` pendente |
| **S6** | Submódulos **sem** alteração pendente não decidida | `git status` sem `m` em `OMEGA_INTELLIGENCE_OS` / `OMEGA_OS_Kernel` **ou** commit explícito que as integre |
| **S7** | Remoto alinhado à política (sem ahead/behind não resolvido) | `git status -sb` sem `[ahead X, behind Y]` não tratado **ou** PR/branch documentado |
| **S8** | Política P5 (métricas P95/P99) referenciada onde publicam números | Evidência: parágrafo ou doc de produto |

---

## 3. Etapas finais — executar **nesta ordem** (operador PSA / DevOps)

**Prefixos:** `REPO_ROOT` = raiz `nebular-kuiper`; `EVID` = `…\evidencia_pre_demo`; `NEBULAR_KUIPER_ROOT=$REPO_ROOT`.

### Etapa A — Tier-0 e manifesto

```text
cd EVID
python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head
python verify_tier0_psa.py
```

**Sucesso:** exit 0; idealmente **sem** linha `AVISO` sobre HEAD/manifesto.

### Etapa B — Gate e PRFs

```text
cd EVID
python psa_gate_conselho_tier0.py --out-relatorio 04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt
python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head
python verify_tier0_psa.py
python 04_relatorios_tarefa\psa_refutation_checklist.py --validate 04_relatorios_tarefa\templates_auditoria_psa\prova_PRF-PHFS02-20260403-001.json
(repetir PHFS03, PHFS04)
```

**Sucesso:** `GATE_GLOBAL: PASS`; PRFs PASS; verify exit 0.

### Etapa C — Submódulos (fechar P1)

Escolher integração **ou** reset conforme `RUNBOOK` secção P1; até `git status` não mostrar `m` nos dois caminhos **ou** commit que fixe o estado pretendido.

### Etapa D — Git: manifesto e trabalho pendente

```text
cd REPO_ROOT
git add evidencia_pre_demo/03_hashes_manifestos/MANIFEST_RUN_20260329.json
git add (demais ficheiros Tier-0 homologados)
git commit -m "chore: selo final Tier-0 PSA manifesto alinhado (CONCL-OMEGA-TIER0-SELO-20260403-001)"
```

**Nota:** após este commit, correr **Etapa A** outra vez (sync + verify) **se** a política exigir `git_commit_sha` = HEAD no último commit.

### Etapa E — Remoto

```text
git fetch origin
(git pull --rebase origin main   OU   merge, conforme política)
git push origin main
```

**Sucesso:** `git status -sb` alinhado com a política (ex.: `main` = `origin/main`).

### Etapa F — Tag opcional (arquivo institucional)

```text
git tag -a psa-tier0-concl-fin-sense-20260403 -m "CONCL-OMEGA-TIER0-SELO-20260403-001"
git push origin psa-tier0-concl-fin-sense-20260403
```

---

## 4. Minuta para o Conselho (copiar / colar)

- **Processo:** Tier-0 PSA / Fin-Sense MVP — encerramento selado sob **`CONCL-OMEGA-TIER0-SELO-20260403-001`**.
- **Evidência:** anexar saída de `verify_tier0_psa.py` (última linha **ESTADO: OK**), excerto `GATE_GLOBAL: PASS`, e lista PRFs PASS.
- **Repositório:** SHA do commit homologado: `________________` (`git rev-parse HEAD`).
- **Pendências RUNBOOK:** declaradas **zero** após verificação de **S1–S8**.

---

## 5. Fim do processo

Quando **S1–S8** estiverem cumpridas e **Etapas A–E** (e **F** se usada) executadas, o processo descrito neste pacote fica **concluído e selado** para efeitos de auditoria interna, **sem obrigação** de novo documento paralelo.

**ID:** `CONCL-OMEGA-TIER0-SELO-20260403-001` · **Versão:** 1.0 FINAL

---

*Última verificação automática neste workspace (apenas referência): `psa_sync` + `verify` com **HEAD = manifest** e **ESTADO OK**; permanecem para o operador: **commit de manifesto**, **submódulos**, **sincronização remota** — conforme secções 2–3.*
