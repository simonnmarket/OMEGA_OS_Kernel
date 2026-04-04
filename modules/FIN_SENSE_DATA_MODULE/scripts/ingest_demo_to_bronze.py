"""
Demo: grava Bronze (TBL_MARKET_TICKS_RAW) em FIN_SENSE_DATA/hub (raiz do workspace).
Uso: python scripts/ingest_demo_to_bronze.py [caminho.csv opcional]
"""

from __future__ import annotations

import csv
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

# nebular-kuiper/modules/FIN_SENSE_DATA_MODULE/scripts -> parents[2] = modules, [3] = nebular-kuiper
def _nebular_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _pkg_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_pkg() -> None:
    sys.path.insert(0, str(_pkg_root()))


def main() -> int:
    _ensure_pkg()
    from fin_sense_data_module.core_ingestor import ingest_row_validated
    from fin_sense_data_module.storage.storage_interface import FinSenseStorage

    nebular = _nebular_root()
    hub = nebular / "FIN_SENSE_DATA" / "hub"
    hub.mkdir(parents=True, exist_ok=True)
    store = FinSenseStorage(hub, layer="bronze")
    demo_csv = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    file_hash = hashlib.sha256(b"demo_seed").hexdigest()

    rows = []
    if demo_csv and demo_csv.is_file():
        with demo_csv.open(newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for line in r:
                rows.append(dict(line))
    else:
        ts = datetime.now(timezone.utc).isoformat()
        row = {
            "symbol": "XAUUSD",
            "exchange": "MT5",
            "figi": "BBG000B9XRY7",
            "isin": "US8807791022",
            "timestamp_utc": ts,
            "seq_no": 1,
            "bid": 2650.0,
            "ask": 2650.1,
            "recv_ts": ts,
        }
        ingest_row_validated(
            "TBL_MARKET_TICKS_RAW",
            row,
            source="DEMO",
            operator="ingest_demo",
            file_hash=file_hash,
        )
        rows = [row]

    ref_ts = datetime.now(timezone.utc)
    out = store.write_json_batch(
        "TBL_MARKET_TICKS_RAW",
        rows,
        ref_time=ref_ts,
        symbol=rows[0].get("symbol", "GLOBAL"),
        batch_id="demo_ingest",
    )
    store.write_manifest(
        {
            "table": "TBL_MARKET_TICKS_RAW",
            "rows": len(rows),
            "output": str(out),
            "file_hash": file_hash,
            "hub_root": str(hub),
        },
        manifest_name=f"demo_{int(ref_ts.timestamp())}.json",
    )
    print(f"OK: wrote {len(rows)} rows -> {out}")
    print(f"HUB_ROOT={hub}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
