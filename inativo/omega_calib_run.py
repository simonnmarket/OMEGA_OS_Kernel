"""
omega_calib_run.py — Calibração COMPLETA — Todos os Ativos/TFs
Versão FINAL: session_filter bypass para H1/H4/D1, load_csv com datetime auto
"""
import sys, json, glob
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\OMEGA_PROJETO\OMEGA_OHLCV_DATA")))
import volume_calibrate as _vc
from volume_calibrate import run_calibration


# --- Override load_csv: suporta datetime string OU epoch ---
def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"time", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV faltando colunas: {missing}")
    df = df[list(required)].copy()
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df["time"].dtype == object:
        df["time"] = pd.to_datetime(df["time"]).astype("int64") // 10**9
    else:
        df["time"] = pd.to_numeric(df["time"], errors="coerce")
    return df.sort_values("time").reset_index(drop=True).dropna()


# --- session_filter seguro: bypass para H1/H4/D1 ---
# Filtro de sessão intraday não faz sentido para HTF ou dados históricos de 1971
def session_filter_safe(df: pd.DataFrame, symbol: str) -> bool:
    if "time" not in df.columns or len(df) < 2:
        return True
    times = df["time"].values
    delta = abs(float(times[1]) - float(times[0]))
    # H1 = 3600s, H4 = 14400s, D1 = 86400s — todos bypass
    if delta >= 3600:
        return True
    if symbol.upper() in {"BTCUSD"}:
        return True
    try:
        hours = pd.to_datetime(df["time"], unit="s").dt.hour
        return float((hours.between(7, 19)).mean()) >= 0.5
    except Exception:
        return True


# --- liquidity_filter relaxado para tick_volume ---
def liquidity_filter_relaxed(df: pd.DataFrame,
                              cv_max: float = 2.0,
                              pct_above: float = 0.60) -> bool:
    vols = df["volume"].values
    if len(vols) < 50:
        return False
    cv  = float(np.std(vols) / max(np.mean(vols), 1e-9))
    thr = float(np.percentile(vols, 30))
    pct = float(np.mean(vols > thr))
    return (cv <= cv_max) and (pct >= pct_above)


# Injectar overrides no módulo
_vc.load_csv = load_csv
_vc.session_filter = session_filter_safe

# ── Directório e descoberta automática de CSVs ────────────────────────────────
ROOT = Path(r"c:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\OHLCV_DATA")
OUT  = ROOT / "volume_calib_results_full.json"

all_csvs = glob.glob(str(ROOT / "**" / "*.csv"), recursive=True)
TARGETS  = [
    str(Path(p).relative_to(ROOT)).replace("\\", "/")
    for p in all_csvs
    if "_INDEX" not in p
]

print("=" * 68)
print("  OMEGA CALIBRAÇÃO COMPLETA — TODOS OS ATIVOS/TFs")
print(f"  CSVs encontrados: {len(TARGETS)}")
print("=" * 68)

datasets = {}
for rel in sorted(TARGETS):
    path = ROOT / rel
    try:
        df      = load_csv(path)
        symbol  = rel.split("/")[0]
        n       = len(df)
        if n < 100:
            print(f"  [SKIP] {rel:<40} n={n} (insuficiente)")
            continue
        liq_ok  = liquidity_filter_relaxed(df)
        sess_ok = session_filter_safe(df, symbol)
        t_s = pd.to_datetime(df["time"].iloc[0],  unit="s").strftime("%Y-%m-%d")
        t_e = pd.to_datetime(df["time"].iloc[-1], unit="s").strftime("%Y-%m-%d")
        status = "OK  " if (liq_ok and sess_ok) else "SKIP"
        print(f"  [{status}] {rel:<40} {n:>8,} barras | {t_s} → {t_e}")
        if liq_ok and sess_ok:
            key = rel.replace("/", "_").replace(".csv", "")
            datasets[key] = df
    except Exception as e:
        print(f"  [ERR ] {rel}: {e}")

print()
print(f"  {len(datasets)} datasets aprovados.")

if not datasets:
    print("  ERRO: Nenhum dataset aprovado.")
    sys.exit(1)

grid = {
    "vol_z":    [1.5, 2.0, 2.5],
    "min_conf": [0.2, 0.3, 0.4],
    "vwap_mult":[1.5, 2.0, 2.5],
}
n_splits = 5
total    = len(grid["vol_z"]) * len(grid["min_conf"]) * len(grid["vwap_mult"]) * len(datasets)
print(f"  Grid: {total} combinações | walk-forward: {n_splits} splits | alpha=0.05")
print(f"  Output: {OUT}")
print()

calib = run_calibration(datasets, grid, n_splits=n_splits, alpha=0.05)

slim = dict(calib)
slim["results"] = [
    {k: v for k, v in r.items() if k != "events"}
    for r in calib.get("results", [])
]
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(slim, f, indent=2, ensure_ascii=False)

results = calib.get("results", [])
print(f"\n{'=' * 68}")
print(f"  RESULTADO FINAL — {len(results)} combinações APROVADAS / {total}")
print(f"  Bonferroni: {calib.get('bonferroni', {})}")
print(f"  FDR:        {calib.get('fdr', {})}")

if results:
    print(f"\n  TOP 10 (Sharpe OOS):")
    for i, r in enumerate(results[:10], 1):
        m  = r["metrics"]
        wf = r["walk_forward"]
        vm = r.get("vwap_std_mult", r.get("vwap_mult", "?"))
        print(f"\n  [{i:>2}] {r['symbol_tf']}")
        print(f"        vol_z={r['vol_z_threshold']} | min_conf={r['min_confidence']} | vwap_mult={vm}")
        print(f"        Trades={m.get('trades')} | WR={m.get('win_rate',0):.1%} | Sharpe IS={m.get('sharpe',0):.4f}")
        print(f"        Sharpe OOS={wf.get('mean_sharpe_oos',0):.4f} | Overfit={wf.get('overfitting_score',1):.4f} | Robusto={wf.get('is_robust')}")
        print(f"        PF={m.get('profit_factor',0):.3f} | MaxDD={m.get('max_drawdown',0):.2%} | p={m.get('p_value','N/A')}")
else:
    print("\n  Nenhuma combinação aprovada nos critérios IS+OOS+stat.")

print(f"\n  Resultados em: {OUT}")
print("=" * 68)
