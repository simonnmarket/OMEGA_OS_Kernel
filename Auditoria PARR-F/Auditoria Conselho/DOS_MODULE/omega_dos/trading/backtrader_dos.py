"""
Backtrader + DOS-TRADING — integração opcional (especificação Conselho).

Requer: pip install "omega-dos[backtrader]"
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _require_backtrader():
    try:
        import backtrader as bt  # noqa: F401
    except ImportError as e:
        raise RuntimeError("Instale dependência opcional: pip install 'omega-dos[backtrader]'") from e
    return __import__("backtrader", fromlist=["*"])


def run_backtrader_mt5(
    csv_path: str,
    *,
    initial_cash: float = 1_000_000.0,
    commission: float = 0.0001,
) -> Dict[str, Any]:
    """Executa cerebro Backtrader com estratégia DOS e analisador de métricas."""
    bt = _require_backtrader()

    class DOSTradingStrategy(bt.Strategy):
        params = (("size", 100_000), ("sl_pct", 0.01), ("tp_pct", 0.018), ("min_strength", 0.6))

        def __init__(self) -> None:
            self.signals: List[Dict[str, Any]] = []
            self.layer1 = bt.indicators.SMA(self.data.close, period=5)
            self.layer2 = bt.indicators.RSI(self.data.close, period=14)
            self.layer3_vol = bt.indicators.StdDev(self.data.close, period=20)

        def next(self) -> None:
            price_signal = 1 if self.data.close[0] > self.layer1[0] else -1
            rsi_signal = 1 if self.layer2[0] < 30 else -1 if self.layer2[0] > 70 else 0
            vol_regime = "high" if self.layer3_vol[0] > 0.015 else "low"
            adaptive_filter = 0.7 if vol_regime == "high" else 0.6
            composite = price_signal * 0.4 + rsi_signal * 0.3 + (1 if vol_regime == "low" else 0) * 0.3
            signal_strength = abs(composite)
            if signal_strength >= adaptive_filter and not self.position:
                direction = 1 if composite > 0 else -1
                size = self.p.size / self.data.close[0]
                if direction > 0:
                    self.buy(size=size)
                else:
                    self.sell(size=size)
                self.signals.append(
                    {
                        "bar": len(self.data),
                        "time": self.data.datetime.date(0),
                        "strength": signal_strength,
                        "direction": direction,
                        "regime": vol_regime,
                        "entry": float(self.data.close[0]),
                    }
                )

    class DOSAnalyzer(bt.Analyzer):
        def __init__(self) -> None:
            self.pnl_series: List[float] = []

        def notify_trade(self, trade) -> None:  # type: ignore[no-untyped-def]
            if trade.isclosed:
                self.pnl_series.append(float(trade.pnlcomm))

        def get_analysis(self) -> Dict[str, Any]:
            pnls = np.array(self.pnl_series, dtype=float)
            if pnls.size == 0:
                return {"var_95_usd": 0.0, "raroc_pct": 0.0, "sharpe_ratio": 0.0, "profit_factor": 0.0}
            var_95 = float(-np.percentile(pnls, 5))
            tail = pnls[pnls <= -var_95]
            cvar_95 = float(-tail.mean()) if tail.size else 0.0
            exposure = 100_000.0
            capital_charge = exposure * 0.08
            risk_capital = 1_000_000.0 + capital_charge
            raroc = float(pnls.sum() / risk_capital * 100.0)
            pos = pnls[pnls > 0]
            neg = pnls[pnls <= 0]
            pf = float(pos.sum() / abs(neg.sum())) if neg.size else float("inf")
            sharpe = float(np.mean(pnls) / np.std(pnls, ddof=1) * np.sqrt(252)) if np.std(pnls, ddof=1) > 0 else 0.0
            return {
                "total_trades": int(pnls.size),
                "profit_factor": pf,
                "var_95_usd": var_95,
                "cvar_95_usd": cvar_95,
                "raroc_pct": raroc,
                "sharpe_ratio": sharpe,
            }

    cerebro = bt.Cerebro()
    df = pd.read_csv(csv_path, parse_dates=["time"], index_col="time")
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(DOSTradingStrategy)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(DOSAnalyzer, _name="dos")
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    logger.info("Backtrader + DOS iniciado | %s", csv_path)
    results = cerebro.run()
    strat = results[0]
    dos_metrics = strat.analyzers.dos.get_analysis()
    return {
        "final_value": float(cerebro.broker.getvalue()),
        "dos": dos_metrics,
    }
