# Evidências automáticas — RT-A (Custódia)
**Gerado:** `2026-03-30T22:26:19Z` (UTC)
**REPO_ROOT:** `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper`
**evidencia_pre_demo:** `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo`

## Git
- `git rev-parse HEAD`: `2497789d961c29f57b152f35e3aca8e0719fe3e3`

## Inventário — manifestos
| Ficheiro | Bytes | SHA3-256 (prefixo) |
|----------|-------|---------------------|
| `MANIFEST_RUN_20260329.json` | 2745 | `324b5a23420886e762ef6edb…` |

## Ficheiros de stress — bytes + SHA3-256 + contagens
| Ficheiro | Bytes | SHA3-256 | Linhas | signal_fired True | abs(z)>=3.75 | abs(z)>1e6 |
|----------|-------|----------|--------|-------------------|--------------|------------|
| `STRESS_2Y_SWING_TRADE.csv` | 16074566 | `6b7f8fee065cb24a6b74ed25ef365c8b73648b47e2fb4562d4cddcb53b695809` | 100000 | 402 | 402 | 1 |
| `STRESS_2Y_DAY_TRADE.csv` | 16083040 | `570f334880e428ba67b1737c6f838611e316b7e42563034b6293f2d154939a75` | 100000 | 197 | 197 | 1 |
| `STRESS_2Y_SCALPING.csv` | 16098982 | `12825b5958591a4417163c2bceb988cd12dbfd6ef99cc3402a08d0fb8dff7405` | 100000 | 375 | 375 | 1 |

### Notas de leitura
- `signal_fired True` e contagens com abs(z)>=3.75 devem coincidir se o gateway ligar sinal ao limiar 3.75.
- Valores com abs(z)>1e6 indicam possível instabilidade numérica pontual.

## verify_tier0_psa.py
- **Exit code:** `0`

```text
=== verify_tier0_psa.py ===
REPO_ROOT: C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper
MANIFEST:  C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\03_hashes_manifestos\MANIFEST_RUN_20260329.json

[1] Git HEAD vs manifest git_commit_sha
    HEAD:             2497789d961c29f57b152f35e3aca8e0719fe3e3
    manifest:         2497789d961c29f57b152f35e3aca8e0719fe3e3
    OK: coincidem.

[2] git cat-file -t <sha_manifest>
    tipo: commit

[3] Ficheiros do manifesto (bytes + SHA3-256)
    [OK] STRESS_2Y_DAY_TRADE.csv bytes=16083040 sha3=570f334880e428ba...
    [OK] STRESS_2Y_SCALPING.csv bytes=16098982 sha3=12825b5958591a44...
    [OK] STRESS_2Y_SWING_TRADE.csv bytes=16074566 sha3=6b7f8fee065cb24a...
    [OK] XAGUSD_M1_RAW.csv bytes=4855796 sha3=bead7b55a34b5e5e...
    [OK] XAUUSD_M1_RAW.csv bytes=5199973 sha3=50bd0e2b68d43402...
    [OK] DEMO_LOG_SWING_TRADE_20260330_SMOKE10.csv bytes=1708 sha3=9e963544569ccee2...

[4] Gateway — opportunity_cost
    OK: encontrado `abs(y_price - (0.5 * x_price))`

--- RESUMO ---
ESTADO: OK (Tier-0 verificação automática passou)
```

## Próximo passo (humano)
1. Copiar este conteúdo para o RT-A oficial ou anexar como evidência.
2. Redigir reconciliação textual com qualquer relatório externo que alegue zero sinais.
3. Se `verify` falhar, alinhar manifesto e `git_commit_sha` antes de concluir a Fase A.
