"""Clustering não supervisionado em features FIN-SENSE (scikit-learn, seed fixo).

HARDENING: fallback controlado para dados constantes ou clusters degenerados.
"""

from __future__ import annotations

import logging
import warnings
from typing import Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def default_feature_columns() -> tuple[str, ...]:
    """Colunas típicas do demo swing quando disponíveis."""
    return ("z", "spread", "beta", "cpu_pct", "proc_ms", "opp_cost")


def cluster_feature_matrix(
    df: pd.DataFrame,
    *,
    columns: Sequence[str] | None = None,
    n_clusters: int = 3,
    random_state: int = 42,
) -> tuple[pd.Series, Pipeline]:
    """
    KMeans com pipeline StandardScaler → Imputer → KMeans (seed fixa).

    HARDENING: Captura warnings do sklearn quando dados são constantes
    e faz fallback para 1 cluster em vez de propagar exceção silenciosa.
    """
    cols = list(columns) if columns is not None else list(default_feature_columns())
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas em falta no DataFrame: {missing}")

    X = df.loc[:, cols].to_numpy(dtype=float)
    if X.size == 0:
        empty = pd.Series(dtype=int)
        pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(n_clusters=max(1, n_clusters), random_state=random_state, n_init=10)),
        ])
        return empty, pipe

    n_clusters = int(max(1, min(n_clusters, len(df))))

    # Verificação de dados constantes (evita warning do sklearn)
    valid_data = np.isfinite(X)
    if valid_data.any():
        col_std = np.nanstd(X, axis=0)
        n_varying = int(np.sum(col_std > 1e-12))
        if n_varying == 0:
            logger.warning(
                "Clustering: todas as %d features são constantes; forçando 1 cluster",
                len(cols),
            )
            n_clusters = 1

    pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("kmeans", KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)),
    ])

    # Suprimir warnings do sklearn em dados já tratados
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning, module="sklearn")
        warnings.filterwarnings("ignore", message=".*divide by zero.*")
        labels = pipe.fit_predict(X)

    return pd.Series(labels, index=df.index, name="cluster_id", dtype=int), pipe
