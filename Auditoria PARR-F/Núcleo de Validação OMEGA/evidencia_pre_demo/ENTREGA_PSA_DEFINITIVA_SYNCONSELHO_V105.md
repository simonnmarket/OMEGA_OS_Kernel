# Entrega definitiva PSA — síntese Conselho + execução objectiva (V10.5)

**ID:** ENTREGA-PSA-SYNCONSELHO-V105  
**Data:** 31 de março de 2026  
**Destinatário:** PSA (único executor operacional de correcções e gates Tier-0)  
**Origem:** consolidação de `Auditoria PARR-F/Auditoria Conselho/` + instrumentos em `evidencia_pre_demo/`

---

## 1. Documentos revistos (pasta Conselho)

| Ficheiro | Conteúdo útil | Risco / correcção obrigatória |
|----------|----------------|--------------------------------|
| **CKO - Red Team.txt** | Verificação de SHA3 do CSV de stress; código Python de recálculo. | Manter como anexo técnico; caminho do CSV deve ser o **absoluto** ou relativo à raiz do repo. |
| **COO - Chief Operating Officer.txt** | Exige **origem do ficheiro**, **comando**, **commit** e **âmbito** (stress vs demo vs produção) por número. | **Incorporar** no fluxo PSA: nenhum número no relatório ao Board sem estes quatro campos. |
| **CIO - Chief Information Officer.md** | Tabela de parâmetros; trava anti-drift. | **Erro factual:** P50/P95 atribuídos a `verify_tier0_psa.py` — esse script **não** imprime percentis de Z. **Fonte correcta:** `audit_trade_count.py` ou `qa_independente_v105.py` (coluna `z_score`). |
| **CQO - Chief Quant Officer.txt** | Aprovação executiva; blocos de código pandas. | **Erro no sample:** uso de `df['z']` em `STRESS_V10_5_SWING_TRADE.csv` — a coluna é **`z_score`**. Esse bloco **falha** se executado literalmente. **Não** reutilizar sem correcção. |

**Convergência transversal (todos):** warm-up 20k, sincronia M1 XAU/XAG, VitalSigns, separação laboratório/live — **mantêm-se** como requisitos de engenharia.

---

## 2. Verdade canónica (o que o PSA deve citar)

| Métrica | Valor (stress SWING V10.5, disco actual) | Script que imprime o número |
|---------|------------------------------------------|------------------------------|
| SHA3 ficheiro `STRESS_V10_5_SWING_TRADE.csv` | `112b5958dfc3e9c4e157d63304f500d5cb02e07a8fe1a47f723d08027d0d36df` | `audit_trade_count.py` |
| Linhas | 100000 | idem |
| `signal_fired_true` | 222 | idem |
| P50, P95, P99 de \|Z\| | ver stdout (ex.: P95 ≈ 1,885867) | idem (`z_score`) |
| `verify_tier0_psa.py` | `ESTADO: OK` se manifesto + HEAD alinhados | `verify_tier0_psa.py` |

**`verify_tier0_psa.py`:** integridade de **manifesto**, **HEAD vs git_commit_sha**, **bytes/SHA3** dos ficheiros listados, **gateway** opp_cost. **Não** substitui `audit_trade_count.py` para percentis.

---

## 3. Ferramenta única de gate (NOVO)

### 3.1 `psa_gate_conselho_tier0.py`

Executa **numa só chamada**:

1. `git rev-parse HEAD`
2. `audit_trade_count.py` no `STRESS_V10_5_SWING_TRADE.csv` com `--expect-rows 100000 --min-signals 1`
3. `verify_tier0_psa.py`

**Critério:** saída `GATE_GLOBAL: PASS` e código de saída **0**.

**Comando (PowerShell, raiz do repo):**

```powershell
Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
$env:NEBULAR_KUIPER_ROOT = (Get-Location).Path
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py"
```

**Gravar relatório em ficheiro:**

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py" `
  --out-relatorio "04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt"
```

### 3.2 Wrapper PowerShell

```powershell
& "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\run_psa_gate_conselho_tier0.ps1"
```

---

## 4. Após qualquer alteração de código ou documento rastreado

1. `python psa_sync_manifest_from_disk.py` (actualizar bytes + SHA3 no JSON).  
2. `git add` / `git commit`.  
3. `python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head` e novo commit até `verify_tier0_psa.py` OK (ver `DOC_PSA_FINAL_EXECUCAO_CORRECOES_20260331.md`).  
4. `python psa_gate_conselho_tier0.py` → **PASS**.

---

## 5. Resposta ao COO (checklist obrigatória para relatórios ao Board)

Para **cada** número citado:

| Campo | Exemplo |
|-------|---------|
| Ficheiro | `02_logs_execucao/STRESS_V10_5_SWING_TRADE.csv` |
| Comando | `python .../audit_trade_count.py --csv ...` |
| Commit | `git rev-parse HEAD` no momento do relatório |
| Âmbito | **Stress offline** (não confundir com demo MT5) |

---

## 6. Artefactos de referência (já no repositório)

| Documento | Função |
|-----------|--------|
| `AUDITORIA_COMPLIANCE_CONSELHO_V105_FINAL.md` | Dossiê Board (ajustar apenas se números mudarem — reexecutar gate). |
| `PACOTE_PSA_OMEGA_VERDADE_UNIFICADA_20260331.md` | Regras R1–R4 e procedimentos A–E. |
| `DOC_PSA_FINAL_EXECUCAO_CORRECOES_20260331.md` | Manifesto + Git. |

---

## 7. Inclusão dos novos scripts no manifesto (quando aplicável)

Quando `psa_gate_conselho_tier0.py` (e/ou `run_psa_gate_conselho_tier0.ps1`) forem considerados artefactos auditados, adicionar entrada em `MANIFEST_RUN_20260329.json` e correr `psa_sync_manifest_from_disk.py`.

---

## 8. Declaração de limitações (Tier-0 honesto)

- **Stress** não prova **live**; prova coerência offline + custódia.  
- **P95** de \|Z\| no stress **não** é prova de “edge” comercial; é descritivo da amostra.  
- Comparação **402 vs 222** só é válida se se declararem **dois CSVs** e **duas** configurações (evitar mistura no mesmo parágrafo sem rótulo).

---

**Fim da entrega ENTREGA-PSA-SYNCONSELHO-V105**

*Critério final objectivo: `psa_gate_conselho_tier0.py` → `GATE_GLOBAL: PASS`.*
