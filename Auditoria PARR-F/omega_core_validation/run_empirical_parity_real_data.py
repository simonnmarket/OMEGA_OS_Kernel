#!/usr/bin/env python3
"""
Execução empírica objetiva — paridade / deriva (Métrica 10, DOCUMENTO_TÉCNICO §11).

REGRAS:
  - Apenas dados lidos de ficheiros CSV existentes (histórico completo disponível no merge).
  - Sem projeção, sem preenchimento sintético de gaps: alinhamento = inner join na coluna temporal.
  - Saída: relatório JSON + texto + SHA-256 dos inputs (rastreabilidade).

Uso típico (PowerShell, a partir desta pasta):
  python run_empirical_parity_real_data.py ^
    --y-csv "C:\\...\\XAUUSD_M1.csv" ^
    --x-csv "C:\\...\\AUDJPY_M1.csv" ^
    --out-dir ".\\PSA_EMPIRICA_OUT"

Dependências: numpy, pandas (já cobertas por requirements.txt do núcleo).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Garantir imports do núcleo no mesmo directório que este script
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import v821_batch

from parity_report import parity_ewma_z_pandas_vs_recursive, parity_full_batch_vs_online


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_series_pair(
    path_y: Path,
    path_x: Path,
    time_col: str,
    value_col: str,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    dy = pd.read_csv(path_y)
    dx = pd.read_csv(path_x)
    for name, df in ("Y", dy), ("X", dx):
        if time_col not in df.columns or value_col not in df.columns:
            raise SystemExit(
                f"CSV {name}: faltam colunas obrigatórias {time_col!r} e {value_col!r}. "
                f"Colunas actuais: {list(df.columns)}"
            )
    dy = dy[[time_col, value_col]].rename(columns={value_col: "y_val"})
    dx = dx[[time_col, value_col]].rename(columns={value_col: "x_val"})
    merged = pd.merge(dy, dx, on=time_col, how="inner").sort_values(time_col)
    if merged.empty:
        raise SystemExit("Merge inner sobre tempo produziu 0 linhas — verifique sobreposição de timestamps.")
    y = merged["y_val"].astype(float).to_numpy()
    x = merged["x_val"].astype(float).to_numpy()
    return y, x, merged


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Paridade empírica batch vs online + EWMA pandas vs recursivo (dados reais CSV)."
    )
    parser.add_argument(
        "--y-csv",
        type=Path,
        required=True,
        help="CSV da série y (ex.: XAUUSD_M1) com colunas time + valor.",
    )
    parser.add_argument(
        "--x-csv",
        type=Path,
        required=True,
        help="CSV da série x (ex.: AUDJPY_M1) com colunas time + valor.",
    )
    parser.add_argument("--time-col", default="time", help="Nome da coluna temporal (exact match no join).")
    parser.add_argument(
        "--value-col",
        default="linha",
        help="Nome da coluna de preço/série (padrão OHLCV linha nos teus ficheiros).",
    )
    parser.add_argument("--window-ols", type=int, default=500, help="Janela OLS batch (V8.2.1).")
    parser.add_argument("--ewma-span", type=int, default=100, help="Span EWMA (batch e online).")
    parser.add_argument("--forgetting", type=float, default=0.995, help="Lambda RLS motor online.")
    parser.add_argument("--p0-scale", type=float, default=1e4, help="p0_scale RLS.")
    parser.add_argument("--eps", type=float, default=1e-10, help="Epsilon denominador Z.")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Pasta de saída (defeito: PSA_EMPIRICA_OUT_<UTC timestamp> nesta pasta).",
    )
    args = parser.parse_args()

    path_y = args.y_csv.resolve()
    path_x = args.x_csv.resolve()
    if not path_y.is_file():
        raise SystemExit(f"Ficheiro y inexistente: {path_y}")
    if not path_x.is_file():
        raise SystemExit(f"Ficheiro x inexistente: {path_x}")

    out_dir = args.out_dir
    if out_dir is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_dir = _ROOT / f"PSA_EMPIRICA_OUT_{ts}"
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    y, x, merged = load_series_pair(path_y, path_x, args.time_col, args.value_col)

    spread_batch, z_batch = v821_batch.v821_causal_spread_and_z(
        y,
        x,
        window_ols=args.window_ols,
        ewma_span=args.ewma_span,
        eps=args.eps,
    )

    rep_ewma = parity_ewma_z_pandas_vs_recursive(spread_batch, ewma_span=args.ewma_span, eps=args.eps)
    rep_full = parity_full_batch_vs_online(
        y,
        x,
        window_ols=args.window_ols,
        ewma_span=args.ewma_span,
        forgetting=args.forgetting,
        p0_scale=args.p0_scale,
        eps=args.eps,
    )

    meta = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "script": Path(__file__).name,
        "python": sys.version.split()[0],
        "inputs": {
            "y_csv": str(path_y),
            "x_csv": str(path_x),
            "sha256_y": sha256_file(path_y),
            "sha256_x": sha256_file(path_x),
            "time_col": args.time_col,
            "value_col": args.value_col,
        },
        "parameters": {
            "window_ols": args.window_ols,
            "ewma_span": args.ewma_span,
            "forgetting_rls": args.forgetting,
            "p0_scale": args.p0_scale,
            "eps": args.eps,
        },
        "merge_stats": {
            "n_rows_after_inner_join": int(len(merged)),
            "t_first": str(merged[args.time_col].iloc[0]),
            "t_last": str(merged[args.time_col].iloc[-1]),
        },
        "parity_ewma_same_spread_batch": rep_ewma,
        "parity_full_batch_vs_online": rep_full,
        "notes": [
            "spread_batch usa OLS em janela; spread online usa inovação RLS — MSE elevado em rep_full pode ser estrutural.",
            "rep_ewma compara apenas a camada EWMA sobre o mesmo spread_batch (pandas vs recursivo).",
            "Nenhuma linha foi sintetizada: apenas inner join temporal sobre CSV existentes.",
        ],
    }

    json_path = out_dir / "RELATORIO_EMPIRICO_PARIDADE.json"
    txt_path = out_dir / "RELATORIO_EMPIRICO_PARIDADE.txt"
    csv_path = out_dir / "serie_alinhada_merge.csv"

    json_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    merged.to_csv(csv_path, index=False)

    lines = [
        "RELATÓRIO EMPÍRICO — PARIDADE (OMEGA núcleo)",
        "=" * 60,
        f"UTC: {meta['generated_utc']}",
        f"Linhas após inner join: {meta['merge_stats']['n_rows_after_inner_join']}",
        f"Primeiro tempo: {meta['merge_stats']['t_first']}",
        f"Último tempo: {meta['merge_stats']['t_last']}",
        "",
        "Ficheiros e SHA256:",
        f"  Y: {path_y}",
        f"       {meta['inputs']['sha256_y']}",
        f"  X: {path_x}",
        f"       {meta['inputs']['sha256_x']}",
        "",
        "Parâmetros:",
        json.dumps(meta["parameters"], indent=2),
        "",
        "10.A Paridade EWMA (mesmo spread batch):",
        json.dumps(rep_ewma, indent=2, ensure_ascii=False),
        "",
        "10.B Paridade completa batch vs online:",
        json.dumps(rep_full, indent=2, ensure_ascii=False),
        "",
        f"Série alinhada gravada em: {csv_path}",
        f"JSON completo: {json_path}",
    ]
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    print("\n".join(lines))
    print(f"\nConcluído. Pasta de saída: {out_dir}")


if __name__ == "__main__":
    main()
