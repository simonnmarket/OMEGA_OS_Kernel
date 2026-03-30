"""
Motor online: RLS (α,β) + spread causal + Z com μ e σ do passo anterior (EWMA).

Por observação (y_t, x_t):
1. s_t = y_t - φ_t^T θ_{t-1}   (innovação; θ ainda não actualizado)
2. z_t = (s_t - μ_{t-1}) / (√v_{t-1} + ε)  (primeira barra: z := 0)
3. μ_t = (1-α)·μ_{t-1} + α·s_t
4. v_t = (1-α)·v_{t-1} + α·(s_t - μ_t)²
5. Actualizar θ_t via RLS.

Nota: a variância EWMA difere ligeiramente de pandas ewm.std(); este módulo é
contrato explícito online. Comparar com v821_batch.py (referência V8.2.1) em testes separados.
"""

from __future__ import annotations

import numpy as np

from rls_regression import RLSRegression2D


class OnlineRLSEWMACausalZ:
    def __init__(
        self,
        forgetting: float = 0.98,
        ewma_span: int = 100,
        eps: float = 1e-10,
        p0_scale: float = 1e4,
    ):
        self.rls = RLSRegression2D(forgetting=forgetting, p0_scale=p0_scale)
        self.alpha = 2.0 / (ewma_span + 1.0)
        self.eps = eps
        self.mu = 0.0
        self.var = 1e-8
        self._n = 0

    def step(self, y: float, x: float) -> tuple[float, float, float]:
        """Retorna (spread_t, z_t, y_hat_pre)."""
        s, y_hat = self.rls.innovation(y, x)

        if self._n == 0:
            z = 0.0
            self.mu = float(s)
            self.var = max(self.eps**2, 1e-8)
        else:
            sig = float(np.sqrt(max(self.var, 0.0)))
            z = (s - self.mu) / (sig + self.eps)
            mu_new = (1.0 - self.alpha) * self.mu + self.alpha * s
            self.var = (1.0 - self.alpha) * self.var + self.alpha * (s - mu_new) ** 2
            self.mu = mu_new

        self.rls.update(y, x)
        self._n += 1
        return s, z, y_hat
