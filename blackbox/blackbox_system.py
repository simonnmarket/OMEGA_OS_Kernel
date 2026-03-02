"""
Blackbox System – Liquidity Zones, Traps, and Absorption (Python scaffold)

Fuses the two MQL snippets into a lightweight, dependency-free Python
pipeline:
- Liquidity zones and traps (rejection, sweep, fake breakout)
- Absorption pattern (price up with falling volume)
- Benchmark (buy&hold/MA cross) and performance metrics

Replace thresholds/heuristics with calibrated values when you have data.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class Config:
    lookback: int = 100
    vol_z_threshold: float = 2.0
    vol_percentile: float = 95.0
    min_price_change: float = 0.0005
    min_confidence: float = 0.2
    max_history: int = 5000


@dataclass
class Zone:
    price: float
    volume: float
    timestamp: float


@dataclass
class Signal:
    direction: int  # 1 buy, -1 sell, 0 none
    confidence: float
    reason: str
    price: Optional[float] = None


@dataclass
class Metrics:
    trades: int
    win_rate: float
    expectancy: float
    profit_factor: float
    sharpe: float
    sortino: float
    max_drawdown: float
    total_return: float
    alpha_total: Optional[float] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def mean(x: List[float]) -> float:
    return sum(x) / len(x) if x else 0.0


def std(x: List[float]) -> float:
    if len(x) < 2:
        return 0.0
    m = mean(x)
    var = sum((v - m) ** 2 for v in x) / (len(x) - 1)
    return var ** 0.5


def percentile(x: List[float], p: float) -> float:
    if not x:
        return 0.0
    xs = sorted(x)
    k = int(len(xs) * p / 100.0)
    k = min(max(k, 0), len(xs) - 1)
    return xs[k]


def max_drawdown(eq: List[float]) -> float:
    peak = -1e9
    dd = 0.0
    for v in eq:
        if v > peak:
            peak = v
        dd = min(dd, (v - peak) / peak if peak > 0 else 0.0)
    return dd


# ---------------------------------------------------------------------------
# Core system
# ---------------------------------------------------------------------------
class BlackboxSystem:
    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or Config()
        self.prices: List[float] = []
        self.volumes: List[float] = []
        self.timestamps: List[float] = []
        self.liquidity_zones: List[Zone] = []
        self.trade_returns: List[float] = []
        self.benchmark_returns: List[float] = []

    # --- Data update ---
    def update_bar(self, bar: Dict[str, Any]) -> None:
        """
        bar: dict with keys 'close','open','high','low','volume','time' (epoch seconds)
        """
        if not bar or "close" not in bar:
            return
        close = float(bar.get("close", 0.0))
        volume = float(bar.get("volume", 0.0))
        ts = float(bar.get("time", time.time()))
        self.prices.append(close)
        self.volumes.append(volume)
        self.timestamps.append(ts)

        if len(self.prices) > self.cfg.max_history:
            self.prices = self.prices[-self.cfg.max_history:]
            self.volumes = self.volumes[-self.cfg.max_history:]
            self.timestamps = self.timestamps[-self.cfg.max_history:]

    # --- Detection logic ---
    def _volume_zscore(self) -> float:
        if len(self.volumes) < self.cfg.lookback:
            return 0.0
        window = self.volumes[-self.cfg.lookback:]
        mv = mean(window)
        sv = std(window)
        return (window[-1] - mv) / sv if sv > 0 else 0.0

    def _volume_percentile(self) -> float:
        if len(self.volumes) < self.cfg.lookback:
            return 0.0
        return percentile(self.volumes[-self.cfg.lookback:], self.cfg.vol_percentile)

    def detect_liquidity_zone(self) -> Optional[Zone]:
        if len(self.prices) < self.cfg.lookback:
            return None
        z = self._volume_zscore()
        perc = self._volume_percentile()
        last_vol = self.volumes[-1]
        price = self.prices[-1]
        if (z >= self.cfg.vol_z_threshold) or (last_vol >= perc):
            zone = Zone(price=price, volume=last_vol, timestamp=self.timestamps[-1])
            self.liquidity_zones.append(zone)
            return zone
        return None

    def check_rejection(self, zone_price: float) -> bool:
        if len(self.prices) < 2:
            return False
        high = max(self.prices[-2], self.prices[-1])
        low = min(self.prices[-2], self.prices[-1])
        return low <= zone_price <= high

    def check_sweep(self) -> bool:
        if len(self.prices) < 2:
            return False
        prev_close = self.prices[-2]
        curr_close = self.prices[-1]
        return abs(curr_close - prev_close) > self.cfg.min_price_change

    def check_trap(self, zone_price: float) -> bool:
        if len(self.prices) < 2:
            return False
        prev_close = self.prices[-2]
        curr_close = self.prices[-1]
        return (curr_close > zone_price and prev_close < zone_price) or (curr_close < zone_price and prev_close > zone_price)

    def check_absorption(self) -> bool:
        if len(self.prices) < 2:
            return False
        curr_close = self.prices[-1]
        prev_close = self.prices[-2]
        curr_vol = self.volumes[-1] if self.volumes else 0.0
        prev_vol = self.volumes[-2] if len(self.volumes) > 1 else curr_vol
        price_up = curr_close > prev_close
        vol_down = curr_vol < prev_vol
        price_change = curr_close - prev_close
        return price_up and vol_down and price_change >= self.cfg.min_price_change

    # --- Signal logic ---
    def generate_signal(self) -> Signal:
        zone = self.liquidity_zones[-1] if self.liquidity_zones else None
        zone_hit = False
        if zone:
            zone_hit = self.check_rejection(zone.price)
        sweep = self.check_sweep()
        trap = zone and self.check_trap(zone.price)
        absorption = self.check_absorption()

        conf = 0.0
        reasons = []
        if zone_hit:
            conf += 0.3
            reasons.append("zone_hit")
        if sweep:
            conf += 0.2
            reasons.append("sweep")
        if trap:
            conf += 0.3
            reasons.append("trap")
        if absorption:
            conf += 0.4
            reasons.append("absorption")

        if conf < self.cfg.min_confidence:
            return Signal(direction=0, confidence=conf, reason="low_confidence", price=self.prices[-1] if self.prices else None)

        direction = 1 if (absorption or trap) else 0
        return Signal(direction=direction, confidence=min(conf, 1.0),
                      reason="+".join(reasons), price=self.prices[-1] if self.prices else None)

    # --- Benchmark and returns ---
    def latest_return(self) -> Optional[float]:
        if len(self.prices) < 2:
            return None
        return (self.prices[-1] - self.prices[-2]) / self.prices[-2]

    def compute_benchmark_ret(self, bench_type: str = "buy_hold",
                              ma_fast: int = 12, ma_slow: int = 48) -> Optional[float]:
        pr = self.latest_return()
        if pr is None:
            return None
        if bench_type == "buy_hold":
            return pr
        if bench_type == "ma_cross":
            if len(self.prices) < ma_slow:
                return None
            ma_f = sum(self.prices[-ma_fast:]) / ma_fast
            ma_s = sum(self.prices[-ma_slow:]) / ma_slow
            dirn = 1.0 if ma_f > ma_s else -1.0
            return dirn * pr
        return None

    # --- Metrics ---
    def record_trade_return(self, ret: float, bench_ret: Optional[float] = None) -> None:
        self.trade_returns.append(ret)
        if len(self.trade_returns) > self.cfg.max_history:
            self.trade_returns = self.trade_returns[-self.cfg.max_history:]
        if bench_ret is not None:
            self.benchmark_returns.append(bench_ret)
            if len(self.benchmark_returns) > self.cfg.max_history:
                self.benchmark_returns = self.benchmark_returns[-self.cfg.max_history:]

    def compute_metrics(self) -> Metrics:
        r = self.trade_returns
        if not r:
            return Metrics(0, 0, 0, float("inf"), 0, 0, 0, 0)
        wins = [x for x in r if x > 0]
        losses = [x for x in r if x < 0]
        win_rate = len(wins) / len(r) if r else 0.0
        avg_win = mean(wins) if wins else 0.0
        avg_loss = abs(mean(losses)) if losses else 0.0
        expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss
        profit_factor = (sum(wins) / abs(sum(losses))) if losses else float("inf")
        mean_ret = mean(r)
        std_ret = std(r)
        sharpe = (mean_ret / std_ret) * (len(r) ** 0.5) if std_ret > 0 else 0.0
        downside = std([x for x in r if x < 0])
        sortino = (mean_ret / downside) * (len(r) ** 0.5) if downside > 0 else 0.0
        eq = []
        acc = 1.0
        for x in r:
            acc *= (1 + x)
            eq.append(acc)
        max_dd = max_drawdown(eq)

        alpha_total = None
        if self.benchmark_returns:
            bench_acc = 1.0
            for x in self.benchmark_returns:
                bench_acc *= (1 + x)
            alpha_total = (acc - 1.0) - (bench_acc - 1.0)

        return Metrics(
            trades=len(r),
            win_rate=win_rate,
            expectancy=expectancy,
            profit_factor=profit_factor,
            sharpe=sharpe,
            sortino=sortino,
            max_drawdown=max_dd,
            total_return=acc - 1.0,
            alpha_total=alpha_total,
        )

    # --- Export ---
    def export_metrics(self, path: str) -> None:
        metrics = asdict(self.compute_metrics())
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)


# ---------------------------------------------------------------------------
# Example usage (pseudo)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cfg = Config()
    bb = BlackboxSystem(cfg)

    # Dummy bars
    bars = [
        {"close": 1.0, "open": 1.0, "high": 1.0, "low": 1.0, "volume": 1000, "time": time.time()},
        {"close": 1.002, "open": 1.0, "high": 1.003, "low": 0.999, "volume": 1500, "time": time.time()+60},
        {"close": 1.001, "open": 1.002, "high": 1.004, "low": 1.0, "volume": 800, "time": time.time()+120},
    ]

    for b in bars:
        bb.update_bar(b)
        bb.detect_liquidity_zone()
        sig = bb.generate_signal()
        if sig.direction != 0:
            bench = bb.compute_benchmark_ret()
            bb.record_trade_return(0.001, bench_ret=bench)
        print("Signal:", sig)

    bb.export_metrics("blackbox_metrics.json")
    print("Metrics:", bb.compute_metrics())
