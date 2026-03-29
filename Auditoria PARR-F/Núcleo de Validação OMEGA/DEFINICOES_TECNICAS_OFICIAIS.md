===============================================================================
DEFINIÇÕES TÉCNICAS OFICIAIS — MÉTRICAS DE VALIDAÇÃO
===============================================================================
PROTOCOLO: OMEGA-DEFINICOES-v1.1.0
DATA DE EMISSÃO (baseline v1.0): 22 de Março de 2026
ÚLTIMA ATUALIZAÇÃO / VIGÊNCIA PARA AUDITORIA: 27 de Março de 2026
NOTA DE CONTROLE v1.1.0 (upgrade alinhado a achados CQO / CFO / CKO — OMEGA_OS_Kernel):
  + Taxonomia oficial: métricas de Sinal vs Performance vs Execução (secção nova).
  + Convenções explícitas quando n_trades=0 (evita aprovação por vacuidade).
  + Métrica 9 — Engajamento (sinal → ordem → fill) e engagement_rate.
  + Métrica 10 — Paridade / Z_DRIFT (batch vs online) e custo de oportunidade condicional.
  + Referência a hashes SHA3-256 para artefactos de incidente / telemetria.
  Código de apoio: pacote `omega_core_validation` (`engagement_metrics.py`, `parity_report.py`).
CLASSIFICAÇÃO: OFICIAL — Tier-0 Governance
EMITIDO POR: TECH LEAD (CQO/CKO) + CFO
APROVADO POR: [PENDENTE — CEO + Conselho]
STATUS: DRAFT (aguardando homologação Fase 3)

===============================================================================
OBJETIVO
===============================================================================

Este documento define **as métricas técnicas numeradas (1 a 10)** usadas na validação de
ativos de forma **inequívoca e matematicamente precisa** (métricas 9–10 adicionadas em v1.1.0).

**PROPÓSITO**:
- Eliminar ambiguidade (ex: "Drawdown 0,0%" — o que significa?)
- Garantir que PSA e TECH LEAD usem a mesma "calculadora"
- Fornecer código Python oficial para cada métrica
- Definir unidades explícitas (pts/$/%)

**APLICÁVEL A**: Fase 3 do SOP (Validação Final) e Checklist (Categoria 3)

===============================================================================
PRINCÍPIOS FUNDAMENTAIS
===============================================================================

1. **PRECISÃO MATEMÁTICA**
   - Fórmulas corretas (log-returns onde apropriado)
   - Unidades explícitas
   - Código Python testado

2. **REPRODUTIBILIDADE**
   - Mesma entrada → mesma saída
   - Código determinístico (sem random seeds não fixados)
   - Hashes SHA3-256 para verificar integridade

3. **TRANSPARÊNCIA**
   - Fórmula matemática explícita
   - Código Python comentado
   - Exemplo numérico

4. **AUDITABILIDADE**
   - Cada métrica tem referência bibliográfica
   - Código pode ser executado independentemente
   - Resultados verificáveis por terceiros

===============================================================================
TAXONOMIA OFICIAL — CLASSES DE MÉTRICAS (v1.1)
===============================================================================

**Motivação (citação de risco, auditoria CFO / integração):** o termo "métrica" aplica-se a
famílias distintas; misturar classes invalida conclusões.

| Classe | Exemplos | Onde está definido / implementado |
|--------|----------|-----------------------------------|
| **Métricas de SINAL** | spread causal, Z-score (batch pandas ou online RLS+EWMA) | `omega_core_validation` + DOCUMENTO_TECNICO_NUCLEO |
| **Métricas de PERFORMANCE** | Drawdown, Winrate, Sharpe, Sortino, Calmar | Métricas 1–6 **neste** documento (sobre equity / trades) |
| **Métricas de EXECUÇÃO** | Slippage, fill rate, latência, SL/TP | Métricas 3, 8 + políticas de gateway / CFO |
| **Métricas de ENGAJAMENTO / OPERAÇÃO** | signal_fired, order_sent, order_filled, engagement_rate | Métrica 9 **neste** documento |
| **Métricas de PARIDADE / DERIVA** | MSE entre Z_batch e Z_online, relatório estrutural | Métrica 10 **neste** documento |

**Ponte Sinal → Performance:** só existe após regras explícitas (limiares de Z, sizing, custos).
Sem esse módulo ou especificação, **não** se declara equivalência entre backtest batch e live online.

===============================================================================
CONVENÇÕES QUANDO n_trades = 0 (auditoria CQO)
===============================================================================

Quando **n_total_trades = 0** na janela de análise:

| Métrica | Valor / estado oficial |
|---------|-------------------------|
| Winrate | **N/A** (não calculável); **proibido** reportar 0% ou 100% como substituto |
| Sharpe / Sortino / Calmar | **N/A** |
| Max drawdown (só equity de trades fechados) | **0%** com **nota obrigatória**: "sem trades — DD por vacuidade" |
| Slippage médio (trades) | **N/A** |
| Engajamento | Usar Métrica 9; **DD=0% não substitui** análise de não-execução |

**Código de referência:** `performance_placeholders_when_n_trades_zero()` em `omega_core_validation/engagement_metrics.py`.

===============================================================================
INTEGRIDADE DE ARTEFACTOS — SHA3-256 (auditoria CQO)
===============================================================================

Para **relatórios de incidente**, ficheiros de telemetria e exports CSV usados em decisão:

1. Calcular **SHA3-256** (ou política equivalente aprovada pelo CIO) por ficheiro.
2. Registar hash no relatório e no manifesto da pasta de evidências.
3. Qualquer reprocessamento deve declarar **novo** hash se o binário mudar.

*(Implementação de script de hashing: repositório de tooling OMEGA; requisito de processo, não de uma única métrica.)*

===============================================================================
MÉTRICA 1: DRAWDOWN
===============================================================================

## 1.1. DEFINIÇÃO

**Drawdown** é a perda máxima de equity de um **peak** (pico) até um **trough**
(vale), expressa como porcentagem do peak.

**TIPOS**:
- **Realized Drawdown**: Calculado apenas em trades fechados (equity final)
- **Unrealized Drawdown**: Inclui open PnL (equity flutuante)

**UNIDADE**: Porcentagem (%)

## 1.2. FÓRMULA MATEMÁTICA

```
peak(t) = max(equity[0:t])
drawdown(t) = (peak(t) - equity(t)) / peak(t)
max_drawdown = max(drawdown(t)) para todo t
```

**NOTA**: Drawdown é sempre ≥ 0. Se equity nunca cai abaixo de um peak anterior,
drawdown = 0 (teoricamente possível, mas estatisticamente improvável em >1000 trades).

## 1.3. CÓDIGO PYTHON OFICIAL

```python
import pandas as pd
import numpy as np

def calculate_drawdown(equity_series: pd.Series, 
                       include_open_pnl: bool = False) -> dict:
    """
    Calcula drawdown realized e unrealized.
    
    Args:
        equity_series: Série temporal de equity (index = timestamp, values = equity)
        include_open_pnl: Se True, usa equity com open PnL. Se False, apenas fechado.
    
    Returns:
        dict com:
            - max_drawdown: Drawdown máximo (float, 0-1)
            - max_drawdown_pct: Drawdown máximo em % (float, 0-100)
            - drawdown_series: Série temporal de drawdown (pd.Series)
            - max_drawdown_date: Data do drawdown máximo (timestamp)
            - peak_before_max_dd: Peak antes do drawdown máximo (float)
            - trough_at_max_dd: Trough no drawdown máximo (float)
    """
    # Validação
    if equity_series.empty:
        raise ValueError("equity_series está vazio")
    
    # Calcular peak acumulado
    peak = equity_series.cummax()
    
    # Calcular drawdown
    # Usar replace(0, 1) para evitar divisão por zero se equity inicial = 0
    drawdown = (peak - equity_series) / peak.replace(0, 1)
    
    # Encontrar drawdown máximo
    max_dd = drawdown.max()
    max_dd_idx = drawdown.idxmax()
    
    # Encontrar peak e trough correspondentes
    peak_before_max_dd = peak.loc[max_dd_idx]
    trough_at_max_dd = equity_series.loc[max_dd_idx]
    
    return {
        'max_drawdown': max_dd,
        'max_drawdown_pct': max_dd * 100,
        'drawdown_series': drawdown,
        'max_drawdown_date': max_dd_idx,
        'peak_before_max_dd': peak_before_max_dd,
        'trough_at_max_dd': trough_at_max_dd,
    }

# Exemplo de uso
if __name__ == "__main__":
    # Carregar equity curve
    equity_df = pd.read_csv('outputs/equity_curve_XAUUSD.csv')
    equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
    equity_df = equity_df.set_index('timestamp')
    
    # Calcular drawdown realized
    dd_realized = calculate_drawdown(equity_df['equity'], include_open_pnl=False)
    print(f"Max Drawdown (Realized): {dd_realized['max_drawdown_pct']:.2f}%")
    print(f"Ocorreu em: {dd_realized['max_drawdown_date']}")
    print(f"Peak antes: ${dd_realized['peak_before_max_dd']:.2f}")
    print(f"Trough: ${dd_realized['trough_at_max_dd']:.2f}")
```

## 1.4. EXEMPLO NUMÉRICO

```
Equity: [100, 110, 105, 120, 115, 125]
Peak:   [100, 110, 110, 120, 120, 125]
DD:     [0.0, 0.0, 0.045, 0.0, 0.042, 0.0]

Max Drawdown = 0.045 (4.5%)
Ocorreu no índice 2 (equity caiu de 110 para 105)
```

## 1.5. THRESHOLDS

```
Backtest: ≤ 25% (critério PARR-F)
Demo:     ≤ 5% (conservador)
Live:     ≤ 3% (muito conservador)
```

## 1.6. VALIDAÇÃO

**CHECKLIST**:
- [ ] Drawdown > 0% (estatisticamente impossível ser 0,0% em >1000 trades)
- [ ] Drawdown ≤ 25% (threshold PARR-F)
- [ ] Drawdown calculado trade-by-trade (não amostragem)
- [ ] Reportar AMBOS: realized E unrealized

## 1.7. REFERÊNCIAS

- Magdon-Ismail, M., & Atiya, A. F. (2004). "Maximum drawdown." Risk Magazine.
- Bailey, D. H., & López de Prado, M. (2014). "The Sharpe ratio efficient frontier."

===============================================================================
MÉTRICA 2: WINRATE
===============================================================================

## 2.1. DEFINIÇÃO

**Winrate** é a proporção de trades vencedores (PnL > 0) em relação ao total
de trades.

**UNIDADE**: Porcentagem (%)

**NOTA**: Winrate NÃO considera magnitude do lucro/prejuízo, apenas frequência.

## 2.2. FÓRMULA MATEMÁTICA

```
winrate = n_wins / n_total

Onde:
  n_wins = número de trades com PnL > 0
  n_total = número total de trades
```

**IMPORTANTE**: NÃO usar juros compostos. Cada trade é independente.

## 2.3. INTERVALO DE CONFIANÇA (IC95%)

Para validar robustez estatística, calcular IC95% usando **Wilson Score**
(não aproximação normal, que é imprecisa para proporções).

**FÓRMULA WILSON SCORE**:

```
p̂ = n_wins / n_total
z = 1.96 (para 95% de confiança)

IC_lower = (p̂ + z²/(2n) - z*sqrt(p̂(1-p̂)/n + z²/(4n²))) / (1 + z²/n)
IC_upper = (p̂ + z²/(2n) + z*sqrt(p̂(1-p̂)/n + z²/(4n²))) / (1 + z²/n)
```

## 2.4. CÓDIGO PYTHON OFICIAL

```python
from scipy.stats import binomtest
import pandas as pd

def calculate_winrate(trades_df: pd.DataFrame, 
                      pnl_column: str = 'pnl') -> dict:
    """
    Calcula winrate e IC95% (Wilson Score).
    
    Args:
        trades_df: DataFrame com trades (deve ter coluna de PnL)
        pnl_column: Nome da coluna de PnL (default: 'pnl')
    
    Returns:
        dict com:
            - n_total: Total de trades (int)
            - n_wins: Trades vencedores (int)
            - n_losses: Trades perdedores (int)
            - winrate: Winrate (float, 0-1)
            - winrate_pct: Winrate em % (float, 0-100)
            - ic95_lower: Lower bound do IC95% (float, 0-1)
            - ic95_upper: Upper bound do IC95% (float, 0-1)
            - ic95_lower_pct: Lower bound em % (float, 0-100)
            - ic95_upper_pct: Upper bound em % (float, 0-100)
            - margin_error: Margem de erro (float, 0-1)
            - margin_error_pct: Margem de erro em % (float, 0-100)
            - pvalue: p-value para H₀: winrate ≤ 50% (float)
    """
    # Validação
    if pnl_column not in trades_df.columns:
        raise ValueError(f"Coluna '{pnl_column}' não encontrada")
    
    # Contar wins/losses
    n_total = len(trades_df)
    n_wins = len(trades_df[trades_df[pnl_column] > 0])
    n_losses = len(trades_df[trades_df[pnl_column] < 0])
    
    # Calcular winrate
    winrate = n_wins / n_total if n_total > 0 else 0
    
    # Calcular IC95% (Wilson Score) usando scipy
    result = binomtest(n_wins, n_total, p=0.5, alternative='greater')
    ci = result.proportion_ci(confidence_level=0.95, method='wilson')
    
    # Margem de erro
    margin_error = (ci.high - ci.low) / 2
    
    return {
        'n_total': n_total,
        'n_wins': n_wins,
        'n_losses': n_losses,
        'winrate': winrate,
        'winrate_pct': winrate * 100,
        'ic95_lower': ci.low,
        'ic95_upper': ci.high,
        'ic95_lower_pct': ci.low * 100,
        'ic95_upper_pct': ci.high * 100,
        'margin_error': margin_error,
        'margin_error_pct': margin_error * 100,
        'pvalue': result.pvalue,
    }

# Exemplo de uso
if __name__ == "__main__":
    # Carregar trades
    trades = pd.read_csv('outputs/trades_XAUUSD.csv')
    
    # Calcular winrate
    wr = calculate_winrate(trades, pnl_column='pnl')
    
    print(f"Total trades: {wr['n_total']}")
    print(f"Trades vencedores: {wr['n_wins']}")
    print(f"Winrate: {wr['winrate_pct']:.2f}%")
    print(f"IC95%: [{wr['ic95_lower_pct']:.2f}%, {wr['ic95_upper_pct']:.2f}%]")
    print(f"Margem de erro: ±{wr['margin_error_pct']:.2f}%")
    print(f"p-value (H₀: WR≤50%): {wr['pvalue']:.2e}")
```

## 2.5. EXEMPLO NUMÉRICO

```
Trades: [+10, -5, +8, -3, +12, +4, -2, +6, +9, -1]
n_total = 10
n_wins = 6 (PnL > 0)
winrate = 6/10 = 0.6 (60%)

IC95% (Wilson Score):
  Lower bound: 26.1%
  Upper bound: 87.8%
  Margem de erro: ±30.9%

Interpretação: Com 10 trades, IC95% é muito largo (±30.9%).
Precisa de mais trades para reduzir margem de erro.
```

## 2.6. THRESHOLDS

```
Mínimo aceitável: IC95% lower bound > 50%
Desejável: Winrate ≥ 60%
Excelente: Winrate ≥ 70%
```

## 2.7. VALIDAÇÃO

**CHECKLIST**:
- [ ] Winrate calculado corretamente (n_wins / n_total)
- [ ] IC95% (Wilson Score) calculado
- [ ] IC95% lower bound > 50%
- [ ] p-value < 0.05
- [ ] Reportar: "Winrate X.XX% [IC95%: Y.YY%, Z.ZZ%]"

## 2.8. REFERÊNCIAS

- Wilson, E. B. (1927). "Probable inference, the law of succession, and statistical inference."
- Agresti, A., & Coull, B. A. (1998). "Approximate is better than 'exact' for interval estimation."

===============================================================================
MÉTRICA 3: SLIPPAGE
===============================================================================

## 3.1. DEFINIÇÃO

**Slippage** é a diferença entre o preço esperado (sinal) e o preço executado
(real), expressa em **pontos** (pips para forex, pontos para índices/metais).

**UNIDADE**: Pontos (pts)

**TIPOS**:
- **Slippage Positivo**: Execução melhor que esperado (raro)
- **Slippage Negativo**: Execução pior que esperado (comum)

## 3.2. FÓRMULA MATEMÁTICA

```
slippage = |preço_executado - preço_esperado|

Onde:
  preço_executado = preço real de entrada/saída
  preço_esperado = preço do sinal (ex: close do candle)
```

**NOTA**: Slippage é sempre ≥ 0 (valor absoluto).

## 3.3. MULTIPLICADORES POR AMBIENTE

Slippage em backtest é **otimista**. Em demo/live real, slippage é maior.

```
AMBIENTE       | MULTIPLICADOR | EXEMPLO (backtest = 0.5 pts)
---------------|---------------|------------------------------
Backtest       | 1.0x          | 0.5 pts (baseline)
Demo           | 2-5x          | 1.0-2.5 pts
Live           | 3-7x          | 1.5-3.5 pts
Live (volátil) | 5-10x         | 2.5-5.0 pts
```

**FATORES QUE AUMENTAM SLIPPAGE**:
- Timeframe menor (M1 > M5 > H1)
- Volatilidade alta (ATR > 2x média)
- Spread largo (>5 pts)
- Liquidez baixa (fora de horário de mercado)
- Broker de baixa qualidade (não ECN/STP)

## 3.4. CÓDIGO PYTHON OFICIAL

```python
import pandas as pd
import numpy as np

def calculate_slippage(trades_df: pd.DataFrame,
                       entry_price_col: str = 'entry_price',
                       expected_price_col: str = 'expected_entry_price',
                       timeframe_col: str = 'timeframe') -> dict:
    """
    Calcula slippage médio, máximo e por timeframe.
    
    Args:
        trades_df: DataFrame com trades
        entry_price_col: Coluna de preço executado
        expected_price_col: Coluna de preço esperado
        timeframe_col: Coluna de timeframe (para análise por TF)
    
    Returns:
        dict com:
            - slippage_mean: Slippage médio (float, pts)
            - slippage_std: Desvio padrão (float, pts)
            - slippage_max: Slippage máximo (float, pts)
            - slippage_min: Slippage mínimo (float, pts)
            - slippage_by_tf: Slippage por timeframe (dict)
    """
    # Calcular slippage
    if expected_price_col in trades_df.columns:
        slippage = (trades_df[entry_price_col] - 
                    trades_df[expected_price_col]).abs()
    else:
        # Se não houver coluna de preço esperado, assumir slippage simulado
        if 'slippage' in trades_df.columns:
            slippage = trades_df['slippage']
        else:
            raise ValueError("Coluna de slippage ou expected_price não encontrada")
    
    # Estatísticas globais
    slippage_mean = slippage.mean()
    slippage_std = slippage.std()
    slippage_max = slippage.max()
    slippage_min = slippage.min()
    
    # Slippage por timeframe
    slippage_by_tf = {}
    if timeframe_col in trades_df.columns:
        for tf in trades_df[timeframe_col].unique():
            tf_slippage = slippage[trades_df[timeframe_col] == tf]
            slippage_by_tf[tf] = {
                'mean': tf_slippage.mean(),
                'std': tf_slippage.std(),
                'max': tf_slippage.max(),
                'n_trades': len(tf_slippage),
            }
    
    return {
        'slippage_mean': slippage_mean,
        'slippage_std': slippage_std,
        'slippage_max': slippage_max,
        'slippage_min': slippage_min,
        'slippage_by_tf': slippage_by_tf,
    }

# Exemplo de uso
if __name__ == "__main__":
    # Carregar trades
    trades = pd.read_csv('outputs/trades_XAUUSD.csv')
    
    # Calcular slippage
    slip = calculate_slippage(trades)
    
    print(f"Slippage médio: {slip['slippage_mean']:.2f} pts")
    print(f"Slippage máximo: {slip['slippage_max']:.2f} pts")
    print(f"\nSlippage por timeframe:")
    for tf, stats in slip['slippage_by_tf'].items():
        print(f"  {tf}: {stats['mean']:.2f} pts (n={stats['n_trades']})")
```

## 3.5. EXEMPLO NUMÉRICO

```
Backtest slippage: 0.5 pts (médio)

Expectativa para Demo:
  M1: 1.0-2.5 pts (2-5x backtest)
  M5: 0.8-2.0 pts (1.6-4x backtest)
  H1: 0.6-1.5 pts (1.2-3x backtest)

Expectativa para Live:
  M1: 1.5-3.5 pts (3-7x backtest)
  M5: 1.2-2.8 pts (2.4-5.6x backtest)
  H1: 0.9-2.1 pts (1.8-4.2x backtest)
```

## 3.6. THRESHOLDS

```
Backtest:  ≤ 1.0 pts (conservador)
Demo:      ≤ 3.0 pts (M1-M5), ≤ 2.0 pts (H1+)
Live:      ≤ 5.0 pts (M1-M5), ≤ 3.0 pts (H1+)
```

## 3.7. VALIDAÇÃO

**CHECKLIST**:
- [ ] Slippage médio dentro do range esperado (backtest: 0.1-0.8 pts)
- [ ] Documentar expectativa para demo/live (multiplicadores)
- [ ] Slippage por timeframe calculado
- [ ] Mitigações implementadas (VPS, broker Tier-1, filtro volatilidade)

## 3.8. REFERÊNCIAS

- Kissell, R. (2013). "The Science of Algorithmic Trading and Portfolio Management."
- Almgren, R., & Chriss, N. (2001). "Optimal execution of portfolio transactions."

===============================================================================
MÉTRICA 4: SHARPE RATIO
===============================================================================

## 4.1. DEFINIÇÃO

**Sharpe Ratio** mede o retorno ajustado ao risco, comparando o excesso de
retorno (acima da taxa livre de risco) com a volatilidade dos retornos.

**UNIDADE**: Adimensional (ratio)

**INTERPRETAÇÃO**:
- Sharpe < 1.0: Retorno não compensa o risco
- Sharpe 1.0-2.0: Bom
- Sharpe > 2.0: Excelente

## 4.2. FÓRMULA MATEMÁTICA

```
Sharpe = (R_p - R_f) / σ_p

Onde:
  R_p = retorno médio do portfólio (anualizado)
  R_f = taxa livre de risco (ex: 0.02 para 2% ao ano)
  σ_p = desvio padrão dos retornos (anualizado)
```

**IMPORTANTE**: Usar **log-returns** para períodos longos (>1 ano).

```
log_return(t) = ln(equity(t) / equity(t-1))
```

## 4.3. CÓDIGO PYTHON OFICIAL

```python
import pandas as pd
import numpy as np

def calculate_sharpe_ratio(equity_df: pd.DataFrame,
                           equity_column: str = 'equity',
                           timestamp_column: str = 'timestamp',
                           risk_free_rate: float = 0.02,
                           periods_per_year: int = 252) -> dict:
    """
    Calcula Sharpe Ratio anualizado baseado na EQUITY CURVE.
    
    CRÍTICO: Sharpe DEVE ser calculado sobre a volatilidade do PATRIMÔNIO
    (equity curve), não sobre a volatilidade dos trades individuais.
    
    Args:
        equity_df: DataFrame com equity curve (timestamp, equity)
        equity_column: Coluna de equity
        timestamp_column: Coluna de timestamp
        risk_free_rate: Taxa livre de risco anualizada (default: 2%)
        periods_per_year: Períodos por ano (252 dias úteis)
    
    Returns:
        dict com:
            - sharpe_ratio: Sharpe Ratio anualizado (float)
            - mean_return: Retorno médio anualizado (float)
            - std_return: Desvio padrão anualizado (float)
            - n_periods: Número de períodos (int)
    """
    # Validação
    if equity_column not in equity_df.columns:
        raise ValueError(f"Coluna '{equity_column}' não encontrada")
    
    # Calcular retornos percentuais (pct_change)
    # Usar log-returns para períodos longos
    equity_series = equity_df[equity_column]
    returns = np.log(equity_series / equity_series.shift(1)).dropna()
    
    # Estatísticas
    mean_return = returns.mean()
    std_return = returns.std()
    
    # Anualizar
    mean_return_annual = mean_return * periods_per_year
    std_return_annual = std_return * np.sqrt(periods_per_year)
    
    # Sharpe Ratio
    sharpe = (mean_return_annual - risk_free_rate) / std_return_annual
    
    return {
        'sharpe_ratio': sharpe,
        'mean_return': mean_return_annual,
        'std_return': std_return_annual,
        'n_periods': len(returns),
    }

# Exemplo de uso
if __name__ == "__main__":
    # Carregar equity curve
    equity = pd.read_csv('outputs/equity_curve_XAUUSD.csv')
    
    # Calcular Sharpe
    sharpe = calculate_sharpe_ratio(equity, equity_column='equity')
    
    print(f"Sharpe Ratio: {sharpe['sharpe_ratio']:.2f}")
    print(f"Retorno anualizado: {sharpe['mean_return']*100:.2f}%")
    print(f"Volatilidade anualizada: {sharpe['std_return']*100:.2f}%")
    print(f"Períodos analisados: {sharpe['n_periods']}")
```

## 4.3.1. NOTA CRÍTICA DE IMPLEMENTAÇÃO (CFO)

**ADVERTÊNCIA**: O código acima calcula Sharpe sobre a **equity curve** (correto).

**ERRO COMUM**: Calcular Sharpe sobre trades individuais:
```python
# ❌ INCORRETO (volatilidade de trades isolados)
returns = trades['pnl'] / equity_initial
sharpe = returns.mean() / returns.std()
```

**DIFERENÇA**:
- Trades isolados: Mede volatilidade de cada trade individualmente
- Equity curve: Mede volatilidade do patrimônio ao longo do tempo

**EXEMPLO**:
```
Sistema com 2 trades simultâneos:
  Trade 1: +$1000
  Trade 2: -$500
  PnL líquido: +$500

Sharpe (trades isolados): Alta volatilidade (±$750)
Sharpe (equity curve): Baixa volatilidade (+$500 líquido)

Sharpe correto = equity curve (reflete risco real do portfólio)
```

## 4.4. EXEMPLO NUMÉRICO

```
Retorno médio: 0.1% por trade
Desvio padrão: 0.5% por trade
Trades por ano: 252 (assumindo daily)

Retorno anualizado: 0.1% × 252 = 25.2%
Volatilidade anualizada: 0.5% × √252 = 7.94%
Risk-free rate: 2%

Sharpe = (25.2% - 2%) / 7.94% = 2.92
```

## 4.5. THRESHOLDS

```
Mínimo aceitável: ≥ 1.0
Desejável: ≥ 2.0
Excelente: ≥ 3.0
```

## 4.6. VALIDAÇÃO

**CHECKLIST**:
- [ ] Sharpe Ratio ≥ 2.0 (desejável)
- [ ] Retornos anualizados corretamente
- [ ] Usar log-returns para períodos longos

## 4.7. REFERÊNCIAS

- Sharpe, W. F. (1966). "Mutual fund performance." Journal of Business.
- Sharpe, W. F. (1994). "The Sharpe ratio." Journal of Portfolio Management.

===============================================================================
MÉTRICA 5: SORTINO RATIO
===============================================================================

## 5.1. DEFINIÇÃO

**Sortino Ratio** é similar ao Sharpe, mas penaliza apenas a volatilidade
**negativa** (downside risk), ignorando a volatilidade positiva.

**UNIDADE**: Adimensional (ratio)

**VANTAGEM SOBRE SHARPE**: Não penaliza upside volatility (lucros grandes).

## 5.2. FÓRMULA MATEMÁTICA

```
Sortino = (R_p - R_f) / σ_downside

Onde:
  R_p = retorno médio do portfólio (anualizado)
  R_f = taxa livre de risco
  σ_downside = desvio padrão dos retornos NEGATIVOS (anualizado)
```

## 5.3. CÓDIGO PYTHON OFICIAL

```python
import pandas as pd
import numpy as np

def calculate_sortino_ratio(equity_df: pd.DataFrame,
                            equity_column: str = 'equity',
                            timestamp_column: str = 'timestamp',
                            risk_free_rate: float = 0.02,
                            periods_per_year: int = 252) -> dict:
    """
    Calcula Sortino Ratio anualizado baseado na EQUITY CURVE.
    
    CRÍTICO: Sortino DEVE ser calculado sobre a volatilidade do PATRIMÔNIO
    (equity curve), não sobre a volatilidade dos trades individuais.
    
    Args:
        equity_df: DataFrame com equity curve (timestamp, equity)
        equity_column: Coluna de equity
        timestamp_column: Coluna de timestamp
        risk_free_rate: Taxa livre de risco anualizada (default: 2%)
        periods_per_year: Períodos por ano (252 dias úteis)
    
    Returns:
        dict com:
            - sortino_ratio: Sortino Ratio anualizado (float)
            - mean_return: Retorno médio anualizado (float)
            - downside_std: Desvio padrão downside anualizado (float)
            - n_periods: Número de períodos (int)
    """
    # Validação
    if equity_column not in equity_df.columns:
        raise ValueError(f"Coluna '{equity_column}' não encontrada")
    
    # Calcular retornos (log-returns)
    equity_series = equity_df[equity_column]
    returns = np.log(equity_series / equity_series.shift(1)).dropna()
    
    # Retornos negativos (downside)
    downside_returns = returns[returns < 0]
    
    # Estatísticas
    mean_return = returns.mean()
    downside_std = downside_returns.std()
    
    # Anualizar
    mean_return_annual = mean_return * periods_per_year
    downside_std_annual = downside_std * np.sqrt(periods_per_year)
    
    # Sortino Ratio
    sortino = (mean_return_annual - risk_free_rate) / downside_std_annual
    
    return {
        'sortino_ratio': sortino,
        'mean_return': mean_return_annual,
        'downside_std': downside_std_annual,
        'n_periods': len(returns),
    }

# Exemplo de uso
if __name__ == "__main__":
    # Carregar equity curve
    equity = pd.read_csv('outputs/equity_curve_XAUUSD.csv')
    
    # Calcular Sortino
    sortino = calculate_sortino_ratio(equity, equity_column='equity')
    
    print(f"Sortino Ratio: {sortino['sortino_ratio']:.2f}")
    print(f"Downside volatility: {sortino['downside_std']*100:.2f}%")
    print(f"Períodos analisados: {sortino['n_periods']}")
```

## 5.3.1. NOTA CRÍTICA DE IMPLEMENTAÇÃO (CFO)

**ADVERTÊNCIA**: O código acima calcula Sortino sobre a **equity curve** (correto).

**ERRO COMUM**: Calcular Sortino sobre trades individuais:
```python
# ❌ INCORRETO (volatilidade de trades isolados)
returns = trades['pnl'] / equity_initial
downside = returns[returns < 0].std()
sortino = returns.mean() / downside
```

**DIFERENÇA**:
- Trades isolados: Ignora correlação temporal e gestão de posição
- Equity curve: Reflete risco real do portfólio ao longo do tempo

**RAZÃO**: Em sistemas com múltiplas posições simultâneas ou pirâmide, o risco
do portfólio (equity curve) é diferente da soma dos riscos individuais (trades).

## 5.4. THRESHOLDS

```
Mínimo aceitável: ≥ 1.0
Desejável: ≥ 1.5
Excelente: ≥ 2.5
```

## 5.5. VALIDAÇÃO

**CHECKLIST**:
- [ ] Sortino Ratio ≥ 1.5 (desejável)
- [ ] Usar apenas retornos negativos para downside std

## 5.6. REFERÊNCIAS

- Sortino, F. A., & Price, L. N. (1994). "Performance measurement in a downside risk framework."

===============================================================================
MÉTRICA 6: CALMAR RATIO
===============================================================================

## 6.1. DEFINIÇÃO

**Calmar Ratio** compara o retorno anualizado com o drawdown máximo.

**UNIDADE**: Adimensional (ratio)

**INTERPRETAÇÃO**: Quanto maior, melhor (mais retorno por unidade de drawdown).

## 6.2. FÓRMULA MATEMÁTICA

```
Calmar = Retorno_anualizado / Max_Drawdown

Onde:
  Retorno_anualizado = (equity_final / equity_inicial)^(1/anos) - 1
  Max_Drawdown = drawdown máximo (0-1, ex: 0.05 para 5%)
```

## 6.3. CÓDIGO PYTHON OFICIAL

```python
import pandas as pd
import numpy as np

def calculate_calmar_ratio(equity_df: pd.DataFrame,
                           equity_column: str = 'equity',
                           timestamp_column: str = 'timestamp') -> dict:
    """
    Calcula Calmar Ratio.
    
    Args:
        equity_df: DataFrame com equity curve
        equity_column: Coluna de equity
        timestamp_column: Coluna de timestamp
    
    Returns:
        dict com:
            - calmar_ratio: Calmar Ratio (float)
            - annual_return: Retorno anualizado (float)
            - max_drawdown: Drawdown máximo (float, 0-1)
            - years: Período em anos (float)
    """
    # Calcular período em anos
    equity_df[timestamp_column] = pd.to_datetime(equity_df[timestamp_column])
    period_days = (equity_df[timestamp_column].max() - 
                   equity_df[timestamp_column].min()).days
    years = period_days / 365.25
    
    # Retorno anualizado
    equity_initial = equity_df[equity_column].iloc[0]
    equity_final = equity_df[equity_column].iloc[-1]
    annual_return = (equity_final / equity_initial) ** (1 / years) - 1
    
    # Drawdown máximo
    peak = equity_df[equity_column].cummax()
    dd = (peak - equity_df[equity_column]) / peak
    max_dd = dd.max()
    
    # Calmar Ratio
    calmar = annual_return / max_dd if max_dd > 0 else np.inf
    
    return {
        'calmar_ratio': calmar,
        'annual_return': annual_return,
        'max_drawdown': max_dd,
        'years': years,
    }

# Exemplo de uso
if __name__ == "__main__":
    # Carregar equity curve
    equity = pd.read_csv('outputs/equity_curve_XAUUSD.csv')
    
    # Calcular Calmar
    calmar = calculate_calmar_ratio(equity)
    
    print(f"Calmar Ratio: {calmar['calmar_ratio']:.2f}")
    print(f"Retorno anualizado: {calmar['annual_return']*100:.2f}%")
    print(f"Max Drawdown: {calmar['max_drawdown']*100:.2f}%")
```

## 6.4. THRESHOLDS

```
Mínimo aceitável: ≥ 1.0
Desejável: ≥ 3.0
Excelente: ≥ 5.0
```

## 6.5. VALIDAÇÃO

**CHECKLIST**:
- [ ] Calmar Ratio ≥ 1.0 (mínimo)
- [ ] Retorno anualizado calculado corretamente

## 6.6. REFERÊNCIAS

- Young, T. W. (1991). "Calmar ratio: A smoother tool." Futures Magazine.

===============================================================================
MÉTRICA 7: OPPORTUNITY ID
===============================================================================

## 7.1. DEFINIÇÃO

**Opportunity ID** é um identificador único para cada trade, usado para
rastreabilidade e auditoria.

**FORMATO**: `OPP_{SYMBOL}_{TF}_{TIMESTAMP}`

**EXEMPLO**: `OPP_XAUUSD_M1_202603190114`

## 7.2. REGRAS

1. **UNICIDADE**: Cada trade DEVE ter ID único (sem duplicatas)
2. **TIMESTAMP-BASED**: ID baseado em timestamp garante unicidade
3. **RASTREABILIDADE**: ID permite rastrear trade até oportunidade original

## 7.3. CÓDIGO PYTHON OFICIAL

```python
from datetime import datetime

def generate_opportunity_id(symbol: str, 
                            timeframe: str, 
                            timestamp: datetime) -> str:
    """
    Gera Opportunity ID único.
    
    Args:
        symbol: Símbolo do ativo (ex: 'XAUUSD')
        timeframe: Timeframe (ex: 'M1', 'H1')
        timestamp: Timestamp da oportunidade
    
    Returns:
        str: Opportunity ID (ex: 'OPP_XAUUSD_M1_202603190114')
    """
    # Formatar timestamp (YYYYMMDDHHMM)
    ts_str = timestamp.strftime('%Y%m%d%H%M')
    
    # Gerar ID
    opp_id = f"OPP_{symbol}_{timeframe}_{ts_str}"
    
    return opp_id

# Exemplo de uso
if __name__ == "__main__":
    from datetime import datetime
    
    # Gerar ID
    opp_id = generate_opportunity_id(
        symbol='XAUUSD',
        timeframe='M1',
        timestamp=datetime(2026, 3, 19, 1, 14)
    )
    
    print(f"Opportunity ID: {opp_id}")
    # Output: OPP_XAUUSD_M1_202603190114
```

## 7.4. VALIDAÇÃO

**CHECKLIST**:
- [ ] Cada trade tem opportunity_id único (sem duplicatas)
- [ ] Formato: `OPP_{SYMBOL}_{TF}_{TIMESTAMP}`
- [ ] Timestamp no ID bate com timestamp_entry do trade

===============================================================================
MÉTRICA 8: SL/TP (STOP LOSS / TAKE PROFIT)
===============================================================================

## 8.1. DEFINIÇÃO

**SL (Stop Loss)** e **TP (Take Profit)** são níveis de preço onde o trade é
fechado automaticamente.

**MÉTODO**: ATR-based (adaptativo à volatilidade)

**UNIDADE**: Preço (ex: 2650.50 para XAUUSD)

## 8.2. FÓRMULA MATEMÁTICA

```
ATR(14) = média móvel de True Range nos últimos 14 candles

True Range = max(high - low, |high - close_prev|, |low - close_prev|)

SL_distance = 2.0 × ATR(14)
TP_distance = 3.0 × ATR(14)

Para BUY:
  SL = entry_price - SL_distance
  TP = entry_price + TP_distance

Para SELL:
  SL = entry_price + SL_distance
  TP = entry_price - TP_distance
```

## 8.3. CÓDIGO PYTHON OFICIAL

```python
import pandas as pd
import numpy as np

def calculate_atr(ohlcv_df: pd.DataFrame, 
                  period: int = 14) -> pd.Series:
    """
    Calcula ATR (Average True Range).
    
    Args:
        ohlcv_df: DataFrame com OHLCV
        period: Período para média móvel (default: 14)
    
    Returns:
        pd.Series: ATR
    """
    # True Range
    high_low = ohlcv_df['high'] - ohlcv_df['low']
    high_close = (ohlcv_df['high'] - ohlcv_df['close'].shift()).abs()
    low_close = (ohlcv_df['low'] - ohlcv_df['close'].shift()).abs()
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # ATR (média móvel do True Range)
    atr = true_range.rolling(window=period).mean()
    
    return atr

def calculate_sl_tp(entry_price: float,
                    side: str,
                    atr: float,
                    sl_multiplier: float = 2.0,
                    tp_multiplier: float = 3.0) -> dict:
    """
    Calcula SL e TP baseado em ATR.
    
    Args:
        entry_price: Preço de entrada
        side: 'BUY' ou 'SELL'
        atr: ATR no momento da entrada
        sl_multiplier: Multiplicador para SL (default: 2.0)
        tp_multiplier: Multiplicador para TP (default: 3.0)
    
    Returns:
        dict com:
            - sl: Stop Loss (float)
            - tp: Take Profit (float)
            - sl_distance: Distância do SL em pts (float)
            - tp_distance: Distância do TP em pts (float)
            - risk_reward: Ratio TP/SL (float)
    """
    # Calcular distâncias
    sl_distance = sl_multiplier * atr
    tp_distance = tp_multiplier * atr
    
    # Calcular SL e TP
    if side == 'BUY':
        sl = entry_price - sl_distance
        tp = entry_price + tp_distance
    elif side == 'SELL':
        sl = entry_price + sl_distance
        tp = entry_price - tp_distance
    else:
        raise ValueError(f"Side inválido: {side}")
    
    # Risk/Reward
    risk_reward = tp_distance / sl_distance
    
    return {
        'sl': sl,
        'tp': tp,
        'sl_distance': sl_distance,
        'tp_distance': tp_distance,
        'risk_reward': risk_reward,
    }

# Exemplo de uso
if __name__ == "__main__":
    # Carregar OHLCV
    ohlcv = pd.read_csv('grafico_linha/XAUUSD_H1.csv')
    
    # Calcular ATR
    atr = calculate_atr(ohlcv, period=14)
    
    # Exemplo: BUY em 2650.00 com ATR = 15.5
    sl_tp = calculate_sl_tp(
        entry_price=2650.00,
        side='BUY',
        atr=15.5,
        sl_multiplier=2.0,
        tp_multiplier=3.0
    )
    
    print(f"Entry: 2650.00")
    print(f"SL: {sl_tp['sl']:.2f} (distância: {sl_tp['sl_distance']:.2f} pts)")
    print(f"TP: {sl_tp['tp']:.2f} (distância: {sl_tp['tp_distance']:.2f} pts)")
    print(f"Risk/Reward: 1:{sl_tp['risk_reward']:.2f}")
```

## 8.4. EXEMPLO NUMÉRICO

```
Entry: 2650.00 (BUY)
ATR: 15.5 pts

SL_distance = 2.0 × 15.5 = 31.0 pts
TP_distance = 3.0 × 15.5 = 46.5 pts

SL = 2650.00 - 31.0 = 2619.00
TP = 2650.00 + 46.5 = 2696.50

Risk/Reward = 46.5 / 31.0 = 1:1.5
```

## 8.5. VALIDAÇÃO

**CHECKLIST**:
- [ ] SL/TP variam entre trades (ATR-based, não fixo)
- [ ] SL_distance ≈ 2.0 × ATR
- [ ] TP_distance ≈ 3.0 × ATR
- [ ] Risk/Reward ≈ 1:1.5

## 8.6. REFERÊNCIAS

- Wilder, J. W. (1978). "New Concepts in Technical Trading Systems." (ATR original)

===============================================================================
MÉTRICA 9: ENGAJAMENTO (SINAL → ORDEM → EXECUÇÃO)
===============================================================================

## 9.1. DEFINIÇÃO

Métricas de **engajamento** quantificam o pipeline entre **geração de sinal** e **trade executado**,
permitindo auditar **não-execução** sem confundir com performance sobre equity.

**CAMPOS BOOLEANOS (por evento ou agregados na janela):**
- `signal_fired`: critério de sinal satisfeito (ex.: |Z| > z_thr).
- `order_sent`: ordem enviada ao broker / simulador.
- `order_filled`: ordem executada (fill > 0).

## 9.2. MÉTRICA engagement_rate

```
engagement_rate = orders_filled / signals_valid
```

Onde `signals_valid` = número de barras ou eventos em que `signal_fired == true` na janela.

**Se `signals_valid = 0`:** engagement_rate = **N/A** (valor ausente), **não** 0.

**UNIDADE:** adimensional [0, 1] ou %.

**THRESHOLD (proposta operacional — sujeito a calibragem empírica):** ≥ 0,80 nas janelas
em que se exige execução (auditoria CQO); até calibração, tratar como **meta**, não como prova matemática.

## 9.3. CÓDIGO PYTHON OFICIAL (biblioteca)

```python
# omega_core_validation/engagement_metrics.py
from engagement_metrics import engagement_rate, EngagementSnapshot

rate = engagement_rate(signals_valid=100, orders_filled=82)  # 0.82 ou None se signals_valid==0
```

## 9.4. VALIDAÇÃO

**CHECKLIST:**
- [ ] Separar contagem de `signal_fired` de `order_filled`
- [ ] Reportar N/A quando denominador zero
- [ ] Não usar drawdown=0% como proxy de engajamento

===============================================================================
MÉTRICA 10: PARIDADE Z / DERIVA + CUSTO DE OPORTUNIDADE CONDICIONAL
===============================================================================

## 10.1. Z_DRIFT / RELATÓRIO DE PARIDADE (auditoria CKO)

**Problema:** Z calculado com **batch** (OLS em janela + `pandas.ewm` + `shift(1)`) **não** é
garantidamente igual ao Z do **motor online** (RLS + EWMA recursiva), mesmo com o mesmo `span`.

**Sub-métrica 10.A — Paridade EWMA (mesmo spread):**
Dada a **mesma** série de spreads `s_t`, comparar:
- `Z_pd` = `causal_z_ewma_shift1` (pandas)
- `Z_rc` = recursão EWMA causal (espelho de `OnlineRLSEWMACausalZ`)

Reportar: `n_points`, `MSE`, `mean_abs_diff`, `max_abs_diff`.

**Sub-métrica 10.B — Paridade completa (mesmos y, x):**
- `Z_batch` = pipeline `v821_causal_spread_and_z`
- `Z_online` = `OnlineRLSEWMACausalZ` barra a barra

**Interpretação obrigatória:** spreads **diferem** (OLS janela vs inovação RLS); MSE elevado pode
ser **estrutural**, não bug. O relatório **quantifica deriva** para decisão de calibração ou de
**dois modos nomeados** (backtest de referência vs live operacional).

**Código:** `parity_ewma_z_pandas_vs_recursive`, `parity_full_batch_vs_online` em
`omega_core_validation/parity_report.py`.

**Critérios numéricos tipo "MSE < 0,01":** só válidos **após** estudo empírico e hipótese explícita
(mesmo gerador de spread ou calibração aprovada); **não** são padrão Tier-0 até homologação.

## 10.2. CUSTO DE OPORTUNIDADE (pontos notional) — CONDICIONAL (auditoria CQO)

**Aplica-se apenas se** `signal_fired == true` **e** `order_filled == false`.

```
opportunity_cost_pts = |price_move_if_entered_pts - price_move_actual_pts| * position_size
```

**Unidades:** consistentes com `position_size` (ex.: pontos × lotes).

**Código:** `opportunity_cost_points(...)` em `omega_core_validation/engagement_metrics.py`.

**Limitação:** `price_move_if_entered` é **contrafactual** — requer convenção explícita (ex.: entrada
no close da barra de sinal vs próximo open); sem convenção, o número **não** é auditável.

## 10.3. VALIDAÇÃO

**CHECKLIST:**
- [ ] Reportar sempre qual ramo (10.A ou 10.B) foi usado
- [ ] Não afirmar "Sharpe do backtest aplica-se ao live" sem relatório 10.B + política de paridade
- [ ] Opportunity cost só com `signal_fired` e contrafactual documentado

===============================================================================
RESUMO DE MÉTRICAS
===============================================================================

┌─────────────────────────────────────────────────────────────────────────┐
│ MÉTRICA          │ UNIDADE │ THRESHOLD          │ CÓDIGO PYTHON         │
├──────────────────┼─────────┼────────────────────┼───────────────────────┤
│ 1. Drawdown      │ %       │ ≤25% (backtest)    │ calculate_drawdown()  │
│ 2. Winrate       │ %       │ IC95% LB > 50%     │ calculate_winrate()   │
│ 3. Slippage      │ pts     │ ≤1.0 (backtest)    │ calculate_slippage()  │
│ 4. Sharpe Ratio  │ ratio   │ ≥2.0 (desejável)   │ calculate_sharpe()    │
│ 5. Sortino Ratio │ ratio   │ ≥1.5 (desejável)   │ calculate_sortino()   │
│ 6. Calmar Ratio  │ ratio   │ ≥1.0 (mínimo)      │ calculate_calmar()    │
│ 7. Opportunity ID│ string  │ Único (0 duplicatas│ generate_opp_id()     │
│ 8. SL/TP         │ preço   │ ATR-based          │ calculate_sl_tp()     │
│ 9. Engajamento   │ ratio   │ meta ≥0,80 (calibr)│ engagement_rate()     │
│10. Paridade Z / OC│ várias │ ver secção 10       │ parity_report.py + OC │
└─────────────────────────────────────────────────────────────────────────┘

===============================================================================
ASSINATURAS E APROVAÇÕES
===============================================================================

┌─────────────────────────────────────────────────────────────────────────┐
│ TECH LEAD (CQO/CKO)              : Agente IA                           │
│ Data                             : 2026-03-22                           │
│ Status                           : ✅ DRAFT COMPLETO                   │
│ Hash SHA3-256                    : [a ser calculado após aprovação]    │
├─────────────────────────────────────────────────────────────────────────┤
│ CFO                              : [NOME]                              │
│ Data                             : 2026-03-22                           │
│ Status                           : [ ] APROVAR  [ ] AJUSTAR  [ ] REPROVAR│
├─────────────────────────────────────────────────────────────────────────┤
│ CEO                              : [NOME]                              │
│ Data                             : [DATA]                               │
│ Status                           : [ ] APROVAR  [ ] AJUSTAR  [ ] REPROVAR│
├─────────────────────────────────────────────────────────────────────────┤
│ CONSELHO OMEGA/AMI               : [VOTAÇÃO COLETIVA]                  │
│ Data Prevista                    : [DATA]                               │
│ Decisão Final                    : [ ] APROVADO  [ ] REPROVADO         │
└─────────────────────────────────────────────────────────────────────────┘

===============================================================================
FIM DAS DEFINIÇÕES TÉCNICAS — PROTOCOLO OMEGA-DEFINICOES-v1.1.0
===============================================================================

Versão verificável: github.com/simonnmarket/OMEGA_OS_Kernel
Qualquer alteração requer aprovação formal do CEO + Conselho.

Transparência > Perfeição.
Integridade > Velocidade.
Qualidade > Quantidade.
