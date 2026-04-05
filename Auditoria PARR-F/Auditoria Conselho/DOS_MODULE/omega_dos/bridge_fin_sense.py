"""
Ponte de dados FIN-SENSE ↔ DOS.

Lê `bronze.demo_log_swing_trade` quando Postgres disponível (mesmo DSN que
`fin_sense_data_module.demo_log_swing_ingest.get_connection_dsn`), ou aceita
DataFrames já materializados (testes / notebooks).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import time

import pandas as pd


REQUIRED_SWING_COLS = (
    "ts",
    "y",
    "x",
    "spread",
    "z",
    "beta",
    "signal_fired",
    "order_filled",
    "ram_mb",
    "cpu_pct",
    "proc_ms",
    "opp_cost",
)


@dataclass
class FinSenseSwingBundle:
    """Pacote mínimo para o pipeline DOS a partir do demo swing."""

    market: pd.DataFrame
    ingestion_ids: list[str]
    source: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.market.empty:
            errors.append("market: DataFrame vazio")
            return errors
        for c in REQUIRED_SWING_COLS:
            if c not in self.market.columns:
                errors.append(f"market: coluna em falta: {c}")
        return errors


def swing_bronze_to_market_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza tipos numéricos a partir da tabela bronze (nomes alinhados ao CSV demo)."""
    out = df.copy()
    if "ts" in out.columns:
        out["ts"] = pd.to_datetime(out["ts"], utc=True, errors="coerce")
    num_cols = ["y", "x", "spread", "z", "beta", "ram_mb", "cpu_pct", "proc_ms", "opp_cost"]
    for c in num_cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in ("signal_fired", "order_filled"):
        if c in out.columns:
            out[c] = out[c].astype(str).str.lower().isin(("true", "1", "t"))
    return out.sort_values("ts").reset_index(drop=True)


def load_demo_swing_from_postgres(
    *,
    limit_rows: Optional[int] = None,
    ingestion_id: Optional[str] = None,
) -> FinSenseSwingBundle:
    """Carrega linhas de bronze.demo_log_swing_trade via psycopg (opcional [postgres])."""
    try:
        import psycopg
    except ImportError as e:
        raise RuntimeError("Instale: pip install 'omega-dos[postgres]' e psycopg") from e

    from fin_sense_data_module.demo_log_swing_ingest import get_connection_dsn

    dsn = get_connection_dsn()
    sql = """
        SELECT ts, y, x, spread, z, beta, signal_fired, order_filled,
               ram_mb, cpu_pct, proc_ms, opp_cost,
               sha3_line, source_file, ingestion_id, ingest_ts
        FROM bronze.demo_log_swing_trade
    """
    params: list[Any] = []
    if ingestion_id:
        sql += " WHERE ingestion_id = %s"
        params.append(ingestion_id)
    sql += " ORDER BY ts ASC"
    if limit_rows is not None:
        sql += " LIMIT %s"
        params.append(int(limit_rows))

    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with psycopg.connect(dsn, connect_timeout=10) as conn:
                df = pd.read_sql_query(sql, conn, params=params if params else None)
            break
        except Exception as e:  # pragma: no cover - só em runtime Postgres
            last_err = e
            if attempt == 2:
                raise
            time.sleep(1.5 * (2**attempt))
    else:
        if last_err:
            raise last_err

    if df.empty:
        return FinSenseSwingBundle(market=df, ingestion_ids=[], source="postgres:empty")

    df = swing_bronze_to_market_frame(df)
    ids = sorted(df["ingestion_id"].dropna().astype(str).unique().tolist()) if "ingestion_id" in df.columns else []
    return FinSenseSwingBundle(market=df, ingestion_ids=ids, source="postgres:bronze.demo_log_swing_trade")


def synthetic_positions_trades_from_swing(
    market: pd.DataFrame,
    *,
    portfolio_id: str = "DEFAULT",
    symbol: str = "SYNTH",
    notional_usd: float = 10_000.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Deriva posições e trades sintéticos determinísticos a partir do preço `y`.

    Convénção explícita: PnL por passo = retorno simples * notional em USD (auditoria).
    Não substitui livro de ordens real — apenas encadeia métricas quando só existe o demo swing.
    """
    if market.empty or "y" not in market.columns:
        return pd.DataFrame(), pd.DataFrame()

    y = market["y"].astype(float)
    r = y.pct_change().fillna(0.0)
    qty = pd.Series(1.0, index=market.index)
    pnl_step = notional_usd * r
    cum_pnl = pnl_step.cumsum()

    positions = pd.DataFrame(
        {
            "portfolio_id": portfolio_id,
            "symbol": symbol,
            "ts": market["ts"] if "ts" in market.columns else pd.RangeIndex(len(market)),
            "qty": qty,
            "notional_usd": notional_usd,
            "mark_price": y,
            "unrealized_pnl_usd": cum_pnl,
            "currency": "USD",
        }
    )

    trades = pd.DataFrame(
        {
            "order_id": market.index.map(lambda i: f"ORD-{i}"),
            "exec_id": market.index.map(lambda i: f"EX-{i}"),
            "fill_price": y,
            "size": qty,
            "pnl_step_usd": pnl_step,
            "side": (r >= 0).map({True: "BUY", False: "SELL"}),
        }
    )
    return positions, trades
