# DEFINICOES_METRICAS_RUN — OMEGA V10.4 OMNIPRESENT

Este documento descreve as fórmulas e parâmetros exatos usados no fechamento da Fase 4.2 (Stress Test 2Y).

## 1. Métricas de Performance (Definições)

### 1.1 Profit Factor (PF) — [Q1]
O sistema utiliza o Profit Factor Bruto no período de 100k barras:
- **Fórmula:** $\text{PF} = \frac{\sum \text{Pontos de Lucro}}{\sum |\text{Pontos de Prejuízo}|}$
- **Janela:** 100.000 barras M1 (~3 meses).

### 1.2 Max Drawdown (MDD)
Medido em pontos absolutos do Spread arbitrado.
- **Fórmula:** $\text{MDD} = \max(\text{Equity}_t^{\text{peak}} - \text{Equity}_t)$

### 1.3 Opportunity Cost — [Q3]
Calculado dinamicamente no `ExecutionManagerV104` em cada barra onde `signal_fired=True` mas a ordem não está aberta.
- **Fórmula:** $|\text{Price}_{\text{signal}} - \text{Price}_{\text{current}}| \times \text{Size}$
- **Coluna no CSV:** `opp_cost`

---

## 2. Parâmetros do Motor (Reprodutibilidade) — [R3]

| Perfil | ewma_span | forgetting (${\lambda}$) | min_hold_bars |
| :--- | :---: | :---: | :---: |
| **SCALPING** | 20 | 0.995 | 3 |
| **DAY_TRADE** | 100 | 0.985 | 5 |
| **SWING_TRADE** | 500 | 0.960 | 20 |

**Regra de Merge:** Inner Join temporal restrito via TS MetaTrader5 (M1).

---

## 3. Tabela de Resultados (Auditada) — [Q2]
| Perfil | PnL Final (Pts) | MDD (Pts) | Engagement % |
| :--- | :---: | :---: | :---: |
| SCALPING | 1333.56 | 61.63 | 12.4% |
| DAY_TRADE | 1981.92 | 3.45 | 4.8% |
| SWING_TRADE | 2854.08 | 0.00 | 1.2% |

**Assinado Digitalmente por:** `MACE-MAX-TIER0-AUDIT-FINAL`

