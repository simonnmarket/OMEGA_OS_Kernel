# Documento final — Execução, correcções e conclusão da fase (PH-TR-01 / pós FS-04)

| Campo | Valor |
|-------|--------|
| **Doc-ID** | `DOC-FINAL-EXEC-PH-TR01-20260327` |
| **Versão** | 1.0 |
| **Tipo** | Pacote **executável** — PSA / equipa técnica |
| **Fase alvo** | **PH-TR-01** (transição Tier-0, gate, prontidão para Conselho) **após** conclusão **PH-FS-01…PH-FS-04** |
| **Normas** | `DOC-UNICO-ENCERRAMENTO-AUDITORIA-20260327` v2.0 · `DOC-UNICO-PSA-MESTRE-20260403` · `DOC-OFC-PSA-PROVAS-AUD-20260403` |

---

## 1. Raiz do repositorío (obrigatório fixar)

Todas as rotas abaixo assumem a **raiz Git** do projecto **nebular-kuiper**.

| Conceito | Valor (exemplo neste ambiente) |
|----------|---------------------------------|
| **Raiz repo** | `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper` |
| **Pasta de relatórios PSA (04)** | `Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa` |
| **Variável opcional** | `NEBULAR_KUIPER_ROOT` = raiz do repo (usada pelo gate) |

**Link local (explorador / browser):**  
[Abrir pasta 04_relatorios_tarefa](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/04_relatorios_tarefa/)

---

## 2. Estado pré-requisito (FS — já concluído)

Antes de executar esta fase, deve existir:

| Verificação | Artefacto |
|-------------|-----------|
| Encerramento FS | `DOCUMENTO_UNICO_OFICIAL_PSA_ENCERRAMENTO_AUDITORIA_E_PROXIMOS_PASSOS.md` **v2.0** |
| KPI | `KPI_REPORT_20260403-001.json` |
| Catálogo §4 | `CATALOGO_OHLCV_PLANO_v1.md` (KPI-06 PROVADO) |
| PRFs | `templates_auditoria_psa/prova_PRF-PHFS02-*.json` … `prova_PRF-PHFS04-20260403-001.json` |
| Matriz | `templates_auditoria_psa/MATRIZ_SOL_TAR_REQ_PRF_DEC_TEMPLATE.csv` |
| Log | `PSA_RUN_LOG.jsonl` (inclui trilho PH-FS-04) |
| Manifesto | `03_hashes_manifestos/MANIFEST_RUN_20260329.json` (`git_commit_sha` alinhado ao HEAD) |

---

## 3. O que esta fase resolve (PH-TR-01)

| Objectivo | Descrição |
|-----------|-----------|
| **Gate Tier-0** | Revalidar **git HEAD**, **audit_trade_count** no stress CSV, **verify_tier0_psa** contra manifesto. |
| **Correcções** | Corrigir **falhas de gate** (ficheiros em falta no manifesto, paths) e **re-sincronizar** manifesto se a política do Conselho o exigir. |
| **Provas PRF** | Garantir que **todas** as PRFs em uso passam `--validate` e que **`git_head`** = `git rev-parse HEAD` **no momento do commit** de selo. |
| **Conclusão da etapa** | **GATE_GLOBAL: PASS** + relatório gravado + opcional linha em `PSA_RUN_LOG.jsonl` (`gate_pass` ou `audit_record`). |

---

## 4. Scripts — localização e invocação

### 4.1 Gate Conselho Tier-0 (principal)

| Item | Valor |
|------|--------|
| **Ficheiro** | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/psa_gate_conselho_tier0.py` |
| **Link** | [psa_gate_conselho_tier0.py](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/psa_gate_conselho_tier0.py) |

**PowerShell (na raiz do repo):**

```powershell
Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:NEBULAR_KUIPER_ROOT = (Get-Location).Path
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py" --out-relatorio "04_relatorios_tarefa\PSA_GATE_CONSELHO_ULTIMO.txt"
```

**Interpretação:** `GATE_GLOBAL: PASS` apenas se `audit_trade_count` e `verify_tier0_psa` terminarem com **exit 0**.

---

### 4.2 Validação de provas PRF (JSON)

| Item | Valor |
|------|--------|
| **Ficheiro** | `04_relatorios_tarefa/psa_refutation_checklist.py` |
| **Link** | [psa_refutation_checklist.py](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/04_relatorios_tarefa/psa_refutation_checklist.py) |

**Validar as três PRFs FS:**

```powershell
Set-Location "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$base = "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\templates_auditoria_psa"
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\psa_refutation_checklist.py" --validate "$base\prova_PRF-PHFS02-20260403-001.json"
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\psa_refutation_checklist.py" --validate "$base\prova_PRF-PHFS03-20260403-001.json"
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\04_relatorios_tarefa\psa_refutation_checklist.py" --validate "$base\prova_PRF-PHFS04-20260403-001.json"
```

**Esperado:** três linhas `PASS proof file OK` e **exit code 0**.

---

### 4.3 Kit FIN-SENSE (referência / métricas)

| Item | Valor |
|------|--------|
| **Ficheiro** | `04_relatorios_tarefa/finsense_validation_kit.py` |
| **Link** | [finsense_validation_kit.py](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/04_relatorios_tarefa/finsense_validation_kit.py) |

Uso conforme imports nos pipelines de QA do repositório (não é o gate principal; ver docstrings no ficheiro).

---

### 4.4 Scripts chamados *internamente* pelo gate

| Script | Caminho relativo à raiz |
|--------|-------------------------|
| `audit_trade_count.py` | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/audit_trade_count.py` |
| `verify_tier0_psa.py` | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/verify_tier0_psa.py` |

**Dados:** `02_logs_execucao/STRESS_V10_5_SWING_TRADE.csv`  
**Manifesto:** `03_hashes_manifestos/MANIFEST_RUN_20260329.json`

---

## 5. Correcções típicas se `GATE_GLOBAL: FAIL`

| Sintoma | Acção |
|---------|--------|
| `verify_tier0_psa exit: 1` — ficheiro em falta | Criar o ficheiro referido **ou** actualizar o manifesto (processo `psa_sync_manifest_from_disk.py` se existir no repo) **ou** remover entrada obsoleta com aprovação. |
| `proof_id` / `req_id` PRF inválidos | Corrigir JSON e alinhar `MATRIZ_*`; voltar a correr §4.2. |
| **`git_head` PRF ≠ HEAD** | Actualizar campo `git_head` na PRF para `git rev-parse HEAD` do commit de selo; revalidar §4.2. |
| HEAD manifesto desalinhado | Após commit, actualizar `git_commit_sha` no `MANIFEST_RUN_*.json` (processo oficial do projeto). |

---

## 6. Sequência recomendada (checklist de execução)

1. `Set-Location` para a **raiz** do repo.  
2. `git status` — working tree limpo ou alterações apenas documentadas.  
3. `git rev-parse HEAD` — anotar SHA.  
4. Executar §4.2 (três `--validate` nas PRFs).  
5. Executar §4.1 (gate com `--out-relatorio` para `PSA_GATE_CONSELHO_ULTIMO.txt`).  
6. Se **PASS**: abrir [PSA_GATE_CONSELHO_ULTIMO.txt](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt) e confirmar resumo.  
7. Opcional: acrescentar em `PSA_RUN_LOG.jsonl` uma linha JSON com `action`: `gate_pass`, `git_head`: SHA actual, `metrics.verify_tier0_exit`: 0.  
8. **Conselho:** anexar pacote mínimo: `DOC-UNICO-ENCERRAMENTO-AUDITORIA-20260327` v2.0, `KPI_REPORT_20260403-001.json`, matriz, `PSA_GATE_CONSELHO_ULTIMO.txt`, amostra do `PSA_RUN_LOG.jsonl`.

---

## 7. Artefactos de referência (links rápidos)

| Documento | Link local |
|-----------|------------|
| Encerramento FS v2.0 | [DOCUMENTO_UNICO_OFICIAL_PSA_ENCERRAMENTO_AUDITORIA_E_PROXIMOS_PASSOS.md](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOCUMENTO_UNICO_OFICIAL_PSA_ENCERRAMENTO_AUDITORIA_E_PROXIMOS_PASSOS.md) |
| Auditoria processo | [DOCUMENTO_UNICO_AUDITORIA_CONCLUSAO_E_FALHAS_PROCESSO.md](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/04_relatorios_tarefa/DOCUMENTO_UNICO_AUDITORIA_CONCLUSAO_E_FALHAS_PROCESSO.md) |
| KPI Report | [KPI_REPORT_20260403-001.json](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/04_relatorios_tarefa/KPI_REPORT_20260403-001.json) |
| Catálogo OHLCV | [CATALOGO_OHLCV_PLANO_v1.md](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/04_relatorios_tarefa/CATALOGO_OHLCV_PLANO_v1.md) |
| Log PSA | [PSA_RUN_LOG.jsonl](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/04_relatorios_tarefa/PSA_RUN_LOG.jsonl) |
| Manifesto | [MANIFEST_RUN_20260329.json](file:///C:/Users/Lenovo/.gemini/antigravity/playground/nebular-kuiper/Auditoria%20PARR-F/N%C3%BAcleo%20de%20Valida%C3%A7%C3%A3o%20OMEGA/evidencia_pre_demo/03_hashes_manifestos/MANIFEST_RUN_20260329.json) |

*(Se a raiz do repo for diferente, substituir o prefixo `C:\Users\Lenovo\.gemini\...\nebular-kuiper` nos links `file:///`. Os links usam codificação URL para acentos e espaços.)*

---

## 8. Critérios de conclusão desta etapa (PH-TR-01)

| # | Critério |
|---|----------|
| C1 | `psa_refutation_checklist.py --validate` → **PASS** para todas as PRFs activas (FS-02, FS-03, FS-04). |
| C2 | `psa_gate_conselho_tier0.py` → **GATE_GLOBAL: PASS** e `PSA_GATE_CONSELHO_ULTIMO.txt` actualizado. |
| C3 | `git_commit_sha` no manifesto = `git rev-parse HEAD` (após último commit de sincronização). |
| C4 | Pacote ao Conselho preparado (lista §6 item 8). |

---

## 9. Fecho

Este documento é o **pacote único de execução** para a fase **PH-TR-01**: scripts, caminhos, correcções típicas, links e critérios de conclusão. Qualquer alteração de estrutura de pastas no repo exige **revisão** dos caminhos e nova **corrida de gate**.

---

*Fim — `DOC-FINAL-EXEC-PH-TR01-20260327` v1.0*
