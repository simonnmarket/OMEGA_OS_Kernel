# Runbook único — Fecho de pendências operacionais OMEGA / PSA Tier-0

| **ID do documento** | `RUNBOOK-OMEGA-PEND-20260403-001` |
|---------------------|-----------------------------------|
| **Versão** | 1.0 |
| **Data** | 2026-04-03 |
| **Âmbito** | Encerrar, de forma **única e rastreável**, todas as fontes de divergência operacional listadas em auditoria; servir de **guia único** quando o PSA emitir conclusões — sem reabrir ciclos de documentos paralelos. |

---

## 1. Princípio de governação (alinhado à equipa)

O **módulo** é considerado **construído e validado** pelos **testes e pela cadeia Tier-0** definida para esse pacote. **Evidências posteriores** à execução (dados novos, ambiente, drift de branch, metadado `git_commit_sha` desalinhado) tratam-se como **variáveis operacionais** ou **estado de repositório**, **não** como falha automática da construção do módulo — salvo quando um teste objectivo (hash, exit code, contrato) falhar.

Este runbook **não substitui** `INSTR-PSA-DEF-20260403-001`; **complementa-o** com o que falta para **lista de pendências = zero** no processo operacional global do repo.

---

## 2. Constantes (ajustar se o caminho local for diferente)

| Símbolo | Valor típico (Windows) |
|---------|-------------------------|
| `REPO_ROOT` | `…\nebular-kuiper` (raiz do clone) |
| `EVID` | `REPO_ROOT\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo` |

**Variável opcional:** `NEBULAR_KUIPER_ROOT` = caminho absoluto de `REPO_ROOT`.

---

## 3. Pendências → ações → critério de fecho

### P1 — Submódulos / pastas `OMEGA_INTELLIGENCE_OS` e `OMEGA_OS_Kernel` (estado `m` no `git status`)

**Efeito se ficar aberto:** builds ou pipelines que dependam destes caminhos podem divergir entre máquinas.

**Ações (escolher UMA linha de decisão):**

**A) Integrar alterações pretendidas**

```powershell
cd $REPO_ROOT
git submodule status
git -C OMEGA_INTELLIGENCE_OS status
git -C OMEGA_OS_Kernel status
# Em cada pasta: rever diff, commit no sub-repositório se aplicável, depois na raiz:
git add OMEGA_INTELLIGENCE_OS OMEGA_OS_Kernel
git commit -m "chore: alinhar submódulos OMEGA_INTELLIGENCE_OS / OMEGA_OS_Kernel"
```

**B) Descartar alterações locais não desejadas**

```powershell
cd $REPO_ROOT
git submodule update --init --recursive
git -C OMEGA_INTELLIGENCE_OS checkout -- .
git -C OMEGA_OS_Kernel checkout -- .
# ou reset duro apenas se política interna permitir
```

**Critério de fecho P1:** `git status` **sem** `m` nestes caminhos (ou commit explícito que os fixe).

---

### P2 — Divergência remota (`main` ahead of `origin/main`)

**Efeito:** outro clone em `origin/main` não reproduz o mesmo estado até push/pull.

**Ações:**

```powershell
cd $REPO_ROOT
git fetch origin
git log --oneline origin/main..HEAD
# Revisar commits locais; quando aprovado:
git push origin main
```

**Critério de fecho P2:** `git status -sb` sem `ahead N` **ou** política explícita de branch de integração documentada (ex.: PR aberto).

---

### P3 — AVISO `HEAD` ≠ `git_commit_sha` no manifesto

**Efeito:** metadado desalinhado; **não** invalida secção [3] do verify após a mitigação do script.

**Ações:**

```powershell
cd $EVID
python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head
python verify_tier0_psa.py
```

**Critério de fecho P3:** `verify_tier0_psa.py` com **exit 0** e **sem** AVISO de divergência **ou** aceitação explícita de AVISO com registo em minuta (equipa aceita metadado pendente até próximo sync).

---

### P4 — Gate e PRFs (pacote PSA)

**Ações:**

```powershell
cd $EVID
python psa_gate_conselho_tier0.py --out-relatorio 04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt
python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head
python verify_tier0_psa.py
python 04_relatorios_tarefa\psa_refutation_checklist.py --validate "04_relatorios_tarefa\templates_auditoria_psa\prova_PRF-PHFS02-20260403-001.json"
# repetir para PHFS03 e PHFS04 (ajustar apenas o nome do ficheiro prova_PRF-…)
```

(CWD = `evidencia_pre_demo`; caminhos relativos a essa pasta.)

**Critério de fecho P4:** `GATE_GLOBAL: PASS`, PRFs com **PASS**, `verify` **exit 0** após sync se o gate alterou ficheiros manifestados.

---

### P5 — Métricas numéricas (stress / `z_score`)

**Efeito:** interpretação errada se se usar só `abs_z_max`; **não** é falha Tier-0 se o gate aceitar critérios opcionais.

**Ações:** em relatórios e dashboards, **priorizar P95/P99** (ou métricas acordadas) para narrativa; documentar no relatório de produto que **outliers extremos** podem existir por artefacto numérico.

**Critério de fecho P5:** política de narrativa **escrita** (parágrafo no relatório interno) — não exige novo script.

---

### P6 — Novos commits / entradas no manifesto

**Regra:** qualquer ficheiro novo rastreado no `MANIFEST_RUN_*.json` exige **sync + verify** após edição.

**Critério de fecho P6:** manifesto sempre actualizado via `psa_sync_manifest_from_disk.py` antes de homologação.

---

### P7 — Ambiente (Python, paths, dados)

**Ações mínimas:**

```powershell
python --version
cd $EVID
dir 02_logs_execucao\STRESS_V10_5_SWING_TRADE.csv
echo $env:NEBULAR_KUIPER_ROOT
```

**Critério de fecho P7:** mesmo `REPO_ROOT`, mesma versão Python documentada, ficheiros de stress presentes nos paths do manifesto.

---

## 4. Ordem única recomendada (uma passagem)

1. P1 (submódulos)  
2. P3 → P4 (sync, verify, gate, PRFs, sync de novo se necessário)  
3. P2 (push)  
4. P5 (texto de narrativa de métricas)  
5. P6–P7 verificação final

---

## 5. Script consolidado (PowerShell — bloco único)

Copiar para `.ps1` ou colar no terminal **após** definir `$REPO_ROOT`:

```powershell
$REPO_ROOT = "C:\caminho\para\nebular-kuiper"  # EDITAR
$EVID = Join-Path $REPO_ROOT "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo"
$env:NEBULAR_KUIPER_ROOT = $REPO_ROOT
Set-Location $EVID
python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python verify_tier0_psa.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python psa_gate_conselho_tier0.py --out-relatorio 04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head
python verify_tier0_psa.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Set-Location $REPO_ROOT
git status -sb
```

Depois executar PRFs manualmente ou acrescentar linhas `python ... psa_refutation_checklist.py --validate ...` conforme P4.

---

## 6. Definição de “processo fechado” para este runbook

| # | Condição |
|---|----------|
| C1 | `verify_tier0_psa.py` → exit **0** |
| C2 | `psa_gate_conselho_tier0.py` → **GATE_GLOBAL: PASS** na última corrida |
| C3 | PRFs relevantes → **PASS** |
| C4 | `git status` sem pendências não decididas em P1; remoto alinhado conforme P2 |
| C5 | Política P5 registada onde publicam métricas |

Quando **C1–C5** forem verdadeiros, considera-se **fechado o processo de pendências** coberto por este ID; o PSA pode emitir documento de conclusão **sem** reabrir itens desta lista.

---

## 7. Fim do documento

**ID:** `RUNBOOK-OMEGA-PEND-20260403-001` · **Versão:** 1.0
