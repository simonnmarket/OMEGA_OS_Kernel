# OMEGA Data Operating System (DOS) — `omega-dos`

**Versão:** 2.0.0 — **HARDENED**

Biblioteca Python alinhada à especificação de Conselho **`DOC-OFC-DOS-TRADING-V1.0-20260405-001`** (*DATA OPERATING SYSTEM - DOS*, documento final 05/04/2026). Hardening institucional aplicado em 06/04/2026 conforme `AUDIT-DOS-MODULE-CONSELHO-20260406-001`.

## Funcionalidades

1. **FIN-SENSE** — `run_dos_pipeline` sobre `bronze.demo_log_swing_trade` (ou `DataFrame` equivalente).
2. **DOS-TRADING V2.0** — quatro camadas de interpretação sobre ticks/barras **MT5** (CSV `mt5_data/{SYMBOL}_M1_{YEAR}.csv`), com **preços Decimal**, **custos variáveis** e **backtest sem look-ahead**.
3. **Métricas Tier-0** — `Tier0Metrics` (VaR/CVaR/RAROC/Sortino/Omega/Sharpe/Calmar) sobre séries de retornos.
4. **Backtrader (opcional)** — `omega_dos.trading.backtrader_dos.run_backtrader_mt5` com extra `[backtrader]`.

## 1. FIN-SENSE — pipeline `omega_dos.pipeline`

- **Entrada**: colunas do demo swing (`y`, `x`, `spread`, `z`, `beta`, flags, `ram_mb`, `cpu_pct`, `proc_ms`, `opp_cost`).
- **Saída**: `DosPipelineResult` com VaR/CVaR histórico, regimes, clusters e proveniência SHA-256.
- **⚠️ PnL HYPOTHETICAL**: O PnL derivado de `synthetic_positions_trades_from_swing` é **sintético** e rotulado explicitamente como `HYPOTHETICAL`. Não utilizar como PnL realizado em relatórios executivos sem validação COO/CFO.

```python
from omega_dos.pipeline import run_dos_pipeline

result = run_dos_pipeline(market=df, source="frame", notional_usd=10_000.0)
result = run_dos_pipeline(source="postgres", limit_rows=50_000)
# result.summary["pnl_type"] == "HYPOTHETICAL"
```

## 2. DOS-TRADING V2.0 — MT5 (`omega_dos.trading.dos_trading_v1`)

- **Entrada**: OHLC + `time` nos CSV por ano; directório por defeito `mt5_data/` ou `DOS_MT5_DIR`.
- **Camadas**: (1) estrutura de preço, (2) microestrutura, (3) regime vol configurável, (4) sinal composto.
- **Preços Decimal**: `TradingSignal.entry_price`, `stop_loss`, `take_profit` usam `decimal.Decimal` com precisão 28 dígitos.
- **Backtest**: Sem look-ahead (bar-a-bar SL/TP), slippage e comissão configuráveis via `BacktestConfig`.
- **Validação rígida**: CSVs malformados, NaN, inf e outliers são rejeitados automaticamente.
- **Logging JSON**: Logs estruturados com `trace_id` e masking de credenciais (var `DOS_LOG_JSON=1`).

```python
from omega_dos import DOS_TRADING_V1, BacktestConfig, VolatilityBins

# Configuração customizada
bins = VolatilityBins(low_upper=0.003, medium_upper=0.012)
bt = BacktestConfig(slippage_bps=1.0, commission_bps=2.0, notional_usd=500_000.0)
trader = DOS_TRADING_V1("mt5_data/", vol_bins=bins, backtest_config=bt)
report = trader.run_full_pipeline("XAUUSD")
# report["backtest"]["total_costs_bps"] == 3.0
```

Standalone (equivalente ao script da especificação):

```bash
mkdir mt5_data
# Copiar XAUUSD_M1_2024.csv, etc.
python dos_trading_v1.py
```

- **Logging em ficheiro**: opcional via `DOS_LOG_FILE=caminho/dos.log`.
- **Logging JSON**: `DOS_LOG_JSON=1` (default) ou `DOS_LOG_JSON=0` para texto plano.

## 3. Métricas institucionais — `Tier0Metrics`

```python
from omega_dos import Tier0Metrics
import pandas as pd

returns = pd.Series(...)  # retornos por período
m = Tier0Metrics(returns, exposure=1_000_000.0)
print(m.full_analysis())
```

## 4. Backtrader (opcional)

> ⚠️ Para séries com mais de 500k barras, considere amostrar ou particionar os dados para evitar consumo excessivo de memória.

```bash
pip install "omega-dos[backtrader]"
```

```python
from omega_dos.trading.backtrader_dos import run_backtrader_mt5
run_backtrader_mt5("mt5_data/XAUUSD_M1_2025.csv")
```

## Instalação (monorepo)

```bash
cd modules/FIN_SENSE_DATA_MODULE && pip install -e .
cd modules/DOS_MODULE && pip install -e ".[dev]"
```

Postgres opcional: `pip install -e ".[postgres]"` e `PGPASS` (mesmo contrato que `get_connection_dsn()`).

## Variáveis de ambiente

| Variável | Significado | Default |
|----------|-------------|---------|
| `DOS_PG_SCHEMA` | Schema DDL opcional | `dos` |
| `FIN_SENSE_SCHEMA_VERSION` | Referência documental FIN-SENSE | `1.2.0` |
| `DOS_MT5_DIR` | Directório de CSV MT5 | `mt5_data/` |
| `DOS_LOG_FILE` | Se definido, registo adicional em ficheiro | — |
| `DOS_LOG_JSON` | `1` = logs JSON estruturados, `0` = texto plano | `1` |

## DDL opcional

`omega_dos/sql/ddl_dos.sql` — tabela `dos.pipeline_run`.

## Testes

```bash
cd modules/DOS_MODULE && python -m pytest -q
# Resultado esperado: 10 passed
```

## Hardening aplicado (v2.0.0)

| Categoria | Item | Estado |
|-----------|------|--------|
| CRÍTICA | Decimal para preços/SL/TP | ✅ |
| CRÍTICA | Backtest sem look-ahead + custos | ✅ |
| CRÍTICA | PnL rotulado HYPOTHETICAL | ✅ |
| CRÍTICA | Segurança Postgres (retry, parametrizado) | ✅ |
| ALTA | Logging JSON + trace_id + masking | ✅ |
| ALTA | Validação rígida schema MT5 | ✅ |
| ALTA | Bins de volatilidade configuráveis | ✅ |
| MÉDIA | Digest incremental (anti-OOM) | ✅ |
| BAIXA | sklearn fallback dados constantes | ✅ |

## Limitações

- Resultados de **backtest** e **sinais** dependem dos CSV e dos parâmetros; não constituem promessa de desempenho futuro.
- Métricas históricas não substituem stress testing nem validação de negócio.
- PnL FIN-SENSE é **HYPOTHETICAL** até existir livro/posições reais.
- Backtrader: séries muito grandes (>500k) podem exigir chunking/amostragem.

## Documento para o Conselho

Ver `CONSELHO_DOS_MODULE.md`.
