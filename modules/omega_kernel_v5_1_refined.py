"""
OMEGA SUPREME V5.1 (Refinado) — Kernel de Confluência Macro+Micro

Correções e reforços:
- Cálculo de pavio (wick) usando OHLC correto.
- Heikin Ashi com warmup e tolerância de igualdade (eps).
- Dimensão Fractal (Higuchi) com janela fixa, clamp [1.0, 2.0] e guarda de amostra.
- Guardas de dados: checagem de tamanho mínimo e NaN.
- Score parametrizável e autorização agressiva condicionada a estado válido.

Integração sugerida:
- Alimente este kernel com OHLCV alinhados (np.ndarray shape (N,4) para O,H,L,C e volume shape (N,)).
- Use o estado retornado para filtrar/ponderar sinais e para liberar ou não escalonamento agressivo (p.ex., 18 pernas).
- Mantenha filtros externos de risco (spread, DD diário, kill switch); não estão inclusos aqui.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
import numpy as np
import logging

logger = logging.getLogger("OMEGA_KERNEL_V5_1_REFINED")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


class MarketRegime(Enum):
    STRUCTURAL_TREND = auto()
    V_FLOW_ABSORPTION = auto()
    COMMAND_INERTIA = auto()
    CHOPPY_NOISE = auto()
    INSUFFICIENT_DATA = auto()


@dataclass
class KernelConfig:
    z_price_threshold: float = 1.8
    z_vol_threshold: float = 1.5
    wick_ratio_min: float = 0.6
    wick_window: int = 3            # barras para wick/absorção
    atr_window: int = 14            # ATR para normalizar wick
    vol_confirm_mult: float = 1.0   # vol >= mult * vol_média valida HA comando
    hfd_threshold: float = 1.35
    min_samples_z: int = 20
    min_samples_hfd: int = 50
    hfd_window: int = 200           # janela fixa para HFD
    hfd_kmax: int = 10              # k máximo para Higuchi
    eps: float = 1e-9


@dataclass
class OMEGAState:
    regime: MarketRegime
    signal_strength: float      # 0.0 a 1.0
    bias: str                   # BUY / SELL / NEUTRAL
    is_aggressive_allowed: bool # Autorização para escalonamento agressivo
    details: Optional[dict] = None


class OMEGAKernelV51Refined:
    def __init__(self, cfg: KernelConfig = KernelConfig()):
        self.cfg = cfg
        self.prev_ha = {"open": None, "close": None}

    # ------------------ Cálculos base ------------------
    def compute_higuchi(self, closes: np.ndarray) -> float:
        cfg = self.cfg
        if len(closes) < max(cfg.min_samples_hfd, cfg.hfd_kmax * 2):
            return 1.5
        series = closes[-cfg.hfd_window:] if len(closes) > cfg.hfd_window else closes
        n = len(series)
        if n < cfg.hfd_kmax * 2:
            return 1.5

        def higuchi_fd(x: np.ndarray, kmax: int) -> float:
            n = len(x)
            Lk = []
            k_values = range(1, kmax + 1)
            for k in k_values:
                Lm = []
                for m in range(k):
                    idx = np.arange(m, n, k)
                    if len(idx) < 2:
                        continue
                    lm = (n - 1) / (len(idx) * k) * np.sum(np.abs(np.diff(x[idx])))
                    Lm.append(lm)
                if len(Lm) == 0:
                    continue
                Lk.append(np.mean(Lm))
            if len(Lk) < 2:
                return 1.5
            logk = np.log(1.0 / np.array(list(k_values))[: len(Lk)])
            logLk = np.log(np.array(Lk))
            slope, _ = np.polyfit(logk, logLk, 1)
            return 2.0 + slope  # D = 2 - slope; com log(1/k) → 2+slope

        hfd = higuchi_fd(series, cfg.hfd_kmax)
        return float(np.clip(hfd, 1.0, 2.0))

    def compute_ha_commander(self, o: float, h: float, l: float, c: float, vol: float, vol_window_mean: float) -> dict:
        cfg = self.cfg
        if self.prev_ha["open"] is None:
            # warmup: primeira vela HA igual ao candle atual
            ha_open = (o + h + l + c) / 4.0
            ha_close = ha_open
            self.prev_ha = {"open": ha_open, "close": ha_close}

        ha_close = (o + h + l + c) / 4.0
        ha_open = (self.prev_ha["open"] + self.prev_ha["close"]) / 2.0
        ha_high = max(h, ha_open, ha_close)
        ha_low = min(l, ha_open, ha_close)

        self.prev_ha = {"open": ha_open, "close": ha_close}

        bull_command = (np.isclose(ha_low, ha_open, rtol=1e-5, atol=cfg.eps)) and (ha_close > ha_open)
        bear_command = (np.isclose(ha_high, ha_open, rtol=1e-5, atol=cfg.eps)) and (ha_close < ha_open)

        # Confirmação por volume
        vol_ok = vol >= vol_window_mean * cfg.vol_confirm_mult

        bias = "BUY" if (bull_command and vol_ok) else "SELL" if (bear_command and vol_ok) else "NEUTRAL"

        return {
            "is_command": (bull_command or bear_command) and vol_ok,
            "bias": bias,
            "ha_open": ha_open,
            "ha_close": ha_close,
            "vol_ok": vol_ok,
        }

    def _atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, window: int) -> float:
        tr = []
        for i in range(1, len(highs)):
            tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
        if len(tr) == 0:
            return 0.0
        return float(np.mean(tr[-window:])) if len(tr) >= window else float(np.mean(tr))

    def analyze_v_flow(self, ohlc: np.ndarray, volumes: np.ndarray) -> dict:
        cfg = self.cfg
        if len(ohlc) < max(cfg.min_samples_z, cfg.wick_window + 1):
            return {"valid": False}

        closes = ohlc[:, 3]
        window_c = closes[-cfg.min_samples_z:]
        window_v = volumes[-cfg.min_samples_z:]

        if np.any(~np.isfinite(window_c)) or np.any(~np.isfinite(window_v)):
            return {"valid": False}

        current_close = closes[-1]
        mean_p = np.mean(window_c)
        std_p = np.std(window_c)
        z_price = (current_close - mean_p) / (std_p + cfg.eps)

        mean_v = np.mean(window_v)
        std_v = np.std(window_v)
        z_vol = (volumes[-1] - mean_v) / (std_v + cfg.eps)

        # Wick: usa última barra, mas confirma com janela para absorção
        o, h, l, c = ohlc[-1]
        bar_range = max(h - l, cfg.eps)
        upper_wick = h - max(o, c)
        lower_wick = min(o, c) - l
        wick_ratio = (lower_wick / bar_range) if z_price < 0 else (upper_wick / bar_range)

        # Confirmação por janela de wick + ATR normalizado
        highs = ohlc[-cfg.wick_window :, 1]
        lows = ohlc[-cfg.wick_window :, 2]
        closes_w = ohlc[-cfg.wick_window :, 3]
        atr_val = self._atr(highs, lows, closes_w, min(cfg.atr_window, len(closes_w)))
        # wick normalizado da última barra e média da janela
        wick_last = lower_wick if z_price < 0 else upper_wick
        wick_norm = wick_last / (atr_val + cfg.eps)

        wick_ratios_window = []
        for i in range(len(highs)):
            rng = max(highs[i] - lows[i], cfg.eps)
            u_w = highs[i] - max(ohlc[-cfg.wick_window + i, 0], closes_w[i])
            l_w = min(ohlc[-cfg.wick_window + i, 0], closes_w[i]) - lows[i]
            wr_i = (l_w / rng) if z_price < 0 else (u_w / rng)
            wick_ratios_window.append(wr_i)
        wick_ratio_avg = float(np.mean(wick_ratios_window)) if len(wick_ratios_window) else 0.0

        is_panic = (abs(z_price) > cfg.z_price_threshold) and (z_vol > cfg.z_vol_threshold)

        return {
            "valid": True,
            "z_price": z_price,
            "z_vol": z_vol,
            "wick_ratio": wick_ratio,
            "wick_ratio_avg": wick_ratio_avg,
            "wick_norm": wick_norm,
            "is_panic": is_panic,
            "atr": atr_val,
        }

    # ------------------ Engine ------------------
    def engine_step(self, ohlcv: np.ndarray) -> OMEGAState:
        """
        ohlcv: np.ndarray shape (N,5) com colunas [O,H,L,C,V]; N deve ser alinhado e >= min_samples.
        """
        cfg = self.cfg
        if ohlcv.ndim != 2 or ohlcv.shape[1] < 5:
            return OMEGAState(MarketRegime.INSUFFICIENT_DATA, 0.0, "NEUTRAL", False, {"error": "bad_shape"})

        if len(ohlcv) < max(cfg.min_samples_z, cfg.min_samples_hfd):
            return OMEGAState(MarketRegime.INSUFFICIENT_DATA, 0.0, "NEUTRAL", False, {"error": "short_series"})

        # Extrai OHLC e Volume
        prices = ohlcv[:, :4]
        volumes = ohlcv[:, 4]

        # Sanitização
        if np.any(~np.isfinite(prices)) or np.any(~np.isfinite(volumes)):
            return OMEGAState(MarketRegime.INSUFFICIENT_DATA, 0.0, "NEUTRAL", False, {"error": "nan_values"})

        o, h, l, c = prices[-1]

        # 1) Macro Fractal
        hfd = self.compute_higuchi(prices[:, 3])

        # 2) Micro V-Flow
        v_flow = self.analyze_v_flow(prices, volumes)
        if not v_flow.get("valid", False):
            return OMEGAState(MarketRegime.INSUFFICIENT_DATA, 0.0, "NEUTRAL", False, {"error": "vflow_invalid"})

        # 3) Heikin Ashi Commander
        vol_window_mean = np.mean(volumes[-cfg.min_samples_z :])
        ha_info = self.compute_ha_commander(o, h, l, c, volumes[-1], vol_window_mean)

        # Scoring
        score = 0
        if hfd < cfg.hfd_threshold:
            score += 25
        if v_flow["is_panic"]:
            score += 25
        wick_ok = (v_flow["wick_ratio_avg"] > cfg.wick_ratio_min) and (v_flow["wick_norm"] > 0.5)
        if wick_ok:
            score += 25
        if ha_info["is_command"]:
            score += 25

        # Regime
        if score >= 90:
            regime = MarketRegime.COMMAND_INERTIA
            aggressive = True
        elif score >= 60:
            regime = MarketRegime.V_FLOW_ABSORPTION
            aggressive = False  # liberar só com risco externo aprovado
        elif score >= 40 and hfd < cfg.hfd_threshold:
            regime = MarketRegime.STRUCTURAL_TREND
            aggressive = False
        else:
            regime = MarketRegime.CHOPPY_NOISE
            aggressive = False

        details = {
            "hfd": hfd,
            "z_price": v_flow["z_price"],
            "z_vol": v_flow["z_vol"],
            "wick_ratio": v_flow["wick_ratio"],
            "wick_ratio_avg": v_flow["wick_ratio_avg"],
            "wick_norm": v_flow["wick_norm"],
            "atr": v_flow["atr"],
            "ha_bias": ha_info["bias"],
            "ha_vol_ok": ha_info["vol_ok"],
            "raw_score": score,
        }

        return OMEGAState(
            regime=regime,
            signal_strength=score / 100.0,
            bias=ha_info["bias"],
            is_aggressive_allowed=aggressive,
            details=details,
        )


# --------------- Execução de diagnóstico ---------------
if __name__ == "__main__":
    # Mock simples para teste rápido
    np.random.seed(42)
    closes = np.cumsum(np.random.normal(0, 1, 300)) + 2000
    highs = closes + np.random.uniform(0.1, 1.0, 300)
    lows = closes - np.random.uniform(0.1, 1.0, 300)
    opens = closes + np.random.uniform(-0.5, 0.5, 300)
    vols = np.random.lognormal(mean=6, sigma=0.5, size=300)

    ohlcv = np.column_stack([opens, highs, lows, closes, vols])

    kernel = OMEGAKernelV51Refined()
    state = kernel.engine_step(ohlcv)
    logger.info("State: %s | Strength: %.2f | Bias: %s | Aggressive: %s | details=%s",
                state.regime.name, state.signal_strength, state.bias,
                state.is_aggressive_allowed, state.details)
