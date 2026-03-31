# Pacote PSA — OMEGA: verdade unificada (código + procedimentos + métricas)

**ID:** PACOTE-PSA-VU-20260331  
**Destinatário:** PSA (Engenharia)  
**Objetivo:** eliminar subjetividade nos relatórios ao Conselho; qualquer número citado deve ser **reprodutível** por comando e, quando aplicável, **SHA3 do ficheiro**.

**Problema a resolver (“ontem”):** números divergentes (ex.: 47 vs 222), afirmações sem ficheiro, e manifesto desactualizado após alteração de código — tudo isso **invalida** a cadeia de custódia Tier-0.

---

## 1. Regras obrigatórias (binárias)

| ID | Regra | Cumprimento |
|----|--------|-------------|
| R1 | Nenhum relatório ao CQO/CIO/COO contém contagens “de cabeça”. | Só valores saídos de `audit_trade_count.py`, `verify_tier0_psa.py`, ou scripts listados abaixo, **copiados integrais**. |
| R2 | Todo CSV citado inclui **nome** + **SHA3-256 do ficheiro** (saída do `audit_trade_count` ou `certutil` / Python). | PASS/FAIL |
| R3 | Após alterar ficheiro Python referenciado em `MANIFEST_RUN_*.json`, o manifesto **deve** ser actualizado + `git commit` + `verify_tier0_psa.py` → **ESTADO: OK**. | PASS/FAIL |
| R4 | Parâmetros de mercado ao vivo (`λ`, `span`, `MIN_Z`, warm-up) só mudam com **novo** RT + actualização de manifesto. | PASS/FAIL |

---

## 2. Raiz do repositório e variável de ambiente

| Variável | Valor (exemplo Windows) |
|----------|-------------------------|
| `NEBULAR_KUIPER_ROOT` | `C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper` |

Todos os comandos assumem PowerShell na raiz do repo:

```powershell
Set-Location -LiteralPath $env:NEBULAR_KUIPER_ROOT
```

---

## 3. Mapa de custódia (caminhos canónicos)

| Papel | Caminho relativo à raiz `nebular-kuiper` |
|-------|-------------------------------------------|
| Evidência + scripts | `Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\` |
| Logs stress / custódia | `...\evidencia_pre_demo\02_logs_execucao\` |
| Manifestos | `...\evidencia_pre_demo\03_hashes_manifestos\` |
| Live demo (orquestrador) | `Auditoria PARR-F\11_live_demo_cycle_1.py` |
| Verificação integridade | `...\evidencia_pre_demo\verify_tier0_psa.py` |
| Contagem objectiva | `...\evidencia_pre_demo\audit_trade_count.py` |
| QA percentis (V10.5 SWING) | `...\evidencia_pre_demo\qa_independente_v105.py` |
| Demo pós-corida | `...\evidencia_pre_demo\verificar_demo_apos_noturno.py` |
| Evidências RT-A automáticas | `...\evidencia_pre_demo\gerar_evidencias_rt_a.py` |
| Registo de métricas (definições) | `...\evidencia_pre_demo\05_metrics_registry.csv` |
| **Execução PSA — correcções + manifesto** | `...\evidencia_pre_demo\DOC_PSA_FINAL_EXECUCAO_CORRECOES_20260331.md` |
| **Sincronizar manifesto com disco** | `...\evidencia_pre_demo\psa_sync_manifest_from_disk.py` |

---

## 4. Parâmetros congelados — live + motor (fonte: código)

Ficheiro: `Auditoria PARR-F\11_live_demo_cycle_1.py` (versão no momento do último merge; confirmar com `git log -1 -- 11_live_demo_cycle_1.py`).

| Parâmetro | Valor | Unidade / nota |
|-----------|--------|----------------|
| `ASSET_Y` / `ASSET_X` | XAUUSD / XAGUSD | — |
| `PROFILE` | SWING_TRADE | — |
| `SPAN_WARMUP` (EWMA span) | 500 | barras (nome no código) |
| `LAMBDA` | 0.9998 | — |
| `MIN_HOLD` | 20 | barras |
| `MIN_Z_ENTRY` | 2.0 | σ |
| Warm-up MT5 | 20000 | barras M1 por ativo (`copy_rates_from_pos`) |
| VitalSigns `window_size` | 30 | barras |
| VitalSigns `volatility_floor` | 0.05 | desvio-padrão de \|Z\| na janela |

**Memória efectiva (N):** \(N = 1/(1-\lambda)\) → com λ=0,9998, **N = 5000** barras (valor de referência; não substitui verificação empírica).

---

## 5. Procedimento A — integridade Tier-0 (manifesto + Git + ficheiros)

**Comando (PowerShell):**

```powershell
Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:NEBULAR_KUIPER_ROOT = (Get-Location).Path
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\verify_tier0_psa.py"
```

**Critério de sucesso objectivo:**

- Última linha: `ESTADO: OK (Tier-0 verificação automática passou)`
- Código de saída: `0`

**Interpretação das secções:**

1. `[1]` — `HEAD` **deve** igualar `git_commit_sha` no JSON do manifesto.
2. `[3]` — para cada ficheiro listado: bytes e SHA3 no disco **iguais** ao manifesto.
3. `[4]` — gateway contém a substring exacta `abs(y_price - (0.5 * x_price))`.

**Se falhar por `11_live_demo_cycle_1.py` (bytes/hash):** o ficheiro foi alterado após o manifesto. **Acção:** actualizar entrada correspondente em `03_hashes_manifestos\MANIFEST_RUN_20260329.json` com tamanho e SHA3 actuais, **ou** regenerar manifesto pelo processo interno aprovado, **depois** `git commit` e repetir Procedimento A.

**SHA3 de um ficheiro (auxiliar, Python one-liner):**

```powershell
python -c "import hashlib, pathlib; p=pathlib.Path(r'Auditoria PARR-F\11_live_demo_cycle_1.py'); b=p.read_bytes(); print('bytes', len(b)); print('sha3', hashlib.sha3_256(b).hexdigest())"
```

---

## 6. Procedimento B — métricas objectivas de CSV (stress ou demo)

**Comando:**

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\audit_trade_count.py" `
  --csv "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\02_logs_execucao\STRESS_V10_5_SWING_TRADE.csv"
```

**Saída obrigatória a anexar ao relatório (exemplo de formato; números mudam se o CSV mudar):**

```
=== audit_trade_count.py ===
arquivo: STRESS_V10_5_SWING_TRADE.csv
sha3_256_arquivo: <hex64>
linhas: 100000
signal_fired_true: <inteiro>
z_coluna: z_score
abs_z_max: ...
abs_z_p50: ...
abs_z_p95: ...
abs_z_p99: ...
( aviso_outlier: ... se aplicável )
```

**Gates opcionais (códigos de saída):**

| Flag | Significado falha |
|------|-------------------|
| `--expect-rows N` | exit 2 se `linhas ≠ N` |
| `--min-signals N` | exit 3 se `signal_fired_true < N` |
| `--min-abs-z-max V` | exit 4 se `max(|Z|) < V` (susceptível a outliers) |
| `--min-abs-z-p95 V` | exit 5 se `P95(|Z|) < V` |

**Regra narrativa:** se aparecer `aviso_outlier`, **não** usar `abs_z_max` bruto em texto executivo; usar **P95/P99** + `signal_fired_true`.

**Snapshot de referência (executado na geração deste pacote; reexecutar sempre antes de citar):**

- Ficheiro: `STRESS_V10_5_SWING_TRADE.csv`
- `sha3_256_arquivo`: `112b5958dfc3e9c4e157d63304f500d5cb02e07a8fe1a47f723d08027d0d36df`
- `linhas`: 100000  
- `signal_fired_true`: 222  
- `abs_z_p95`: 1.885867 (aprox.; confirmar com saída actual)

---

## 7. Procedimento C — QA independente V10.5 (SWING)

**Comando:**

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\qa_independente_v105.py"
```

**Critério:** script faz `assert total_bars == 100000` e imprime percentis de `z_score`. **Anexar stdout integral.**

---

## 8. Procedimento D — verificação de log DEMO após corrida

**Comando:**

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\verificar_demo_apos_noturno.py" `
  --csv "C:\caminho\completo\para\DEMO_LOG_SWING_TRADE_YYYYMMDD_THHMM.csv"
```

**Critério:** exit 0 e bloquear texto “STATUS: Leitura OK”. Coluna Z: `z` (não `z_score`).

---

## 9. Procedimento E — evidências RT-A (stress 2Y)

**Comando:**

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\gerar_evidencias_rt_a.py"
```

**Uso:** gera texto com contagens por ficheiro listado em `STRESS_2Y_*.csv`; anexar stdout ou ficheiro `--out` conforme script.

---

## 10. Execução live — `11_live_demo_cycle_1.py`

**Smoke (10 barras):**

```powershell
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --smoke
```

**Ciclo (ex.: 500 barras):**

```powershell
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --bars 500
```

**Comportamento VitalSigns:** após 30 barras com desvio-padrão de \|Z\| na janela **inferior** a 0,05, levanta `SystemError` (flatline). **Não** é substituto de heartbeat por tempo (4 h) — se o COO exigir, implementar ticket separado.

**Log:** escrito em `omega_core_validation\evidencia_demo_<AAAAMMDD>\DEMO_LOG_*.csv` (caminho impresso no consola).

---

## 11. Template mínimo de relatório ao Conselho (copiar/preencher)

```
GIT_HEAD: <saída de: git rev-parse HEAD>
MANIFEST: 03_hashes_manifestos/MANIFEST_RUN_20260329.json — git_commit_sha = <igual ao HEAD?>

FICHEIRO STRESS CITADO:
  nome: 
  sha3_256_arquivo: <de audit_trade_count.py>

MÉTRICAS (colar stdout de audit_trade_count.py sem editar):
  linhas:
  signal_fired_true:
  abs_z_p95:
  abs_z_p99:

verify_tier0_psa.py: ESTADO OK / FALHA (última linha)

LIMITAÇÕES DECLARADAS:
  - Stress offline ≠ MT5 live (paridade só com RT-E + demo log).
```

---

## 12. Relação com documentos já existentes

| Documento | Função |
|-----------|--------|
| `ANALISE_FINAL_CONSELHO_E_GAPS_OMEGA_20260331.md` | Síntese AFC (coerência Conselho vs repo) |
| `RT_E_VITALSIGNS_MANDATO_20260331.md` | Mandato VitalSigns + template verdade |

---

## 13. Checklist final PSA (antes de enviar e-mail ao Conselho)

- [ ] `verify_tier0_psa.py` → **ESTADO OK**
- [ ] `audit_trade_count.py` no CSV citado → stdout anexado
- [ ] Nenhum número no corpo do parecer que **não** apareça nesses outputs
- [ ] Manifesto actualizado se qualquer ficheiro rastreado mudou
- [ ] `git status` limpo; commit SHA referenciado no cabeçalho do relatório

---

**Fim do pacote PACOTE-PSA-VU-20260331**

*Documento gerado para execução sem ambiguidade: critérios são PASS/FAIL ou números reprodutíveis por comando.*
