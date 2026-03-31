Parâmetro PSA — síntese Conselho (actualizado) + instruções operacionais

**ID:** PARAM-PSA-CONSELHO-20260331-v2  
**Data:** 31 de março de 2026  
**Fonte:** `Auditoria PARR-F/Auditoria Conselho/` (ficheiros revistos nesta data)  
**Destinatário:** PSA (execução e arquivo)

---

## 1. Inventário da pasta Conselho

| Ficheiro | Papel declarado | Nota de análise |
|----------|------------------|-----------------|
| `CKO - Red Team.txt` | CEO / Comando: Fase E, leitura do certificado, `abs_z_max` vs P50/P95, passos smoke + run, monitorização. | **Base técnica sólida** para operação; explica outlier em `abs_z_max`. |
| `COO - Chief Operating Officer.txt` | Liberação demo, métricas stress, gates, KPIs 24h, comandos `git checkout`, `psa_gate`, `--live`. | Ver **secção 4** (correcções obrigatórias a memorandos). |
| `CQO - Chief Quant Officer.txt` | Validação certificado, HEAD, gates, métricas, tese P95 vs threshold, Fase E 30 dias, critérios sucesso/falha. | Alinhado ao **ENTREGA consolidado** sobre P95 e threshold **por barra**. |
| `CIO - Chief Information Officer.txt` | *(Conteúdo actual: duplicado do parecer COO — mesmo texto “PARECER COO”.)* | **Duplicação de ficheiro:** não acrescenta parecer CIO distinto; recomenda-se **um** ficheiro ou texto CIO próprio no futuro. |

---

## 2. Parâmetro único (valores que o PSA deve usar e citar)

| Chave | Valor | Origem |
|-------|--------|--------|
| `git_head` | `bfbcb21752f38667c4a4bd4b736f03bf109f2fe6` | Conselho + certificado; **confirmar** com `git rev-parse HEAD` antes de cada run. |
| `stress_csv` | `evidencia_pre_demo/02_logs_execucao/STRESS_V10_5_SWING_TRADE.csv` | Custódia |
| `sha3_stress_csv` | `112b5958dfc3e9c4e157d63304f500d5cb02e07a8fe1a47f723d08027d0d36df` | `audit_trade_count.py` |
| `linhas_stress` | 100000 | idem |
| `signal_fired_true` | 222 | idem |
| `abs_z_p50` | ≈ 0,695670 | idem (`z_score`) |
| `abs_z_p95` | ≈ 1,885867 | idem (**inferior** a 2,0 — distribuição global) |
| `abs_z_p99` | ≈ 2,579635 | idem |
| `abs_z_max` | valor muito elevado (outlier) | **Não** usar em narrativa executiva; ver aviso no stdout |
| `threshold_entrada` | \|Z\| ≥ 2,0 | `MIN_Z_ENTRY` no `11_live_demo_cycle_1.py` |
| `lambda_rls` | 0,9998 | orquestrador |
| `ewma_span` | 500 | `SPAN_WARMUP` |
| `warmup_barras_mt5` | 20000 | `copy_rates_from_pos` |
| `vital_signs_janela` | 30 | `VitalSignsMonitor` |
| `vital_signs_piso_std` | 0,05 | idem |
| `orquestrador` | `Auditoria PARR-F/11_live_demo_cycle_1.py` v1.3.0 | manifesto |
| `gate_unico` | `psa_gate_conselho_tier0.py` → **GATE_GLOBAL: PASS** | ambos exit 0 |

**Tese matemática (CQO + ENTREGA):** P95 global ≈ 1,886 **não** contradiz threshold 2,0; o limiar aplica-se **por barra**. P99 ≈ 2,58 mostra que \|Z\|≥2 é **atingível** em parte da série.

---

## 3. Convergência do Conselho (sem contradição útil)

1. **Custódia Tier-0:** `verify_tier0_psa.py` **ESTADO OK** + manifesto alinhado ao HEAD.  
2. **Métricas stress:** `audit_trade_count.py` exit 0; **222** sinais; SHA3 do CSV acima.  
3. **Hotfixes no live:** warm-up **20k**, **sync** `r1x[0][0] == current_t`, **VitalSigns** `check_pulse(z)`.  
4. **Fase E:** autorização de **demo MT5** com monitorização (CKO/COO/CQO com prazos e KPIs diferentes — ver secção 6).  
5. **CKO:** interpretação correta de **abs_z_max** (artefacto / transiente); foco operacional em **P50/P95**.

---

## 4. Correcções a aplicar aos memorandos (erros detectados)

| Problema | Onde aparece | Correcção PSA |
|----------|----------------|-----------------|
| **G5 “P95 ≥ 2,0”** | COO checklist | **Falso.** P95 ≈ 1,886 **é menor** que 2,0. O gate G5 deve ser reformulado (ex.: “threshold por barra verificável” + `signal_fired` > 0), não P95 global ≥ 2. |
| **“P95 confirma threshold 2,0”** | COO texto | Substituir por: “P95 global descreve calmaria; disparos ocorrem quando \|Z\|≥2 **na barra**; 222 eventos no stress.” |
| **`python ... --live`** | COO | O script **não** tem flag `--live`. Uso: `--smoke` ou `--bars N` (predefinição 500). |
| **`tail -f` / `grep`** | COO | Comandos Unix; em Windows usar **PowerShell** (`Get-Content -Wait -Tail`) ou seguir o **consola** do Python. |
| **Ficheiro CIO = COO** | `CIO - Chief Information Officer.txt` | Tratar como **duplicado** até haver CIO separado. |

---

## 5. Instruções PSA — sequência obrigatória

### 5.1 Antes de qualquer demo

```powershell
Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:NEBULAR_KUIPER_ROOT = (Get-Location).Path
git rev-parse HEAD
# Deve coincidir com bfbcb21752f38667c4a4bd4b736f03bf109f2fe6 se estiver no commit acordado

python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py" --out-relatorio "04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt"
```

**Sucesso:** `GATE_GLOBAL: PASS`, exit code **0**.

### 5.2 Demo MT5 (conforme CKO + código real)

```powershell
# Passo 1 — fumo (10 barras)
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --smoke

# Passo 2 — ciclo (ex.: 500 barras; ajustar --bars conforme necessidade)
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --bars 500
```

**Não existe** `--live` no argparse actual.

### 5.3 Pós-demo (log CSV)

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\verificar_demo_apos_noturno.py" --csv "<caminho\DEMO_LOG_*.csv>"
```

### 5.4 Após alterar ficheiros no manifesto

`psa_sync_manifest_from_disk.py` → commit → alinhar `git_commit_sha` → `verify_tier0_psa.py` OK (detalhe em `DOC_PSA_FINAL_EXECUCAO_CORRECOES_20260331.md`).

---

## 6. Prazos e KPIs (harmonizar memos)

Os ficheiros **não** coincidem todos nos mesmos números:

| Origem | Duração / janela sugerida |
|--------|----------------------------|
| CKO | Smoke + run; foco em skips e flatline. |
| COO | Exemplo **24h** e KPIs M001/M005/M010/M011. |
| CQO | **30 dias** demo, reporte diário, PF/DD, etc. |

**Instrução PSA:** seguir **ordem explícita do CEO/COO vigente** para a **corrida actual**; tratar **30 dias** como programa CQO separado **se** aprovado pelo Board. Documentar no **RT-E** qual cronograma foi executado.

---

## 7. Documentos canónicos no repositório (não substituir por só Conselho .txt)

| Documento | Função |
|-----------|--------|
| `ENTREGA_PSA_CONSELHO_CONSOLIDADO_FINAL.md` | Parâmetros + instruções + correcções de tese |
| `CERTIFICADO_FINAL_SDR_V105.md` | Prova + HEAD + SHA manifesto |
| `PACOTE_PSA_OMEGA_VERDADE_UNIFICADA_20260331.md` | Regras R1–R4 |

---

## 8. Limitações (Tier-0)

- **PASS** em stress **≠** lucro **≠** desempenho garantido em demo.  
- Memorandos humanos podem conter **erros aritméticos** (ex.: G5); **prevalecem** os scripts.  
- **Duplicado CIO/COO** deve ser corrigido na pasta Conselho para evitar confusão futura.

---

**Fim do PARAM-PSA-CONSELHO-20260331-v2**

*PSA: arquivar este ficheiro com o último `PSA_GATE_CONSELHO_ULTIMO.txt` e o output de `git rev-parse HEAD` da mesma sessão.*
