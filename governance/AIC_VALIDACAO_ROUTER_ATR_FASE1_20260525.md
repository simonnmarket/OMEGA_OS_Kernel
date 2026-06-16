# AIC — Validação Fase 1 Router/ATR (código)

| Campo | Valor |
|-------|--------|
| **Documento** | AIC-VALID-ROUTER-FASE1-20260525 |
| **Data** | 2026-05-25 |
| **Branch** | `feat/execution-router-atr-20260523` |
| **Commit** | `37ec0b4` |
| **Base** | P0 APROVADO (`AIC_VALIDACAO_PSA_P0_ABC_20260525.md`) |
| **Executor PSA** | Devin |

---

## 1. Veredito em uma frase

| Nível | Veredito |
|-------|----------|
| **Código + UT (Nível 1–2)** | **✅ APROVADO** |
| **Smoke MT5 SM-R1..R3 (Nível 4)** | **⏸️ PENDENTE CEO/PSA** — sessão com liquidez + ordem XAUUSD H4 |

**Falha A (ATR M1 vs H4):** **corrigida em código** — confirmação vivo depende de SM-R2.

---

## 2. Verificação independente AIC

| Item | Evidência | Resultado |
|------|-----------|-----------|
| Commit `37ec0b4` | `git log` branch `feat/execution-router-atr-20260523` | ✅ |
| `get_execution_tf_atr(symbol, signal_tf, confidence)` | `shadow_loop.py` L1986–2026 | ✅ assinatura + `_TF_MAP` |
| Call site main SL/TP | L3628 `get_execution_tf_atr(asset, tf, _conf_score)` | ✅ |
| Call site trailing | L4401 + `_fin_signal_tf` do ledger | ✅ |
| T-F1a `partial_taken` | 4 inits + L4480–4482 on success | ✅ |
| `signal_tf` no ledger entry | L4216 area | ✅ |
| pytest | 34/34 PASS (reproduzido AIC) | ✅ |
| Regressão P0 UT-1..9 | Incluídos nos 34 | ✅ |

---

## 3. Tabela UT-R (AIC)

| ID | Critério | AIC |
|----|----------|-----|
| UT-R1 | H4 ATR > 250; eff_sl ≥ max(atr×mult, 1500) | **PASS** |
| UT-R2 | M15 → TIMEFRAME_M15 | **PASS** |
| UT-R3 | partial_taken lifecycle | **PASS** |
| UT-R4 | TF desconhecido → H1 | **PASS** |
| UT-R5 | sanitize_sl_tp com atr 3000 | **PASS** |

---

## 4. O que posso / não posso afirmar

| Afirmação | Confiança |
|-----------|-----------|
| ATR para SL/TP usa `signal_tf` do ciclo (não M1 fixo) | **Alta** — código + UT-R1/R2 |
| D1 `partial_taken` fechado (CEO Opção A) | **Alta** — UT-R3 + wiring L4480 |
| XAUUSD H4 paper terá SL ≥ $20 na próxima entrada | **Média** — depende SM-R2 em MT5 |
| Falha B/C (cascata, M1-GATE) resolvidas | **N/A** — Fase 2+ |

---

## 5. Smoke Fase 1 — pendente (mandato Sec. 7.4)

| ID | Critério | Responsável |
|----|----------|-------------|
| SM-R1 | 1 ordem paper XAUUSD **H4**; log `atr_tf=H4` | CEO ou PSA + MT5 |
| SM-R2 | SL ≥ **$20** (≥2000 pts × 0.01) no PaperReport | idem |
| SM-R3 | TP ≥ 2× SL | idem |

**Comando sugerido:**

```powershell
cd C:\OMEGA_QUANTUM_LAB\SOURCE_CODE
git checkout feat/execution-router-atr-20260523
$env:PYTHONPATH = (Get-Location).Path
$env:OMEGA_MAGIC_NUMBER = "234001"
$env:OMEGA_MAX_POS_PER_ASSET = "1"
python -u core_engines/shadow_loop.py --mode paper --ativos XAUUSD --timeframes H4 --equity 10000
```

**PASS SM-R:** log mostra `get_execution_tf_atr` com `tf=H4`, `atr_pts` >> 250, e se ordem executar — `sl_pts` ou distância USD ≥ 20.

---

## 6. Próximos passos

| # | Quem | Acção |
|---|------|--------|
| 1 | PSA | `git push -u origin feat/execution-router-atr-20260523` |
| 2 | PSA | Criar `PSA_RELATORIO_ROUTER_ATR_20260523.md` (esqueleto + SM-R quando existir) |
| 3 | CEO/PSA | SM-R1..R3 quando sessão com liquidez (não Memorial Day) |
| 4 | AIC | Após SM-R PASS → **APROVADO Fase 1 completo**; autorizar Fase 2 ou merge |
| 5 | CEO | Merge P0 + Router quando confortável |

---

## 7. Proibições (ainda vigentes)

- Fase 2 Router cascata / M1-GATE — não iniciar sem AIC Fase 1 smoke PASS  
- TRE — mandato separado  
- 24×7 produção — até SM-R ou smoke com entrada real  

---

*AIC Tech Lead — Fase 1 código APROVADO — smoke SM-R pendente — 2026-05-25*
