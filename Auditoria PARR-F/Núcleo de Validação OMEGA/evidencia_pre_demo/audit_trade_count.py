#!/usr/bin/env python3
"""
Contagem objetiva de sinais e estatísticas de Z — relatórios ao Conselho (sem números manuais).

Uso:
  python audit_trade_count.py --csv 02_logs_execucao/STRESS_V10_5_SWING_TRADE.csv
  python audit_trade_count.py --csv "C:\\...\\DEMO_LOG_SWING_TRADE_20260331_T1200.csv"

Critérios opcionais (exit code):
  --expect-rows N       falha (exit 2) se len(df) != N
  --min-signals N       falha (exit 3) se contagem signal_fired < N
  --min-abs-z-max V     falha (exit 4) se max(|Z|) < V (cuidado: outliers)
  --min-abs-z-p95 V     falha (exit 5) se P95(|Z|) < V (recomendado para gates)

Colunas Z aceites: z_score (stress) ou z (demo). Coluna sinais: signal_fired.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def _z_series(df: pd.DataFrame) -> pd.Series:
    if "z_score" in df.columns:
        return pd.to_numeric(df["z_score"], errors="coerce")
    if "z" in df.columns:
        return pd.to_numeric(df["z"], errors="coerce")
    raise SystemExit("ERRO: coluna Z ausente (esperado z_score ou z).")


def _signal_mask(df: pd.DataFrame) -> pd.Series:
    if "signal_fired" not in df.columns:
        raise SystemExit("ERRO: coluna signal_fired ausente.")
    s = df["signal_fired"]
    if s.dtype == bool:
        return s
    return s.astype(str).str.lower().isin(("true", "1", "yes"))


def _sha3_file(p: Path) -> str:
    h = hashlib.sha3_256()
    h.update(p.read_bytes())
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Métricas objetivas: trades + Z")
    ap.add_argument("--csv", required=True, type=Path, help="Ficheiro CSV (stress ou demo)")
    ap.add_argument("--expect-rows", type=int, default=None, help="Falha se número de linhas != N")
    ap.add_argument("--min-signals", type=int, default=None, help="Falha se sinais < N")
    ap.add_argument("--min-abs-z-max", type=float, default=None, help="Falha se max(|Z|) < V")
    ap.add_argument("--min-abs-z-p95", type=float, default=None, help="Falha se P95(|Z|) < V")
    args = ap.parse_args()

    p = args.csv.resolve()
    if not p.is_file():
        print(f"ERRO: ficheiro não encontrado: {p}", file=sys.stderr)
        return 1

    df = pd.read_csv(p)
    n = len(df)
    z = _z_series(df)
    z_abs = np.abs(z.dropna())
    sig = _signal_mask(df)
    n_sig = int(sig.sum())
    z_max = float(z_abs.max()) if len(z_abs) else float("nan")
    p95 = float(np.percentile(z_abs, 95)) if len(z_abs) else float("nan")
    p50 = float(np.percentile(z_abs, 50)) if len(z_abs) else float("nan")
    p99 = float(np.percentile(z_abs, 99)) if len(z_abs) else float("nan")

    sha3 = _sha3_file(p)

    print("=== audit_trade_count.py ===")
    print(f"arquivo: {p.name}")
    print(f"sha3_256_arquivo: {sha3}")
    print(f"linhas: {n}")
    print(f"signal_fired_true: {n_sig}")
    print(f"z_coluna: {'z_score' if 'z_score' in df.columns else 'z'}")
    print(f"abs_z_max: {z_max:.6f}")
    print(f"abs_z_p50: {p50:.6f}")
    print(f"abs_z_p95: {p95:.6f}")
    print(f"abs_z_p99: {p99:.6f}")
    if not np.isnan(z_max) and z_max > 1e6:
        print(
            "aviso_outlier: abs_z_max muito elevado — possível artefacto numérico; "
            "para narrativa use P95/P99 (não max bruto)."
        )

    if args.expect_rows is not None and n != args.expect_rows:
        print(f"FALHA_CRITERIO: linhas {n} != esperado {args.expect_rows}")
        return 2
    if args.min_signals is not None and n_sig < args.min_signals:
        print(f"FALHA_CRITERIO: sinais {n_sig} < mínimo {args.min_signals}")
        return 3
    if args.min_abs_z_max is not None and (np.isnan(z_max) or z_max < args.min_abs_z_max):
        print(f"FALHA_CRITERIO: abs_z_max {z_max} < mínimo {args.min_abs_z_max}")
        return 4
    if args.min_abs_z_p95 is not None and (np.isnan(p95) or p95 < args.min_abs_z_p95):
        print(f"FALHA_CRITERIO: abs_z_p95 {p95} < mínimo {args.min_abs_z_p95}")
        return 5

    print("criterios_opcionais: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
