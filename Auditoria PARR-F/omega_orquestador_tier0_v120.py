#!/usr/bin/env python3
"""
OMEGA ORQUESTRADOR TIER-0 — Referência PARR-F v1.2.0
ID: REQ-PARRF-DIRETRIZES-CRITICAS-CODIGO-TIER0-V120-20260411

RECADO_AGENTES_IA (obrigatório):
- Não integrar FIN-SENSE / MT5 / risk_elite neste ficheiro sem documento + aprovação.
- Não afirmar "produção" ou "zero bypass" sem prova (grep recursivo, processos parados).
- Manter um único lineage de orquestrador; versionar aqui (v120), não duplicar mains.

Funcionalidade:
- 4 camadas: DOS -> Kernel -> Risk -> Executor (dry-run)
- trace_id UUID v4; audit JSON por execução
- Executor recusa se risk.cleared == False

Executar: python omega_orquestador_tier0_v120.py
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("OMEGA.ORCHESTRATOR.PARRF")

MIN_CONFIDENCE = float(os.environ.get("OMEGA_MIN_CONFIDENCE", "0.6"))
VAR_BLOCK_USD = float(os.environ.get("OMEGA_VAR_BLOCK_USD", "5e6"))
MOMENTUM_THRESHOLD = float(os.environ.get("OMEGA_MOMENTUM_THRESHOLD", "0.002"))


@dataclass
class DOSMetricsLayer:
    """Stub L1. Produção: substituir por fin_sense_l1_esqueleto_v120.FinSenseL1Layer (aprovado)."""

    def compute_metrics(self, symbol: str) -> Dict[str, Any]:
        logger.info("[L1 DOS] compute_metrics symbol=%s", symbol)

        if os.environ.get("OMEGA_SIMULATE_NO_DATA", "").strip() == "1":
            return {
                "symbol": symbol,
                "var_95_usd": float("nan"),
                "cvar_95_usd": float("nan"),
                "regime_data": "NO_DATA_AVAILABLE",
                "momentum_1m_pct": 0.0,
                "effective_spread": float("nan"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "provenance_sha256": "",
                "errors": ["NO_DATA_AVAILABLE"],
            }

        if os.environ.get("OMEGA_DEMO_HIGH_VAR", "").strip() == "1":
            var_95 = 850_000.0
            regime = "PANIC_VARIANCE"
        else:
            var_95 = 10_000.0
            regime = "CHOPPY_NOISE"

        mom = float(os.environ.get("OMEGA_DEMO_MOMENTUM_PCT", "0") or 0)
        payload = f"{symbol}|{regime}|{var_95}|{mom}"
        digest = hashlib.sha256(payload.encode()).hexdigest()

        return {
            "symbol": symbol,
            "var_95_usd": var_95,
            "cvar_95_usd": var_95 * 1.15,
            "regime_data": regime,
            "momentum_1m_pct": mom,
            "effective_spread": 0.12,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provenance_sha256": digest,
            "errors": [],
        }


@dataclass
class KernelDecisionLayer:
    def make_decision(self, dos_metrics: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[L2 KERNEL] make_decision")
        symbol = dos_metrics.get("symbol", "XAUUSD")
        errs = dos_metrics.get("errors") or []
        if errs or dos_metrics.get("regime_data") == "NO_DATA_AVAILABLE":
            return {
                "symbol": symbol,
                "direction": "HOLD",
                "confidence": 0.0,
                "position_size": 0.0,
                "regime": "NO_DATA",
                "strategy_tag": "NO_DATA",
                "var_exposure": float(dos_metrics.get("var_95_usd") or 0.0),
            }

        var_95 = float(dos_metrics.get("var_95_usd", 0.0))
        mom = float(dos_metrics.get("momentum_1m_pct", 0.0))
        rd = dos_metrics.get("regime_data", "UNKNOWN")

        if abs(mom) >= MOMENTUM_THRESHOLD:
            direction = "BUY" if mom > 0 else "SELL"
            conf = min(0.95, 0.55 + min(abs(mom) / 0.02, 0.4))
            return {
                "symbol": symbol,
                "direction": direction,
                "confidence": conf,
                "position_size": float(os.environ.get("OMEGA_PROPOSED_LOT", "0.01")),
                "regime": "TREND_MOMENTUM",
                "strategy_tag": "MOMENTUM",
                "var_exposure": var_95,
            }

        if rd == "PANIC_VARIANCE":
            return {
                "symbol": symbol,
                "direction": "HOLD",
                "confidence": 0.35,
                "position_size": 0.0,
                "regime": "PANIC_VARIANCE",
                "strategy_tag": "DEFENSIVE",
                "var_exposure": var_95,
            }

        return {
            "symbol": symbol,
            "direction": "HOLD",
            "confidence": 0.25,
            "position_size": 0.0,
            "regime": "CHOPPY_NOISE",
            "strategy_tag": "DEFAULT",
            "var_exposure": var_95,
        }


@dataclass
class RiskValveLayer:
    def validate_trade(
        self,
        kernel_decision: Dict[str, Any],
        dos_metrics: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        logger.info("[L3 RISK] validate_trade")
        reasons: List[str] = []

        if dos_metrics.get("errors"):
            reasons.append("DOS_ERRORS")

        if kernel_decision.get("direction") in ("HOLD", None, ""):
            reasons.append("HOLD_OR_NEUTRAL")

        conf = float(kernel_decision.get("confidence", 0))
        if conf < MIN_CONFIDENCE:
            reasons.append("LOW_CONFIDENCE")

        if kernel_decision.get("regime") == "CHOPPY_NOISE":
            reasons.append("REGIME_CHOPPY")

        if kernel_decision.get("regime") == "NO_DATA":
            reasons.append("NO_DATA_REGIME")

        ve = float(kernel_decision.get("var_exposure", 0.0))
        if ve == ve and ve > VAR_BLOCK_USD:
            reasons.append("VAR_LIMIT")

        return len(reasons) == 0, reasons


@dataclass
class MQL5ExecutorLayer:
    def execute(
        self,
        decision: Dict[str, Any],
        risk_snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        logger.info("[L4 EXEC] execute")
        if not risk_snapshot.get("cleared"):
            return {
                "order_id": None,
                "symbol": decision.get("symbol"),
                "direction": decision.get("direction"),
                "size": decision.get("position_size", 0.0),
                "status": "EXECUTOR_REFUSED_RISK_NOT_CLEARED",
                "reasons": risk_snapshot.get("reasons", []),
            }
        return {
            "order_id": f"DRY_{uuid.uuid4().hex[:12]}",
            "symbol": decision.get("symbol"),
            "direction": decision.get("direction"),
            "size": decision.get("position_size", 0.0),
            "status": "DRY_RUN_SUCCESS",
            "fill_price": None,
        }


@dataclass
class OmegaOrchestrator:
    dos: DOSMetricsLayer = field(default_factory=DOSMetricsLayer)
    kernel: KernelDecisionLayer = field(default_factory=KernelDecisionLayer)
    risk: RiskValveLayer = field(default_factory=RiskValveLayer)
    executor: MQL5ExecutorLayer = field(default_factory=MQL5ExecutorLayer)

    def full_pipeline(self, symbol: str = "XAUUSD") -> Dict[str, Any]:
        trace_id = str(uuid.uuid4())
        out: Dict[str, Any] = {
            "doc_id": "REQ-PARRF-DIRETRIZES-CRITICAS-CODIGO-TIER0-V120-20260411",
            "orchestrator_version": "1.2.0",
            "trace_id": trace_id,
            "symbol": symbol,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "layers": {},
        }
        try:
            out["layers"]["dos"] = self.dos.compute_metrics(symbol)
            kd = self.kernel.make_decision(out["layers"]["dos"])
            out["layers"]["kernel"] = kd

            cleared, reasons = self.risk.validate_trade(kd, out["layers"]["dos"])
            risk_snap = {"cleared": cleared, "reasons": reasons}
            out["layers"]["risk"] = risk_snap

            ex = self.executor.execute(kd, risk_snap)
            out["layers"]["executor"] = ex

            if cleared and ex.get("status") == "DRY_RUN_SUCCESS":
                out["status"] = "EXECUTED_DRY_RUN"
            elif not cleared:
                out["status"] = "RISK_BLOCKED"
            else:
                out["status"] = "EXECUTOR_BLOCKED_OR_DEGRADED"
        except Exception as e:
            logger.exception("Pipeline error")
            out["status"] = "ERROR"
            out["error"] = str(e)

        self._write_audit(out)
        return out

    def _write_audit(self, payload: Dict[str, Any]) -> None:
        log_dir = Path(os.environ.get("OMEGA_AUDIT_DIR", "."))
        log_dir.mkdir(parents=True, exist_ok=True)
        tid = payload.get("trace_id", "unknown")
        fn = log_dir / f"omega_audit_PARRF_{tid}.json"
        fn.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
        logger.info("Audit: %s", fn)


def main() -> int:
    r = OmegaOrchestrator().full_pipeline("XAUUSD")
    print("STATUS:", r.get("status"))
    print("TRACE:", r.get("trace_id"))
    return 0 if r.get("status") != "ERROR" else 1


if __name__ == "__main__":
    raise SystemExit(main())
