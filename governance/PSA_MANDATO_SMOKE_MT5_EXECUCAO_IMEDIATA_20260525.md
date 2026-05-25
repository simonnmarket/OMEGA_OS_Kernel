# PSA — Smoke MT5 Imediato (substitui Fase A CEO)

| Campo | Valor |
|-------|--------|
| **Documento** | PSA-SMOKE-MT5-20260525 |
| **Emitido** | AIC Tech Lead |
| **Autorização CEO** | PSA pode aceder MT5 e executar smoke **agora** |
| **Objectivo** | Fechar Fase A + preencher relatório Sec. 4–7; entregar pacote para AIC |
| **Branch** | `fix/cicc-remediation-p0-abc-20260522` |
| **HEAD mínimo** | `ed6452e` (código) + `54ee899` (docs) |
| **Proibido** | Fase E Router/ATR; TRE; merge `main` sem AIC |

---

## 0. Mensagem CEO → PSA (copiar e enviar)

```text
PSA,

Autorizado executar smoke MT5 AGORA no terminal do ambiente OMEGA.
Seguir integralmente:

governance/PSA_MANDATO_SMOKE_MT5_EXECUCAO_IMEDIATA_20260525.md

Entregar pasta audit/smoke/PSA_ENTREGA_SMOKE_<data>/ + relatório Sec. 4-7 preenchido.
Commit com mensagem: "smoke: PSA execução MT5 P0-ABC Sec 4-7".

CEO só revisa o pacote; AIC emite validação depois.
```

---

## 1. Pré-requisitos (5 min)

| # | Check | Comando / acção | PASS se |
|---|-------|-----------------|---------|
| P1 | Pasta repo | `cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE` | Existe |
| P2 | Branch | `git branch --show-current` | `fix/cicc-remediation-p0-abc-20260522` |
| P3 | pytest | Ver Sec. 2 | 29/29 PASS |
| P4 | **MT5 aberto** | Iniciar MetaTrader 5; login **510075151** ou conta paper CEO | `connected=True` no log |
| P5 | Algo Trading | MT5 → Ferramentas → Opções → Expert Advisors → **Allow algorithmic trading** | ON |
| P6 | Conta limpa | Sec. 3.1 | 0 posições magic `234001` / comment `OV2\|` |
| P7 | Mercado | EURUSD negociável (não “market closed”) | Símbolo activo |

**Se P6 FAIL:** fechar posições OMEGA manualmente no MT5 antes do smoke.

---

## 2. Gate pytest (antes do smoke)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
python -m pytest tests/test_p0_abc_20260522.py tests/test_runner_targets_v1_only.py tests/test_order_magic_propagation.py -q
```

**PASS:** `29 passed` — se FAIL, **parar** e reportar CEO.

---

## 3. Pré-check posições

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
python scripts/check_positions_now.py *> audit\smoke\pre_check_positions.txt
```

Guardar output. **PASS:** nenhuma posição OMEGA aberta (ou listar excepção no relatório).

---

## 4. Executar smoke completo (obrigatório)

### 4.1 Script (preferido — corrigido para PowerShell)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
& .\scripts\run_p0_smoke_ceo.ps1
```

**Aguardar** até mensagem final: `P0 smoke CEO CONCLUIDO. Log: ...`

**Se o script falhar:** executar passos 4.2 manualmente (um comando por linha).

### 4.2 Manual (fallback)

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
$env:PYTHONIOENCODING = "utf-8"

python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD --timeframes H1 --equity 10000
python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD --timeframes H1 --equity 10000
python -u core_engines/shadow_loop.py --mode paper --ativos XAUUSD --timeframes H1 --equity 10000
python -u core_engines/shadow_loop.py --mode paper --ativos EURUSD GBPJPY XAUUSD --timeframes H1 --equity 10000
python scripts/psa_position_pnl_reconcile.py --since "2026-05-25 00:00:00"
```

(Ajustar data `--since` para o dia UTC do smoke.)

---

## 5. Pacote de entrega (obrigatório — AIC lê isto)

Criar pasta:

```text
audit/smoke/PSA_ENTREGA_SMOKE_20260525/
```

| Ficheiro | Conteúdo |
|----------|----------|
| `00_RESUMO_SMOKE.md` | Tabela SM/P2a/G/REG PASS/FAIL + veredito PSA |
| `01_log_smoke_completo.log` | Cópia do `p0_smoke_ceo_*.log` mais recente |
| `02_pre_check_positions.txt` | Output Sec. 3 |
| `03_reconcile_output.txt` | stdout do `psa_position_pnl_reconcile.py` |
| `04_ultimas_50_linhas.txt` | Últimas 50 linhas do log smoke |
| `05_mt5_positions_pos_smoke.txt` | `check_positions_now.py` após smoke |
| `06_CODE_SHA3.txt` | Linhas `[FORENSIC] CODE_SHA3=` de cada ciclo |
| `07_git_head.txt` | `git log -1 --oneline` + `git rev-parse HEAD` |

---

## 6. Preencher relatório PSA (obrigatório)

**Ficheiro:** `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md`

### Sec. 4 — Smoke unitário

| ID | Como avaliar PASS |
|----|-------------------|
| SM-1 | Log termina `PAPER LOOP CONCLUÍDO` + exit 0 no 1º EURUSD |
| SM-2 | MT5: ≤1 posição EURUSD por direção (BUY/SELL) |
| SM-3 | 2º ciclo EURUSD: log contém SKIP/1pos/MAX_POS/already **ou** não abre 2ª mesma direcção |
| SM-4 | 0 linhas PaperReport EXEC com `fill=0` no período smoke |
| SM-5 | Se BE aplicado: SL ≠ entry no log `[MT5_MODIFY_SL]` ou posição |
| SM-6 | Ciclo XAUUSD: `eff_sl` / sl_pts ≥ 1500 no log ou PaperReport |
| SM-7 | Tentativa hedge: log `anti_hedge` / bloqueio |

Colar em **“Últimas 50 linhas log smoke”** o conteúdo de `04_ultimas_50_linhas.txt`.

**Resultado Sec. 4:** marcar ☑ Todos PASS ou ☐ Algum FAIL.

### Sec. 5 — P2a

| ID | PASS se |
|----|---------|
| P2a-1 | Portfolio 3 ativos exit 0 |
| P2a-2 | 0 pares BUY+SELL mesmo símbolo |
| P2a-3 | ≤1 pos/(ativo,direção) |

### Sec. 6 — Reconcile

Preencher tabela G3, G4, G5, P0-8 R, REG-1, REG-2 com output de `03_reconcile_output.txt`.

### Sec. 7.8 — PnL

Preencher Δ Equity, Σ deals, Σ feedback, total_realized_pnl, floating.

### Sec. 7.9 — Quantum/harmonic

1 parágrafo ou **N/A** com justificação (“smoke P0 não activa harmonic”).

### Sec. 9 — Veredito PSA

| Condição | Veredito |
|----------|----------|
| Sec. 4–6 todos PASS | **APROVADO** (smoke) |
| Qualquer FAIL | **REPROVADO** + lista fixes |

**Nota:** Veredito **final P0 institucional** só após AIC Sec. C.

---

## 7. Critérios de “smoke inconclusivo” (não marcar PASS)

| Situação | Acção PSA |
|----------|-----------|
| `[PSA_FEED] Dados stale` + 0 execuções | **FAIL SM-1** ou repetir quando mercado aberto — documentar |
| Só `NO_TREND` / `IA HOLD` sem ordens | SM-2/3 **N/A** — indicar “sem entrada; repetir em sessão com sinal” |
| `Invalid "comment"` | **FAIL** — regressão; não APROVADO |
| `MARKET_CLOSED` em entrada (não fecho) | Documentar; forex pode estar fechado |

---

## 8. Commit e notificação

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git add governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md audit/smoke/PSA_ENTREGA_SMOKE_*
git commit -m "smoke: PSA execução MT5 P0-ABC Sec 4-7 (20260525)"
git push origin fix/cicc-remediation-p0-abc-20260522
```

**Mensagem ao CEO + AIC:**

```text
Smoke MT5 concluído.
Pacote: audit/smoke/PSA_ENTREGA_SMOKE_20260525/
Relatório: governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md Sec 4-7
Veredito PSA smoke: APROVADO | REPROVADO
Commit: <hash>
```

---

## 9. O que a AIC fará depois (sem acção PSA)

1. Ler `00_RESUMO_SMOKE.md` + relatório Sec. 4–7.
2. Emitir `governance/AIC_VALIDACAO_PSA_P0_ABC_20260525.md` (ou data do dia).
3. Veredito **APROVADO** / **REPROVADO** → autoriza ou bloqueia Fase E.

---

## 10. Proibições

- Não iniciar `feat/execution-router-atr-20260523`.
- Não `run_omega_24x7.ps1` overnight neste mandato.
- Não alterar código P0 durante smoke (só preencher relatório).
- Não declarar “produção 24/7 OK” — apenas smoke P0.

---

## 11. Referências rápidas

| Item | Caminho |
|------|---------|
| Script smoke | `scripts/run_p0_smoke_ceo.ps1` |
| Relatório | `governance/PSA_RELATORIO_VALIDACAO_P0_ABC_20260522.md` |
| Mandato fecho P0 | `governance/PSA_MANDATO_FECHO_P0_E_TRANSICAO_LEVEL_20260523.md` |
| Template AIC | `governance/AIC_VALIDACAO_PSA_P0_ABC_20260523_TEMPLATE.md` |

---

**Tempo estimado:** 30–90 min (depende de duração dos ciclos + mercado).

**Assinatura AIC:** mandato emitido para execução PSA imediata.
