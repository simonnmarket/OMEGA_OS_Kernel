# Parâmetro PSA — fechamento de fase (Conselho + técnica + instruções)

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
