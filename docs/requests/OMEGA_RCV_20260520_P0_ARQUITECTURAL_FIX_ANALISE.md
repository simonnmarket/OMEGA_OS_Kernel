# Análise técnica — OMEGA-RCV-20260520-P0-ARQUITECTURAL-FIX

**Documento CKO:** Documento Técnico Definitivo — Conselho (RCA execução)  
**Data análise:** 2026-05-20  
**Código verificado:** `core_engines/shadow_loop.py` (path live paper), `audit/paper/trade_feedback.jsonl`, pacote `OMEGA_DIAGNOSTIC_DATA_20260518`

---

## 1. Veredito executivo (BLUF)

| Afirmação CKO | Confiança | Evidência |
| --- | --- | --- |
| HALT / não reiniciar sem remediação | **Alta** | KS DD 12,9%; alinhado com estado conhecido |
| Problema na **ponte de execução**, não na IA | **Média-alta** | `trade_feedback`: **0** fechos com `AGENT_IA`; **811** com `NULL` |
| Execução **2 passos** (entrada sem SL + modify) no código **actual** | **Baixa** | `mt5_send_order` envia `sl`/`tp` no **primeiro** `order_send` |
| Perfil **<1 min** em massa de perdas | **Alta** | 477/533 perdas (89,5%) com `duration_min < 1` |
| **NULL** domina perdas | **Alta** | 308/533 perdas (57,8%) com fonte NULL; CKO cita 77,9% nos SL — ordem de grandeza compatível |
| Rollover **00:05 UTC** como cluster | **Não confirmado** neste extract | Só 1 perda em `00:05` no `trade_feedback`; requer cruzamento MT5 deals↔posição |
| 4 mandatos são **necessários** antes de restart | **Alta** (governança) | Mesmo com Mandato 1 parcialmente já no código, 2–4 **não existem** |

**Recomendação:** Tratar este documento como **P0 acima** da corrida 24h diagnóstico CKO. **Não iniciar** runner até mandatos implementados + prova de log (rejeição 10016 sem posição órfã).

---

## 2. Mandato 1 — Execução atómica

### O que o CKO descreve

Entrada com `sl=0`, depois `PositionModify` — janela sem proteção no broker.

### O que o código faz hoje (`mt5_send_order`, ~L1283–1307)

```1283:1307:C:\OMEGA_QUANTUM_LAB\SOURCE_CODE\core_engines\shadow_loop.py
    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        ...
        "sl":           sl_price,
        "tp":           tp_price,
        ...
    }
    ...
    result = mt5.order_send(request)
```

`mt5_modify_position_sl` existe para **trailing stop / breakeven** em posições já abertas (~L4130), não como injecção inicial de SL.

### Gaps residuais (ainda válidos)

1. `order_check` falha → log *"enviando mesmo assim (demo)"* — risco de enviar ordem inválida.
2. Sem política explícita: **10016 INVALID_STOPS → abortar**, nunca retry sem SL.
3. Possível comportamento histórico / outro módulo (`executor_original.py` também envia SL no primeiro pacote).

**Mandato 1:** Reforçar (não reinventar): proibir retry pós-10016; falhar fechado; teste broker com log de rejeição.

---

## 3. Mandato 2 — Spread Guard (SL ≥ 3× spread)

### Estado actual

- Existe **EDGE GATE** (`OMEGA_EDGE_MIN_ATR_OVER_SPR`, ADX) — bloqueia momentum fraco, **não** a regra SL vs spread do CKO.
- `min_dist = max(trade_stops_level, spread*2)` em `mt5_send_order` — protege distância broker, **não** compara `sl_pts` vs spread×3 antes de entrar.

**Mandato 2:** **Não implementado.** Implementar em pré-execução (~antes de `mt5_send_order`), status `SKIP_SPREAD_GUARD`.

---

## 4. Mandato 3 — Blackout rollover (23:55–00:10 UTC)

**Não encontrado** no `shadow_loop.py`.

**Mandato 3:** **Não implementado.** Nota: janela CKO no pseudo-código usa `seconds_from_midnight < 600` mas comentário diz 23:50–00:10 — alinhar implementação ao texto (23:55–00:10 UTC).

---

## 5. Mandato 4 — Bloqueio fonte NULL

### Telemetria (evidência)

`audit/paper/trade_feedback.jsonl` — eventos `position_closed`:

| signal_source | Total |
| --- | ---: |
| NULL | 811 |
| MOMENTUM_MT5 | 188 |
| SYNC_RECOVERY | 49 |
| AGENT_IA | **0** |

Perdas (`result=LOSS`): NULL **57,8%**, MOMENTUM **33,6%**, SYNC **8,6%**.

**Interpretação:** NULL não prova sozinho um “ramo fantasma” de código — muitas entradas no ledger **sem** `signal_source` persistido (sync, histórico, falha de tagging). Ainda assim, **bloquear execução sem fonte** é correto e força higiene.

**Mandato 4:** **Não implementado** como gate; `signal_source` inicia `None` no ciclo (~L2554) e default `MOMENTUM_MT5` (~L2708) — gate deve ser **immediately before** `mt5_send_order`.

---

## 6. Perfil temporal (<1 min)

| Métrica | CKO | Verificado (`trade_feedback` perdas) |
| --- | --- | --- |
| Morte <1 min | 93,7% (829/885 SL) | **89,5%** (477/533 perdas) |
| 1–5 min | 3,5% | **10,1%** (54/533) |

**Conclusão:** Assinatura de **SL apertado vs spread/microestrutura** é **consistente** com os dados internos.

---

## 7. Relação com documentos Desktop anteriores

| Tema | Diretiva 24h CKO | Este RCV P0 |
| --- | --- | --- |
| Prioridade | Corrida diagnóstico (equity, 0,2%) | **Stop total** até fix arquitectural |
| `--equity 10000` | Remover | Continua válido mas **secundário** vs mandatos |
| Fallback OFF | Sim | Alinhado (MOMENTUM ainda aparece em perdas históricas) |
| IA “inocente” | Parcial | **Fortalecido** por 0 fechos `AGENT_IA` no feedback |

**Ordem de precedência sugerida para o Conselho:**

1. **OMEGA-RCV-20260520-P0** (4 mandatos + prova 10016)  
2. Só depois: modo diagnóstico 24h (Diretiva CKO anterior)  
3. PSA GAP-02 (`risk_config`) em paralelo para patch ATR

---

## 8. Condição de restart (CKO)

> Log de teste com ordem **rejeitada** 10016 (Invalid Stops), sem abrir posição desprotegida.

**Aceitável.** Complementar com:

- Amostra de ordem **aceite** com SL visível no MT5 no mesmo tick.
- Zero posições abertas com `position.sl == 0` após fill (script de verificação).

---

## 9. Esforço estimado (engenharia)

| Mandato | Esforço | Ficheiro principal |
| --- | --- | --- |
| M1 Reforço atómico + 10016 | 1–2 h | `shadow_loop.py` (`mt5_send_order`) |
| M2 Spread guard | 1–2 h | Pré-exec ~L3876 |
| M3 Rollover blackout | 30 min | Idem |
| M4 NULL block | 30 min | Idem |
| Testes + log CEO | 1 h | Demo MT5 |

Total: **~4–6 h** (alinhado com CKO “1–2 h” se só um engenheiro e sem testes formais).

---

## 10. Pasta Desktop — pode apagar?

| Acção | Recomendação |
| --- | --- |
| Apagar os 4 TXT antigos (Resumo, Memorando, CIO, Diretiva 24h) | **Sim**, após guardar **este RCV** como documento mestre |
| Copiar RCV para repo | **Sim** — `docs/requests/OMEGA_RCV_20260520_P0_ARQUITECTURAL_FIX.md` (texto CEO) |
| Apagar sem backup | **Não** |

---

*Análise nível código + dados — não substitui validação em conta demo após patch.*
