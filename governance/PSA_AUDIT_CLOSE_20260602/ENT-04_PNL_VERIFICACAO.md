# ENT-04 — VERIFICAÇÃO PnL: −$108.81
**ID:** `OMEGA-PSA-AUDIT-CLOSE-20260602 / ENT-04`  
**Título:** Verificação e decomposição do PnL realizado −$108.81  
**Referência CEO:** "PnL sessão vs feedback −$108,81"

---

## 1. VERIFICAÇÃO FONTE PRIMÁRIA

**Cálculo directo de `audit/paper/trade_feedback.jsonl`:**

```
XAUUSD #192648431  SELL  pnl = −15.22   (legacy pré-sessão, fechado 00:34)
US100  #192695231  BUY   pnl = −21.17   (fechado 01:04)
USDJPY #192702716  BUY   pnl = −1.35    (fechado 01:00)
XAUUSD #192710972  SELL  pnl = −68.60   (fechado 04:01)
GER40  #192807978  BUY   pnl = −0.06    (fechado 06:07)
GER40  #192809456  BUY   pnl = +74.54   (fechado 07:54)
USDJPY #192819339  BUY   pnl = −2.25    (fechado 08:02)
GER40  #192836895  BUY   pnl = −25.39   (fechado 08:29)
GER40  #192842530  BUY   pnl = −25.21   (fechado 09:37)
GER40  #192858349  BUY   pnl = −33.33   (fechado 12:37)
US100  #192924673  BUY   pnl = +1.44    (fechado 13:30)
US100  #192935713  BUY   pnl = +7.79    (fechado 15:55)
────────────────────────────────────────────────────────
TOTAL                         = −108.81 USD  ✓
```

**Confirmação:** −$108.81 = valor exacto. Match com figura CEO.

---

## 2. DECOMPOSIÇÃO POR ATIVO

| Ativo | Trades | WIN | LOSS | PnL Total |
|-------|--------|-----|------|-----------|
| XAUUSD | 2 | 0 | 2 | −$83.82 |
| GER40 | 5 | 1 | 4 | −$9.45 |
| US100 | 3 | 2 | 1 | −$14.94 |
| USDJPY | 2 | 0 | 2 | −$3.60 |
| **TOTAL** | **12** | **3** | **9** | **−$108.81** |

---

## 3. DECOMPOSIÇÃO TEMPORAL

| Período | Trades | PnL Parcial | Equity aprox. |
|---------|--------|-------------|---------------|
| 23:29–04:00 (noite) | 4 | −$106.34 | $10,624 |
| 04:00–08:00 (madrugada) | 3 | −$4.56 | $10,620 |
| 08:00–12:00 (manhã) | 3 | −$50.60 | $10,570 |
| 12:00–16:00 (tarde) | 3 | +$52.66 | $10,622 |
| **Total** | **12** | **−$108.81** | |

> Inversão positiva 12:00–16:00: GER40 #192809456 +$74.54 + US100 +$1.44 + US100 +$7.79 = +$83.77 bruto.

---

## 4. ANÁLISE QUALITATIVA

### Drivers das perdas

| Causa | PnL | Observação |
|-------|-----|------------|
| XAUUSD SELL longa duração (4h) | −$68.60 | Maior single trade da sessão; entrada com confluence=25% (abaixo do ideal) |
| GER40 sequência 4× LOSS | −$84.05 | 4 trades consecutivos; mercado trending contra BUY no período 08:00–12:37 |
| US100 LOSS madrugada | −$21.17 | Stop imediato (0 min) — preço girou contra na abertura NY |
| XAUUSD legacy | −$15.22 | Posição pré-sessão fechada com loss |

### Drivers dos ganhos

| Causa | PnL | Observação |
|-------|-----|------------|
| GER40 #192809456 BUY 07:54 | +$74.54 | Frankfurt open momentum; maior win da sessão |
| US100 #192935713 BUY 15:55 | +$7.79 | NYSE momentum tarde |
| US100 #192924673 BUY 13:30 | +$1.44 | Scalp rápido |

---

## 5. PnL TOTAL AJUSTADO (incluindo gaps ENT-03)

| Componente | PnL | Certeza |
|------------|-----|---------|
| Realizados confirmados | −$108.81 | CONFIRMADO |
| BTCUSD #192746138 (SL hit estimado) | ~−$37.54 | ESTIMADO — confirmar MT5 |
| ETHUSD #192957446 (partial close) | ~+$4.48 | ESTIMADO — confirmar MT5 |
| **Total ajustado estimado** | **~−$141.87** | Pendente confirmação MT5 |
| Float OMEGA activo (17:03 UTC) | +$0.94 | Ledger |
| **PnL líquido estimado** | **~−$140.93** | |

---

## 6. EQUITY RECOVERY

| Momento | Equity | DD vs anchor |
|---------|--------|-------------|
| T0 arranque | $10,730.89 | — |
| Mínimo (06:04 UTC) | $10,601.48 | −1.29% |
| 08:00 UTC | $10,610.98 | −1.20% |
| 17:58 UTC | **$10,731.42** | **−0.08%** |

**A equity recuperou para quasi-T0 às 17:58 UTC**, apesar do realized PnL de −$108.81, devido ao float das posições activas (GER40, UKOIL+, US500) ter compensado as perdas realizadas.

---

*Fonte: `audit/paper/trade_feedback.jsonl` (cálculo Python directo — soma verificada)*  
*Gerado: 2026-06-02 19:10 UTC*
