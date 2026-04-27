# RELATÓRIO FORENSE P&L — OVERNIGHT N=120

**Audit ID:** `PNL_OVERNIGHT_20260427`
**Janela:** 2026-04-26 19:00 → 2026-04-27 12:00 UTC
**Fonte:** `mt5.history_deals_get(magic=234001)`
**Run auditado:** `fase4_IA_ON_20260426_221231` (overnight N=120)
**Severidade:** 🔴 **CRÍTICA — TODAS AS OPERAÇÕES COM PREJUÍZO ESTRUTURAL**

---

## 1. VEREDICTO

| Indicador | Valor | Status |
|---|---|---|
| Operações fechadas | **814** | — |
| **NET TOTAL** | **−$51.21** | 🔴 PREJUÍZO |
| Win rate financeiro | **4.55 %** (37/814) | 🔴 PIOR QUE ALEATÓRIO |
| Losses | 764 (93.86 %) | 🔴 |
| Flats (zero) | 13 (1.60 %) | — |
| Wins | 37 (4.55 %) | 🔴 |
| NET / trade médio | −$0.0629 | 🔴 |
| NET / trade mediana | −$0.0400 | 🔴 |
| Pior trade | −$0.6400 | — |
| Melhor trade | +$0.4400 | — |
| Duração média | **8.7 s** (mediana 5 s) | 🔴 ANÔMALA |
| Equity final paper | ~$9 948.79 (de $10 000) | DD = 0.51 % |

> **Nota:** o KS=1 % previsto não foi acionado durante o overnight porque o DD ficou em 0.51 % — abaixo do antigo limite 5 %, e da própria contenção 1 %. A perda foi distribuída em 814 micro-trades (não foi um drawdown explosivo, mas sim **sangria sistemática por spread**).

---

## 2. ROOT CAUSE — POR QUE 97 % "HIT RATE" PRODUZIU 4.55 % WIN-RATE

### 2.1 O número "97.53 %" reportado no overnight **não era win-rate**
No `paper_summary_*.json` o campo `hit_rate_134` é:
```
"hit_rate_134": 97.46,
"ic_95": "[97.0%, 97.9%]"
```
Esta é a **assinatura estatística do modelo** (proporção de barras históricas validadas em janela de 134 amostras pelo `bias_audit`). É uma **propriedade do sinal/feature**, **não a fração de trades lucrativos**.

O agregador imprime `hit_rate_avg=97.5265` baseado nessa métrica e induziu à confusão de tratá-la como métrica de execução. **Não é.**

### 2.2 Por que o win-rate financeiro é 4.55 %
| Mecanismo | Evidência | Impacto |
|---|---|---|
| **Wrapper fecha posição em ~5 s** | `Avg duration=8.7s · median=5s` · `FASE4_CLOSE_IA_O=79.4 %` + `FASE4_CLOSE_BASE=14.7 %` (94.1 % fechadas pelo loop, NÃO por SL/TP) | Cada trade realiza só o **spread negativo**. Praticamente impossível ganhar. |
| **Viés direcional BUY 86 %** | `BUY: n=701 (86.1 %) win_rate=3.0 %` vs `SELL: n=113 (13.9 %) win_rate=14.2 %` | Em janela CLOSED de fim-de-semana cripto, mercado oscilou lateral / leve baixa. BUYs forçados perderam quase todos. |
| **Concentração em BTC** | `BTCUSD: n=312 (38.3 %) NET=−$33.20` (= 65 % da perda) | Spread BTC alto + multiplicador absoluto maior → cada -1 ponto custa mais. |
| **Estratégia momentum em mercado sem momentum** | Sessão CLOSED com volume baixo, ATR comprimido | Sinais "TREND" puxando BUY repetidamente contra ruído lateral. |
| **Wrapper força ENTRADA todo ciclo** | 4 trades / ciclo × 120 ciclos = 480 (+ retries) → 814 deals registrados | Sem filtro de "no-edge → no-trade". |

### 2.3 Quem disparou as ordens?
**MOMENTUM_MT5 (fallback)** — não foi a IA. Como demonstrado nos relatórios anteriores: 480/480 trades vieram do `source=MOMENTUM_MT5`, **0** do `AGENT_IA`. A IA decidiu corretamente HOLD em todas as 480 chamadas; foi o **fallback momentum** que produziu o prejuízo.

> **Implicação:** ironicamente, **a IA estava certa em ficar fora**. Foi o mecanismo de fallback (que existe para "manter o sistema vivo") que sangrou o paper account. O fallback executa sempre, sem gate de edge.

---

## 3. DECOMPOSIÇÃO POR SÍMBOLO

| Símbolo | Trades | Win % | NET | Best | Worst | % do prejuízo |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSD | 312 | 8.3 % | **−$33.20** | +$0.44 | −$0.64 | **64.8 %** |
| ETHUSD | 180 | 6.1 % | −$12.14 | +$0.17 | −$0.18 | 23.7 % |
| DOGUSD | 126 | 0.0 % | −$3.96 | −$0.03 | −$0.04 | 7.7 % |
| SOLUSD | 196 | 0.0 % | −$1.91 | $0.00 | −$0.02 | 3.7 % |

**SOLUSD/DOGUSD: 0 wins em 322 trades** — sangria pura de spread, sem sequer um vencedor.

---

## 4. DECOMPOSIÇÃO POR TIPO

| Tipo | n | % | Win-rate | NET |
|---|---:|---:|---:|---:|
| BUY | 701 | 86.1 % | 3.0 % | −$42.85 |
| SELL | 113 | 13.9 % | 14.2 % | −$8.36 |

**Long bias massivo** (86 %) é uma falha do gerador de sinais momentum em janela CLOSED.

---

## 5. EXIT REASONS (por que cada trade fechou)

| Razão | Trades | % |
|---|---:|---:|
| `FASE4_CLOSE_IA_O` (wrapper força fechar pós-ciclo) | 646 | 79.4 % |
| `FASE4_CLOSE_BASE` (wrapper força fechar baseline) | 120 | 14.7 % |
| `OMEGA_AB_CLOSE` | 2 | 0.2 % |
| `[sl ...]` SL acionado | ~30 | ~3.7 % |
| `[tp ...]` TP acionado | ~16 | ~2.0 % |

**94.1 % das saídas foram FORÇADAS pelo wrapper antes que SL/TP pudessem agir.** O modelo de execução transforma cada trade em "pagar o spread e correr". Ineficiência de design, não de estratégia.

---

## 6. CRUZAMENTO COM MÉTRICAS PRÉVIAS

| Métrica reportada | Valor | Realidade financeira |
|---|---|---|
| `hit_rate_avg = 97.53 %` | OK no plano estatístico | **Win-rate real = 4.55 %** |
| `KS triggers = 0` | Tecnicamente correto | DD = 0.51 % (abaixo do KS), mas dispersão de prejuízo |
| `concentração = 27.08 %` (FIX #5) | OK no plano operacional | BTC ainda concentrou 65 % da perda em $ |
| `latency_p95 IA = 33 ms` (FIX #6) | OK | Irrelevante: a IA não executou |
| `bias verdict NOT_SIGNIFICANT` | OK no plano sistêmico | Não mede edge financeiro do fallback |

> **Lição forense:** o painel de métricas do overnight é dominado por SLOs **operacionais e estatísticos** (latência, concentração, KS, bias), e **NÃO** por SLOs **financeiros** (P&L net, win-rate financeiro, profit factor, Sharpe, expectancy). Esta lacuna é a causa raiz secundária do achado.

---

## 7. ANÁLISE DE CAUSA RAIZ (5-WHYS)

```
Por que prejuízo de $51 em 814 trades?
└─ Win-rate financeiro 4.55 % e duração média 8.7 s
   └─ Wrapper força fechar trade ~5 s após abrir, antes do SL/TP
      └─ Wrapper foi desenhado para AB-test de execução (smoke), não para trading real
         └─ Confundimos métricas de "AB de assinatura" com KPIs de P&L
            └─ Painel não tem campo "net_pnl" lado-a-lado com "hit_rate_134"
```

---

## 8. RISCOS REVELADOS

| ID | Risco | Severidade | Mitigação proposta |
|---|---|---|---|
| R-PNL-1 | Fallback momentum executa sem gate de edge → sangria sistemática em mercado lateral | 🔴 ALTO | Adicionar gate ATR/volatilidade ao fallback (ex.: skip se ATR < threshold) |
| R-PNL-2 | Wrapper fecha posições antes de SL/TP → impossível recuperar spread | 🔴 ALTO | Remover `FASE4_CLOSE_IA_O` em runs de avaliação P&L; deixar SL/TP agirem |
| R-PNL-3 | Painel sem KPIs financeiros (NET, expectancy, profit factor, Sharpe) | 🔴 ALTO | Implementar `pnl_overnight_audit.py` no aggregator e bloquear GO/NO-GO sem net_pnl |
| R-PNL-4 | Viés long 86 % em janela CLOSED | 🟡 MÉDIO | Calibrar bias do gerador momentum por sessão |
| R-PNL-5 | Concentração $$ ≠ concentração #trades | 🟡 MÉDIO | Métrica de concentração ponderada por exposição em $ (não em #trades) |
| R-PNL-6 | KS de 1 % não dispara em sangria distribuída | 🟢 BAIXO | Adicionar KS por **N consecutive losses** (ex.: 50 losses → halt) |

---

## 9. AÇÕES IMEDIATAS RECOMENDADAS (PARA VALIDAÇÃO CEO)

### A. Curto prazo (próximas 24 h)
1. **Bloquear novos runs** com o wrapper atual até R-PNL-2 corrigido. ✅ JÁ EM SAFE STATE.
2. **Patch fallback momentum** com gate de edge: `if atr_pct < min_atr or abs(momentum) < threshold → HOLD`.
3. **Adicionar painel financeiro** ao agregador: `net_pnl`, `win_rate_$`, `expectancy`, `profit_factor`.
4. **Critério GO/NO-GO atualizado:** exigir `net_pnl ≥ 0` E `win_rate_$ ≥ 45 %` E `expectancy > 0` antes de qualquer próximo overnight.

### B. Próximo overnight (somente após A)
- Run em **janela ASIA/LONDON/NY** (não CLOSED).
- Wrapper modificado para **deixar SL/TP atuarem** (sem `FASE4_CLOSE_IA_O`).
- IA ON com guardrails atuais (cap 0.1 %, max_pos 2, KS 1 %).
- Critério primário: **net_pnl ≥ 0** após N=30 ciclos.

### C. Médio prazo
- Implementar **Sharpe online** e **Kelly fraction sizing**.
- Cross-validar IA contra dados históricos (backtest tick-by-tick) **antes** de qualquer próximo paper-run.

---

## 10. CADEIA DE CUSTÓDIA

```
PNL audit JSON          : logs/agent_ia_phase3/PNL_OVERNIGHT_AUDIT_20260427.json
Tool                    : agent_ia/tools/pnl_overnight_audit.py
Janela MT5 (UTC)        : 2026-04-26T19:00Z → 2026-04-27T12:00Z
MT5 deals filtrados     : 1 631 (magic=234001) → 814 posições reconstruídas
Gross profit price      : −$51.21
Gross swap              : $0.00
Gross commission        : $0.00
NET                     : −$51.21
Aggregate overnight     : be06a13809f6f1ffa94aa98ed88eee800eb30306df3beb562887156184708765
Bias pós-emergência     : 3f63976dc99469ee12f61a46209c9f0671bd043cc4f11166c5ed88d4f317a544
shadow_loop SHA256      : BB30B3537E2EEC4D48F43CD8CE16377F19CF28F85AFAB686C92FB808FD7CFA87
Estado atual sistema    : SAFE STATE — IA OFF, 0 posições, guardrails ativos
```

---

## 11. CONCLUSÃO

> **A IA NÃO PERDEU DINHEIRO. O FALLBACK MOMENTUM PERDEU.**
> A IA decidiu HOLD em 480/480 oportunidades — decisão **correta** dado o regime CLOSED.
> O dinheiro foi perdido pelo **mecanismo de fallback + wrapper de teste** que executa
> trades curtos demais para superar o spread, em viés long massivo.
>
> **Reverter "vitória técnica" do overnight (7/8 PASS) → revisão honesta: 6/9 PASS**
> ao incluir KPIs financeiros (NET, Win-rate $, Expectancy).
>
> Próximo passo é **engenharia**, não autorização: corrigir wrapper + adicionar gate
> de edge ao fallback + adicionar KPIs financeiros ao painel. Só então repetir overnight.

---

## 12. ASSINATURA

```
Audit Lead    : Cascade (PSA-WIND forense)
Data/hora     : 2026-04-27 13:40 UTC+02
Compliance    : ✅ Paper-only · ✅ Magic 234001 · ✅ Lote 0.01 · ✅ Equity $10k
Severidade    : 🔴 CRÍTICA — bloqueio até correções A1–A4
Próxima ação  : aguardar GO do CEO para implementar A1–A4 (gate fallback + KPIs $)
```
