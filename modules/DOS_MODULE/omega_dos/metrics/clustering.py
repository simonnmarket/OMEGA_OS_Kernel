"""Clustering não supervisionado em features FIN-SENSE (scikit-learn, seed fixo)."""

from __future__ import annotations

from typing import Sequence

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


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
    KMeans com pipeline StandardScaler → Imputer → KMeans (seed fixa para reprodutibilidade).

    Devolve série de labels alinhada ao índice de `df` e o pipeline treinado.
    """
    cols = list(columns) if columns is not None else list(default_feature_columns())
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas em falta no DataFrame: {missing}")

    X = df.loc[:, cols].to_numpy(dtype=float)
    if X.size == 0:
        empty = pd.Series(dtype=int)
        pipe = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("kmeans", KMeans(n_clusters=max(1, n_clusters), random_state=random_state, n_init=10)),
            ]
        )
        return empty, pipe

    n_clusters = int(max(1, min(n_clusters, len(df))))
    pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)),
        ]
    )
    labels = pipe.fit_predict(X)
    return pd.Series(labels, index=df.index, name="cluster_id", dtype=int), pipe
