# Entrega PSA — Consolidação Conselho + instruções operacionais (V10.5)

**ID:** ENTREGA-PSA-CONSELHO-CONSOLIDADO-FINAL  
**Data:** 31 de março de 2026  
**Destinatário:** PSA (execução técnica única)  
**Fonte:** `Auditoria PARR-F/Auditoria Conselho/` (CKO, COO, CIO, CQO) + instrumentos Tier-0 em `evidencia_pre_demo/`  
**HEAD canónico (verificar com `git rev-parse HEAD`):** `f391196c8b7cf323f42d9f524afcec49ee896afa`

---

## 1. Resumo executivo para o PSA

O Conselho **converge** nos seguintes pontos **técnicos** (independentemente do tom de cada memo):

| Tema | Decisão consolidada |
|------|---------------------|
| **Warm-up** | 20.000 barras M1 por ativo antes do ciclo live (`11_live_demo_cycle_1.py`). |
| **Sincronia** | Só processar quando `r1x[0][0] == current_t` (anti-drift XAU/XAG). |
| **VitalSigns** | Janela 30; desvio-padrão de \|Z\| na janela abaixo de 0,05 → `SystemError` (flatline). |
| **Threshold** | \|Z\| ≥ 2.0 para entrada (`MIN_Z_ENTRY`). |
| **Custódia** | `MANIFEST_RUN_20260329.json` + `verify_tier0_psa.py` + `audit_trade_count.py` + `psa_gate_conselho_tier0.py`. |
| **Fase E** | COO/CQO/CKO: autorização de **demo live** MT5 sujeita a monitoramento e critérios de aceitação definidos nos memos. |

---

## 2. Síntese por conselheiro (ficheiros na pasta Conselho)

### 2.1 CKO — Red Team (`CKO - Red Team.txt`)

- Confirma **GATE_GLOBAL: PASS** e papel do `psa_gate_conselho_tier0.py`.
- Define **HEAD** `f391196c8...` como imagem de referência para o ciclo.
- **Pré-lançamento:** script exemplo `verify_commit.py` (prefixo 9 caracteres) — opcional; o **gate oficial** continua a ser `psa_gate_conselho_tier0.py`.
- **Operação:** observar oscilação de Z nas primeiras barras; **skips** consecutivos por feed de prata; parar manualmente se Z travar e VitalSigns não disparar.

### 2.2 COO (`COO - Chief Operating Officer.txt`)

- **Libera Fase E** com base em `GATE_GLOBAL: PASS` e métricas do stress.
- **Métricas de aceitação (exemplo no memo):** limiares de `signal_fired` e P95 em janela de demo — **validar sempre** com `audit_trade_count.py` no **log DEMO** correspondente, não só no stress.

**Correção factual obrigatória (erro num documento COO):**  
alguns textos escrevem **P95 ≥ 2.0** como “suporte” ao threshold. **Isso é falso matematicamente** para o stress `STRESS_V10_5_SWING_TRADE.csv`: o **P95 de \|Z\|** é **~1,886** ( **inferior** a 2.0). O threshold **2.0** aplica-se **por barra**; os **222** disparos são **barras** em que a regra \|Z\|≥2 foi satisfeita **e** `signal_fired` — **não** significa que o P95 global da série seja ≥2. **Não** usar P95 como prova de “threshold globalmente acima de 2”.

### 2.3 CIO (`CIO - Chief Information Officer.txt`)

- Dossiê executivo de imunização; **atenção:** contém campos **placeholder** (ex.: hashes `a1b2c3d4...`) e **mistura** “HASH MANIFESTO” com SHA Git — **não** usar como fonte de verdade. **Fonte:** manifesto real + `verify_tier0_psa.py`.

### 2.4 CQO (`CQO - Chief Quant Officer.txt`)

- Confirma gates e métricas; **inconsistência interna:** em parte do texto o **HEAD** ainda aparece como `1632010c...` enquanto o commit citado é `f391196c8...`. **Prevalece** o repositório: `git rev-parse HEAD` **deve** coincidir com `git_commit_sha` no manifesto e com a secção “HEAD canónico” **deste** documento.

---

## 3. Verdade única (métricas stress — reprodutível)

| Métrica | Origem | Comando |
|---------|--------|---------|
| SHA3 do CSV stress | `audit_trade_count.py` (stdout) | Ver secção 5 |
| `signal_fired_true`, P50, P95, P99 | idem | coluna **`z_score`** (não `z`) |
| Integridade manifesto + HEAD | `verify_tier0_psa.py` | idem |

**Valores esperados** para `STRESS_V10_5_SWING_TRADE.csv` (confirmar sempre com stdout actual):

- Linhas: 100000  
- `signal_fired_true`: 222  
- `abs_z_p95`: ≈ 1,886 (**inferior** a 2,0 — **normal** para distribuição global)

---

## 4. Instruções PSA — ordem obrigatória

### 4.1 Antes de qualquer demo live

1. **Raiz do repositório**

   ```powershell
   Set-Location -LiteralPath "C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper"
   $env:NEBULAR_KUIPER_ROOT = (Get-Location).Path
   ```

2. **Gate único**

   ```powershell
   python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py"
   ```

   **Sucesso:** `GATE_GLOBAL: PASS` e código de saída **0**.

3. **(Opcional)** Wrapper:

   ```powershell
   & "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\run_psa_gate_conselho_tier0.ps1"
   ```

4. **Gravar evidência**

   ```powershell
   python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py" `
     --out-relatorio "04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt"
   ```

### 4.2 Após editar código ou documentos rastreados no manifesto

1. `python ...\psa_sync_manifest_from_disk.py`  
2. `git add` / `git commit`  
3. `python ...\psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head` e novo commit até `verify_tier0_psa.py` OK (detalhe em `DOC_PSA_FINAL_EXECUCAO_CORRECOES_20260331.md`).

### 4.3 Demo live (`11_live_demo_cycle_1.py` v1.3.0)

```powershell
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --smoke
```

Smoke: 10 barras — VitalSigns **pode não** encher janela (30); para teste de flatline, usar `--bars` ≥ 30.

```powershell
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --bars 500
```

**Pós-demo:** `verificar_demo_apos_noturno.py --csv <path\DEMO_LOG_*.csv>` (ver `evidencia_pre_demo`).

### 4.4 Paridade stress ↔ live (recomendação)

- Mesmos **λ**, **span**, **MIN_Z**, **warm-up**, **regra de sync**; relatórios **separando** “stress CSV” vs “demo live” (ver `ENTREGA_PSA_DEFINITIVA_SYNCONSELHO_V105.md`).

---

## 5. Comandos de referência (copiar)

```powershell
# HEAD
git rev-parse HEAD

# Gate
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py"

# Métricas stress
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\audit_trade_count.py" `
  --csv "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\02_logs_execucao\STRESS_V10_5_SWING_TRADE.csv"

# Tier-0 manifesto
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\verify_tier0_psa.py"
```

---

## 6. Documentos de apoio no repositório

| Documento | Função |
|-----------|--------|
| `ENTREGA_PSA_DEFINITIVA_SYNCONSELHO_V105.md` | Conselho vs ferramentas + correções CIO/CQO |
| `PACOTE_PSA_OMEGA_VERDADE_UNIFICADA_20260331.md` | Regras R1–R4 e procedimentos |
| `DOC_PSA_FINAL_EXECUCAO_CORRECOES_20260331.md` | Manifesto + Git |
| `AUDITORIA_COMPLIANCE_CONSELHO_V105_FINAL.md` | Dossiê Board (actualizar HEAD se mudar commit) |

---

## 7. Limitações (Tier-0 honesto)

- **PASS** no **stress** **não** garante lucro nem **performance** em demo/real.  
- **Gates** **não** substituem **julgamento** de risco, **compliance** legal ou **aprovação** de **capital**.  
- Memos do Conselho podem conter **ambivalências**; **este** ficheiro + **stdout** dos scripts **prevalecem** em caso de conflito numérico.

---

**Fim do documento ENTREGA-PSA-CONSELHO-CONSOLIDADO-FINAL**

*PSA: arquivar este ficheiro junto com o último `PSA_GATE_CONSELHO_ULTIMO.txt` e o `git rev-parse HEAD` da mesma execução.*
