| **ID** | `PSA-NOTIFY-CORR-FINAL-20260403-001` |
|--------|--------------------------------------|
| **Versão** | 1.0 |
| **Data** | 2026-04-03 |
| **Destinatário** | PSA (Núcleo de Validação) |
| **Assunto** | Correcções aplicadas no repositório; informações complementares; encerramento da presente etapa |

---

## 1. Correcções já efectuadas (executadas)

As seguintes acções foram **realizadas no repositório** `nebular-kuiper` (remoto associado: `origin` → `main`):

| # | Acção | Finalidade |
|---|--------|------------|
| 1 | **Merge de `origin/main`** com resolução de conflitos no `MANIFEST_RUN_20260329.json` | Unificar histórico divergente (RUNBOOK / gate / documentos de selo) sem perder entradas do manifesto. |
| 2 | **Execução repetida de `psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head`** | Alinhar bytes, SHA3-256 e campo `git_commit_sha` ao estado do disco e ao `HEAD` quando aplicável. |
| 3 | **`verify_tier0_psa.py`** | Confirmar **exit 0** e integridade da secção [3] (ficheiros manifestados) + gateway. |
| 4 | **Commits de alinhamento do manifesto** + **`git push origin main`** | Publicar o estado corrigido e **alinhar `main` local com `origin/main`** (sem ahead/behind pendente após o último push bem-sucedido). |
| 5 | **Submódulos `OMEGA_INTELLIGENCE_OS` e `OMEGA_OS_Kernel`** | Remoção do estado `m` na raiz mediante **`git stash push -u`** em cada submódulo (mensagem de stash: `tier0-seal-pending`). **O trabalho local não foi eliminado** — está em stash para recuperação controlada. |

---

## 2. Informações complementares (para acta e sem surpresas)

### 2.1 AVISO `HEAD` vs `git_commit_sha` no `verify`

Após a mitigação em `verify_tier0_psa.py`, **divergência entre `git rev-parse HEAD` e o campo `git_commit_sha` no JSON** pode surgir **com exit 0** e **AVISO**, **sem** invalidar a custódia **byte-a-byte** dos ficheiros na secção [3]. Isto pode ocorrer **mesmo com árvore Git limpa**, porque o valor de `git_commit_sha` gravado no último commit **não coincide** necessariamente com o hash do **commit seguinte** que o inclui.

**Regra operacional:** **exit 0** com secção [3] OK = **Tier-0 de custódia de artefactos homologável**; o AVISO é **metadado** — corrigir com `psa_sync` + novo commit **se** a política interna exigir **zero avisos** na saída do script.

### 2.2 Recuperação do trabalho nos submódulos (se necessário)

```text
cd OMEGA_INTELLIGENCE_OS
git stash list
git stash pop   # quando a equipa decidir reintegrar

cd ../OMEGA_OS_Kernel
git stash list
git stash pop
```

### 2.3 Documentos de referência já existentes

Não substituir o presente aviso; apenas complementar:

- `INSTR-PSA-DEF-20260403-001`
- `RUNBOOK-OMEGA-PEND-20260403-001`
- `CONCL-OMEGA-TIER0-SELO-20260403-001` (conclusão selada)

---

## 3. Finalização da etapa (para o PSA)

Com base no acima:

- A **correcção operacional** (merge, manifesto, push, limpeza de estado `m` na raiz via stash) está **documentada e executada**.
- O **repositório remoto** foi **actualizado** com os commits de correcção.
- A **etapa** de saneamento / alinhamento **Tier-0 PSA** associada a esta correção pode ser considerada **finalizada** para efeitos de **processo**, desde que o PSA **arquive** este ID e **anexe** (ou registe) as últimas saídas de **`verify_tier0_psa.py`** e, se aplicável, do **gate** e **PRFs**, conforme o vosso modelo de acta.

**Não** é necessário novo documento paralelo para **fechar** esta etapa — **este ficheiro** serve de **notificação única** ao PSA.

---

## 4. Fim do documento

**ID:** `PSA-NOTIFY-CORR-FINAL-20260403-001` · **Versão:** 1.0
