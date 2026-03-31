Parâmetro PSA — fechamento de fase (Conselho + técnica + instruções)

**ID:** PARAM-PSA-FECHAMENTO-FASE-FINAL  
**Versão:** 3.0 (substitui actualizações anteriores do livrete operacional)  
**Data:** 31 de março de 2026  
**Ficheiro canónico único:** `PARAMETRO_PSA_INSTRUCOES_CONSELHO_ATUAL.md` (ID interno PARAM-PSA-CONSELHO-20260331-v2) — **não** alterar o nome do ficheiro no disco; o ID lógico mantém-se.

---

## 1. Análise dos documentos actuais (`Auditoria Conselho/`)

| Ficheiro | Conteúdo essencial | Avaliação |
|----------|-------------------|-----------|
| **CKO — Red Team** | **REDAUD** (“dúvida razoável”): não afirma perfeição sem ver código; lista **GAP1** warm-up se MT5 devolver &lt; 20k barras; **GAP2** lógica de saída; **GAP3** validação de `--smoke`. | **Correção científica útil.** Complementa o Tier-0 sem o anular. |
| **COO** | Declara **PARAM-PSA-v2** canónico; corrige memos antigos (G5, `--live`, etc.); sequência PowerShell; **GO** demo. | Alinhado ao livrete; **HEAD** no texto pode ficar **desactualizado** — ver secção 2. |
| **CIO** | Conteúdo **idêntico** ao COO (parecer COO no ficheiro CIO). | **Duplicado administrativo** — só histórico até haver CIO distinto. |
| **CQO** | Confirma base única, gates, parâmetros, tese P95 vs threshold, sequência 5.1–5.4. | **Alinhado** ao repositório de scripts. |

**Síntese:** A fase de **parametrização, custódia e unificação documental** pode ser **encerrada** com o **CKO** a impor **prudência operacional** (REDAUD), não contradição.

---

## 2. HEAD Git (regra única)

Os memos COO/CQO citam `bfbcb217...`. **O HEAD válido é sempre** o resultado **actual** de:

```powershell
git rev-parse HEAD
```

Após **cada** commit, actualizar o manifesto (`psa_sync_manifest_from_disk.py` + alinhamento `git_commit_sha`) e **não** confiar em SHA “congelado” em memorandos.

---

## 3. Resposta técnica aos GAPs do CKO (verificação no código)

### GAP 1 — Histórico &lt; 20.000 barras no MT5

- **Estado:** `warm_up()` pede 20.000 barras, faz `merge` por `time` e itera `df`. O número efectivo de linhas é **`len(df)`** (barras **comuns** aos dois ativos).
- **Risco:** Se o broker devolver pouca história ou o `merge` reduzir muito as linhas, o motor aquece com **menos** que o desejado **sem** `RuntimeError` específico para “&lt; 20000”.
- **Acção PSA (imediata):** Ler a linha de consola `[OK] Motor aquecido com N barras sincronizadas.` Se **N** for muito inferior a 20.000, **documentar** no RT-E e **não** tratar como paridade total com o stress — considerar **outro** broker/conta ou **patch** futuro (verificação explícita `len(df) < 19000` → aviso/stop).

### GAP 2 — Lógica de saída

- **Estado:** `ExecutionManagerV104.manage()` em `10_mt5_gateway_V10_4_OMNIPRESENT.py` implementa fecho com **mínimo de barras** (`min_hold_bars`) e condição **Z atravessa 0** (LONG: `z_val >= 0`; SHORT: `z_val <= 0`). Ver linhas ~119–132 do gateway.
- **Conclusão:** Existe **lógica de saída**; o CKO pediu prova — **satisfeita** por referência ao ficheiro.

### GAP 3 — `argparse` e `--smoke`

- **Estado:** `11_live_demo_cycle_1.py` define `parser.add_argument("--smoke", ...)` e `--bars` (linhas ~83–84).
- **Conclusão:** O comando do livrete **é válido** na árvore actual.

---

## 4. Parâmetros canónicos (tabela única)

| Chave | Valor / regra |
|-------|----------------|
| Documento operacional | `PARAMETRO_PSA_INSTRUCOES_CONSELHO_ATUAL.md` |
| Stress CSV | `02_logs_execucao/STRESS_V10_5_SWING_TRADE.csv` |
| SHA3 CSV | Saída de `audit_trade_count.py` |
| `signal_fired_true` (stress) | 222 (revalidar com script) |
| Threshold entrada | \|Z\| ≥ 2,0 (`MIN_Z_ENTRY`) |
| λ / span / warm-up MT5 | 0,9998 / 500 / 20.000 |
| VitalSigns | janela 30, piso std 0,05 |
| Gate | `psa_gate_conselho_tier0.py` → **GATE_GLOBAL: PASS** |

---

## 5. Instruções PSA — fechar custódia e actualizar sistema

### 5.1 Sempre antes de demo ou release

```powershell
Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:NEBULAR_KUIPER_ROOT = (Get-Location).Path
git rev-parse HEAD

python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py" --out-relatorio "04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt"
```

- **Obrigatório:** `GATE_GLOBAL: PASS` e `verify_tier0_psa` **ESTADO OK**.
- Se **FAIL:** `python ...\psa_sync_manifest_from_disk.py` (e `--set-git-commit-sha-from-head` após commit, conforme `DOC_PSA_FINAL_EXECUCAO_CORRECOES_20260331.md`).

### 5.2 Demo MT5

```powershell
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --smoke
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --bars 500
```

- Confirmar **N** barras no warm-up no stdout; se **N** &lt;&lt; 20000, seguir secção 3 (GAP1).

### 5.3 Pós-demo

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\verificar_demo_apos_noturno.py" --csv "<caminho completo DEMO_LOG_*.csv>"
```

### 5.4 Documentação técnica de apoio (não duplicar no Conselho)

| Documento | Uso |
|-----------|-----|
| `ENTREGA_PSA_CONSELHO_CONSOLIDADO_FINAL.md` | Tese P95 / threshold |
| `CERTIFICADO_FINAL_SDR_V105.md` | Prova + hashes |
| `PACOTE_PSA_OMEGA_VERDADE_UNIFICADA_20260331.md` | Regras R1–R4 |
| `DOC_PSA_FINAL_EXECUCAO_CORRECOES_20260331.md` | Manifesto + Git |

---

## 6. Podemos concluir esta fase?

| Critério | Estado |
|----------|--------|
| Base operacional única (PARAM livrete) | **Sim** |
| Memorandos `.txt` como histórico | **Sim** (recomendado) |
| Gates e scripts como autoridade numérica | **Sim** |
| CKO REDAUD | Implica **continuidade** de vigilância em **execução** (warm-up, logs), **não** reabre a fase de documentação se o gate estiver PASS |

**Conclusão:** **Sim** — a **fase de consolidação documental / parametrização Tier-0** pode ser **declarada concluída**, com a ressalva CKO: a **fase seguinte** é **operação demo + evidência RT-E**, não “zero risco”.

---

## 7. Limitações

- Tier-0 **PASS** não garante PnL nem ausência de bugs de mercado.
- Memorandos humanos podem ficar **desactualizados** (HEAD); **prevalecem** `git rev-parse` e os scripts.

---

**Fim do PARAM-PSA-FECHAMENTO-FASE-FINAL**

*PSA: arquivar juntamente com o último `PSA_GATE_CONSELHO_ULTIMO.txt` e `git rev-parse HEAD` da mesma sessão.*

=======================

Parâmetro PSA — síntese Conselho (actualizado) + instruções operacionais

**Encerramento de fase (análise CKO REDAUD + fechamento):** ver `PARAMETRO_PSA_FECHAMENTO_FASE_FINAL.md` (v3.0).

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
| `git_head` | **Sempre** o output actual de `git rev-parse HEAD` (ex.: após unificação: `3641bdf658ca63e0b15f03a243c6c5c8ce4a409e`) | **Não** fixar um SHA no livrete após novos commits; o manifesto `git_commit_sha` deve coincidir com o HEAD do momento. |
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
