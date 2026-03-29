"""Provas: RLS λ=1 aproxima OLS em amostra completa; innovação coerente com θ antes do passo."""

import numpy as np

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rls_regression import RLSRegression2D, batch_ols_alpha_beta


def test_rls_lambda1_matches_batch_ols():
    rng = np.random.default_rng(42)
    n = 800
    x = rng.normal(size=n)
    true_a, true_b = 2.0, -1.5
    y = true_a + true_b * x + rng.normal(scale=0.2, size=n)

    rls = RLSRegression2D(forgetting=1.0, p0_scale=1e3)
    for i in range(n):
        rls.update(y[i], x[i])

    batch = batch_ols_alpha_beta(y, x)
    np.testing.assert_allclose(rls.theta, batch, rtol=5e-3, atol=5e-3)


def test_innovation_matches_y_minus_phi_theta():
    rls = RLSRegression2D(forgetting=1.0, p0_scale=1e3)
    y, x = 5.0, 1.2
    theta_before = rls.theta.copy()
    phi = np.array([1.0, x])
    s, yh = rls.innovation(y, x)
    np.testing.assert_allclose(s, y - phi @ theta_before)
    np.testing.assert_allclose(yh, phi @ theta_before)
