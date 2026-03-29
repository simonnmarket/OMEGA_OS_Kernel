#!/usr/bin/env python3
"""
Gera evidências numéricas a partir de live_feed/*.csv + manifest + confronto com proxy Yahoo.
Escreve: data_lake_metrics.json (ao lado deste script).
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / "live_feed"
OUT_JSON = ROOT / "data_lake_metrics.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_mt5_literal_csv(path: Path) -> pd.DataFrame:
    """Formato observado: linhas com tuplos string '(time, o,h,l,c, ...)'"""
    rows = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or line == "0":
                continue
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            if not line.startswith("("):
                continue
            try:
                t = ast.literal_eval(line)
            except (SyntaxError, ValueError):
                continue
            if len(t) >= 5:
                rows.append({"time": int(t[0]), "open": float(t[1]), "high": float(t[2]), "low": float(t[3]), "close": float(t[4])})
    return pd.DataFrame(rows).sort_values("time").reset_index(drop=True)


def rolling_spread_ols(Y: np.ndarray, X: np.ndarray, window: int) -> np.ndarray:
    """S_t = Y_t - a_t - b_t X_t com OLS só em [t-window, t-1]."""
    n = len(Y)
    spreads = np.full(n - window, np.nan)
    Xd = np.column_stack([np.ones(window), np.zeros(window)])
    for i in range(window, n):
        wy = Y[i - window : i]
        wx = X[i - window : i]
        Xd[:, 1] = wx
        beta, _, _, _ = np.linalg.lstsq(Xd, wy, rcond=None)
        spreads[i - window] = Y[i] - beta[0] - beta[1] * X[i]
    return spreads


def main() -> int:
    fx = LIVE / "XAUUSD_MADRUGADA_M1.csv"
    fa = LIVE / "XAGUSD_MADRUGADA_M1.csv"
    if not fx.is_file() or not fa.is_file():
        print("Ficheiros M1 em falta em live_feed/", file=sys.stderr)
        return 1

    dfy = parse_mt5_literal_csv(fx)
    dfx = parse_mt5_literal_csv(fa)
    m = pd.merge(dfy, dfx, on="time", suffixes=("_y", "_x"), how="inner")
    Y = m["close_y"].values.astype(float)
    X = m["close_x"].values.astype(float)
    n = len(m)

    # --- Engle-Granger: Y ~ const + X (níveis)
    Xsm = sm.add_constant(X)
    ols_eg = sm.OLS(Y, Xsm).fit()
    resid_eg = Y - ols_eg.predict(Xsm)
    adf_eg = adfuller(resid_eg, autolag="AIC")

    # Janelas padrão V8.2.x; se amostra < 610 barras, usar janelas adaptativas (documentar no relatório).
    window_ols = 500
    ewma_span = 100
    if n < 610:
        window_ols = max(80, min(200, n // 3))
        ewma_span = max(30, min(60, window_ols // 4))
    if n <= window_ols + ewma_span + 10:
        print("Amostra curta demais para OLS rolante", n, window_ols, ewma_span, file=sys.stderr)
        return 1

    spreads = rolling_spread_ols(Y, X, window_ols)
    s_ser = pd.Series(spreads)
    ewm = s_ser.ewm(span=ewma_span, adjust=False)
    mu_t1 = ewm.mean().iloc[-2]
    std_t1 = ewm.std().iloc[-2]
    z_last = (s_ser.iloc[-1] - mu_t1) / (std_t1 + 1e-12)

    adf_roll = adfuller(s_ser.values, autolag="AIC")

    # Johansen trace (2D) — replicar teste simples com statsmodels
    j_err = None
    try:
        from statsmodels.tsa.vector_ar.vecm import coint_johansen

        # Johansen espera matriz (nobs, neqs); níveis
        data_j = np.column_stack([Y, X])
        jres = coint_johansen(data_j, det_order=0, k_ar_diff=1)
        j_trace_0 = float(jres.lr1[0])
        j_crit_95 = float(jres.cvt[0, 1])
        johansen_ok = j_trace_0 > j_crit_95
    except Exception as e:
        j_trace_0 = j_crit_95 = None
        johansen_ok = None
        j_err = str(e)

    manifest_path = ROOT / "data_manifest_v82.json"
    manifest = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    johansen_file = ROOT / "johansen_m1_results.json"
    johansen_file_content = {}
    if johansen_file.is_file():
        johansen_file_content = json.loads(johansen_file.read_text(encoding="utf-8"))

    out = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_files": {
            "XAUUSD": {"path": str(fx), "sha256": sha256_file(fx), "rows_parsed": len(dfy)},
            "XAGUSD": {"path": str(fa), "sha256": sha256_file(fa), "rows_parsed": len(dfx)},
        },
        "merge_inner_on_time": {
            "rows": int(n),
            "time_first": int(m["time"].iloc[0]),
            "time_last": int(m["time"].iloc[-1]),
            "pct_aligned": float(n / min(len(dfy), len(dfx))) if len(dfy) and len(dfx) else None,
        },
        "engle_granger_levels_full_sample": {
            "alpha": float(ols_eg.params[0]),
            "beta": float(ols_eg.params[1]),
            "adf_statistic": float(adf_eg[0]),
            "pvalue": float(adf_eg[1]),
            "nobs": int(adf_eg[3]),
        },
        "rolling_ols_spread_motor_v821": {
            "window_ols_effective": window_ols,
            "ewma_span_effective": ewma_span,
            "note_if_adaptive": n < 610,
            "spread_series_len": len(s_ser),
            "adf_on_full_spread_series": {
                "adf_statistic": float(adf_roll[0]),
                "pvalue": float(adf_roll[1]),
                "nobs": int(adf_roll[3]),
            },
            "last_bar_z_causal_style": float(z_last),
        },
        "johansen_recomputed_statsmodels": {
            "trace_statistic_r0": j_trace_0,
            "crit_95_r0": j_crit_95,
            "reject_r0_cointegration_95": johansen_ok,
            "error": j_err if johansen_ok is None else None,
        },
        "files_crosscheck": {
            "data_manifest_v82": manifest,
            "johansen_m1_results_json": johansen_file_content,
        },
    }

    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "ok", "out": str(OUT_JSON), "n": n}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
