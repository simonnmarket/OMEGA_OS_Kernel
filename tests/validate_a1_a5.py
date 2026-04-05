"""
Validação A1–A5 (relatório textual para DOC-TESTES-FASE2-FATIA1.md).

Sem Postgres: executa apenas verificações locais (A2 integridade SHA3 em amostra).
Com PGPASS: tenta A1 (COUNT) após definir RUN_INGEST=1 e ficheiro CSV.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "modules" / "FIN_SENSE_DATA_MODULE"
sys.path.insert(0, str(PKG))


def main() -> int:
    from fin_sense_data_module.demo_log_swing_ingest import count_rows_in_csv, verify_row_sha3
    import csv

    print("=== VALIDAÇÃO A1–A5 (Fase 2 Fatia 1) ===\n")
    csv_path = os.getenv("VALIDATE_CSV")
    if not csv_path:
        demo = ROOT / "Auditoria PARR-F" / "omega_core_validation" / "evidencia_demo_20260401" / "DEMO_LOG_SWING_TRADE_20260401_T0046.csv"
        if demo.is_file():
            csv_path = str(demo)
        else:
            print("A1: SKIP (defina VALIDATE_CSV=... ou coloque demo CSV)")
            return 0

    p = Path(csv_path)
    n = count_rows_in_csv(p)
    print(f"A1 (zero-loss): linhas CSV = {n} (comparar com SELECT COUNT após ingestão)")
    bad = 0
    with p.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        fn = list(r.fieldnames or [])
        for i, row in enumerate(r):
            ok, exp, got = verify_row_sha3(dict(row), fn)
            if not ok:
                print(f"A2 FAIL linha {i+2} exp={exp[:16]} got={got[:16]}")
                bad += 1
                if bad > 5:
                    break
    if bad == 0:
        print(f"A2 (reprodutibilidade SHA3): OK em todas as {n} linhas (amostra completa)")
    else:
        print("A2: FALHA")
        return 1

    print("A3 (latência batch): medir com ingest_pipeline.py + time.process_time no log")
    print("A4 (observabilidade): ver errors.log após ingestão")
    has_pass = bool(os.getenv("PGPASS") or os.getenv("PGPASSWORD"))
    print(f"A5 (PGPASS definido): {'OK' if has_pass else 'SKIP — defina PGPASS'}")

    if has_pass and os.getenv("RUN_DB_COUNT") == "1":
        import psycopg
        from fin_sense_data_module.demo_log_swing_ingest import get_connection_dsn

        with psycopg.connect(get_connection_dsn()) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM bronze.demo_log_swing_trade")
                c = cur.fetchone()[0]
        print(f"A1 DB: COUNT(*) = {c} (CSV={n}) match={c == n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
