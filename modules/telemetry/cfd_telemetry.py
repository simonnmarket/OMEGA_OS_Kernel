"""
Telemetry CFD V5.5.0
--------------------
Módulo independente para auditoria/telemetria de replays (CSV) sem placeholders.
Calcula métricas de churn, drawdown, PF, equity curve e salva uma versão
augmentada do CSV com colunas de telemetria.

Dependências: pandas, numpy (já usados no ambiente).
Não depende dos demais módulos do kernel.
"""

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

import numpy as np
import pandas as pd


@dataclass
class TelemetrySummary:
    file: str
    sha256: str
    symbol: str
    fx_rate: float
    trades: int
    wins: int
    winrate_pct: float
    pnl: float                 # após conversão FX
    gross_pos: float           # após conversão FX
    gross_neg: float           # após conversão FX
    pf: float
    churn_le_3s: int
    median_duration_s: float
    mean_duration_s: float
    max_dd_abs: float
    max_dd_pct: float
    equity_final: float
    cagr_est_pct: Optional[float]
    start_ts: Optional[str]
    end_ts: Optional[str]
    reason_counts: Dict[str, int]
    fr_total: Optional[float]
    alerts: List[str]


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_telemetry(
    df: pd.DataFrame,
    start_equity: float = 10_000.0,
) -> pd.DataFrame:
    """Adiciona colunas de telemetria (equity, drawdown, churn, etc.)."""
    df = df.copy()
    if "duration_s" not in df or "pnl_net" not in df:
        raise ValueError("CSV deve conter colunas 'duration_s' e 'pnl_net'.")

    df["is_win"] = df["pnl_net"] > 0
    df["churn_flag"] = df["duration_s"] <= 3

    eq = start_equity + df["pnl_net"].cumsum()
    df["equity"] = eq
    peak = df["equity"].cummax()
    df["dd"] = peak - df["equity"]
    df["dd_pct"] = np.where(peak != 0, df["dd"] / peak * 100.0, 0.0)

    return df


def validate_required_columns(df: pd.DataFrame, path: Path) -> None:
    """Valida colunas obrigatórias antes de processar."""
    required = ["ts_open", "ts_close", "duration_s", "pnl_net"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(
            f"CSV {path.name} faltando colunas obrigatórias: {missing}. "
            f"Colunas encontradas: {list(df.columns)}"
        )


def check_critical_thresholds(
    summary: TelemetrySummary,
    trades_max: int = 10_000,  # valor alto por padrão, ajuste conforme uso
    churn_max: int = 0,
    median_duration_min: float = 0.0,
    pnl_min: float = -float("inf"),
    fr_max: Optional[float] = None,
    max_dd_pct_max: Optional[float] = None,
    pf_min: Optional[float] = None,
) -> List[str]:
    """Retorna lista de alertas se métricas críticas falharem."""
    alerts: List[str] = []
    if summary.trades >= trades_max:
        alerts.append(f"FAIL: trades={summary.trades} >= {trades_max}")
    if summary.churn_le_3s > churn_max:
        alerts.append(f"FAIL: churn_le_3s={summary.churn_le_3s} > {churn_max}")
    if summary.median_duration_s < median_duration_min:
        alerts.append(
            f"FAIL: median_duration_s={summary.median_duration_s:.1f} < {median_duration_min}"
        )
    if summary.pnl <= pnl_min:
        alerts.append(f"FAIL: pnl={summary.pnl:.2f} <= {pnl_min}")
    if pf_min is not None and summary.pf < pf_min:
        alerts.append(f"FAIL: pf={summary.pf:.2f} < {pf_min}")
    if max_dd_pct_max is not None and summary.max_dd_pct > max_dd_pct_max:
        alerts.append(
            f"FAIL: max_dd_pct={summary.max_dd_pct:.2f}% > {max_dd_pct_max}%"
        )
    if fr_max is not None and summary.fr_total is not None and summary.fr_total > fr_max:
        alerts.append(f"FAIL: fr_total={summary.fr_total:.3f} > {fr_max}")
    return alerts


def summarize(
    df: pd.DataFrame,
    file: str,
    sha256: str,
    start_equity: float = 10_000.0,
    symbol: str = "ALL",
    fx_rate: float = 1.0,
) -> TelemetrySummary:
    trades = len(df)
    # Aplicar FX
    pnl_series = df["pnl_net"] * fx_rate
    wins = int((pnl_series > 0).sum())
    pnl = float(pnl_series.sum())
    gross_pos = float(pnl_series[pnl_series > 0].sum())
    gross_neg = float(pnl_series[pnl_series < 0].sum())
    pf = gross_pos / abs(gross_neg) if gross_neg != 0 else float("inf")
    churn = int((df["duration_s"] <= 3).sum())
    median_dur = float(df["duration_s"].median()) if trades else 0.0
    mean_dur = float(df["duration_s"].mean()) if trades else 0.0

    eq = start_equity + pnl_series.cumsum()
    peak = eq.cummax()
    dd = (peak - eq)
    max_dd_abs = float(dd.max())
    max_dd_pct = float(((dd / peak.replace(0, 1)) * 100).max())
    equity_final = float(eq.iloc[-1]) if trades else start_equity

    # CAGR estimado
    try:
        start_ts = pd.to_datetime(df["ts_open"].iloc[0])
        end_ts = pd.to_datetime(df["ts_close"].iloc[-1])
        years = max((end_ts - start_ts).total_seconds() / (365 * 24 * 3600), 1e-9)
        cagr = ((equity_final) / start_equity) ** (1 / years) - 1
        cagr_pct = float(cagr * 100)
    except Exception:
        start_ts = None
        end_ts = None
        cagr_pct = None

    reason_counts = (
        df["reason_exit"].value_counts().to_dict() if "reason_exit" in df else {}
    )

    fr_total = None
    cost_cols = ["spread_cost", "slippage_cost", "commission_cost", "swap_cost", "total_cost"]
    if set(cost_cols) & set(df.columns):
        total_cost = 0.0
        for c in cost_cols:
            if c in df.columns:
                total_cost += float((df[c] * fx_rate).sum())
        if pnl != 0:
            fr_total = abs(total_cost) / abs(pnl)

    return TelemetrySummary(
        file=file,
        sha256=sha256,
        symbol=symbol,
        fx_rate=fx_rate,
        trades=trades,
        wins=wins,
        winrate_pct=round(wins / trades * 100, 2) if trades else 0.0,
        pnl=pnl,
        gross_pos=gross_pos,
        gross_neg=gross_neg,
        pf=pf,
        churn_le_3s=churn,
        median_duration_s=median_dur,
        mean_duration_s=mean_dur,
        max_dd_abs=max_dd_abs,
        max_dd_pct=max_dd_pct,
        equity_final=equity_final,
        cagr_est_pct=cagr_pct,
        start_ts=str(start_ts) if start_ts is not None else None,
        end_ts=str(end_ts) if end_ts is not None else None,
        reason_counts=reason_counts,
        fr_total=fr_total,
        alerts=[],
    )


def process_file(
    path: Path,
    out_dir: Path,
    start_equity: float = 10_000.0,
    fx_rate: float = 1.0,
    thresholds: Optional[Dict[str, float]] = None,
) -> List[TelemetrySummary]:
    df = pd.read_csv(path)
    validate_required_columns(df, path)
    # aplica FX em coluna pnl_net (cria coluna convertida para referência)
    df["pnl_net_fx"] = df["pnl_net"] * fx_rate
    h = sha256_file(path)

    # Agrupamento por símbolo (se existir coluna 'symbol'); senão, único grupo "ALL"
    summaries: List[TelemetrySummary] = []
    if "symbol" in df.columns:
        symbols = df["symbol"].unique()
        for sym in symbols:
            df_sym = df[df["symbol"] == sym]
            df_aug = compute_telemetry(df_sym, start_equity=start_equity)
            df_aug["pnl_net"] = df_sym["pnl_net"] * fx_rate
            out_path = out_dir / f"{path.stem}_{sym}_augmented.csv"
            df_aug.to_csv(out_path, index=False)
            summary = summarize(
                df_sym,
                file=path.name,
                sha256=h,
                start_equity=start_equity,
                symbol=str(sym),
                fx_rate=fx_rate,
            )
            summaries.append(summary)
    else:
        df_aug = compute_telemetry(df, start_equity=start_equity)
        df_aug["pnl_net"] = df["pnl_net"] * fx_rate
        out_path = out_dir / f"{path.stem}_augmented.csv"
        df_aug.to_csv(out_path, index=False)
        summary = summarize(
            df,
            file=path.name,
            sha256=h,
            start_equity=start_equity,
            symbol="ALL",
            fx_rate=fx_rate,
        )
        summaries.append(summary)

    # salva resumos JSON (lista)
    summary_path = out_dir / f"{path.stem}_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(s) for s in summaries], f, ensure_ascii=False, indent=2)

    # Avalia thresholds e imprime alertas
    if thresholds:
        for s in summaries:
            alerts = check_critical_thresholds(
                s,
                trades_max=int(thresholds.get("trades_max", 10_000)),
                churn_max=int(thresholds.get("churn_max", 0)),
                median_duration_min=float(thresholds.get("median_duration_min", 0.0)),
                pnl_min=float(thresholds.get("pnl_min", -float("inf"))),
                fr_max=thresholds.get("fr_max"),
                max_dd_pct_max=thresholds.get("max_dd_pct_max"),
                pf_min=thresholds.get("pf_min"),
            )
            s.alerts = alerts
            if alerts:
                print(f"⚠️ ALERTAS para {s.file} / {s.symbol}:")
                for a in alerts:
                    print(f"  - {a}")
        # regravar JSON com alerts
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump([asdict(s) for s in summaries], f, ensure_ascii=False, indent=2)

    return summaries


def main():
    parser = argparse.ArgumentParser(description="Telemetry CFD V5.5.0")
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Lista de CSVs de replay (ex.: REPLAY_FOCAL_M1_2026.csv)",
    )
    parser.add_argument(
        "--out-dir",
        default=".",
        help="Diretório de saída para CSVs augmentados e resumos JSON",
    )
    parser.add_argument(
        "--start-equity",
        type=float,
        default=10_000.0,
        help="Capital inicial para curva de equity",
    )
    parser.add_argument(
        "--fx-rate",
        type=float,
        default=1.0,
        help="Fator de conversão FX aplicado ao PnL (ex.: USD->BRL).",
    )
    parser.add_argument(
        "--trades-max", type=int, default=10_000, help="Limite para alerta de trades."
    )
    parser.add_argument(
        "--churn-max", type=int, default=0, help="Limite para alerta de churn (<=3s)."
    )
    parser.add_argument(
        "--median-duration-min",
        type=float,
        default=0.0,
        help="Duração mediana mínima (s) para alerta.",
    )
    parser.add_argument(
        "--pnl-min",
        type=float,
        default=-float("inf"),
        help="PnL mínimo para alerta.",
    )
    parser.add_argument(
        "--fr-max",
        type=float,
        default=None,
        help="FR máximo para alerta (se custos disponíveis).",
    )
    parser.add_argument(
        "--max-dd-pct-max",
        type=float,
        default=None,
        help="DD%% máximo para alerta.",
    )
    parser.add_argument(
        "--pf-min",
        type=float,
        default=None,
        help="PF mínimo para alerta.",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    for file in args.files:
        p = Path(file)
        if not p.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {p}")
        summaries.extend(
            process_file(
                p,
                out_dir,
                start_equity=args.start_equity,
                fx_rate=args.fx_rate,
                thresholds={
                    "trades_max": args.trades_max,
                    "churn_max": args.churn_max,
                    "median_duration_min": args.median_duration_min,
                    "pnl_min": args.pnl_min,
                    "fr_max": args.fr_max,
                    "max_dd_pct_max": args.max_dd_pct_max,
                    "pf_min": args.pf_min,
                },
            )
        )

    # Imprime resumo agregado
    for s in summaries:
        print(json.dumps(asdict(s), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
