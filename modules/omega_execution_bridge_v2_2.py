#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 OMEGA EXECUTION BRIDGE v2.2 — FILE BRIDGE (MT5 Common / Files)
=============================================================================
ID: MOD-EXECCBRIDGE-001 | Tier: TIER-0

Nota de nomenclatura: a pasta pode chamar-se "ZMQ to MQL5 Bridge", mas este
módulo implementa uma ponte **JSON atómica** (AIRequest/AIResponse), não ZMQ.

Correcções v2.2 (audit_reports + execução local v2.1):
- P0: `timeout_s` dos regimes mapeado para `response_timeout_s` (evita TypeError).
- P0: `compute_from_bars` seguro sem pandas instalado (sem `pd.DataFrame` em isinstance).
- P1: `strength` combina `confidence` (sinal) com voltagem normalizada em [v_min, v_max].
- P1: aviso de latência separa escrita atómica vs espera total por feedback (bloqueante na thread).
- P1: Kill-switch com guarda `anchor_equity > 0` (alinhado a políticas explícitas).
- P2: payload JSON inclui `components_fired` opcional (compat EA / auditoria).
- PSA v2.2.1: bloco Numba opcional (checklist); pesos `confidence_weight`/`voltage_weight`.
- Self-test: regimes default/forex/crypto/metal + fallback dict sem pandas.

IMPORTANTE: `execute_signal` permanece bloqueante na thread chamadora durante o
poll de feedback (`time.sleep`). Isto é intencional para uso síncrono seguro.
=============================================================================
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Optional: MetaTrader5 (reservado / health futuro; não obrigatório à ponte ficheiro) ──
try:
    import MetaTrader5 as mt5  # noqa: F401
    _HAS_MT5 = True
except ImportError:
    mt5 = None
    _HAS_MT5 = False

# ── Optional: Numba (checklist OMEGA — import com fallback; bridge não usa JIT) ──
try:
    from numba import njit  # noqa: F401
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False

    def _dummy_njit(fn=None, **kwargs):
        if fn is not None:
            return fn

        def decorator(f):
            return f

        return decorator

    njit = _dummy_njit  # type: ignore[misc, assignment]

# ── Optional: Pandas ───────────────────────────────────────────────────────
try:
    import pandas as pd
    _HAS_PANDAS = True
except ImportError:
    pd = None
    _HAS_PANDAS = False

log = logging.getLogger("OMEGA.EXECUTION_BRIDGE")

# ═══════════════════════════════════════════════════════════════════════════
# REGIME DEFAULTS (timeout_s → response_timeout_s no factory)
# ═══════════════════════════════════════════════════════════════════════════
BRIDGE_REGIME_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "default": {"voltage_max": 3.3, "timeout_s": 2.0},
    "forex": {"voltage_max": 5.0, "timeout_s": 1.5},
    "crypto": {"voltage_max": 3.3, "timeout_s": 2.5},
    "metal": {"voltage_max": 5.0, "timeout_s": 1.5},
}
VALID_REGIMES = ("forex", "crypto", "metal", "default")


@dataclass
class BridgeConfig:
    """Configuração da ponte ficheiro ↔ MT5 Common Files."""

    mql5_data_dir: str = ""
    regime: str = "default"
    voltage_min: float = 0.0
    voltage_max: float = 3.3
    poll_interval_ms: float = 1.0
    response_timeout_s: float = 2.0
    require_ks_check: bool = True
    ks_anchor_file: str = "audit/risk/ks_daily_state.json"
    default_signal_source: str = "OMEGA_SYNAPSE"
    request_prefix: str = "AIRequest"
    response_prefix: str = "AIResponse"
    # Se True, força strength a partir só de confidence (ignora voltage na mistura)
    strength_from_confidence_only: bool = False
    # Ortogonalidade: pesos da mistura strength (normalizados para soma 1)
    confidence_weight: float = 0.5
    voltage_weight: float = 0.5

    def __post_init__(self) -> None:
        self.voltage_max = max(0.1, float(self.voltage_max))
        self.voltage_min = float(self.voltage_min)
        if self.voltage_min >= self.voltage_max:
            self.voltage_min = 0.0
        self.poll_interval_ms = max(0.001, float(self.poll_interval_ms))
        self.response_timeout_s = max(0.1, float(self.response_timeout_s))
        if self.regime not in VALID_REGIMES:
            self.regime = "default"
        cw = max(0.0, float(self.confidence_weight))
        vw = max(0.0, float(self.voltage_weight))
        s = cw + vw
        if s <= 1e-12:
            self.confidence_weight = 0.5
            self.voltage_weight = 0.5
        else:
            self.confidence_weight = cw / s
            self.voltage_weight = vw / s


@dataclass
class ComponentState:
    """Estado devolvido ao pipeline OMEGA."""

    is_valid: bool
    direction: int
    strength: float
    n_bars: int
    symbol: str = ""
    execution_latency_us: float = 0.0
    atomic_write_success: bool = False
    ks_check_passed: bool = True
    feedback_received: bool = False
    write_latency_us: float = 0.0
    warning: Optional[str] = None


class ComponentEngine:
    """Motor síncrono: escreve pedido JSON e faz poll da resposta."""

    def __init__(self, config: BridgeConfig) -> None:
        self._cfg = config

    @classmethod
    def from_config(cls, regime: str = "default", **overrides: Any) -> "ComponentEngine":
        """Factory com defaults por regime; chaves desconhecidas são ignoradas."""
        reg = regime if regime in VALID_REGIMES else "default"
        defaults = dict(BRIDGE_REGIME_DEFAULTS.get(reg, BRIDGE_REGIME_DEFAULTS["default"]))
        if "timeout_s" in defaults:
            defaults["response_timeout_s"] = defaults.pop("timeout_s")
        merged: Dict[str, Any] = {"regime": reg, **defaults, **overrides}
        allowed = {f.name for f in fields(BridgeConfig)}
        cfg_kwargs = {k: v for k, v in merged.items() if k in allowed}
        return cls(BridgeConfig(**cfg_kwargs))

    @property
    def _data_dir(self) -> Path:
        if self._cfg.mql5_data_dir:
            return Path(self._cfg.mql5_data_dir)
        appdata = os.getenv("APPDATA")
        if appdata and os.name == "nt":
            return Path(appdata) / "MetaQuotes" / "Terminal" / "Common" / "Files"
        return Path.cwd() / "mt5_common_files"

    @staticmethod
    def _is_dataframe(obj: Any) -> bool:
        return bool(_HAS_PANDAS and pd is not None and isinstance(obj, pd.DataFrame))

    def compute_from_bars(self, df: Any, symbol: str = "UNKNOWN") -> ComponentState:
        """Valida um pacote de sinal (DataFrame, dict ou list[dict]) e executa."""
        if df is None:
            return self._invalid(symbol, "Input is None")
        if isinstance(df, (str, bytes, int, float)):
            return self._invalid(symbol, "Invalid input type")

        row: Dict[str, Any]
        if self._is_dataframe(df):
            row = df.iloc[0].to_dict()
        elif isinstance(df, list) and len(df) > 0 and isinstance(df[0], dict):
            row = dict(df[0])
        elif isinstance(df, dict):
            row = dict(df)
        else:
            return self._invalid(symbol, "Invalid input type")

        req = {"symbol", "action", "confidence"}
        if not req.issubset(row.keys()):
            return self._invalid(symbol, f"Missing keys: {req - set(row.keys())}")

        return self.execute_signal(
            symbol=str(row["symbol"]),
            action=str(row["action"]),
            confidence=float(row["confidence"]),
            volume=float(row.get("volume", 0.01)),
            voltage=float(row.get("voltage", 0.0)),
            components_fired=int(row.get("components_fired", 0) or 0),
        )

    def _normalize_strength(self, confidence: float, voltage: float) -> float:
        span = max(self._cfg.voltage_max - self._cfg.voltage_min, 1e-9)
        v = (float(voltage) - float(self._cfg.voltage_min)) / span
        volt_norm = max(0.0, min(1.0, v))
        conf = max(0.0, min(1.0, float(confidence)))
        if self._cfg.strength_from_confidence_only:
            return conf
        w_c = float(self._cfg.confidence_weight)
        w_v = float(self._cfg.voltage_weight)
        return max(0.0, min(1.0, w_c * conf + w_v * volt_norm))

    def execute_signal(
        self,
        symbol: str,
        action: str,
        confidence: float,
        volume: float = 0.01,
        voltage: float = 0.0,
        components_fired: int = 0,
    ) -> ComponentState:
        t0 = time.perf_counter_ns()
        strength = self._normalize_strength(confidence, voltage)

        if self._cfg.require_ks_check and not self._check_kill_switch():
            return ComponentState(
                is_valid=False,
                direction=0,
                strength=0.0,
                n_bars=1,
                symbol=symbol,
                ks_check_passed=False,
                warning="KILL_SWITCH_ACTIVE",
            )

        write_ok, write_lat_us = self._atomic_write_sync(
            symbol, action, volume, strength, components_fired, float(confidence)
        )

        t_feedback0 = time.perf_counter_ns()
        feedback = self._wait_for_feedback_sync(symbol)
        feedback_wait_us = (time.perf_counter_ns() - t_feedback0) / 1000.0
        elapsed_us = (time.perf_counter_ns() - t0) / 1000.0

        direction = 1 if action.upper() == "BUY" else (-1 if action.upper() == "SELL" else 0)

        warnings: List[str] = []
        if write_lat_us > 500:
            warnings.append(f"WRITE_SLOW {write_lat_us:.0f}µs")
        if feedback is None:
            warnings.append(
                f"FEEDBACK_TIMEOUT>{self._cfg.response_timeout_s:.2f}s (waited {feedback_wait_us/1e6:.3f}s wall)"
            )
        warn = "; ".join(warnings) if warnings else None

        return ComponentState(
            is_valid=write_ok,
            direction=direction,
            strength=strength,
            n_bars=1,
            symbol=symbol,
            execution_latency_us=round(elapsed_us, 3),
            atomic_write_success=write_ok,
            feedback_received=feedback is not None,
            write_latency_us=round(write_lat_us, 3),
            warning=warn,
        )

    def _atomic_write_sync(
        self,
        symbol: str,
        action: str,
        vol: float,
        strength: float,
        components_fired: int,
        raw_signal_confidence: float,
    ) -> tuple[bool, float]:
        t0 = time.perf_counter_ns()
        d = self._data_dir
        d.mkdir(parents=True, exist_ok=True)

        fname = f"{self._cfg.request_prefix}.{symbol.upper()}.json"
        tmp = d / f"{fname}.tmp"
        final = d / fname

        try:
            payload = {
                "symbol": symbol.upper(),
                "action": action.upper(),
                "price": 0.0,
                "volume": vol,
                "confidence": strength,
                "raw_signal_confidence": max(0.0, min(1.0, float(raw_signal_confidence))),
                "components_fired": int(components_fired),
                "source": self._cfg.default_signal_source,
                "time": int(time.time()),
            }
            text = json.dumps(payload, separators=(",", ":"))
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, final)
            return True, (time.perf_counter_ns() - t0) / 1000.0
        except Exception as e:
            log.error("Write fail %s: %s", symbol, e)
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            return False, (time.perf_counter_ns() - t0) / 1000.0

    def _wait_for_feedback_sync(self, symbol: str) -> Optional[Dict[str, Any]]:
        f_path = self._data_dir / f"{self._cfg.response_prefix}.{symbol.upper()}.json"
        start = time.time()
        while (time.time() - start) < self._cfg.response_timeout_s:
            if f_path.exists():
                try:
                    data = json.loads(f_path.read_text(encoding="utf-8"))
                    f_path.unlink(missing_ok=True)
                    return data
                except Exception:
                    pass
            time.sleep(self._cfg.poll_interval_ms / 1000.0)
        return None

    def _check_kill_switch(self) -> bool:
        ks = Path(self._cfg.ks_anchor_file)
        if not ks.exists():
            return True
        try:
            data = json.loads(ks.read_text(encoding="utf-8"))
            anchor = float(data.get("anchor_equity", 0.0) or 0.0)
            last_eq = float(data.get("last_equity", 0.0) or 0.0)
            max_dd = float(data.get("max_dd_pct", 0.02) or 0.02)
            if anchor <= 0:
                return True
            return last_eq >= anchor * (1.0 - max_dd)
        except Exception:
            return True

    def _invalid(self, symbol: str, reason: str) -> ComponentState:
        log.warning("[%s] ExecutionBridge invalid: %s", symbol, reason)
        return ComponentState(
            is_valid=False,
            direction=0,
            strength=0.0,
            n_bars=0,
            symbol=symbol,
            warning=reason,
        )


def register_module() -> Dict[str, type]:
    return {
        "ComponentEngine": ComponentEngine,
        "BridgeConfig": BridgeConfig,
        "ComponentState": ComponentState,
    }


def run_self_test() -> bool:
    log.info("Running OMEGA Execution Bridge v2.2 self-test...")
    import tempfile

    errors: List[str] = []

    # T00: regimes instanciáveis (regressão v2.1 timeout_s)
    for reg in ("default", "forex", "crypto", "metal"):
        try:
            eng = ComponentEngine.from_config(reg, mql5_data_dir="", require_ks_check=False)
            if eng._cfg.regime != reg:
                errors.append(f"T00: regime mismatch for {reg} (got {eng._cfg.regime})")
        except Exception as e:
            errors.append(f"T00: from_config({reg}) raised: {e}")

    with tempfile.TemporaryDirectory() as tmpdir:
        eng = ComponentEngine.from_config("forex", mql5_data_dir=tmpdir, require_ks_check=False)
        if eng._data_dir != Path(tmpdir):
            errors.append("T01: Path property mismatch")

        if _HAS_MT5:
            log.info("MetaTrader5 module present (optional).")
        else:
            log.info("MetaTrader5 not installed — file bridge does not require it.")
        if _HAS_NUMBA:
            log.info("Numba present (optional import pattern).")
        else:
            log.info("Numba not installed — optional stub active.")

        if _HAS_PANDAS and pd is not None:
            df = pd.DataFrame(
                [{"symbol": "TST", "action": "BUY", "confidence": 0.9, "voltage": 2.5, "components_fired": 2}]
            )
            st = eng.compute_from_bars(df)
        else:
            st = eng.compute_from_bars(
                {"symbol": "TST", "action": "BUY", "confidence": 0.9, "voltage": 2.5, "components_fired": 2}
            )
        if not st.is_valid:
            errors.append("T02: exec failed (write)")
        if st.direction != 1:
            errors.append("T02: direction wrong")

        st_dict = eng.compute_from_bars(
            {"symbol": "TST", "action": "SELL", "confidence": 0.5, "voltage": 1.0}
        )
        if st_dict.direction != -1:
            errors.append("T03: dict SELL direction wrong")

        st_bad = eng.compute_from_bars("string")
        if st_bad.is_valid:
            errors.append("T04: string should be invalid")

    if errors:
        for e in errors:
            log.error("%s", e)
        return False
    log.info("All self-tests PASSED — v2.2")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(0 if run_self_test() else 1)
