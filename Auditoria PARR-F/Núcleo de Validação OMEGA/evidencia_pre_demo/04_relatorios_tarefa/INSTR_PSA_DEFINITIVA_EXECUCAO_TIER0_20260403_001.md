# Instruções definitivas PSA — Tier-0 (execução única)

| **ID** | `INSTR-PSA-DEF-20260403-001` |
|--------|------------------------------|
| **Versão** | 1.0 |
| **Efeito** | Encerra o ciclo infinito commit ↔ manifesto: **exit 0** do `verify_tier0_psa.py` baseia-se em **bytes + SHA3-256** dos ficheiros; `HEAD` ≠ `git_commit_sha` é só **AVISO**, não falha. |

---

## PSA — executar nesta ordem (definitivo)

1. **CWD:** `Auditoria PARR-F/Núcleo de Validação OMEGA/evidencia_pre_demo`

2. **Sincronizar hashes e SHA de commit (quando quiserem alinhar o campo ao HEAD):**  
   `python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head`

3. **Verificar Tier-0:**  
   `python verify_tier0_psa.py`  
   - **Exit 0** = integridade dos ficheiros manifestados + gateway OK.  
   - Se aparecer **AVISO** sobre `HEAD != git_commit_sha`, **não é falha** — façam commit e, se quiserem o campo alinhado, repitam o passo 2.

4. **Gate:**  
   `python psa_gate_conselho_tier0.py --out-relatorio 04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt`  
   Se regravar o gate: passo 2 → 3 outra vez.

5. **PRFs:**  
   `python psa_refutation_checklist.py --validate <caminho/prova_PRF-….json>` por ficheiro.

6. **Commit / push / tag** conforme política interna. Após cada commit que altere ficheiros no manifesto: **passo 2** (opcional para alinhar texto `git_commit_sha`) + **passo 3** (obrigatório para prova).

---

## Regra de ouro

**Prova de custódia = secção [3] do verify (ficheiros).** O campo `git_commit_sha` no JSON é **metadado**; divergir do `HEAD` após commit **já não bloqueia** o Tier-0.

**Fim.**
