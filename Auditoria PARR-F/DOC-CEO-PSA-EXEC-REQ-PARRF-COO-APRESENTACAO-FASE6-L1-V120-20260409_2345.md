# PSA — Documento oficial de execução (Fase 6 L1)

**ID oficial (completo):** `DOC-CEO-PSA-EXEC-REQ-PARRF-COO-APRESENTACAO-FASE6-L1-V120-20260409_2345`  

**Timestamp COO:** 2026-04-09 23:45 CEST  
**Duração prevista:** ~6 minutos  
**Ordem:** sequencial **1 → 2 → 3** (não desviar)

**Documento de apresentação correlato (ID completo):**  
`REQ-PARRF-COO-APRESENTACAO-FASE6-L1-FIN-SENSE-SSOT-V120-20260406`

**Registo consolidado para envio (ID completo):**  
`DOC-PARRF-REGISTO-OFICIAL-CONSOLIDADO-PSA-COO-FASE6-L1-FIN-SENSE-V120-20260410`

**Alvo canónico (COO):** `C:\Users\Lenovo\Desktop\OMEGA_OS_Kernel\Auditoria PARR-F\`

---

## 1. Alinhamento SSOT crítico (~2 min)

**PowerShell (Windows):**

```powershell
cd "C:\Users\Lenovo\Desktop\OMEGA_OS_Kernel\Auditoria PARR-F"
git remote -v
git fetch origin
git rev-parse HEAD   # copiar para o relatório
git pull origin main
git status --porcelain
(Get-Item ".\omega_orquestador_tier0_v120.py").Length   # bytes no disco
Get-FileHash ".\omega_orquestador_tier0_v120.py" -Algorithm SHA256
git hash-object ".\omega_orquestador_tier0_v120.py"
```

*(Em ambientes Unix, equivalente a `ls -la` + tamanho: `wc -c omega_orquestador_tier0_v120.py`.)*

---

## 2. Execução E2E L1 PostgreSQL staging (~3 min)

**DSN:** apenas o confirmado pelo CEO (o exemplo abaixo é placeholder).

```powershell
cd "C:\Users\Lenovo\Desktop\OMEGA_OS_Kernel\Auditoria PARR-F"

$env:FIN_SENSE_DSN = "postgresql://finsense_user:staging_pass@localhost:5432/finsense_staging"
$env:OMEGA_USE_FIN_SENSE_L1 = "1"
$env:FIN_SENSE_L1_VIEW = "v_omega_l1_features_by_symbol"

1..3 | ForEach-Object {
    Write-Host "TESTE E2E $_/3" -ForegroundColor Green
    python omega_orquestador_tier0_v120.py
}
```

---

## 3. Relatório de auditoria obrigatório (~1 min)

```powershell
cd "C:\Users\Lenovo\Desktop\OMEGA_OS_Kernel\Auditoria PARR-F"

Get-ChildItem "omega_audit_PARRF_*.json" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 3 |
    ForEach-Object {
        Write-Host "JSON: $($_.Name)" -ForegroundColor Cyan
        Get-Content $_.FullName -Raw | ConvertFrom-Json | ConvertTo-Json -Depth 8
    }

$latest = Get-ChildItem "omega_audit_PARRF_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Get-Content $latest.FullName -Raw | Select-String "l1_integration_requested|l1_class|FinSenseL1Layer|provenance_sha256|errors"
```

---

## 4. Critérios PASS / FAIL (PSA)

| # | Critério | PASSAR | FALHAR |
|---|----------|--------|--------|
| 1 | `git rev-parse HEAD` = `5cae0a9dda67cc2652c11f86bd117146dcd65300` | SHA coincide | SHA diferente |
| 2 | Integridade `omega_orquestador_tier0_v120.py` | `git hash-object` = `5ffd653825c997958fd810a705f57ecf4b70b920` no SHA canónico *(referência observada)* | Hash diferente sem explicação |
| 2b | *(Legado COO)* Tamanho **9562** bytes (vs 9236 v0.0.1) | Só com confirmação COO para este SHA | Se valor diferente de **9562**, registar e escalar |
| 3 | Três ficheiros `omega_audit_PARRF_*.json` gerados após §2 | 3 ficheiros | Menos de 3 |
| 4 | JSON com `"l1_integration_requested": true` | Flag L1 pedida | Campo ausente / false |
| 5 | JSON com `"l1_class": "FinSenseL1Layer"` | L1 ativo | Stub (`DOSMetricsLayer`) |

**Nota:** tabela e procedimento consolidados em `DOC-PARRF-REGISTO-OFICIAL-CONSOLIDADO-PSA-COO-FASE6-L1-FIN-SENSE-V120-20260410`.

---

## 5. Marco seguinte (Conselho)

| Meta | Critério de sucesso | Artefacto |
|------|---------------------|-----------|
| L1 PostgreSQL real | `layers.dos.errors == []` e `provenance_sha256` preenchido (dados reais) | 3× JSON E2E com evidência **XAUUSD** |

---

## 6. Ordens executivas (COO)

- Executar **1 → 2 → 3** em sequência.
- Colar nos autos **logs completos** (git + JSONs ou excertos estruturados).
- **Não** alterar código durante esta execução PSA, salvo ordem escrita em contrário.
- **Não** afirmar “produção” sem L1 real validado com evidência nos JSONs.

---

**Assinatura de registo:** COO OMEGA OS KERNEL — Fase 6 execução final (texto de rota PSA; arquivo técnico em `Auditoria PARR-F/`).
