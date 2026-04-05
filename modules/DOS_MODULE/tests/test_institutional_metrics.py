from __future__ import annotations

import numpy as np
import pandas as pd

from omega_dos.metrics.institutional import Tier0Metrics


def test_tier0_metrics_deterministic():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0.0005, 0.01, size=500))
    m = Tier0Metrics(r, exposure=1_000_000.0)
    a1 = m.full_analysis()
    a2 = m.full_analysis()
    assert a1["var_95"] == a2["var_95"]
    assert "sharpe" in a1
