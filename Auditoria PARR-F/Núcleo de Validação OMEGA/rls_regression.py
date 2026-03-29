"""
Recursive Least Squares (RLS) com fator de esquecimento λ — estado 2D: [α, β] em y ≈ α + β·x.

Uso causal para spread:
  s_t = y_t - φ_t^T θ_{t-1}   com φ_t = [1, x_t]^T
  depois atualização RLS com (y_t, x_t).

Referência: equações clássicas K / P (ver TECH_SPEC).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class RLSState:
    theta: np.ndarray  # shape (2,)  [alpha, beta]
    P: np.ndarray  # shape (2, 2)


class RLSRegression2D:
    def __init__(self, forgetting: float = 1.0, p0_scale: float = 1e4):
        if not (0 < forgetting <= 1.0):
            raise ValueError("forgetting (λ) deve estar em (0, 1].")
        self.lam = float(forgetting)
        self.theta = np.zeros(2, dtype=float)
        self.P = np.eye(2, dtype=float) * float(p0_scale)

    def predict(self, x: float) -> float:
        phi = np.array([1.0, float(x)], dtype=float)
        return float(phi @ self.theta)

    def innovation(self, y: float, x: float) -> tuple[float, float]:
        """
        Erro de predição antes da atualização (spread causal se y,x são observações atuais).
        Retorna (spread, y_pred).
        """
        phi = np.array([1.0, float(x)], dtype=float)
        y_hat = float(phi @ self.theta)
        return float(y - y_hat), y_hat

    def update(self, y: float, x: float) -> float:
        """
        Uma observação. Retorna spread/innovation s = y - φ^T θ_-.
        """
        phi = np.array([1.0, float(x)], dtype=float)
        e = float(y - phi @ self.theta)
        denom = self.lam + float(phi @ self.P @ phi)
        K = (self.P @ phi) / denom
        self.theta = self.theta + K * e
        self.P = (self.P - np.outer(K, phi @ self.P)) / self.lam
        return e

    def state(self) -> RLSState:
        return RLSState(theta=self.theta.copy(), P=self.P.copy())


def batch_ols_alpha_beta(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """OLS y ~ 1 + x; retorna [alpha, beta]."""
    y = np.asarray(y, dtype=float).ravel()
    x = np.asarray(x, dtype=float).ravel()
    phi = np.column_stack([np.ones(len(x)), x])
    theta, _, _, _ = np.linalg.lstsq(phi, y, rcond=None)
    return theta
