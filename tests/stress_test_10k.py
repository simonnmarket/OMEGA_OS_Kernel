"""
Stress: gera 10k linhas sintéticas DEMO_LOG_SWING_TRADE, valida SHA3 e opcionalmente ingere no Postgres.

Requer: pip install -e modules/FIN_SENSE_DATA_MODULE/[ingest]
Ambiente: PGPASS + PG* para ingestão real; sem isso apenas valida integridade local.
"""

from __future__ import annotations

import csv
import os
import sys
import tempfile
from pathlib import Path

# repo root = parents[1] of tests/stress_test_10k.py
ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "modules" / "FIN_SENSE_DATA_MODULE"
sys.path.insert(0, str(PKG))


_FIELD_ORDER = (
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


def _make_row(i: int) -> dict[str, str]:
    ts = f"2026-04-01T{12 + (i // 60):02d}:{i % 60:02d}:00"
    base = {
        "ts": ts,
        "y": str(4600.0 + (i % 100) * 0.01),
        "x": str(75.0 + (i % 10) * 0.001),
        "spread": str(-40.0 + (i % 5)),
        "z": str((i % 20) * 0.01 - 0.1),
        "beta": str(43.3 + (i % 7) * 0.001),
        "signal_fired": "False",
        "order_filled": "False",
        "ram_mb": str(70.0 + (i % 5)),
        "cpu_pct": str(10.0 + (i % 8)),
        "proc_ms": str(0.5 + (i % 3) * 0.1),
        "opp_cost": "0.00",
    }
    from fin_sense_data_module.demo_log_swing_ingest import canonical_sha3_hex

    fn = list(_FIELD_ORDER) + ["sha3_256"]
    row = dict(base)
    row["sha3_256"] = canonical_sha3_hex(row, fn)
    return row


def main() -> int:
    from fin_sense_data_module.demo_log_swing_ingest import canonical_sha3_hex, verify_row_sha3

    n = 10_000
    fieldnames = list(_FIELD_ORDER) + ["sha3_256"]

    rows = [_make_row(i) for i in range(n)]
    for i, row in enumerate(rows):
        ok, _, _ = verify_row_sha3(row, fieldnames)
        if not ok:
            print(f"FAIL sha3 linha {i}")
            return 1

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as tf:
        w = csv.DictWriter(tf, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)
        path = Path(tf.name)

    print(f"OK: {n} linhas sintéticas com SHA3 válido -> {path}")

    if os.getenv("PGPASS") or os.getenv("PGPASSWORD"):
        from fin_sense_data_module.demo_log_swing_ingest import get_connection_dsn, ingest_file_to_postgres
        import psycopg

        ingest_file_to_postgres(path, batch_size=1000, truncate_first=True)
        dsn = get_connection_dsn()
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM bronze.demo_log_swing_trade")
                c = cur.fetchone()[0]
        print(f"OK: COUNT(DB)={c} (esperado {n})")
        if c != n:
            return 1
        path.unlink(missing_ok=True)
    else:
        print("SKIP DB: defina PGPASS para teste de ingestão completo.")
        path.unlink(missing_ok=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
