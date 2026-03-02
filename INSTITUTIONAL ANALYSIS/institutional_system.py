"""
Institutional Analysis – Python Integration (consolidated from 11 parts)

Minimal, dependency-light scaffold to run an institutional analysis pipeline:
- Smart money / liquidity / flow analysis (placeholders with clear interfaces)
- Risk management (exposure, daily limits, drawdown guard)
- Monitoring and reporting hooks
- Central orchestrator with a per-tick pipeline

Notes:
- No external dependencies required (stdlib only). Pandas/NumPy can be added later if needed.
- No look-ahead: all processing is stateful and uses only current/past inputs.
- Replace TODOs with your concrete logic/models.
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
class SmartMoneyState:
    entry_zones: List[float] = field(default_factory=list)
    exit_zones: List[float] = field(default_factory=list)
    stop_zones: List[float] = field(default_factory=list)
    is_accumulating: bool = False
    is_distributing: bool = False
    confidence: float = 0.0


@dataclass
class LiquidityState:
    buy_liquidity: List[float] = field(default_factory=list)
    sell_liquidity: List[float] = field(default_factory=list)
    voids: List[float] = field(default_factory=list)
    pools: List[float] = field(default_factory=list)
    is_liquidity_driven: bool = False
    strength: float = 0.0


@dataclass
class FlowState:
    large_orders: List[float] = field(default_factory=list)
    absorption: float = 0.0
    distribution: float = 0.0
    is_institutional: bool = False
    last_update_ms: int = 0


@dataclass
class InstitutionalData:
    smart: SmartMoneyState = field(default_factory=SmartMoneyState)
    liquidity: LiquidityState = field(default_factory=LiquidityState)
    flow: FlowState = field(default_factory=FlowState)


@dataclass
class RiskControl:
    max_risk_per_trade: float = 0.01  # fraction of equity
    max_daily_loss_limit: float = 0.05      # fraction of equity
    current_exposure: float = 0.0     # fraction of equity
    risk_multiplier: float = 1.0
    is_risk_exceeded: bool = False


@dataclass
class PositionOptimizer:
    optimal_size: float = 0.0
    optimal_entry: float = 0.0
    optimal_stop: float = 0.0
    optimal_target: float = 0.0
    is_optimized: bool = False


@dataclass
class CapitalProtection:
    max_drawdown: float = 0.15  # fraction of equity
    current_drawdown: float = 0.0
    safety_buffer: float = 0.0
    is_protection_active: bool = False
    last_check_ms: int = 0


@dataclass
class InstitutionalRisk:
    control: RiskControl = field(default_factory=RiskControl)
    position: PositionOptimizer = field(default_factory=PositionOptimizer)
    protection: CapitalProtection = field(default_factory=CapitalProtection)


@dataclass
class RiskMetrics:
    exposure: float
    drawdown: float
    risk_multiplier: float
    is_protection_active: bool


@dataclass
class SystemState:
    is_initialized: bool = False
    is_running: bool = False
    is_paused: bool = False
    is_error: bool = False
    last_update_ms: int = 0
    error_count: int = 0


@dataclass
class Signal:
    direction: int  # 1 buy, -1 sell, 0 neutral
    confidence: float
    entry: Optional[float] = None
    stop: Optional[float] = None
    target: Optional[float] = None
    reason: str = ""


@dataclass
class Config:
    # Smart money / liquidity
    min_order_size: float = 100.0
    accumulation_period: int = 20
    confidence_threshold: float = 0.85
    use_adaptive_thresholds: bool = True
    liquidity_threshold: float = 1.5
    void_detection_period: int = 10
    pool_strength_min: float = 0.75
    track_historical_pools: bool = True
    # Risk
    max_risk_per_trade: float = 0.01
    max_daily_loss_limit: float = 0.05  # fraction of equity as max loss per day
    max_drawdown: float = 0.15
    # Execution
    max_error_count: int = 5
    # Benchmark / metrics
    enable_metrics: bool = True
    benchmark_type: str = "buy_hold"  # or "ma_cross"
    ma_fast: int = 12
    ma_slow: int = 48


# ---------------------------------------------------------------------------
# Components (placeholders with clear interfaces)
# ---------------------------------------------------------------------------
class InstitutionalAnalysis:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.data = InstitutionalData()
        self._prices: List[float] = []
        self._volumes: List[float] = []

    def initialize(self) -> bool:
        # TODO: load models/resources; validate dependencies (PVSRA/OrderFlow)
        return True

    def update_market_data(self, tick: Dict[str, Any]) -> None:
        price = tick.get("mid") or tick.get("close") or ((tick.get("bid", 0) + tick.get("ask", 0)) / 2)
        volume = float(tick.get("volume", 0.0) or 0.0)
        if price is None:
            return
        self._prices.append(price)
        self._volumes.append(volume)
        # keep a rolling window for efficiency
        max_len = 5000
        if len(self._prices) > max_len:
            self._prices = self._prices[-max_len:]
            self._volumes = self._volumes[-max_len:]

    def process_institutional_analysis(self) -> None:
        if len(self._prices) < max(20, self.cfg.accumulation_period):
            return
        # simple volume z-score for smart money detection
        vols = self._volumes[-self.cfg.accumulation_period:]
        mean_v = sum(vols) / len(vols)
        std_v = (sum((v - mean_v) ** 2 for v in vols) / max(1, len(vols) - 1)) ** 0.5
        z = 0.0
        if std_v > 0:
            z = (vols[-1] - mean_v) / std_v
        is_acc = z > 2.0
        self.data.smart.is_accumulating = is_acc
        self.data.smart.is_distributing = False if is_acc else z < -2.0
        self.data.smart.confidence = min(1.0, abs(z) / 3.0)

    def update_integrated_analysis(self) -> None:
        # TODO: integrate external signals (PVSRA, order flow)
        pass

    def execute_analysis(self) -> Signal:
        if len(self._prices) < 2:
            return Signal(direction=0, confidence=0.0, reason="not_enough_data")
        price_now = self._prices[-1]
        price_prev = self._prices[-2]
        momentum = price_now - price_prev
        z_conf = self.data.smart.confidence
        if self.data.smart.is_accumulating and momentum > 0:
            return Signal(direction=1, confidence=z_conf, entry=price_now, reason="smart_money_accum+mom_up")
        if self.data.smart.is_distributing and momentum < 0:
            return Signal(direction=-1, confidence=z_conf, entry=price_now, reason="smart_money_dist+mom_down")
        return Signal(direction=0, confidence=0.0, reason="neutral")

    def latest_price(self) -> Optional[float]:
        return self._prices[-1] if self._prices else None

    def latest_return(self) -> Optional[float]:
        if len(self._prices) < 2:
            return None
        return (self._prices[-1] - self._prices[-2]) / self._prices[-2]

    def ma_values(self, fast: int, slow: int) -> Optional[tuple]:
        if len(self._prices) < slow:
            return None
        ma_fast = sum(self._prices[-fast:]) / fast
        ma_slow = sum(self._prices[-slow:]) / slow
        return ma_fast, ma_slow


class InstitutionalML:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def initialize(self) -> bool:
        # TODO: load ML models, scaler, etc.
        return True

    def score(self, features: Dict[str, Any]) -> float:
        # TODO: return probability/score from ML model
        return 0.0


class InstitutionalMonitor:
    def __init__(self):
        self.health: Dict[str, Any] = {}

    def initialize(self) -> bool:
        return True

    def update(self, state: SystemState, risk: InstitutionalRisk) -> None:
        self.health["timestamp_ms"] = int(time.time() * 1000)
        self.health["is_running"] = state.is_running
        self.health["risk_exceeded"] = risk.control.is_risk_exceeded


class InstitutionalReporting:
    def __init__(self):
        self.snapshots: List[Dict[str, Any]] = []
        self.max_snapshots: int = 5000  # avoid unbounded growth
        self.trade_returns: List[float] = []  # realized trade returns for metrics
        self.benchmark_returns: List[float] = []  # baseline returns for comparison

    def initialize(self) -> bool:
        return True

    def snapshot(self, state: SystemState, risk: InstitutionalRisk, signal: Signal,
                 trade_ret: Optional[float]=None, bench_ret: Optional[float]=None) -> None:
        snap = {
            "ts_ms": int(time.time() * 1000),
            "state": asdict(state),
            "risk": {
                "exposure": risk.control.current_exposure,
                "drawdown": risk.protection.current_drawdown,
                "risk_multiplier": risk.control.risk_multiplier,
                "protection": risk.protection.is_protection_active,
            },
            "signal": asdict(signal),
        }
        self.snapshots.append(snap)
        if len(self.snapshots) > self.max_snapshots:
            # drop oldest to avoid memory blow-up
            self.snapshots = self.snapshots[-self.max_snapshots:]
        if trade_ret is not None:
            self.trade_returns.append(trade_ret)
            if len(self.trade_returns) > self.max_snapshots:
                self.trade_returns = self.trade_returns[-self.max_snapshots:]
        if bench_ret is not None:
            self.benchmark_returns.append(bench_ret)
            if len(self.benchmark_returns) > self.max_snapshots:
                self.benchmark_returns = self.benchmark_returns[-self.max_snapshots:]

    def to_json(self) -> str:
        return json.dumps(self.snapshots, indent=2)

    # --- Metrics on realized trade returns (decimal returns) ---
    @staticmethod
    def _mean(x: List[float]) -> float:
        return sum(x) / len(x) if x else 0.0

    @staticmethod
    def _std(x: List[float]) -> float:
        if len(x) < 2:
            return 0.0
        m = sum(x) / len(x)
        var = sum((v - m) ** 2 for v in x) / (len(x) - 1)
        return var ** 0.5

    @staticmethod
    def _max_drawdown(equity_curve: List[float]) -> float:
        peak = -1e9
        dd = 0.0
        for v in equity_curve:
            if v > peak:
                peak = v
            dd = min(dd, (v - peak) / peak if peak > 0 else 0.0)
        return dd

    def compute_metrics(self, benchmark: Optional[List[float]] = None) -> Dict[str, Any]:
        """Compute Sharpe, Sortino, expectancy, win rate, profit factor, max drawdown."""
        r = self.trade_returns
        if not r:
            return {}

        wins = [x for x in r if x > 0]
        losses = [x for x in r if x < 0]
        win_rate = len(wins) / len(r) if r else 0.0
        avg_win = self._mean(wins) if wins else 0.0
        avg_loss = abs(self._mean(losses)) if losses else 0.0
        expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss

        profit_factor = (sum(wins) / abs(sum(losses))) if losses else float("inf")
        mean_ret = self._mean(r)
        std_ret = self._std(r)
        sharpe = (mean_ret / std_ret) * (len(r) ** 0.5) if std_ret > 0 else 0.0
        downside = self._std([x for x in r if x < 0])
        sortino = (mean_ret / downside) * (len(r) ** 0.5) if downside > 0 else 0.0

        eq = []
        acc = 1.0
        for x in r:
            acc *= (1 + x)
            eq.append(acc)
        max_dd = self._max_drawdown(eq)

        metrics = {
            "trades": len(r),
            "win_rate": win_rate,
            "expectancy": expectancy,
            "profit_factor": profit_factor,
            "sharpe": sharpe,
            "sortino": sortino,
            "max_drawdown": max_dd,
            "total_return": acc - 1.0 if eq else 0.0,
        }

        bench = benchmark if benchmark is not None else self.benchmark_returns
        if bench:
            bench_acc = 1.0
            for x in bench:
                bench_acc *= (1 + x)
            metrics["alpha_total"] = metrics["total_return"] - (bench_acc - 1.0)

        return metrics


class InstitutionalRiskManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.risk = InstitutionalRisk()
        self.risk.control.max_risk_per_trade = cfg.max_risk_per_trade
        self.risk.control.max_daily_loss_limit = cfg.max_daily_loss_limit
        self.risk.protection.max_drawdown = cfg.max_drawdown
        self._peak_equity: float = 0.0
        self._daily_pnl: float = 0.0
        self._current_date: Optional[str] = None

    def validate_risk_state(self) -> bool:
        return not self.risk.control.is_risk_exceeded and not self.risk.protection.is_protection_active

    def update_exposure(self, position_value: float, equity: float) -> None:
        if equity <= 0:
            self.risk.control.current_exposure = 0.0
            return
        # Exposição percentual do portfólio (notional/equity), não comparada a max_daily_loss_limit
        self.risk.control.current_exposure = position_value / equity
        # Atualiza pico de equity e drawdown
        if self._peak_equity <= 0:
            self._peak_equity = equity
        self._peak_equity = max(self._peak_equity, equity)
        self.risk.protection.current_drawdown = (
            (self._peak_equity - equity) / self._peak_equity if self._peak_equity > 0 else 0.0
        )

    def update_daily_pnl(self, realized_pnl: float) -> None:
        self._daily_pnl += realized_pnl

    def reset_daily_limits(self, today: str) -> None:
        self._daily_pnl = 0.0
        self._current_date = today

    def check_limits(self, equity: float) -> None:
        # Limite diário por perda (pnl realizado) em valor monetário
        loss_limit_cash = equity * self.cfg.max_daily_loss_limit if equity > 0 else 0.0
        if self._daily_pnl < 0 and loss_limit_cash > 0 and abs(self._daily_pnl) >= loss_limit_cash:
            self.risk.control.is_risk_exceeded = True
        # Drawdown absoluto
        if self.risk.protection.current_drawdown > self.cfg.max_drawdown:
            self.risk.protection.is_protection_active = True

    def optimize_position(self, price: float, equity: float) -> PositionOptimizer:
        """Basic sizing using risk_per_trade and a default 0.5% price stop."""
        po = PositionOptimizer()
        if price <= 0 or equity <= 0:
            return po
        stop_dist = 0.005 * price  # 0.5% do preço
        risk_amt = equity * self.cfg.max_risk_per_trade
        if stop_dist <= 0:
            return po
        size = risk_amt / stop_dist
        po.optimal_size = max(0.0, size)
        po.optimal_entry = price
        po.optimal_stop = price - stop_dist
        po.optimal_target = price + 2 * stop_dist
        po.is_optimized = True
        self.risk.position = po
        return po

    def metrics(self) -> RiskMetrics:
        return RiskMetrics(
            exposure=self.risk.control.current_exposure,
            drawdown=self.risk.protection.current_drawdown,
            risk_multiplier=self.risk.control.risk_multiplier,
            is_protection_active=self.risk.protection.is_protection_active,
        )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------
class InstitutionalSystem:
    def __init__(self, cfg: Optional[Config] = None):
        self.cfg = cfg or Config()
        self.state = SystemState()
        self.analysis = InstitutionalAnalysis(self.cfg)
        self.ml = InstitutionalML(self.cfg)
        self.monitor = InstitutionalMonitor()
        self.reporting = InstitutionalReporting()
        self.risk_manager = InstitutionalRiskManager(self.cfg)

    def initialize(self) -> bool:
        ok = (
            self.analysis.initialize()
            and self.ml.initialize()
            and self.monitor.initialize()
            and self.reporting.initialize()
        )
        self.state.is_initialized = ok
        self.state.is_running = ok
        return ok

    def _compute_benchmark_ret(self) -> Optional[float]:
        """Compute benchmark return based on config (buy_hold or ma_cross)."""
        price_ret = self.analysis.latest_return()
        if price_ret is None:
            return None
        if self.cfg.benchmark_type == "buy_hold":
            return price_ret
        if self.cfg.benchmark_type == "ma_cross":
            ma_vals = self.analysis.ma_values(self.cfg.ma_fast, self.cfg.ma_slow)
            if ma_vals is None:
                return None
            ma_fast, ma_slow = ma_vals
            direction = 1.0 if ma_fast > ma_slow else -1.0
            return direction * price_ret
        return None

    def on_tick(self,
                tick: Dict[str, Any],
                position_value: float,
                equity: float,
                incremental_pnl: float = 0.0,
                trade_ret: Optional[float] = None,
                bench_ret: Optional[float] = None) -> Optional[Signal]:
        try:
            if not self.state.is_running:
                return None

            # Update time and risk
            self.state.last_update_ms = int(time.time() * 1000)
            # Reset diário automático
            today = time.strftime("%Y-%m-%d")
            if self.risk_manager._current_date is None:
                self.risk_manager._current_date = today
            elif self.risk_manager._current_date != today:
                self.risk_manager.reset_daily_limits(today)

            # Update daily PnL (incremental PnL for the last fill)
            if incremental_pnl != 0.0:
                self.risk_manager.update_daily_pnl(incremental_pnl)
            self.risk_manager.update_exposure(position_value, equity)
            self.risk_manager.check_limits(equity)
            if not self.risk_manager.validate_risk_state():
                self.state.is_error = True
                return None

            # Market data and analysis
            self.analysis.update_market_data(tick)
            self.analysis.process_institutional_analysis()
            self.analysis.update_integrated_analysis()
            signal = self.analysis.execute_analysis()

            # Optional: ML score to refine confidence
            # signal.confidence = max(signal.confidence, self.ml.score(features={})), etc.

            # Reporting & monitoring
            self.monitor.update(self.state, self.risk_manager.risk)
            bench_val = bench_ret if bench_ret is not None else self._compute_benchmark_ret()
            self.reporting.snapshot(self.state, self.risk_manager.risk, signal, trade_ret, bench_val)

            return signal
        except Exception as e:
            self.handle_error(e)
            return None

    def export_metrics(self, path: str) -> None:
        """Compute and export performance metrics to a JSON file."""
        bench = self.reporting.benchmark_returns if self.reporting.benchmark_returns else None
        metrics = self.reporting.compute_metrics(bench)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

    def handle_error(self, err: Exception) -> None:
        self.state.is_error = True
        self.state.error_count += 1
        if self.state.error_count > self.cfg.max_error_count:
            self.state.is_running = False


# ---------------------------------------------------------------------------
# Minimal example (pseudo)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    system = InstitutionalSystem()
    if not system.initialize():
        raise SystemExit("Initialization failed")

    # Example tick loop (replace with real feed)
    dummy_ticks = [
        {"bid": 1.0, "ask": 1.0, "volume": 1000, "time": time.time()},
        {"bid": 1.01, "ask": 1.011, "volume": 1200, "time": time.time() + 1},
    ]
    equity = 100_000.0
    position_value = 0.0

    for t in dummy_ticks:
        sig = system.on_tick(t, position_value, equity)
        print("Signal:", sig)

    print("Reports:\n", system.reporting.to_json())
