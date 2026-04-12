# COMPLETION_PROOF (PSA)

| Campo | Valor |
|--------|--------|
| DOC_ID | `DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414` |
| RUN_ID | `20260412T232258Z_d4322ad9` |
| UTC | `2026-04-12T23:22:59.5210262Z` |
| HOST | `LAPTOP-SJN2KACD` |
| USER | `Lenovo` |
| RUN_ROOT | `C:\Users\Lenovo\Desktop\OMEGA_OS_Kernel\Auditoria PARR-F\00_PROVAS_AUDITORIA\PSA\DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414\20260412T232258Z_d4322ad9` |

## Gates (binÃ¡rio)

| Gate | Resultado |
|------|-----------|
| gate_paths_within_audit_zone | PASS |
| gate_four_files_present | PASS |
| gate_manifest_matches_mirror | PASS |
| gate_python_arbiter_selftest | PASS |
| gate_json_schema_parseable | PASS |
| gate_yaml_parseable | PASS |
| gate_completion_artifacts_present | PASS |

## SHA-256 (formato GNU `sha256sum`)
```
a4aaf818990cef12130213267b8655978838f9f3aece11d6265cd1cd80e3634e  mirror/DOC-PSA-EXEC-INTEGRACAO-GOLDEN-POINTS-V120-20260414.md
1b7c395b566d2750c97a57874d160c8dfdb09ee4700c74f33c28492af59e6589  mirror/GATES_NUMERICOS_V1.yaml
a241e0db7014cffe694d48d4717eb2ca57edcaad010dad5b23bd01a9f21b95c5  mirror/ARBITRO_MULTITF_V1.py
5840b5e7f0e3906624edcc68c1bbf0900394c6fcf87f7ec2b85310257796a57c  mirror/AUDIT_JSON_SCHEMA_V1.0.json
009c13223ba3c3bbd3fa9086c0f13f3eb18b53076c10576f1590aa0899e80d8e  MANIFEST.json
```

## Outcome
**OUTCOME=PASS**

Regra: **PASS** implica todos os gates = PASS; qualquer **FAIL** invalida a conclusÃ£o perante o Conselho.
