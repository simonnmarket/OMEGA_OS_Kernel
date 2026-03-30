"""Motor online: sem excepções em série longa; z finito após warm-up."""

import numpy as np

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from online_rls_ewma import OnlineRLSEWMACausalZ


def test_online_runs_without_nan_inf():
    rng = np.random.default_rng(7)
    n = 300
    x = rng.normal(scale=2.0, size=n) + 50
    y = 1.0 + 0.03 * x + rng.normal(scale=0.5, size=n)

    eng = OnlineRLSEWMACausalZ(forgetting=0.995, ewma_span=30)
    zs = []
    for i in range(n):
        s, z, _ = eng.step(float(y[i]), float(x[i]))
        zs.append(z)
    arr = np.array(zs[50:])
    assert np.all(np.isfinite(arr))
