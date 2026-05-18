# PSA — Solicitação CTO (Tier-0)

**Pasta:** `audit/psa_inbound/PSA_SOLICITACAO_CTO_AUDITORIA_20260518/`

| Ficheiro | Descrição |
|----------|-----------|
| `INSTRUCOES_PSA_ENTREGA_TIER0_v1.md` | Instruções completas ao PSA (entrega, anti-contaminação, colunas). |
| `PSA_MANIFEST.template.json` | Modelo de manifesto — **copiar** para o pacote final como `PSA_MANIFEST.json` e preencher. |

**Documento único para o CEO reencaminhar ao PSA:**  
`DOCUMENTO_ENVIAR_AO_PSA.md`

**Script de validação (engenharia / PSA após export):**

- `scripts/validate_psa_tier0_package.py --package <pasta_pacote>`
- `scripts/psa_hash_artifacts.ps1 -PackageDir <pasta_pacote>` (PowerShell — hashes para o manifesto)
- `scripts/psa_seal_manifest.ps1 -PackageDir <pasta_pacote>` (PowerShell — gera `PSA_MANIFEST.sha256`)

**Onde PSA deve gravar o pacote final:**  
`SOURCE_CODE/audit/psa_inbound/PSA_PACOTE_TIER0_<YYYYMMDD>_<HHMMSS>Z/`

Após `PSA_VALIDATION_REPORT.json` com `status: PASS`, a engenharia produz o documento CEO actualizado.
