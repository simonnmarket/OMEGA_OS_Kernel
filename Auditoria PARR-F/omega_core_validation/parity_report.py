"""
Relatório de paridade / deriva entre pipelines de Z (auditoria CKO / CFO).

- Paridade EWMA: mesma série de spreads → Z pandas (shift(1)) vs Z recursivo (mesma
  recorrência que OnlineRLSEWMACausalZ sobre spreads).
- Paridade completa: batch V8.2.1 (OLS janela + Z pandas) vs motor online (RLS + EWMA);
  espera-se divergência estrutural se window OLS ≠ comportamento RLS — o relatório
  quantifica, não força MSE ≈ 0.
"""

from __future__ import annotations

import numpy as np

from v821_batch import causal_z_ewma_shift1, v821_causal_spread_and_z
from online_rls_ewma import OnlineRLSEWMACausalZ


def recursive_ewma_z_on_spreads(
    spreads: np.ndarray,
    ewma_span: int,
    eps: float = 1e-10,
) -> np.ndarray:
    """
    Replica a lógica de Z do OnlineRLSEWMACausalZ para uma série de spreads já conhecidos
    (sem RLS). Primeira observação **finita**: z=0; depois z_t = (s_t - mu_{t-1}) / (sqrt(v_{t-1}) + eps).
    Índices com spread nan permanecem nan na saída.
    """
    spreads = np.asarray(spreads, dtype=float).ravel()
    n = len(spreads)
    alpha = 2.0 / (ewma_span + 1.0)
    z_out = np.full(n, np.nan)
    mu = 0.0
    var = 1e-8
    n_seen = 0
    for t in range(n):
        s = spreads[t]
        if not np.isfinite(s):
            continue
        s = float(s)
        if n_seen == 0:
            z_out[t] = 0.0
            mu = s
            var = max(eps**2, 1e-8)
        else:
            sig = float(np.sqrt(max(var, 0.0)))
            z_out[t] = (s - mu) / (sig + eps)
            mu_new = (1.0 - alpha) * mu + alpha * s
            var = (1.0 - alpha) * var + alpha * (s - mu_new) ** 2
            mu = mu_new
        n_seen += 1
    return z_out


def parity_ewma_z_pandas_vs_recursive(
    spreads: np.ndarray,
    ewma_span: int,
    eps: float = 1e-10,
) -> dict[str, float | int | str]:
    """
    Compara Z_batch (pandas ewm + shift(1)) com Z_recursivo na **mesma** série de spreads.
    """
    s = np.asarray(spreads, dtype=float).ravel()
    z_pd = causal_z_ewma_shift1(s, ewma_span=ewma_span, eps=eps)
    z_rc = recursive_ewma_z_on_spreads(s, ewma_span=ewma_span, eps=eps)
    mask = np.isfinite(z_pd) & np.isfinite(z_rc)
    n = int(mask.sum())
    if n == 0:
        return {
            "n_points": 0,
            "mse": float("nan"),
            "mean_abs_diff": float("nan"),
            "note": "Sem pontos comparáveis.",
        }
    d = z_pd[mask] - z_rc[mask]
    return {
        "n_points": n,
        "mse": float(np.mean(d**2)),
        "mean_abs_diff": float(np.mean(np.abs(d))),
        "max_abs_diff": float(np.max(np.abs(d))),
        "note": "Mesma série de spreads; divergência restante = diferença pandas ewm.std vs recorrência v_t.",
    }


def parity_full_batch_vs_online(
    y: np.ndarray,
    x: np.ndarray,
    window_ols: int,
    ewma_span: int,
    forgetting: float = 0.995,
    p0_scale: float = 1e4,
    eps: float = 1e-10,
) -> dict[str, float | int | str]:
    """
    Batch V8.2.1 vs OnlineRLSEWMACausalZ barra a barra.

    AVISO: spreads diferem (OLS em janela vs inovação RLS); MSE elevado não implica
    bug — indica **dois geradores de sinal**. Use para monitorização, não como teste de igualdade.
    """
    y = np.asarray(y, dtype=float).ravel()
    x = np.asarray(x, dtype=float).ravel()
    _, z_b = v821_causal_spread_and_z(y, x, window_ols=window_ols, ewma_span=ewma_span, eps=eps)
    eng = OnlineRLSEWMACausalZ(
        forgetting=forgetting,
        ewma_span=ewma_span,
        eps=eps,
        p0_scale=p0_scale,
    )
    z_o = np.full(len(y), np.nan)
    for i in range(len(y)):
        _, z_o[i], _ = eng.step(float(y[i]), float(x[i]))
    mask = np.isfinite(z_b) & np.isfinite(z_o)
    n = int(mask.sum())
    if n == 0:
        return {
            "n_points": 0,
            "mse": float("nan"),
            "mean_abs_diff": float("nan"),
            "note": "Sem sobreposição finita.",
        }
    d = z_b[mask] - z_o[mask]
    return {
        "n_points": n,
        "mse": float(np.mean(d**2)),
        "mean_abs_diff": float(np.mean(np.abs(d))),
        "max_abs_diff": float(np.max(np.abs(d))),
        "note": "Spread batch (OLS w) != spread online (RLS); interpretar como Z_DRIFT estrutural.",
    }
