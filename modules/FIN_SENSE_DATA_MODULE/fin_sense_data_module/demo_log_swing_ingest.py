"""Regras canónicas para DEMO_LOG_SWING_TRADE_*.csv — SHA3-256 por linha (Fase 2 Fatia 1)."""

from __future__ import annotations

import csv
import hashlib
import io
import logging
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, List, Mapping, Optional, Sequence, Tuple


def canonical_sha3_hex(row: Mapping[str, str], fieldnames: Sequence[str]) -> str:
    """SHA3-256 do mesmo formato que o gerador do CSV: valores separados por vírgula, ordem das colunas de dados."""
    cols = [c for c in fieldnames if c != "sha3_256"]
    s = ",".join(str(row[c]) for c in cols)
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()


def verify_row_sha3(row: Mapping[str, str], fieldnames: Sequence[str]) -> Tuple[bool, str, str]:
    """Devolve (ok, esperado, calculado)."""
    expected = row.get("sha3_256", "").strip()
    got = canonical_sha3_hex(row, fieldnames)
    return (got == expected, expected, got)


def iter_demo_rows(path: Path) -> Tuple[List[str], Iterator[dict[str, str]]]:
    f = path.open(newline="", encoding="utf-8")
    reader = csv.DictReader(f)

    def _gen() -> Iterator[dict[str, str]]:
        try:
            for row in reader:
                yield {k: (v if v is not None else "") for k, v in row.items()}
        finally:
            f.close()

    return list(reader.fieldnames or []), _gen()


@dataclass
class IngestStats:
    rows_read: int = 0
    rows_inserted: int = 0
    batches: int = 0
    cpu_time_sec: float = 0.0
    copy_flush_ms_p99: float = 0.0


def row_to_db_tuple(
    row: Mapping[str, str],
    *,
    source_file: str,
    ingestion_id: str,
) -> Tuple[str, ...]:
    """Valores como texto para COPY CSV (compatível com Postgres)."""
    return (
        row["ts"].strip(),
        row["y"].strip(),
        row["x"].strip(),
        row["spread"].strip(),
        row["z"].strip(),
        row["beta"].strip(),
        row["signal_fired"].strip(),
        row["order_filled"].strip(),
        row["ram_mb"].strip(),
        row["cpu_pct"].strip(),
        row["proc_ms"].strip(),
        row["opp_cost"].strip(),
        row["sha3_256"].strip(),
        source_file,
        ingestion_id,
    )


DDL_BRONZE_DEMO_LOG = """
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE TABLE IF NOT EXISTS bronze.demo_log_swing_trade (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ NOT NULL,
  y DOUBLE PRECISION NOT NULL,
  x DOUBLE PRECISION NOT NULL,
  spread DOUBLE PRECISION NOT NULL,
  z DOUBLE PRECISION NOT NULL,
  beta DOUBLE PRECISION NOT NULL,
  signal_fired BOOLEAN NOT NULL,
  order_filled BOOLEAN NOT NULL,
  ram_mb DOUBLE PRECISION,
  cpu_pct DOUBLE PRECISION,
  proc_ms DOUBLE PRECISION,
  opp_cost DOUBLE PRECISION,
  sha3_line TEXT NOT NULL,
  source_file TEXT NOT NULL,
  ingestion_id TEXT NOT NULL,
  ingest_ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_demo_log_swing_ingest ON bronze.demo_log_swing_trade (ingestion_id);
"""

COPY_COLUMNS = (
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
    "sha3_line",
    "source_file",
    "ingestion_id",
)


def get_connection_dsn() -> str:
    """Monta DSN a partir de variáveis de ambiente (A5: PGPASS)."""
    password = os.getenv("PGPASS") or os.getenv("PGPASSWORD") or ""
    if not password:
        raise RuntimeError("PGPASS ou PGPASSWORD deve estar definido (segurança A5).")
    host = os.getenv("PGHOST", "127.0.0.1")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER", "postgres")
    db = os.getenv("PGDATABASE", "postgres")
    return f"host={host} port={port} dbname={db} user={user} password={password}"


def ingest_file_to_postgres(
    csv_path: Path,
    *,
    batch_size: int = 1000,
    ensure_schema: bool = True,
    truncate_first: bool = False,
    logger: Optional[logging.Logger] = None,
    conn_factory: Optional[Callable[[str], Any]] = None,
) -> IngestStats:
    """
    Ingere CSV DEMO_LOG_SWING_TRADE para bronze.demo_log_swing_trade com COPY em lotes.
    Valida SHA3 por linha antes de inserir.
    """
    log = logger or logging.getLogger(__name__)
    try:
        import psycopg
    except ImportError as e:
        raise RuntimeError("Instale dependências: pip install 'psycopg[binary]>=3.1'") from e

    dsn = get_connection_dsn()
    connect = conn_factory or (lambda d: psycopg.connect(d, connect_timeout=30))

    stats = IngestStats()
    ingestion_id = str(uuid.uuid4())
    source_file = str(csv_path.resolve())
    fieldnames, row_iter = iter_demo_rows(csv_path)
    if not fieldnames or "sha3_256" not in fieldnames:
        raise ValueError("CSV inválido: cabeçalho esperado com sha3_256")

    flush_times: List[float] = []
    t_cpu0 = time.process_time()

    with connect(dsn) as conn:
        conn.autocommit = False
        with conn.cursor() as cur:
            if ensure_schema:
                cur.execute(DDL_BRONZE_DEMO_LOG)
                conn.commit()
            if truncate_first:
                cur.execute("TRUNCATE bronze.demo_log_swing_trade RESTART IDENTITY CASCADE")
                conn.commit()

        batch: List[Tuple[str, ...]] = []
        for row in row_iter:
            stats.rows_read += 1
            ok, _, got = verify_row_sha3(row, fieldnames)
            if not ok:
                log.error("sha3 mismatch linha %s esperado=%s calculado=%s", stats.rows_read, row.get("sha3_256"), got)
                raise ValueError(f"Integridade SHA3 falhou na linha {stats.rows_read}")
            batch.append(row_to_db_tuple(row, source_file=source_file, ingestion_id=ingestion_id))
            if len(batch) >= batch_size:
                t0 = time.perf_counter()
                _copy_batch(conn, batch)
                flush_times.append((time.perf_counter() - t0) * 1000.0)
                stats.batches += 1
                stats.rows_inserted += len(batch)
                batch.clear()
        if batch:
            t0 = time.perf_counter()
            _copy_batch(conn, batch)
            flush_times.append((time.perf_counter() - t0) * 1000.0)
            stats.batches += 1
            stats.rows_inserted += len(batch)

    stats.cpu_time_sec = time.process_time() - t_cpu0
    if flush_times:
        sorted_f = sorted(flush_times)
        stats.copy_flush_ms_p99 = sorted_f[int(0.99 * (len(sorted_f) - 1))]
    return stats


def _copy_batch(conn: Any, batch: List[Tuple[str, ...]]) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    for tup in batch:
        w.writerow(tup)
    data = buf.getvalue()
    cols = ",".join(COPY_COLUMNS)
    copy_stmt = f"COPY bronze.demo_log_swing_trade ({cols}) FROM STDIN WITH (FORMAT csv)"
    with conn.cursor() as cur:
        with cur.copy(copy_stmt) as copy:
            copy.write(data)
    conn.commit()


def count_rows_in_csv(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        return sum(1 for _ in f) - 1
