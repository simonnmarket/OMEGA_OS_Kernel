# ENT-03 — GAPS DE REGISTO: TICKETS #192746138 e #192957446
**ID:** `OMEGA-PSA-AUDIT-CLOSE-20260602 / ENT-03`  
**Título:** Análise forense dos dois tickets sem `position_closed` em feedback  
**Tickets:** #192746138 (BTCUSD) | #192957446 (ETHUSD)

---

## GAP-01 — BTCUSD #192746138

### Evidência do log

| Timestamp UTC | Evento | Detalhe |
|---------------|--------|---------|
| 2026-06-02T02:08:33 | `position_opened` | BTCUSD SELL 0.07 @ 70,236.50 |
| 2026-06-02T04:08:33 | `[LEDGER] Posicao aberta` | entry=70236.50 confirmada |
| 2026-06-02T04:08:33 | `[PARTIAL_CLOSE] inicializado` | dir=SELL levels=[0.7/1.5/2.5/4.0]ATR |
| 2026-06-02T04:36:32 | `[TRAILING]` | price=70,760.69 peak=70,236.50 trail_SL=70,772.74 |
| 2026-06-02T04:36:32 | `[MT5_MODIFY_SL] ✓` | SL=70,772.74 confirmado MT5 |
| 2026-06-02T04:36:14 | `[PYRAMID_EVAL]` | add=False reason=trend_score<min |
| **2026-06-02T07:38:09** | `MT5 State Sync: 1 posicoes OMEGA` | **BTCUSD desaparece do ledger** |

### Diagnóstico

- Entre 04:36 e 07:38 UTC o BTCUSD passou de `price=70,760.69` → SL=70,772.74 (distância: 12 pts)
- BTC subiu (movimento adverso a SELL), atingindo SL estimado ~70,773
- **SL hit confirmado implicitamente**: posição desaparece de "posicoes OMEGA" no sync das 07:38
- **Ausência de `position_closed`**: o fecho por SL no MT5 não gerou evento de feedback — gap conhecido no `trade_feedback` writer (SL hits externos não criam evento `position_closed` quando o runner não detecta o fecho no ciclo de sync)

### PnL estimado

```
Entrada SELL: 70,236.50
SL hit:       70,772.74
Delta:        +536.24 pts (adverso)
Lot:          0.07
PnL:          −(536.24 × 0.07) ≈ −$37.54
```

### Classificação

| Item | Valor |
|------|-------|
| Tipo fecho | SL hit (stop-loss) |
| PnL estimado | −$37.54 |
| Registado em `trade_feedback` | NÃO — gap de registo |
| Incluído em −$108.81 | NÃO — fora dos realizados |
| Acção requerida | Confirmar em MT5 History; adicionar ao total se confirmado |

---

## GAP-02 — ETHUSD #192957446

### Evidência do log

| Timestamp UTC | Evento | Detalhe |
|---------------|--------|---------|
| 2026-06-02T14:14 | `position_opened` | ETHUSD SELL 0.10 @ 1,966.10 |
| 2026-06-02T16:14:43 | `[LEDGER] Posicao aberta` | entry=1966.10 confirmada |
| 2026-06-02T16:26:58 | `[PYRAMID_EVAL]` | reason=no_open_positions ← **anomalia** |
| 2026-06-02T17:02:57 | `[PYRAMID_EVAL]` | reason=no_open_positions (confirma) |
| 2026-06-02T17:20:53 | `[BREAKEVEN]` | SL movido para 1,967.168 |
| 2026-06-02T17:20:53 | `[MT5_CLOSE_PARTIAL] ✓` | **0.10 lotes @ 1,921.332** (totalidade) |
| 2026-06-02T17:20:53 | `volume MT5 ajustado` | pedido=0.03 → efetivo=0.10 (min_lot=0.10) |
| 2026-06-02T17:20:53 | `[PYRAMID_EVAL]` | reason=no_open_positions (confirmado fechado) |

### Diagnóstico

- Posição SELL entrou @ 1,966.10 com BTC descendo → preço atingiu 1,921.33 (lucro)
- Runner tentou fazer `partial_close` de 0.03 lote (Nível 2.5×ATR) mas min_lot=0.10 → **MT5 forçou fecho total** (0.10 lot)
- `MT5_CLOSE_PARTIAL` executou o fecho completo da posição com sucesso
- **Ausência de `position_closed`**: o evento de feedback não foi criado porque o fecho foi executado via `mt5_close_partial` (path de partial_close) e não via o path principal que escreve `position_closed`

### PnL estimado

```
Entrada SELL: 1,966.10
Fecho:        1,921.33
Delta:        −44.77 pts (favorável a SELL)
Lot:          0.10
PnL:          +(44.77 × 0.10) ≈ +$4.48
```

> ETHUSD 1 lot ≈ 1 ETH em USD/pt — confirmar com pip_value do broker.

### Classificação

| Item | Valor |
|------|-------|
| Tipo fecho | Partial close forçado a total (min_lot constraint) |
| PnL estimado | +$4.48 |
| Registado em `trade_feedback` | NÃO — gap de registo |
| Incluído em −$108.81 | NÃO — fora dos realizados |
| Acção requerida | Confirmar em MT5 History; ajustar total |

---

## CAUSA RAIZ COMUM — AMBOS OS GAPS

O `trade_feedback.jsonl` writer (`position_closed` event) só é chamado no path **principal de fecho** (`shadow_loop` ciclo normal). Dois casos não cobertos:

1. **SL hit externo** (MT5 fecha a posição entre ciclos do runner) → runner detecta no sync mas não chama o writer de feedback
2. **Fecho via `mt5_close_partial`** quando o volume total é fechado (min_lot > pedido) → path `partial_close` não chama o writer `position_closed`

### Impacto em PnL total estimado

| Componente | PnL |
|------------|-----|
| Realizados em feedback | −$108.81 |
| BTCUSD gap estimado | −$37.54 |
| ETHUSD gap estimado | +$4.48 |
| **Total ajustado estimado** | **−$141.87** |

> Confirmar via MT5 History (Deals tab) para valor exato.

---

*Fonte: `audit/paper/omega_24x7_runner.log`, `audit/paper/trade_feedback.jsonl`*  
*Gerado: 2026-06-02 19:10 UTC*
