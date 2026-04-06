"""
DOS-TRADING V1.0 — Refinamento Trading Tier-0 (HARDENED)
Alinhado a: DOC-OFC-DOS-TRADING-V1.0-20260405-001 (Especificação Conselho).
Versão: 2.0.0 — Hardening completo (Sprint 1-4).

Camadas: (1) estrutura de preço, (2) microestrutura, (3) regime, (4) sinal composto.
Hardening: Decimal para preços, logs JSON estruturados, bins configuráveis,
           slippage/custos configuráveis, validação rígida MT5, sanitização NaN/inf.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal, getcontext, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from omega_dos.provenance import sha256_canonical

# ---------------------------------------------------------------------------
# Precisão bancária (28 dígitos significativos)
# ---------------------------------------------------------------------------
getcontext().prec = 28

logger = logging.getLogger(__name__)

REQUIRED_OHLC = ("time", "open", "high", "low", "close")

# Limites de sanitização padrão (XAUUSD-centric; configuráveis)
_DEFAULT_PRICE_FLOOR = 0.0
_DEFAULT_PRICE_CEIL = 1_000_000.0


# ===========================================================================
# LOGGING JSON ESTRUTURADO
# ===========================================================================
class _JSONFormatter(logging.Formatter):
    """Formatter estruturado para observabilidade (ELK/Splunk/CloudWatch)."""

    _SENSITIVE = re.compile(r"(password|secret|dsn|pgpass|token)", re.IGNORECASE)

    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        # Masking de credenciais
        msg = self._SENSITIVE.sub("[REDACTED]", msg)
        entry = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "msg": msg,
            "trace_id": getattr(record, "trace_id", None),
            "correlation_id": getattr(record, "correlation_id", None),
        }
        return json.dumps(entry, default=str, ensure_ascii=False)


def _configure_logging() -> None:
    if logger.handlers:
        return
    use_json = os.getenv("DOS_LOG_JSON", "1").strip() in ("1", "true", "yes")
    handlers: List[logging.Handler] = []

    console = logging.StreamHandler(sys.stdout)
    if use_json:
        console.setFormatter(_JSONFormatter())
    else:
        console.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s | %(funcName)s"
        ))
    handlers.append(console)

    log_path = os.getenv("DOS_LOG_FILE", "").strip()
    if log_path:
        try:
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setFormatter(_JSONFormatter())
            handlers.insert(0, fh)
        except OSError:
            pass

    for h in handlers:
        logger.addHandler(h)
    logger.setLevel(logging.INFO)


# ===========================================================================
# DATA CLASSES — PRECISÃO DECIMAL
# ===========================================================================
@dataclass
class TradingSignal:
    """Sinal de trading com precisão Decimal para preços (compliance Goldman/BlackRock)."""
    timestamp: str
    symbol: str
    regime: str
    signal_strength: float          # estatístico — float OK
    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    confidence: float               # estatístico — float OK
    filter_passed: bool
    false_negative_risk: float      # estatístico — float OK
    direction: int
    vol_regime: str

    def to_audit_dict(self) -> Dict[str, Any]:
        """Serialização auditável com preços em string Decimal."""
        d = asdict(self)
        for k in ("entry_price", "stop_loss", "take_profit"):
            d[k] = str(d[k])
        return d


class MarketRegime(Enum):
    TREND = "trend"
    RANGE = "range"
    BREAKOUT = "breakout"
    VOLATILE = "volatile"


@dataclass
class BacktestConfig:
    """Configuração de backtest institucional (custos variáveis, slippage)."""
    notional_usd: float = 100_000.0
    slippage_bps: float = 0.5           # basis points
    commission_bps: float = 1.0         # basis points
    max_bars_ahead: int = 20
    use_confidence_window: bool = True  # bars_ahead = confidence * max_bars_ahead


@dataclass
class VolatilityBins:
    """Bins de regime de volatilidade — configuráveis por ativo."""
    low_upper: float = 0.005
    medium_upper: float = 0.015
    # high = tudo acima de medium_upper


# ===========================================================================
# CLASSE PRINCIPAL
# ===========================================================================
class DOS_TRADING_V1:
    """
    Módulo de refinamento trading sobre ticks/barras MT5 (CSV).
    HARDENED: Decimal, logs JSON, bins configuráveis, backtest sem look-ahead.
    """

    def __init__(
        self,
        mt5_csv_dir: str = "mt5_data/",
        vol_bins: Optional[VolatilityBins] = None,
        backtest_config: Optional[BacktestConfig] = None,
        trace_id: Optional[str] = None,
    ) -> None:
        _configure_logging()
        self.data_dir = Path(mt5_csv_dir)
        self.vol_bins = vol_bins or VolatilityBins()
        self.bt_config = backtest_config or BacktestConfig()
        self.trace_id = trace_id or uuid.uuid4().hex[:12]
        self.signals_log: List[TradingSignal] = []
        self.diagnosis_log: List[Dict[str, Any]] = []
        logger.info(
            "DOS-TRADING V2.0 HARDENED inicializado | Dados: %s | trace: %s",
            self.data_dir, self.trace_id,
            extra={"trace_id": self.trace_id},
        )

    # -----------------------------------------------------------------------
    # CAMADA 0: INGESTÃO + VALIDAÇÃO RÍGIDA
    # -----------------------------------------------------------------------
    def load_mt5_data(
        self,
        symbol: str = "XAUUSD",
        years: Optional[List[int]] = None,
        price_floor: float = _DEFAULT_PRICE_FLOOR,
        price_ceil: float = _DEFAULT_PRICE_CEIL,
    ) -> pd.DataFrame:
        """Carrega CSVs MT5 com validação rígida de schema, dtypes e sanitização."""
        if years is None:
            years = [2024, 2025, 2026]
        dfs: List[pd.DataFrame] = []
        for year in years:
            csv_path = self.data_dir / f"{symbol}_M1_{year}.csv"
            if not csv_path.exists():
                continue
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                logger.warning(
                    "CSV rejeitado (leitura falhou): %s — %s", csv_path, e,
                    extra={"trace_id": self.trace_id},
                )
                continue

            # Validação rígida de colunas
            missing = [c for c in REQUIRED_OHLC if c not in df.columns]
            if missing:
                logger.warning(
                    "CSV rejeitado (colunas em falta): %s — %s", csv_path, missing,
                    extra={"trace_id": self.trace_id},
                )
                continue

            df = df.loc[:, list(REQUIRED_OHLC)].copy()
            df["time"] = pd.to_datetime(df["time"], errors="coerce", utc=True)

            # Enforcement de dtypes numéricos
            for col in ("open", "high", "low", "close"):
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # Sanitização: remover NaN, inf, outliers
            pre_len = len(df)
            df = df.dropna(subset=["time", "open", "high", "low", "close"])
            for col in ("open", "high", "low", "close"):
                df = df[np.isfinite(df[col])]
                df = df[(df[col] > price_floor) & (df[col] < price_ceil)]

            # Validação de consistência OHLC
            df = df[df["high"] >= df["low"]]
            df = df[(df["close"] >= df["low"]) & (df["close"] <= df["high"])]
            df = df[(df["open"] >= df["low"]) & (df["open"] <= df["high"])]

            post_len = len(df)
            if post_len == 0:
                logger.warning(
                    "CSV rejeitado (0 linhas válidas): %s", csv_path,
                    extra={"trace_id": self.trace_id},
                )
                continue

            if pre_len != post_len:
                logger.info(
                    "CSV sanitizado: %s — %d→%d linhas (%d removidas)",
                    csv_path.name, pre_len, post_len, pre_len - post_len,
                    extra={"trace_id": self.trace_id},
                )

            df["year"] = year
            dfs.append(df)
            logger.info(
                "%s ticks válidos %s: %s", post_len, year, csv_path.name,
                extra={"trace_id": self.trace_id},
            )

        if not dfs:
            logger.error(
                "Nenhum ficheiro MT5 válido encontrado em %s", self.data_dir,
                extra={"trace_id": self.trace_id},
            )
            return pd.DataFrame()

        data = pd.concat(dfs, ignore_index=True).sort_values("time").reset_index(drop=True)
        logger.info(
            "%s ticks carregados | periodo: %s -> %s",
            f"{len(data):,}", data["time"].min(), data["time"].max(),
            extra={"trace_id": self.trace_id},
        )
        return data

    # -----------------------------------------------------------------------
    # CAMADAS 1-4 (in-place para evitar cópias desnecessárias)
    # -----------------------------------------------------------------------
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
        """Camada 2: microestrutura (proxy spread, velocidade ticks, volume proxy)."""
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

    def layer3_market_regime(self, data: pd.DataFrame) -> pd.DataFrame:
        """Camada 3: regime de volatilidade configurável e trend/range/breakout."""
        df = data.copy()
        df["volatility"] = df["close"].pct_change().rolling(20).std()
        df["vol_regime"] = pd.cut(
            df["volatility"],
            bins=[0.0, self.vol_bins.low_upper, self.vol_bins.medium_upper, np.inf],
            labels=["low", "medium", "high"],
        )
        df["price_trend"] = np.sign(df["price_ma5"] - df["price_ma20"])
        df["range_bound"] = (
            df["high"].rolling(20).max() - df["low"].rolling(20).min()
        ) / df["close"].replace(0, np.nan) < 0.02
        df["regime"] = np.where(
            df["range_bound"],
            "range",
            np.where(df["price_trend"] != 0, "trend", "breakout"),
        )
        return df

    @staticmethod
    def layer4_signal_composition(data: pd.DataFrame) -> pd.DataFrame:
        """Camada 4: sinal composto com pesos empíricos."""
        df = data.copy()
        price_weight = 0.3
        micro_weight = 0.25
        regime_weight = 0.45
        df["signal_price"] = np.where(
            df["price_momentum"] > 0.002, 1,
            np.where(df["price_momentum"] < -0.002, -1, 0),
        )
        q30 = df["spread_ma"].quantile(0.3)
        q30_safe = q30 if pd.notna(q30) else df["spread_ma"].median()
        if pd.isna(q30_safe):
            q30_safe = 0.0
        df["signal_micro"] = np.where(
            (df["spread_ma"] < q30_safe) & (df["volume_proxy"] > df["volume_ma"]),
            1, 0,
        )
        df["signal_regime"] = np.where(df["regime"] == "trend", df["price_trend"], 0)
        df["composite_signal"] = (
            df["signal_price"] * price_weight
            + df["signal_micro"] * micro_weight
            + df["signal_regime"] * regime_weight
        )
        df["signal_strength"] = np.abs(df["composite_signal"])
        df["direction"] = np.sign(df["composite_signal"])
        return df

    # -----------------------------------------------------------------------
    # FILTROS ADAPTATIVOS
    # -----------------------------------------------------------------------
    @staticmethod
    def adaptive_filters(vol_regime_label: Any) -> Dict[str, Any]:
        """Filtros por faixa de volatilidade (mapeia labels low|medium|high)."""
        filters = {
            "low_vol": {"min_strength": 0.5, "sl_pct": 0.008, "tp_pct": 0.015},
            "medium_vol": {"min_strength": 0.6, "sl_pct": 0.010, "tp_pct": 0.018},
            "high_vol": {"min_strength": 0.7, "sl_pct": 0.015, "tp_pct": 0.025},
        }
        key = str(vol_regime_label) if pd.notna(vol_regime_label) else "medium"
        mapping = {"low": "low_vol", "medium": "medium_vol", "high": "high_vol"}
        return filters[mapping.get(key, "medium_vol")]

    # -----------------------------------------------------------------------
    # GERAÇÃO DE SINAIS — VETORIZADA + DECIMAL
    # -----------------------------------------------------------------------
    def generate_signals(
        self,
        data: pd.DataFrame,
        symbol: str,
        min_strength: float = 0.6,
    ) -> List[TradingSignal]:
        """Geração vetorizada de sinais com preços Decimal."""
        if data.empty or "vol_regime" not in data.columns:
            return []
        signals: List[TradingSignal] = []
        for vreg in data["vol_regime"].dropna().unique():
            regime_data = data[data["vol_regime"] == vreg]
            rf = self.adaptive_filters(vreg)
            mask = (
                (regime_data["signal_strength"] >= rf["min_strength"])
                & (regime_data["direction"].abs() == 1)
            )
            strong = regime_data.loc[mask]
            if strong.empty:
                continue

            # Vetorização: preparar arrays de uma vez
            directions = strong["direction"].astype(int).values
            confidences = np.minimum(strong["signal_strength"].values * 0.95, 0.95)
            sl_pct = Decimal(str(rf["sl_pct"]))
            tp_pct = Decimal(str(rf["tp_pct"]))
            entries = strong["close"].values
            strengths = strong["signal_strength"].values
            regimes = strong["regime"].values
            times = pd.to_datetime(strong["time"], utc=True, errors="coerce")
            ts_strs = times.dt.strftime("%Y-%m-%dT%H:%M:%SZ").values

            for i in range(len(strong)):
                entry_dec = Decimal(str(float(entries[i])))
                dir_dec = Decimal(str(int(directions[i])))
                signals.append(TradingSignal(
                    timestamp=str(ts_strs[i]),
                    symbol=symbol,
                    regime=str(regimes[i]),
                    signal_strength=float(strengths[i]),
                    entry_price=entry_dec,
                    stop_loss=(entry_dec * (1 - sl_pct * dir_dec)).quantize(
                        Decimal("0.00001"), rounding=ROUND_HALF_UP
                    ),
                    take_profit=(entry_dec * (1 + tp_pct * dir_dec)).quantize(
                        Decimal("0.00001"), rounding=ROUND_HALF_UP
                    ),
                    confidence=float(confidences[i]),
                    filter_passed=True,
                    false_negative_risk=1.0 - float(strengths[i]),
                    direction=int(directions[i]),
                    vol_regime=str(vreg),
                ))

        logger.info(
            "%s sinais gerados | min_strength ref=%s",
            len(signals), min_strength,
            extra={"trace_id": self.trace_id},
        )
        return signals

    # -----------------------------------------------------------------------
    # DIAGNÓSTICO DE FALSOS NEGATIVOS
    # -----------------------------------------------------------------------
    @staticmethod
    def diagnose_false_negatives(
        data: pd.DataFrame, signals: List[TradingSignal]
    ) -> Dict[str, Any]:
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

    # -----------------------------------------------------------------------
    # BACKTEST SEM LOOK-AHEAD — CUSTOS VARIÁVEIS
    # -----------------------------------------------------------------------
    def backtest_signals(
        self,
        signals: List[TradingSignal],
        data: pd.DataFrame,
        *,
        config: Optional[BacktestConfig] = None,
    ) -> Dict[str, Any]:
        """Backtest bar-a-bar sem look-ahead, com slippage e comissão configuráveis."""
        cfg = config or self.bt_config
        empty_result = {
            "profit_factor": 0.0,
            "winrate_pct": 0.0,
            "max_dd_pct": 0.0,
            "total_trades": 0,
            "avg_pnl_pct": 0.0,
            "total_costs_bps": cfg.slippage_bps + cfg.commission_bps,
        }
        if data.empty or not signals:
            return empty_result

        times = pd.to_datetime(data["time"], utc=True)
        slippage_frac = cfg.slippage_bps / 10_000.0
        commission_frac = cfg.commission_bps / 10_000.0
        trades: List[Dict[str, Any]] = []

        for signal in signals:
            entry_f = float(signal.entry_price)
            sl_f = float(signal.stop_loss)
            tp_f = float(signal.take_profit)

            # Slippage na entrada
            entry_adj = entry_f * (1 + slippage_frac * signal.direction)

            bars_ahead = cfg.max_bars_ahead
            if cfg.use_confidence_window:
                bars_ahead = max(1, int(signal.confidence * cfg.max_bars_ahead))

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
                    if low <= sl_f:
                        exit_price = sl_f
                        break
                    if high >= tp_f:
                        exit_price = tp_f
                        break
                elif signal.direction < 0:
                    if high >= sl_f:
                        exit_price = sl_f
                        break
                    if low <= tp_f:
                        exit_price = tp_f
                        break
                exit_price = close

            if exit_price is None:
                exit_price = float(future["close"].iloc[-1])

            # PnL com custos
            gross_pnl_pct = (exit_price - entry_adj) / entry_adj * signal.direction
            cost_pct = (slippage_frac + commission_frac) * 2  # round-trip
            net_pnl_pct = gross_pnl_pct - cost_pct

            trades.append({
                "pnl_pct": net_pnl_pct,
                "pnl_usd": net_pnl_pct * cfg.notional_usd,
                "gross_pnl_pct": gross_pnl_pct,
            })

        if not trades:
            return empty_result

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
            "total_costs_bps": cfg.slippage_bps + cfg.commission_bps,
        }

    # -----------------------------------------------------------------------
    # PIPELINE COMPLETO
    # -----------------------------------------------------------------------
    def run_full_pipeline(self, symbol: str = "XAUUSD") -> Dict[str, Any]:
        data = self.load_mt5_data(symbol)
        if data.empty:
            return {"status": "ERROR", "message": "Sem dados MT5 válidos", "inputs_sha256": None}
        missing = [c for c in REQUIRED_OHLC if c not in data.columns]
        if missing:
            return {
                "status": "ERROR",
                "message": f"Colunas OHLC em falta: {missing}",
                "inputs_sha256": None,
            }

        # Digest incremental (evita OOM)
        sub = data.loc[:, list(REQUIRED_OHLC)].copy()
        sub["time"] = pd.to_datetime(sub["time"], utc=True).astype(str)
        h = hashlib.sha256()
        h.update(",".join(sub.columns).encode("utf-8"))
        chunk = 20_000
        for start in range(0, len(sub), chunk):
            h.update(sub.iloc[start:start + chunk].to_csv(index=False).encode("utf-8"))
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
            "pipeline_version": "2.0",
            "spec_id": "DOC-OFC-DOS-TRADING-V1.0-20260405-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs_sha256": inputs_sha256,
            "trace_id": self.trace_id,
            "vol_bins": {
                "low_upper": self.vol_bins.low_upper,
                "medium_upper": self.vol_bins.medium_upper,
            },
            "backtest_config": {
                "slippage_bps": self.bt_config.slippage_bps,
                "commission_bps": self.bt_config.commission_bps,
                "notional_usd": self.bt_config.notional_usd,
            },
        }
        self.signals_log.extend(signals)
        self.diagnosis_log.append(report)
        logger.info(
            "Pipeline completo: %s sinais, PF=%s, trace=%s",
            len(signals), backtest.get("profit_factor"), self.trace_id,
            extra={"trace_id": self.trace_id},
        )
        return report


def main() -> Dict[str, Any]:
    """Ponto de entrada standalone."""
    _configure_logging()
    logger.info("=== DOS-TRADING V2.0 HARDENED ===")
    trader = DOS_TRADING_V1(os.getenv("DOS_MT5_DIR", "mt5_data/"))
    result = trader.run_full_pipeline("XAUUSD")
    print("\n" + "=" * 60)
    print("DOS-TRADING V2.0 HARDENED — RESULTADOS")
    print("=" * 60)
    print("Status:", result.get("status"))
    print("Sinais:", result.get("signals_generated"))
    if result.get("status") == "SUCCESS":
        bt = result.get("backtest") or {}
        print("Profit Factor:", bt.get("profit_factor"))
        print("Winrate %:", bt.get("winrate_pct"))
        print("Max DD %:", bt.get("max_dd_pct"))
        print("Custos (bps):", bt.get("total_costs_bps"))
        print("FN (est.):", (result.get("diagnosis") or {}).get("false_negatives"))
        print("Trace:", result.get("trace_id"))
        print("Timestamp:", str(result.get("timestamp", ""))[:19])
    return result


if __name__ == "__main__":
    main()
