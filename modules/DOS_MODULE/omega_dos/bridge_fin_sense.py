"""
Ponte de dados FIN-SENSE ↔ DOS (HARDENED).

Lê `bronze.demo_log_swing_trade` quando Postgres disponível (mesmo DSN que
`fin_sense_data_module.demo_log_swing_ingest.get_connection_dsn`), ou aceita
DataFrames já materializados (testes / notebooks).

HARDENING: retry com backoff exponencial + telemetria, SQL 100% parametrizado,
           PnL sintético rotulado explicitamente como HYPOTHETICAL.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_SWING_COLS = (
    "ts", "y", "x", "spread", "z", "beta",
    "signal_fired", "order_filled",
    "ram_mb", "cpu_pct", "proc_ms", "opp_cost",
)

# ---------------------------------------------------------------------------
# PnL HYPOTHETICAL LABEL — compliance BlackRock/Goldman
# ---------------------------------------------------------------------------
PNL_DISCLAIMER = (
    "HYPOTHETICAL: Este PnL é derivado sinteticamente a partir do preço 'y' "
    "e NÃO representa resultado realizado. Não utilizar em relatórios "
    "executivos como PnL de livro real sem validação do COO/CFO."
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
    """Normaliza tipos numéricos a partir da tabela bronze."""
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


def _connect_with_retry(
    dsn: str,
    *,
    max_retries: int = 3,
    base_delay: float = 1.5,
    connect_timeout: int = 10,
) -> Any:
    """Conexão Postgres com retry exponencial e telemetria de falha."""
    import psycopg

    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            conn = psycopg.connect(dsn, connect_timeout=connect_timeout)
            if attempt > 0:
                logger.info(
                    "Postgres: conexão restabelecida após %d tentativa(s)",
                    attempt + 1,
                )
            return conn
        except Exception as e:
            last_err = e
            delay = base_delay * (2 ** attempt)
            logger.warning(
                "Postgres: tentativa %d/%d falhou (%s); retry em %.1fs",
                attempt + 1, max_retries, type(e).__name__, delay,
            )
            if attempt < max_retries - 1:
                time.sleep(delay)

    raise RuntimeError(
        f"Postgres: falha após {max_retries} tentativas"
    ) from last_err


def load_demo_swing_from_postgres(
    *,
    limit_rows: Optional[int] = None,
    ingestion_id: Optional[str] = None,
    max_retries: int = 3,
) -> FinSenseSwingBundle:
    """Carrega linhas de bronze.demo_log_swing_trade via psycopg.

    SQL 100% parametrizado (sem concatenação de strings para valores).
    Retry com backoff exponencial configurável.
    """
    try:
        import psycopg  # noqa: F401
    except ImportError as e:
        raise RuntimeError("Instale: pip install 'omega-dos[postgres]' e psycopg") from e

    from fin_sense_data_module.demo_log_swing_ingest import get_connection_dsn

    dsn = get_connection_dsn()

    # SQL parametrizado — sem concatenação de strings para valores
    base_sql = """
        SELECT ts, y, x, spread, z, beta, signal_fired, order_filled,
               ram_mb, cpu_pct, proc_ms, opp_cost,
               sha3_line, source_file, ingestion_id, ingest_ts
        FROM bronze.demo_log_swing_trade
    """
    conditions: list[str] = []
    params: list[Any] = []

    if ingestion_id:
        conditions.append("ingestion_id = %s")
        params.append(ingestion_id)

    sql = base_sql
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY ts ASC"

    if limit_rows is not None:
        sql += " LIMIT %s"
        params.append(int(limit_rows))

    conn = _connect_with_retry(dsn, max_retries=max_retries)
    try:
        df = pd.read_sql_query(sql, conn, params=params if params else None)
    finally:
        conn.close()

    if df.empty:
        return FinSenseSwingBundle(market=df, ingestion_ids=[], source="postgres:empty")

    df = swing_bronze_to_market_frame(df)
    ids = (
        sorted(df["ingestion_id"].dropna().astype(str).unique().tolist())
        if "ingestion_id" in df.columns
        else []
    )
    return FinSenseSwingBundle(
        market=df, ingestion_ids=ids,
        source="postgres:bronze.demo_log_swing_trade",
    )


def synthetic_positions_trades_from_swing(
    market: pd.DataFrame,
    *,
    portfolio_id: str = "DEFAULT",
    symbol: str = "SYNTH",
    notional_usd: float = 10_000.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Deriva posições e trades sintéticos determinísticos a partir do preço `y`.

    ⚠️  HYPOTHETICAL PnL — NÃO é resultado realizado.
    Convénção explícita: PnL por passo = retorno simples * notional em USD.
    Não substitui livro de ordens real.
    """
    if market.empty or "y" not in market.columns:
        return pd.DataFrame(), pd.DataFrame()

    y = market["y"].astype(float)
    r = y.pct_change().fillna(0.0)
    qty = pd.Series(1.0, index=market.index)
    pnl_step = notional_usd * r
    cum_pnl = pnl_step.cumsum()

    positions = pd.DataFrame({
        "portfolio_id": portfolio_id,
        "symbol": symbol,
        "ts": market["ts"] if "ts" in market.columns else pd.RangeIndex(len(market)),
        "qty": qty,
        "notional_usd": notional_usd,
        "mark_price": y,
        "unrealized_pnl_usd": cum_pnl,
        "currency": "USD",
        "pnl_type": "HYPOTHETICAL",  # ← ROTULADO EXPLICITAMENTE
        "disclaimer": PNL_DISCLAIMER,
    })

    trades = pd.DataFrame({
        "order_id": market.index.map(lambda i: f"ORD-{i}"),
        "exec_id": market.index.map(lambda i: f"EX-{i}"),
        "fill_price": y,
        "size": qty,
        "pnl_step_usd": pnl_step,
        "side": (r >= 0).map({True: "BUY", False: "SELL"}),
        "pnl_type": "HYPOTHETICAL",  # ← ROTULADO EXPLICITAMENTE
    })

    logger.info(
        "PnL HYPOTHETICAL gerado: %d posições, %d trades | %s",
        len(positions), len(trades), PNL_DISCLAIMER[:60],
    )
    return positions, trades
