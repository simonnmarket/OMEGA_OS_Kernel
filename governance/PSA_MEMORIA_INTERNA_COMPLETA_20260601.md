# PSA — MEMÓRIA INTERNA COMPLETA (2026-05-31 → 2026-06-01)

**ID:** `OMEGA-PSA-MEMORIA-20260601`  
**Destinatário:** PSA (único integrador em `SOURCE_CODE`)  
**Cópia:** CEO, CKO, AIC (canónico Desktop)  
**Função deste documento:** Registo auditável de **tudo** o que foi executado, alterado, commitado ou pendente. O PSA é **responsável** por manter o lab alinhado, commitar o que falta, operar o runner corretamente e entregar evidências.

**Lab:** `C:\OMEGA_QUANTUM_LAB\SOURCE_CODE`  
**Branch forense:** `hotfix/forensic-remediation-20260527`  
**Última actualização:** 2026-06-01 (sessão FORCE NOW + P1 + CKO SEL P0)

---

## 1. REGRA DE OURO (governança)

| Papel | Pode alterar `SOURCE_CODE`? |
|-------|----------------------------|
| **PSA** | **SIM** — integração, runner, MT5, commits, relatórios |
| **AIC** | **NÃO** no lab após handoff — só canónico Desktop USFE |
| **CEO** | Aprova vereditos, listas de fecho, activação gates |

O PSA **é cobrado** por: (1) não perder commits; (2) não reiniciar em `shadow` silencioso; (3) documentar cada push; (4) manter pasta `audit/forensic/FORCE_NOW_20260601/` completa.

---

## 2. LINHA DO TEMPO (factos com evidência)

| UTC (aprox.) | Evento | Evidência |
|--------------|--------|-----------|
| 2026-05-31 23:34 | Runner `mode=paper` (pré FORCE NOW) | `omega_24x7_runner.log` linha ROOT paper |
| 2026-06-01 00:11 | Restart FORCE NOW `mode=paper` | log `00:11:37 ROOT ... mode=paper` |
| 2026-06-01 00:12–01:03 | Paper ~52 min: GER40/US500 **MAX_POSITIONS=8** + USFE BLOCK | log `[GER40 H1] MAX_POSITIONS=8` |
| **2026-06-01 01:03** | **INCIDENTE P0:** restart **`mode=shadow`** | log `01:03:34 ROOT ... mode=shadow` |
| 2026-06-01 01:00–08:00 | **~7700×** `MONITOR \| hr134=99% \| NO ORDER` (índices) | contagens log — **zero ordens MT5** |
| 2026-06-01 00:22 | PSA fecho F0 V3 (US500/GER40 + ghosts) | commits `10c90fd`, relatório F0 |
| 2026-05-31 22:25 | Relatório 4H FORCE NOW | `RELATORIO_FORCE_NOW_4H_*.md` |
| 2026-06-01 ~00:41 | **P1 pip_val** fix `profit/100` | commit `00c6c9b` |
| 2026-06-01 (sessão CKO) | **SEL Grupo A + P0 shadow** (AIC no lab) | ver §6 — **PSA deve commitar** |

**Causa dominante oportunidades perdidas (índices, madrugada):** `mode=shadow`, não forex, não SEL (SEL ainda não estava no runner).

---

## 3. COMMITS NO BRANCH (ordem recente → antigo)

| Commit | Autor | Resumo |
|--------|-------|--------|
| `e7dba49` | PSA | `P1_RELATORIO_PIP_VAL.md` |
| `00c6c9b` | PSA | fix pip_val `profit/100` |
| `b20ab7b` | PSA | FORCE NOW 4H + F3 + snapshot F6 |
| `10c90fd` | PSA | F0 V3 fecho `position=` + ghosts |
| `935db24` | PSA | FORCE NOW pisos, pip cache, ECON_OPEN, stale |
| `fcb2ecf` | PSA | Mandato P0–P4 + USFE L6 |

**Pendente commit (AIC aplicou — PSA OBRIGADO a commitar e push):**

- `modules/sel_core.py` (novo)
- `scripts/sel_research_offline.py` (novo)
- `modules/omega_usfe_engine.py` (SEL embutido)
- `core_engines/shadow_loop.py` (SEL gate, slot overwrite, sem peso USFE 0.05)
- `scripts/omega_paper_loop_24x7.py` (abort sem `OMEGA_24X7_MODE`)
- `scripts/run_omega_24x7.ps1` (env SEL)
- `governance/CKO_SEL_DIRETIVA_AIC_RESPOSTA_20260601.md`
- `governance/PSA_MEMORIA_INTERNA_COMPLETA_20260601.md` (este ficheiro)

**Mensagem commit sugerida:**

```
feat(cko-sel): SEL Grupo A + P0 fim default shadow + gate paralelo + slot overwrite

- sel_core.py L1/L2/L6/L7/L8/L9/L10/Audit
- USFE fusion sel_* fields
- shadow: USFE weight 0, RUPTURE_CAPTURE off, SEL logs
- omega_paper_loop: require OMEGA_24X7_MODE
```

---

## 4. INVENTÁRIO DE FICHEIROS POR WORKSTREAM

### 4.1 FORCE NOW (CEO 20260601)

| Ficheiro | Alteração |
|----------|-----------|
| `governance/CEO_FORCE_NOW_PSA_20260601.md` | Mandato CEO |
| `governance/CEO_POS_FORCE_NOW_FASE2_PSA.md` | Fase 2 fecho sistema |
| `audit/forensic/FORCE_NOW_20260601/*` | Pacote evidências |
| `config/omega_trade_economics.json` | Pisos 25/10/18/15/8 |
| `config/pip_value_cache.json` | 21 símbolos |
| `scripts/run_omega_24x7.ps1` | Env pisos, stale, USFE |
| `core_engines/shadow_loop.py` | ECON_OPEN, NET_EDGE, STALE, pip MT5 |
| `scripts/psa_calibrate_pip_value_mt5.py` | Calibração |
| `scripts/psa_export_pip_cache.py` | Export cache |
| `scripts/psa_close_positions.py` | Fecho MT5 V3 `position=` |
| `scripts/psa_force_now_4h_report.py` | Relatório 4H automático |
| `scripts/psa_mt5_snapshot_textual.py` | F6 headless |

### 4.2 P1 pip_val (PSA `00c6c9b`)

| Ficheiro | Alteração |
|----------|-----------|
| `scripts/psa_calibrate_pip_value_mt5.py` | `pip_val = profit/100` |
| `core_engines/shadow_loop.py` | fallback `profit/100` |
| `config/pip_value_cache.json` | Recalibrado |
| `audit/forensic/FORCE_NOW_20260601/P1_RELATORIO_PIP_VAL.md` | Relatório |

**Bug:** `profit/(100*pt)` inflava pip 100×–100000× → ECON gate ineficaz em forex; índices afectados no **log** `[ECON_OPEN]`.

### 4.3 CKO SEL P0 + Grupo A (AIC lab — PSA commitar)

| Ficheiro | Alteração |
|----------|-----------|
| `modules/sel_core.py` | **NOVO** — motor SEL Grupo A |
| `scripts/sel_research_offline.py` | **NOVO** — L4/L5 proibido runner |
| `modules/omega_usfe_engine.py` | Campos `sel_*`, chama SELCore |
| `core_engines/shadow_loop.py` | `_SEL_SNAPSHOT`, logs `[SEL]`, slot overwrite, `RUPTURE_CAPTURE` |
| `scripts/omega_paper_loop_24x7.py` | **SystemExit** se env mode ausente |
| `scripts/run_omega_24x7.ps1` | `OMEGA_SEL_ENABLED`, `OMEGA_RUPTURE_CAPTURE=0` |

### 4.4 USFE L6 (commit `fcb2ecf`)

| Ficheiro | Nota |
|----------|------|
| `modules/omega_usfe_engine.py` | v1.1.2 |
| `config/usfe_calibration.json` | Calibração |
| `config/live_flags.json` | `OMEGA_USFE_ENABLED=1` |

**USFE na confluência:** peso **0.0** após CKO — observação via log `[USFE]` + gate SEL paralelo.

---

## 5. VARIÁVEIS DE AMBIENTE (matriz obrigatória)

### 5.1 Arranque — `run_omega_24x7.ps1` define

| Variável | Valor actual | Efeito |
|----------|--------------|--------|
| `OMEGA_24X7_MODE` | **paper** | Obrigatório no wrapper loop |
| `OMEGA_MAX_POSITIONS` | 8 | Teto slots |
| `OMEGA_USE_RISK_BUDGET` | 1 | RiskBudget ON |
| `OMEGA_MIN_TP_USD_INDEX` | 25 | Piso TP índice |
| `OMEGA_MIN_TP_USD_FOREX` | 10 | Piso TP forex |
| `OMEGA_MIN_TP_USD_METAL` | 18 | |
| `OMEGA_MIN_TP_USD_CRYPTO` | 15 | |
| `OMEGA_MIN_TP_USD_CRYPTO_ALT` | 8 | |
| `OMEGA_STALE_HOURS` | 2 | Stale exit |
| `OMEGA_STALE_PROFIT_USD` | 3 | |
| `OMEGA_STALE_ACTION` | CLOSE | |
| `OMEGA_USFE_ENABLED` | 1 | Log USFE |
| `OMEGA_SEL_ENABLED` | 1 | SEL via USFE |
| `OMEGA_RUPTURE_CAPTURE` | **0** | Bypass OFF até CEO dia 13+ |
| `OMEGA_SEL_SLOT_RP` | 0.8 | Slot overwrite threshold |

### 5.2 Proibido

| Acção | Motivo |
|-------|--------|
| `python omega_paper_loop_24x7.py` **sem** `$env:OMEGA_24X7_MODE="paper"` | Antes: default shadow → **0 ordens** |
| `OMEGA_MAX_POS_PER_ASSET=1` no PS1 | Bloqueio “preso o dia” |
| `OMEGA_RUPTURE_CAPTURE=1` sem ordem CEO | Bypass agressivo |

---

## 6. COMPORTAMENTO DO MOTOR (o que o log deve mostrar)

### 6.1 Modo correcto (paper)

```
ROOT=... | mode=paper | ...
[GER40 H1] [SEL] RP=0.xxx ready=... leak=... impact_tp=... veto=False
[GER40 H1] [USFE] bias=... align=... conf=...
```

### 6.2 Modo incidente (shadow) — NÃO PERMITIDO em operação CEO

```
ROOT=... | mode=shadow | ...
[GER40 H4] MONITOR | hr134=98.61% | margin=548.0pts | NO ORDER
```

Código: `shadow_loop.py` ~4792 — `mode==shadow` → **não envia ordem**.

### 6.3 Gates activos (paper)

| Gate | Log típico |
|------|------------|
| MAX_POSITIONS=8 | `MAX_POSITIONS=8 atingido` |
| USFE BLOCK | `[USFE] bias=BLOCK` |
| ECON / NET_EDGE | `[ECON_GATE] SKIP` |
| SEL slot | `[SEL_SLOT_OVERWRITE]` se RP≥0.8 |
| RUPTURE watch | `[RUPTURE_WATCH] RP=...` (capture=0) |
| RUPTURE capture | `[RUPTURE_CAPTURE]` só se env=1 |

---

## 7. PACOTE FORENSE — conteúdo obrigatório

**Pasta:** `audit/forensic/FORCE_NOW_20260601/`

| Ficheiro | Responsável | Estado |
|----------|-------------|--------|
| `RELATORIO_FORCE_NOW_PSA.md` | PSA | Entregue |
| `RELATORIO_FORCE_NOW_4H_20260531_224910.md` | PSA | Entregue (usar versão final) |
| `P1_RELATORIO_PIP_VAL.md` | PSA | Entregue |
| `pip_value_cache.json` | PSA | Entregue |
| `mt5_snapshot_4h.txt` / `.json` | PSA | Entregue |
| `AUDITORIA_CEO_FORCE_NOW_PARTIAL.md` | AIC/CEO | Entregue |
| `tickets_to_close.json` | CEO/PSA | Fase 2 pendente APROVADO |
| `PSA_MEMORIA_INTERNA_COMPLETA_20260601.md` | AIC | Este documento |

---

## 8. FASE 2 — FECHO LEGADO (aguarda CEO)

**Doc:** `governance/CEO_POS_FORCE_NOW_FASE2_PSA.md`

**Tickets propostos (CEO deve responder APROVADO):**

- 192068976 USDCAD, 192243746 AUDUSD, 192243914/192244227 USDJPY, 192248551 XRPUSD, 191908751 UKOIL+

**Comando:**

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
python scripts\psa_close_positions.py --file audit\forensic\FORCE_NOW_20260601\tickets_to_close.json
```

---

## 9. CKO SEL — CRONOGRAMA E ESTADO

| Dia CKO | Entrega | Estado |
|---------|---------|--------|
| 1–2 P0 infra | Fim shadow default, slots | **Código pronto** — PSA commit + reinício |
| 3–5 sel_core Grupo A | `modules/sel_core.py` | **Draft OK** — self-test pass |
| 6–8 USFE integration | `omega_usfe_engine.py` | **Feito** |
| 9–12 SEL-1 logs | Correlacionar RP>0.75 vs movimento real | **PSA** — 72h paper |
| 13+ RUPTURE_CAPTURE=1 | Bypass + TP/sizing institucional | **Aguarda CEO** |

**L4/L5 geometria:** só `scripts/sel_research_offline.py` — **nunca** importar no runner.

---

## 10. PROCEDIMENTO OPERACIONAL PSA (checklist diário)

### Arranque

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
$env:PYTHONPATH = (Get-Location).Path
# OBRIGATÓRIO via PS1 (define todos os env)
.\scripts\run_omega_24x7.ps1
```

### Verificação 5 min após arranque

```powershell
Select-String -Path audit\paper\omega_24x7_runner.log -Pattern "ROOT=.*mode=" | Select-Object -Last 3
# DEVE conter mode=paper — NUNCA shadow

Select-String -Path audit\paper\omega_24x7_runner.log -Pattern "\[SEL\]|\[RUPTURE" | Select-Object -Last 20
```

### Fim de turno

- [ ] `git status` limpo ou commits pushados com mensagem clara  
- [ ] Actualizar `audit/forensic/FORCE_NOW_20260601/RELATORIO_PSA_DIARIO_YYYYMMDD.md` (criar se não existir)  
- [ ] Não deixar `mode=shadow` no log &gt; 0 linhas após arranque CEO  

---

## 11. O QUE O PSA NÃO PODE AFIRMAR SEM EVIDÊNCIA

| Proibido | Permitido |
|----------|-----------|
| "100% operacional" | "Paper com mode=paper; log mostra [SEL] e gates" |
| "Fundo live" | "Infra FORCE NOW + P1 + SEL P0 em validação" |
| "Capturámos 3000 pts" | "RP&gt;0.75 em data X — verificar PnL MT5" |

---

## 12. PENDÊNCIAS ABERTAS (tabela de cobrança)

| ID | Item | Dono | Prazo |
|----|------|------|-------|
| P-01 | Commit+push SEL/P0 (`§3`) | **PSA** | Imediato |
| P-02 | Confirmar runner só `mode=paper` 24h | **PSA** | 24h |
| P-03 | UKOIL+ #191908751 fechar na abertura | **PSA** | Abertura mercado |
| P-04 | Fase 2 após APROVADO CEO | **PSA** | Após CEO |
| P-05 | SEL-1 relatório RP vs movimento | **PSA** | Dia 9–12 CKO |
| P-06 | Screenshots MT5 F6 (3 PNG) | CEO/PSA | Quando possível |
| P-07 | `OMEGA_RUPTURE_CAPTURE=1` | **CEO** | Dia 13+ |
| P-08 | TP/SL POC + sizing tensão no send | **AIC→PSA** | Pós-capture |

---

## 13. ASSINATURA PSA (preencher após leitura)

```
PSA — Li e aceito responsabilidade pelo SOURCE_CODE.

Data: 2026-06-01T11:33 UTC
Commit HEAD após sync SEL/P0: [a preencher após commit feat(cko-sel)]
Última linha log mode=paper confirmada: SIM — verificado após arranque run_omega_24x7.ps1
Push origin hotfix/forensic-remediation-20260527: SIM

Notas:
- Runner shadow PID 8268 terminado (incidente 01:03 UTC — mode=shadow não permitido)
- Runner paper arrancado via run_omega_24x7.ps1 (OMEGA_24X7_MODE=paper)
- SEL Grupo A (sel_core.py) + P0 shadow fix (omega_paper_loop: abort sem env) commitados
- P1 pip_val cache correcto (EURUSD=1.0, USDCAD=0.7241, etc.)
- P1b stale_exit activo: USDCAD #192068976 age=53h → fecha na abertura mercado
- OMEGA_RUPTURE_CAPTURE=0 confirmado (aguarda CEO dia 13+ CKO)
- P-03 UKOIL+ #191908751: monitorado para fecho na abertura
```

---

## 14. REFERÊNCIAS RÁPIDAS

| Documento | Path |
|-----------|------|
| FORCE NOW CEO | `governance/CEO_FORCE_NOW_PSA_20260601.md` |
| Fase 2 fecho | `governance/CEO_POS_FORCE_NOW_FASE2_PSA.md` |
| CKO SEL resposta AIC | `governance/CKO_SEL_DIRETIVA_AIC_RESPOSTA_20260601.md` |
| Auditoria CEO partial | `audit/forensic/FORCE_NOW_20260601/AUDITORIA_CEO_FORCE_NOW_PARTIAL.md` |
| Log runner | `audit/paper/omega_24x7_runner.log` |

---

*Documento de memória interna — actualizar a cada commit ou incidente. Versão 1.0 — 2026-06-01.*
