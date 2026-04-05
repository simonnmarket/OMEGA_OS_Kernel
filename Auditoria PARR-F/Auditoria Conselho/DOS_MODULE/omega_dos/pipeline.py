"""
Pipeline principal DOS: ingestão FIN-SENSE → métricas → dicionário auditável.

Não persiste em base por defeito; consumidores podem gravar o resultado (JSON/SQL).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any, Literal, Optional

import numpy as np
import pandas as pd

from omega_dos.bridge_fin_sense import (
    FinSenseSwingBundle,
    load_demo_swing_from_postgres,
    synthetic_positions_trades_from_swing,
    swing_bronze_to_market_frame,
)
from omega_dos.config import dos_module_version, fin_sense_schema_version, get_dos_schema
from omega_dos.metrics.clustering import cluster_feature_matrix, default_feature_columns
from omega_dos.metrics.pnl import equity_from_returns, log_returns, pnl_series_from_prices
from omega_dos.metrics.regimes import volatility_regime_labels
from omega_dos.metrics.risk import cvar_historical, var_historical
from omega_dos.provenance import build_provenance_record, sha256_canonical


@dataclass
class DosPipelineResult:
    """Resultado serializável (JSON-friendly) do pipeline."""

    summary: dict[str, Any]
    risk: dict[str, float]
    market_quality: dict[str, Any]
    regimes: dict[str, Any]
    clustering: dict[str, Any]
    provenance: dict[str, Any]
    errors: list[str] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "risk": self.risk,
            "market_quality": self.market_quality,
            "regimes": self.regimes,
            "clustering": self.clustering,
            "provenance": self.provenance,
            "errors": self.errors,
        }


def _digest_frame(df: pd.DataFrame) -> str:
    """Digest estável e incremental do conteúdo tabular (evita OOM em datasets grandes)."""
    if df.empty:
        return sha256_canonical({"rows": 0})
    h = hashlib.sha256()
    h.update(",".join(df.columns).encode("utf-8"))
    chunk = 10_000
    for start in range(0, len(df), chunk):
        part = df.iloc[start : start + chunk]
        # CSV estável sem índice para auditabilidade; evita materializar tudo em lista Python
        h.update(part.to_csv(index=False).encode("utf-8"))
    return h.hexdigest()


def run_dos_pipeline(
    *,
    market: Optional[pd.DataFrame] = None,
    bundle: Optional[FinSenseSwingBundle] = None,
    source: Literal["auto", "postgres", "frame"] = "auto",
    limit_rows: Optional[int] = None,
    ingestion_id: Optional[str] = None,
    notional_usd: float = 10_000.0,
    var_alpha: float = 0.05,
    regime_window: int = 20,
    n_regimes: int = 3,
    n_clusters: int = 3,
) -> DosPipelineResult:
    """
    Executa o pipeline completo.

    - `source=auto`: usa `market` se fornecido; senão tenta Postgres (se PGPASS disponível).
    - `source=postgres`: obriga carregamento via `load_demo_swing_from_postgres`.
    - `source=frame`: obriga `market` não vazio.
    """
    errors: list[str] = []
    b: FinSenseSwingBundle | None = bundle

    if source == "frame":
        if market is None or market.empty:
            return DosPipelineResult(
                summary={},
                risk={},
                market_quality={},
                regimes={},
                clustering={},
                provenance={},
                errors=["source=frame requer market não vazio"],
            )
        mkt = swing_bronze_to_market_frame(market)
    elif source == "postgres":
        try:
            b = load_demo_swing_from_postgres(limit_rows=limit_rows, ingestion_id=ingestion_id)
            mkt = b.market
        except Exception as e:
            return DosPipelineResult(
                summary={},
                risk={},
                market_quality={},
                regimes={},
                clustering={},
                provenance={},
                errors=[f"postgres: {e}"],
            )
    else:
        if market is not None and not market.empty:
            mkt = swing_bronze_to_market_frame(market)
        else:
            try:
                b = load_demo_swing_from_postgres(limit_rows=limit_rows, ingestion_id=ingestion_id)
                mkt = b.market
            except Exception as e:
                return DosPipelineResult(
                    summary={},
                    risk={},
                    market_quality={},
                    regimes={},
                    clustering={},
                    provenance={},
                    errors=[f"auto: sem market e falha Postgres: {e}"],
                )

    if b is None:
        b = FinSenseSwingBundle(market=mkt, ingestion_ids=[], source="frame")

    val_errs: list[str] = b.validate()
    if val_errs:
        errors.extend(val_errs)

    positions, trades = synthetic_positions_trades_from_swing(mkt, notional_usd=notional_usd)
    pnl = pnl_series_from_prices(mkt["y"], notional=notional_usd, use_log_returns=True)
    r = log_returns(mkt["y"])
    eq = equity_from_returns(r.fillna(0.0), initial=notional_usd)

    var_ = var_historical(pnl, alpha=var_alpha, side="loss")
    cvar_ = cvar_historical(pnl, alpha=var_alpha, side="loss")

    regime_lbl = volatility_regime_labels(mkt["y"], window=regime_window, n_regimes=n_regimes)
    regime_counts = regime_lbl.value_counts(dropna=True).to_dict()
    feat_cols = [c for c in default_feature_columns() if c in mkt.columns]
    labels = pd.Series(dtype=int)
    cluster_counts: dict[Any, int] = {}
    try:
        if feat_cols:
            labels, _ = cluster_feature_matrix(mkt, columns=feat_cols, n_clusters=n_clusters)
            cluster_counts = labels.value_counts().to_dict()
    except Exception as e:
        errors.append(f"clustering: {e}")

    summary = {
        "rows": int(len(mkt)),
        "ts_min": str(mkt["ts"].min()) if "ts" in mkt.columns and len(mkt) else None,
        "ts_max": str(mkt["ts"].max()) if "ts" in mkt.columns and len(mkt) else None,
        "ingestion_ids": b.ingestion_ids if b else [],
        "notional_usd": notional_usd,
        "positions_rows": int(len(positions)),
        "trades_rows": int(len(trades)),
    }

    risk = {
        "var_historical_loss": float(var_) if var_ == var_ else float("nan"),
        "cvar_historical_loss": float(cvar_) if cvar_ == cvar_ else float("nan"),
        "var_alpha": var_alpha,
        "pnl_sum": float(pnl.sum()),
        "pnl_mean": float(pnl.mean()) if len(pnl) else float("nan"),
        "equity_final": float(eq.iloc[-1]) if len(eq) else float("nan"),
    }

    market_quality = {
        "z_abs_mean": float(mkt["z"].abs().mean()) if "z" in mkt.columns else None,
        "spread_mean": float(mkt["spread"].mean()) if "spread" in mkt.columns else None,
        "signal_rate": float(mkt["signal_fired"].mean()) if "signal_fired" in mkt.columns else None,
        "fill_rate": float(mkt["order_filled"].mean()) if "order_filled" in mkt.columns else None,
        "cpu_pct_mean": float(mkt["cpu_pct"].mean()) if "cpu_pct" in mkt.columns else None,
        "proc_ms_p95": float(mkt["proc_ms"].quantile(0.95)) if "proc_ms" in mkt.columns else None,
    }

    regimes = {
        "window": regime_window,
        "n_regimes": n_regimes,
        "regime_counts": {str(k): int(v) for k, v in sorted(regime_counts.items(), key=lambda x: str(x[0]))},
    }

    clustering_out = {
        "n_clusters_requested": n_clusters,
        "feature_columns_used": feat_cols,
        "cluster_counts": {str(k): int(v) for k, v in sorted(cluster_counts.items(), key=lambda x: str(x[0]))},
    }

    inputs_digest = _digest_frame(mkt)
    prov = build_provenance_record(
        inputs_digest=inputs_digest,
        code_version=dos_module_version(),
        fin_sense_schema=fin_sense_schema_version(),
        extras={
            "dos_pg_schema": get_dos_schema(),
            "source": b.source if b else "frame",
        },
    )

    return DosPipelineResult(
        summary=summary,
        risk=risk,
        market_quality={k: v for k, v in market_quality.items() if v is not None},
        regimes=regimes,
        clustering=clustering_out,
        provenance=prov,
        errors=errors,
    )
