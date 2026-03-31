# Documento final PSA — execução de correcções e actualização on-time do Tier-0

**ID:** DOC-PSA-FINAL-20260331  
**Audiência:** PSA (único responsável por aplicar correcções e sincronizar custódia)  
**Objectivo:** qualquer alteração em código ou documentos rastreados **deve** seguir esta sequência para que `verify_tier0_psa.py` continue **ESTADO: OK** sem interpretação subjectiva.

---

## 1. Princípio

| Regra | Texto |
|-------|--------|
| P1 | **Todas** as correcções que afectem ficheiros listados em `03_hashes_manifestos/MANIFEST_RUN_20260329.json` são **executadas e validadas pelo PSA**. |
| P2 | Nenhum relatório ao Conselho cita números sem **stdout** de `audit_trade_count.py` ou `verify_tier0_psa.py` (Verdade Unificada). |
| P3 | Após edições, o manifesto **deve** reflectir **bytes** e **SHA3-256** actuais do disco — usar **`psa_sync_manifest_from_disk.py`**. |

---

## 2. Ficheiros de trabalho (caminhos relativos à raiz `nebular-kuiper`)

| Função | Caminho |
|--------|---------|
| Manifesto Tier-0 | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/03_hashes_manifestos/MANIFEST_RUN_20260329.json` |
| Sincronização PSA (novo) | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/psa_sync_manifest_from_disk.py` |
| Verificação automática | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/verify_tier0_psa.py` |
| Métricas CSV objectivas | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/audit_trade_count.py` |
| Runbook PowerShell (verify) | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/run_verify_tier0_psa.ps1` |
| Pacote narrativo completo | `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo/PACOTE_PSA_OMEGA_VERDADE_UNIFICADA_20260331.md` |

**Variável de ambiente (opcional):** `NEBULAR_KUIPER_ROOT` = caminho absoluto da raiz do repositório.

---

## 3. Script PSA — `psa_sync_manifest_from_disk.py`

**O que faz:** para cada entrada em `files` do manifesto, recalcula `bytes` e `sha3_256_full` a partir do disco, usando **a mesma lógica de caminhos** que `verify_tier0_psa.py` (STRESS em `02_logs_execucao`, RAW em `01_raw_mt5`, DEMO_LOG e restantes relativos a `REPO_ROOT`).

**Comandos:**

```powershell
Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:NEBULAR_KUIPER_ROOT = (Get-Location).Path

# Pré-visualizar alterações (não grava)
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_sync_manifest_from_disk.py" --dry-run

# Aplicar bytes + SHA3 ao manifesto
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_sync_manifest_from_disk.py"

# Opcional: alinhar git_commit_sha ao HEAD actual (ver secção 5)
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_sync_manifest_from_disk.py" --set-git-commit-sha-from-head
```

**Critério de sucesso (script):** termina com código `0`; imprime `OK: manifesto gravado:` ou lista de `[UPDATE]`.

---

## 4. Procedimento obrigatório após **qualquer** correcção (código ou doc rastreado)

Execute **na ordem**:

1. **Editar** os ficheiros necessários (ex.: `11_live_demo_cycle_1.py`, RT-E, pacotes `.md`, etc.).
2. **Sincronizar manifesto** (obrigatório se algum ficheiro do manifesto mudou):
   ```powershell
   python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_sync_manifest_from_disk.py"
   ```
3. **Registar métricas** de CSV citados (stress/demo):
   ```powershell
   python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\audit_trade_count.py" --csv "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\02_logs_execucao\STRESS_V10_5_SWING_TRADE.csv"
   ```
   Anexar o **stdout integral** ao dossiê (sem edição manual dos números).
4. **Git:** `git add` dos ficheiros afectados + manifesto; **commit** com mensagem clare (ex.: `PSA: correção X + sync manifest`).
5. **Alinhar `git_commit_sha`** no manifesto ao **novo** HEAD (ver secção 5).
6. **Verificar Tier-0:**
   ```powershell
   python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\verify_tier0_psa.py"
   ```
   **Obrigatório:** última linha `ESTADO: OK (Tier-0 verificação automática passou)` e exit code `0`.

Se **FALHA** em `[3]` (bytes/hash): repetir passo 2. Se **FALHA** em `[1]` (HEAD ≠ manifest): repetir secção 5.

---

## 5. Alinhamento `git_commit_sha` ↔ `HEAD`

O verificador exige: `git rev-parse HEAD` **==** campo `git_commit_sha` no JSON **no disco**.

**Fluxo recomendado (PSA):**

1. Depois do **primeiro** `git commit` que inclua o manifesto já actualizado em bytes/SHA3:
   ```powershell
   python "...\psa_sync_manifest_from_disk.py" --set-git-commit-sha-from-head
   ```
2. `git add` o manifesto + `git commit -m "PSA: alinhar git_commit_sha ao HEAD"`.
3. Executar **de novo** o passo 1: o **HEAD** mudou; pode ser necessário **repetir** `--set-git-commit-sha-from-head` + commit **até** `verify_tier0_psa.py` passar, **ou** usar **`git commit --amend`** no último passo conforme política interna — o critério objectivo é **apenas** `verify_tier0_psa.py` **ESTADO OK**.

**Regra prática:** o loop termina quando `verify_tier0_psa.py` imprime **ESTADO OK** e o working tree está limpo após commit.

---

## 6. Novo ficheiro a rastrear no manifesto

Se um ficheiro **novo** deve entrar na custódia:

1. Adicionar entrada em `files` no JSON (tipo `CODE_VERSION`, `DOCUMENT`, `STRESS_LOG`, etc.) com `relpath` / `filename` coerentes com `verify_tier0_psa.py`.
2. Executar `psa_sync_manifest_from_disk.py` para preencher `bytes` e `sha3_256_full`.
3. Seguir secções 4–5.

---

## 7. Documentos RT-E com SHA Git no texto

Ao actualizar a linha **SHA Git** em `RT_E_VITALSIGNS_MANDATO_20260331.md` (ou similares):

1. Usar o valor de `git rev-parse HEAD` **após** o commit que fecha a alteração **ou** o SHA acordado pela equipa.
2. Correr `psa_sync_manifest_from_disk.py` para actualizar o hash do `.md` no manifesto.
3. Nunca copiar SHA “à mão” sem `git rev-parse HEAD` no mesmo estado do repositório.

---

## 8. Checklist mínimo PSA (antes de declarar “sistema actualizado”)

- [ ] `psa_sync_manifest_from_disk.py` executado (sem `--dry-run` pendente de aplicar).
- [ ] `audit_trade_count.py` no CSV referido pelo relatório (stdout arquivado).
- [ ] `verify_tier0_psa.py` → **ESTADO OK**.
- [ ] `git status` limpo; commit(s) referenciados na comunicação interna.

---

## 9. Incorporação de novos scripts ao manifesto

Quando `psa_sync_manifest_from_disk.py` ou `audit_trade_count.py` forem alterados, **devem** estar listados no manifesto (ou adicionados conforme secção 6) e **sincronizados** antes do próximo gate Tier-0.

---

**Fim do DOC-PSA-FINAL-20260331**

*Documento operacional: sem números subjectivos; critério final = `verify_tier0_psa.py` exit 0.*
