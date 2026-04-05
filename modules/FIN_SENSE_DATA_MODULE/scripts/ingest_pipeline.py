#!/usr/bin/env python3
"""
Pipeline canónico: DEMO_LOG_SWING_TRADE_*.csv → bronze.demo_log_swing_trade (PostgreSQL).

Contrato: governance/DOC-OFC-FASE2-FATIA1-PIPELINE-ZERO-LOSS-CSV-POSTGRES-20260412.md

Requisitos: pip install -e ".[ingest]" e variáveis PG* (obrigatório PGPASS).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


def _pkg_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_pkg() -> None:
    sys.path.insert(0, str(_pkg_root()))


def main() -> int:
    _ensure_pkg()
    parser = argparse.ArgumentParser(description="Ingest DEMO_LOG_SWING_TRADE CSV → PostgreSQL (bronze.demo_log_swing_trade).")
    parser.add_argument("--file", required=True, type=Path, help="Caminho para DEMO_LOG_SWING_TRADE_*.csv")
    parser.add_argument("--batch-size", type=int, default=1000, help="Linhas por COPY (default 1000)")
    parser.add_argument("--truncate", action="store_true", help="TRUNCATE tabela antes (testes / re-run limpo)")
    parser.add_argument("--log-file", type=Path, default=Path("errors.log"), help="Log de erros e eventos")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(args.log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    log = logging.getLogger("ingest_pipeline")

    if not args.file.is_file():
        log.error("Ficheiro não encontrado: %s", args.file)
        return 2

    from fin_sense_data_module.demo_log_swing_ingest import count_rows_in_csv, ingest_file_to_postgres

    try:
        n_csv = count_rows_in_csv(args.file)
        stats = ingest_file_to_postgres(
            args.file,
            batch_size=args.batch_size,
            truncate_first=args.truncate,
            logger=log,
        )
    except Exception as e:
        log.exception("Falha na ingestão: %s", e)
        return 1

    log.info("rows_csv=%s rows_inserted=%s batches=%s cpu_process_s=%.4f copy_p99_ms=%.2f", n_csv, stats.rows_inserted, stats.batches, stats.cpu_time_sec, stats.copy_flush_ms_p99)
    if stats.rows_read != n_csv:
        log.error("Contagem CSV %s != linhas lidas %s", n_csv, stats.rows_read)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
