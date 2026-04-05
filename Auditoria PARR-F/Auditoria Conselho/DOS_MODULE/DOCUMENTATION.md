# OMEGA Data Operating System (DOS) — `omega-dos`

**Versão:** 1.1.0  

Biblioteca Python alinhada à especificação de Conselho **`DOC-OFC-DOS-TRADING-V1.0-20260405-001`** (*DATA OPERATING SYSTEM - DOS*, documento final 05/04/2026). Inclui:

1. **FIN-SENSE** — `run_dos_pipeline` sobre `bronze.demo_log_swing_trade` (ou `DataFrame` equivalente).
2. **DOS-TRADING V1.0** — quatro camadas de interpretação sobre ticks/barras **MT5** (CSV `mt5_data/{SYMBOL}_M1_{YEAR}.csv`).
3. **Métricas Tier-0** — `Tier0Metrics` (VaR/CVaR/RAROC/Sortino/Omega/Sharpe/Calmar) sobre séries de retornos.
4. **Backtrader (opcional)** — `omega_dos.trading.backtrader_dos.run_backtrader_mt5` com extra `[backtrader]`.

## 1. FIN-SENSE — pipeline `omega_dos.pipeline`

- **Entrada**: colunas do demo swing (`y`, `x`, `spread`, `z`, `beta`, flags, `ram_mb`, `cpu_pct`, `proc_ms`, `opp_cost`) alinhadas ao CSV/ingest FIN-SENSE.
- **Saída**: `DosPipelineResult` com VaR/CVaR histórico, regimes, clusters e proveniência SHA-256.
- **Nota**: o PnL derivado de `synthetic_positions_trades_from_swing` é **sintético** até existir livro/posições reais.

```python
from omega_dos.pipeline import run_dos_pipeline

result = run_dos_pipeline(market=df, source="frame", notional_usd=10_000.0)
result = run_dos_pipeline(source="postgres", limit_rows=50_000)
```

## 2. DOS-TRADING V1.0 — MT5 (`omega_dos.trading.dos_trading_v1`)

- **Entrada**: OHLC + `time` nos CSV por ano; directório por defeito `mt5_data/` ou `DOS_MT5_DIR`.
- **Camadas**: (1) estrutura de preço, (2) microestrutura, (3) regime vol + trend/range/breakout, (4) sinal composto; depois sinais, diagnóstico de falsos negativos e backtest simplificado.
- **Execução standalone** (equivalente ao script da especificação):

```bash
mkdir mt5_data
# Copiar XAUUSD_M1_2024.csv, etc.
python dos_trading_v1.py
```

Ou em código:

```python
from omega_dos import DOS_TRADING_V1

trader = DOS_TRADING_V1("mt5_data/")
report = trader.run_full_pipeline("XAUUSD")
```

- **Logging em ficheiro**: opcional via `DOS_LOG_FILE=caminho/dos.log`.

## 3. Métricas institucionais — `Tier0Metrics`

```python
from omega_dos import Tier0Metrics
import pandas as pd

returns = pd.Series(...)  # retornos por período
m = Tier0Metrics(returns, exposure=1_000_000.0)
print(m.full_analysis())
```

## 4. Backtrader (opcional)

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

| Variável | Significado |
|----------|-------------|
| `DOS_PG_SCHEMA` | Schema DDL opcional (default `dos`). |
| `FIN_SENSE_SCHEMA_VERSION` | Referência documental FIN-SENSE (ver `omega_dos.config`). |
| `DOS_MT5_DIR` | Directório de CSV MT5 para o wrapper `main()` de `dos_trading_v1`. |
| `DOS_LOG_FILE` | Se definido, registo adicional em ficheiro. |

## DDL opcional

`omega_dos/sql/ddl_dos.sql` — tabela `dos.pipeline_run`.

## Testes

```bash
cd modules/DOS_MODULE && python -m pytest -q
```

## Limitações

- Resultados de **backtest** e **sinais** no DOS-TRADING dependem dos CSV e dos parâmetros fixados; não constituem promessa de desempenho futuro.
- Métricas históricas não substituem stress testing nem validação de negócio.
- Digest de inputs em séries muito grandes pode exigir estratégia de *chunking* em evoluções futuras.

## Documento para o Conselho

Ver `CONSELHO_DOS_MODULE.md`.
