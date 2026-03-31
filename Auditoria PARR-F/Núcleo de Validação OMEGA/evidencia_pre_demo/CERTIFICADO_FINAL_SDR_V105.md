# Certificado final de conclusão e provas criptográficas — OMEGA V10.5

| Campo | Valor |
|-------|--------|
| **Classificação** | Board-level / prova de custódia (Tier-0) |
| **ID de emissão** | PROVA-FINAL-CONVERGENCIA-V10.5-20260331 |
| **Documento** | CERTIFICADO_FINAL_SDR_V105 |
| **Data** | 31 de março de 2026 |
| **Autor (PSA)** | Antigravity MACE-MAX (Lead PSA) |
| **Assinatura de trancamento (Git HEAD)** | `bfbcb21752f38667c4a4bd4b736f03bf109f2fe6` |

**Referência cruzada:** `ENTREGA_PSA_CONSELHO_CONSOLIDADO_FINAL.md` (exigências absorvidas e rastreadas).

---

## 1. Comprovação de custódia unificada (Tier-0)

A governança acordada foi materializada em **validação reprodutível**: manifesto JSON, ficheiros em disco e **HEAD** do repositório alinhados.

### 1.1 Identificadores objectivos

| Artefacto | Valor |
|-----------|--------|
| **Git HEAD (commit actual)** | `bfbcb21752f38667c4a4bd4b736f03bf109f2fe6` |
| **SHA3-256 do ficheiro** `MANIFEST_RUN_20260329.json` | `2d72db843ab76ec9d06393ff13907fb0784d747afe35692f2d48a17517bfa819` |
| **SHA3-256 do stress** `STRESS_V10_5_SWING_TRADE.csv` | `112b5958dfc3e9c4e157d63304f500d5cb02e07a8fe1a47f723d08027d0d36df` |

*Nota:* o prefixo **bfbcb217** coincide com o **início do hash Git** do commit; o **hash mestre** do manifesto em SHA3-256 é o valor da linha anterior (ficheiro JSON completo).

### 1.2 Relatório do gate de segurança (`psa_gate_conselho_tier0.py`)

Execução consolidada: `audit_trade_count.py` + `verify_tier0_psa.py` → **GATE_GLOBAL: PASS**.

**STDOUT reprodutível** (também arquivável em `04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt`):

```text
PSA_GATE_CONSELHO_TIER0
timestamp_utc: 2026-03-31T20:28:26Z
repo_root: C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper
stress_csv: ...\02_logs_execucao\STRESS_V10_5_SWING_TRADE.csv

=== GIT HEAD (exit 0) ===
bfbcb21752f38667c4a4bd4b736f03bf109f2fe6

=== audit_trade_count.py STRESS_V10_5 (exit 0) ===
=== audit_trade_count.py ===
arquivo: STRESS_V10_5_SWING_TRADE.csv
sha3_256_arquivo: 112b5958dfc3e9c4e157d63304f500d5cb02e07a8fe1a47f723d08027d0d36df
linhas: 100000
signal_fired_true: 222
z_coluna: z_score
abs_z_max: 43231683.487146
abs_z_p50: 0.695670
abs_z_p95: 1.885867
abs_z_p99: 2.579635
aviso_outlier: abs_z_max muito elevado — usar P95/P99 para narrativa (não max bruto).
criterios_opcionais: OK

=== verify_tier0_psa.py (exit 0) ===
...
ESTADO: OK (Tier-0 verificação automática passou)

--- RESUMO ---
audit_trade_count exit: 0
verify_tier0_psa exit: 0
GATE_GLOBAL: PASS
```

**Reexecutar sempre antes de citar números:**

```powershell
python "Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo\psa_gate_conselho_tier0.py" --out-relatorio "04_relatorios_tarefa/PSA_GATE_CONSELHO_ULTIMO.txt"
```

---

## 2. Saneamento da Fase E (gateway live MT5)

O orquestrador `11_live_demo_cycle_1.py` **v1.3.0** incorpora, no código rastreado pelo manifesto:

| Barreira | Implementação |
|----------|----------------|
| **Warm-up RLS** | `copy_rates_from_pos(..., 20000)` barras M1 por ativo (antes 1000). |
| **Anti-drift** | Processamento apenas se `r1x[0][0] == current_t` (paridade de timestamp M1). |
| **VitalSignsMonitor** | `vitals.check_pulse(z)` após `motor.step`; janela 30; piso de desvio-padrão 0,05 → `SystemError` em flatline. |

**Execução demo:**

```powershell
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --smoke
python "Auditoria PARR-F\11_live_demo_cycle_1.py" --bars 500
```

---

## 3. Tese matemática institucional (clarificação Board)

| Afirmação | Estado |
|-----------|--------|
| **P95 global** de \|Z\| no stress V10.5 ≈ **1,886** | Confirmado por `audit_trade_count.py` (**inferior** a 2,0). |
| **Threshold** \|Z\| ≥ 2,0 | Aplica-se **por barra** no motor; não exige P95 ≥ 2. |
| **222** disparos com `signal_fired_true` | Confirmado no mesmo CSV; são eventos pontuais compatíveis com a regra e o motor. |

---

## 4. Assinatura de emissão (pronto para demo live)

- Exigências do **ENTREGA_PSA_CONSELHO_CONSOLIDADO_FINAL** incorporadas no processo e na custódia.
- **HEAD** actual do repositório: **bfbcb21752f38667c4a4bd4b736f03bf109f2fe6** (verificar com `git rev-parse HEAD` no momento da leitura).
- **Estado declarado:** núcleo V10.5 com **quarentena de laboratório** fechada ao nível **Tier-0** em disco; **Fase E** (demo MT5) autorizada a prosseguir conforme ordens do Conselho, com monitoramento VitalSigns e logs `DEMO_LOG_*.csv`.

---

## 5. Limitações (não revogáveis por este certificado)

- Tier-0 **PASS** em stress **não** garante resultado económico nem desempenho em conta real.
- **Outlier** em `abs_z_max` no stress: narrativa deve preferir **P95/P99** (aviso do próprio `audit_trade_count.py`).
- Qualquer novo **commit** altera HEAD e pode exigir **nova** sincronização do manifesto (`psa_sync_manifest_from_disk.py`) e **novo** gate.

---

**MACE-MAX | Antigravity — Lead PSA**  
*Certificado emitido para arquivo Board + pasta `evidencia_pre_demo`.*

---

*Fim do CERTIFICADO_FINAL_SDR_V105*
