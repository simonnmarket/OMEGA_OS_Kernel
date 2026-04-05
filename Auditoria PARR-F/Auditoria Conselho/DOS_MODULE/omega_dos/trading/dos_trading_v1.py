"""
DOS-TRADING V1.0 — Refinamento Trading Tier-0
Alinhado a: DOC-OFC-DOS-TRADING-V1.0-20260405-001 (Especificação Conselho).

Camadas: (1) estrutura de preço, (2) microestrutura, (3) regime, (4) sinal composto.
Correções em relação ao texto-base: mapeamento vol_regime→filtros, `TradingSignal.direction`,
`symbol` explícito, logging opcional em ficheiro, divisão segura em métricas de tick.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from omega_dos.provenance import sha256_canonical

logger = logging.getLogger(__name__)

REQUIRED_OHLC = ("time", "open", "high", "low", "close")


def _configure_logging() -> None:
    if logger.handlers:
        return
    fmt = "%(asctime)s | %(levelname)-8s | %(message)s | %(funcName)s"
    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    log_path = os.getenv("DOS_LOG_FILE", "").strip()
    if log_path:
        try:
            handlers.insert(0, logging.FileHandler(log_path, encoding="utf-8"))
        except OSError:
            pass
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


@dataclass
class TradingSignal:
    timestamp: str
    symbol: str
    regime: str
    signal_strength: float
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    filter_passed: bool
    false_negative_risk: float
    direction: int
    vol_regime: str


class MarketRegime(Enum):
    TREND = "trend"
    RANGE = "range"
    BREAKOUT = "breakout"
    VOLATILE = "volatile"


class DOS_TRADING_V1:
    """
    Módulo de refinamento trading sobre ticks/barras MT5 (CSV).
    Integração FIN-SENSE: dados bronze/ingest podem alimentar a mesma estrutura OHLC
    via `load_mt5_data` ou DataFrame externo padronizado.
    """

    def __init__(self, mt5_csv_dir: str = "mt5_data/") -> None:
        _configure_logging()
        self.data_dir = Path(mt5_csv_dir)
        self.signals_log: List[TradingSignal] = []
        self.diagnosis_log: List[Dict[str, Any]] = []
        logger.info("DOS-TRADING V1.0 inicializado | Dados: %s", self.data_dir)

    def load_mt5_data(self, symbol: str = "XAUUSD", years: Optional[List[int]] = None) -> pd.DataFrame:
        """Camada 0: carrega CSVs `{symbol}_M1_{year}.csv` com validação mínima de schema/numéricos."""
        if years is None:
            years = [2024, 2025, 2026]
        dfs: List[pd.DataFrame] = []
        for year in years:
            csv_path = self.data_dir / f"{symbol}_M1_{year}.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path, parse_dates=["time"])
                missing = [c for c in REQUIRED_OHLC if c not in df.columns]
                if missing:
                    logger.warning("CSV %s faltam colunas: %s", csv_path, missing)
                    continue
                df = df.loc[:, REQUIRED_OHLC].copy()
                df["year"] = year
                # normaliza tipos numéricos
                for col in ("open", "high", "low", "close"):
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                dfs.append(df)
                logger.info("   %s ticks %s: %s", len(df), year, csv_path.name)
        if not dfs:
            logger.error("Nenhum ficheiro MT5 encontrado em %s", self.data_dir)
            return pd.DataFrame()
        data = pd.concat(dfs, ignore_index=True).sort_values("time")
        logger.info(
            "%s ticks carregados | periodo: %s -> %s",
            f"{len(data):,}",
            data["time"].min(),
            data["time"].max(),
        )
        return data

    @staticmethod
    def layer1_price_structure(data: pd.DataFrame) -> pd.DataFrame:
        """Camada 1: estrutura de preço OHLC."""
        df = data.copy()
        df["body_size"] = np.abs(df["close"] - df["open"])
        df["range_size"] = df["high"] - df["low"]
        df["body_ratio"] = df["body_size"] / df["range_size"].replace(0, np.nan)
        df["price_ma5"] = df["close"].rolling(5).mean()
        df["price_ma20"] = df["close"].rolling(20).mean()
        df["price_momentum"] = (df["close"] - df["price_ma20"]) / df["price_ma20"].replace(0, np.nan)
        return df

    @staticmethod
    def layer2_microstructure(data: pd.DataFrame) -> pd.DataFrame:
        """Camada 2: microestrutura (proxy spread, intervalo de ticks, volume proxy)."""
        df = data.copy()
        df["spread_bp"] = ((df["high"] - df["low"]) / df["close"].replace(0, np.nan)) * 10000
        df["spread_ma"] = df["spread_bp"].rolling(20).mean()
        tick_interval = df["time"].diff().dt.total_seconds()
        df["tick_interval"] = tick_interval
        inv_mean = 1.0 / tick_interval.rolling(100).mean().replace(0, np.nan)
        df["tick_velocity"] = inv_mean.replace([np.inf, -np.inf], np.nan)
        df["volume_proxy"] = df["range_size"] * df["body_size"]
        df["volume_ma"] = df["volume_proxy"].rolling(20).mean()
        return df

    @staticmethod
    def layer3_market_regime(data: pd.DataFrame) -> pd.DataFrame:
        """Camada 3: regime de volatilidade e classificação trend/range/breakout."""
        df = data.copy()
        df["volatility"] = df["close"].pct_change().rolling(20).std()
        df["vol_regime"] = pd.cut(
            df["volatility"],
            bins=[0.0, 0.005, 0.015, np.inf],
            labels=["low", "medium", "high"],
        )
        df["price_trend"] = np.sign(df["price_ma5"] - df["price_ma20"])
        df["range_bound"] = (df["high"].rolling(20).max() - df["low"].rolling(20).min()) / df["close"].replace(
            0, np.nan
        ) < 0.02
        df["regime"] = np.where(
            df["range_bound"],
            "range",
            np.where(df["price_trend"] != 0, "trend", "breakout"),
        )
        return df

    @staticmethod
    def layer4_signal_composition(data: pd.DataFrame) -> pd.DataFrame:
        """Camada 4: sinal composto com pesos empíricos da especificação."""
        df = data.copy()
        price_weight = 0.3
        micro_weight = 0.25
        regime_weight = 0.45
        df["signal_price"] = np.where(df["price_momentum"] > 0.002, 1, np.where(df["price_momentum"] < -0.002, -1, 0))
        q30 = df["spread_ma"].quantile(0.3)
        q30_safe = q30 if pd.notna(q30) else df["spread_ma"].median()
        df["signal_micro"] = np.where(
            (df["spread_ma"] < q30_safe) & (df["volume_proxy"] > df["volume_ma"]),
            1,
            0,
        )
        df["signal_regime"] = np.where(df["regime"] == "trend", df["price_trend"], 0)
        df["composite_signal"] = (
            df["signal_price"] * price_weight + df["signal_micro"] * micro_weight + df["signal_regime"] * regime_weight
        )
        df["signal_strength"] = np.abs(df["composite_signal"])
        df["direction"] = np.sign(df["composite_signal"])
        return df

    @staticmethod
    def adaptive_filters(vol_regime_label: Any) -> Dict[str, Any]:
        """Filtros por faixa de volatilidade (mapeia labels `low|medium|high`)."""
        filters = {
            "low_vol": {"min_strength": 0.5, "sl_pct": 0.008, "tp_pct": 0.015},
            "medium_vol": {"min_strength": 0.6, "sl_pct": 0.010, "tp_pct": 0.018},
            "high_vol": {"min_strength": 0.7, "sl_pct": 0.015, "tp_pct": 0.025},
        }
        key = str(vol_regime_label) if pd.notna(vol_regime_label) else "medium"
        mapping = {"low": "low_vol", "medium": "medium_vol", "high": "high_vol"}
        return filters[mapping.get(key, "medium_vol")]

    def generate_signals(
        self,
        data: pd.DataFrame,
        symbol: str,
        min_strength: float = 0.6,
    ) -> List[TradingSignal]:
        """Geração vetorizada de sinais (elimina iterrows e viés de performance)."""
        if data.empty or "vol_regime" not in data.columns:
            return []
        signals: List[TradingSignal] = []
        for vreg in data["vol_regime"].dropna().unique():
            regime_data = data[data["vol_regime"] == vreg].copy()
            rf = self.adaptive_filters(vreg)
            mask = (regime_data["signal_strength"] >= rf["min_strength"]) & (regime_data["direction"].abs() == 1)
            strong = regime_data.loc[mask]
            if strong.empty:
                continue
            direction = strong["direction"].astype(int)
            conf = (strong["signal_strength"] * 0.95).clip(upper=0.95)
            sl_pct = float(rf["sl_pct"])
            tp_pct = float(rf["tp_pct"])
            entry = strong["close"].astype(float)
            ts_iso = pd.to_datetime(strong["time"], utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            for i in range(len(strong)):
                signals.append(
                    TradingSignal(
                        timestamp=ts_iso.iloc[i],
                        symbol=symbol,
                        regime=str(strong["regime"].iloc[i]),
                        signal_strength=float(strong["signal_strength"].iloc[i]),
                        entry_price=float(entry.iloc[i]),
                        stop_loss=float(entry.iloc[i]) * (1 - sl_pct * direction.iloc[i]),
                        take_profit=float(entry.iloc[i]) * (1 + tp_pct * direction.iloc[i]),
                        confidence=float(conf.iloc[i]),
                        filter_passed=True,
                        false_negative_risk=1.0 - float(strong["signal_strength"].iloc[i]),
                        direction=int(direction.iloc[i]),
                        vol_regime=str(vreg),
                    )
                )
        logger.info("%s sinais gerados | min_strength ref=%s", len(signals), min_strength)
        return signals

    @staticmethod
    def diagnose_false_negatives(data: pd.DataFrame, signals: List[TradingSignal]) -> Dict[str, Any]:
        missed = data[data["signal_strength"] > 0.4]
        diagnosis: Dict[str, Any] = {
            "total_opportunities": int(len(missed)),
            "signals_generated": len(signals),
            "false_negatives": max(0, len(missed) - len(signals)),
            "fn_by_regime": {},
        }
        for reg in missed["regime"].dropna().unique():
            diagnosis["fn_by_regime"][str(reg)] = int(len(missed[missed["regime"] == reg]))
        return diagnosis

    def backtest_signals(
        self,
        signals: List[TradingSignal],
        data: pd.DataFrame,
        *,
        notional_usd: float = 100_000.0,
    ) -> Dict[str, Any]:
        """Backtest sem look-ahead: SL/TP bar-a-bar, saída no último close se nada aciona."""
        trades: List[Dict[str, Any]] = []
        if data.empty or not signals:
            return {
                "profit_factor": 0.0,
                "winrate_pct": 0.0,
                "max_dd_pct": 0.0,
                "total_trades": 0,
                "avg_pnl_pct": 0.0,
            }
        times = pd.to_datetime(data["time"], utc=True)
        for signal in signals:
            slippage = signal.entry_price * 0.00005
            entry = signal.entry_price + slippage * signal.direction
            bars_ahead = max(1, int(signal.confidence * 20))
            mask = times > pd.to_datetime(signal.timestamp, utc=True)
            future = data.loc[mask].head(bars_ahead)
            if future.empty:
                continue
            exit_price = None
            for row in future.itertuples():
                high = float(row.high)
                low = float(row.low)
                close = float(row.close)
                if signal.direction > 0:
                    if low <= signal.stop_loss:
                        exit_price = signal.stop_loss
                        break
                    if high >= signal.take_profit:
                        exit_price = signal.take_profit
                        break
                else:
                    if high >= signal.stop_loss:
                        exit_price = signal.stop_loss
                        break
                    if low <= signal.take_profit:
                        exit_price = signal.take_profit
                        break
                exit_price = close  # atualização provisória
            if exit_price is None:
                exit_price = float(future["close"].iloc[-1])
            pnl_pct = (exit_price - entry) / entry * signal.direction
            trades.append({"pnl_pct": pnl_pct, "pnl_usd": pnl_pct * notional_usd})
        if not trades:
            return {
                "profit_factor": 0.0,
                "winrate_pct": 0.0,
                "max_dd_pct": 0.0,
                "total_trades": 0,
                "avg_pnl_pct": 0.0,
            }
        tdf = pd.DataFrame(trades)
        wins = tdf[tdf["pnl_pct"] > 0]
        losses = tdf[tdf["pnl_pct"] <= 0]
        loss_sum = abs(losses["pnl_pct"].sum())
        pf = float(wins["pnl_pct"].sum() / loss_sum) if loss_sum > 0 else float("inf")
        winrate = len(wins) / len(tdf) * 100.0
        eq = (1.0 + tdf["pnl_pct"]).cumprod()
        roll_max = eq.cummax()
        dd = (eq / roll_max - 1.0).min()
        return {
            "profit_factor": round(pf, 4) if np.isfinite(pf) else 0.0,
            "winrate_pct": round(winrate, 2),
            "max_dd_pct": round(float(abs(dd)) * 100, 4),
            "total_trades": int(len(tdf)),
            "avg_pnl_pct": round(float(tdf["pnl_pct"].mean()), 6),
        }

    def run_full_pipeline(self, symbol: str = "XAUUSD") -> Dict[str, Any]:
        data = self.load_mt5_data(symbol)
        if data.empty:
            return {"status": "ERROR", "message": "Sem dados MT5", "inputs_sha256": None}
        missing = [c for c in REQUIRED_OHLC if c not in data.columns]
        if missing:
            return {
                "status": "ERROR",
                "message": f"Colunas OHLC em falta: {missing}",
                "inputs_sha256": None,
            }
        sub = data.loc[:, list(REQUIRED_OHLC)].copy()
        sub["time"] = pd.to_datetime(sub["time"], utc=True).astype(str)
        # digest incremental para evitar OOM
        h = hashlib.sha256()
        h.update(",".join(sub.columns).encode("utf-8"))
        chunk = 20_000
        for start in range(0, len(sub), chunk):
            h.update(sub.iloc[start : start + chunk].to_csv(index=False).encode("utf-8"))
        inputs_sha256 = h.hexdigest()
        data = self.layer1_price_structure(data)
        data = self.layer2_microstructure(data)
        data = self.layer3_market_regime(data)
        data = self.layer4_signal_composition(data)
        signals = self.generate_signals(data, symbol=symbol)
        diagnosis = self.diagnose_false_negatives(data, signals)
        backtest = self.backtest_signals(signals, data)
        report: Dict[str, Any] = {
            "status": "SUCCESS",
            "symbol": symbol,
            "signals_generated": len(signals),
            "diagnosis": diagnosis,
            "backtest": backtest,
            "pipeline_version": "1.0",
            "spec_id": "DOC-OFC-DOS-TRADING-V1.0-20260405-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs_sha256": inputs_sha256,
        }
        self.signals_log.extend(signals)
        self.diagnosis_log.append(report)
        return report


def main() -> Dict[str, Any]:
    """Ponto de entrada standalone (equivalente ao script da especificação)."""
    _configure_logging()
    logger.info("=== DOS-TRADING V1.0 TIER-0 ===")
    trader = DOS_TRADING_V1(os.getenv("DOS_MT5_DIR", "mt5_data/"))
    result = trader.run_full_pipeline("XAUUSD")
    print("\n" + "=" * 60)
    print("DOS-TRADING V1.0 — RESULTADOS")
    print("=" * 60)
    print("Status:", result.get("status"))
    print("Sinais:", result.get("signals_generated"))
    if result.get("status") == "SUCCESS":
        bt = result.get("backtest") or {}
        print("Profit Factor:", bt.get("profit_factor"))
        print("Winrate %:", bt.get("winrate_pct"))
        print("Falsos negativos (est.):", (result.get("diagnosis") or {}).get("false_negatives"))
        print("Timestamp:", str(result.get("timestamp", ""))[:19])
    return result


if __name__ == "__main__":
    main()
