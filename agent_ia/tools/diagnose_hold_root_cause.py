"""
PSA-WIND | DIAGNÓSTICO FORENSE — por que get_signal_for_asset retorna HOLD.

Para cada ativo cripto + alguns FX, executa get_signal e registra:
  - sessão atual + priority_assets + min_confidence
  - dados de mercado disponíveis (build_market_data)
  - melhor agente do ecossistema
  - estratégia escolhida
  - signal.action e signal.reason
  - confidence ajustada vs min_confidence
  - razão final do HOLD/SIGNAL

Saída: logs/agent_ia_phase3/diagnose_hold_<ts>.json + .sha3
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agent_ia"))

import MetaTrader5 as mt5

from agent_ia.core.omega_strategy_catalog import build_market_data, SignalAction
from agent_ia.core.omega_session_calibrator import SessionCalibrator
from agent_ia.core.omega_global_orchestrator import OmegaGlobalOrchestrator

ASSETS = ["BTCUSD", "ETHUSD", "SOLUSD", "DOGUSD", "XAUUSD", "EURUSD"]


def diagnose() -> dict:
    if not mt5.initialize():
        return {"error": "mt5_init_failed"}

    calibrator = SessionCalibrator()
    current_session = calibrator.get_current_session()
    session_config = calibrator.get_config(current_session)

    orch = OmegaGlobalOrchestrator(
        assets=ASSETS,
        total_capital=10000.0,
    )
    # Override para garantir o mesmo calibrator que vai imprimir o config
    calibrator = orch.calibrator
    current_session = calibrator.get_current_session()
    session_config = calibrator.get_config(current_session)

    out = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "current_session": current_session.value,
        "session_config": {
            "priority_assets": session_config.priority_assets,
            "active_strategies": session_config.active_strategies,
            "min_confidence": session_config.min_confidence,
            "max_lot": session_config.max_lot,
            "max_positions": session_config.max_positions,
            "max_spread_pips": session_config.max_spread_pips,
            "spoof_threshold": session_config.spoof_threshold,
        },
        "by_asset": [],
    }

    for asset in ASSETS:
        rec = {"asset": asset}
        # Gate 1: priority_assets
        rec["gate1_in_priority"] = asset in session_config.priority_assets

        # Build market data
        md = build_market_data(asset)
        rec["gate2_market_data_ok"] = bool(md)
        if md:
            rec["market_data_summary"] = {
                "current_price": md.get("current_price"),
                "ema_50": md.get("ema_50"),
                "ema_200": md.get("ema_200"),
                "ema_diff_pct": ((md.get("ema_50", 0) / md.get("ema_200", 1) - 1) * 100) if md.get("ema_200") else None,
                "adx": md.get("adx"),
                "rsi_14": md.get("rsi_14"),
                "atr_14": md.get("atr_14"),
                "spread": md.get("spread"),
                "volume_ratio": md.get("volume_ratio"),
                "roc_10": md.get("roc_10"),
                "price_position": md.get("price_position"),
            }

        # Get best agent
        try:
            agent = orch.ecosystem.get_best_agent_for_asset(asset)
            rec["gate3_agent"] = {
                "exists": agent is not None,
                "active": agent.active if agent else None,
                "agent_id": agent.agent_id if agent else None,
                "strategy": agent.strategy_name if agent else None,
                "kelly_fraction": agent.kelly_fraction if agent else None,
                "qvalue": agent.q_value if agent else None,
                "risk_adj_conf": agent.get_risk_adjusted_confidence() if agent else None,
            }
        except Exception as e:
            rec["gate3_agent"] = {"error": str(e)}

        # Get full signal via orchestrator
        try:
            sig = orch.get_signal_for_asset(asset, market_data=md or None)
            rec["final_signal"] = {
                "action": sig.get("action"),
                "direction": sig.get("direction"),
                "confidence": sig.get("confidence"),
                "lot": sig.get("lot"),
                "strategy": sig.get("strategy"),
                "agent_id": sig.get("agent_id"),
                "reason": sig.get("reason"),
            }
        except Exception as e:
            rec["final_signal"] = {"error": str(e)}

        # If we have an agent, also test the strategy directly
        if md and rec.get("gate3_agent", {}).get("active"):
            try:
                strategy = orch.catalog.get_strategy(agent.strategy_name)
                if strategy:
                    raw = strategy.get_signal(md)
                    rec["raw_strategy_signal"] = {
                        "action": raw.action.value if hasattr(raw.action, "value") else str(raw.action),
                        "confidence": raw.confidence,
                        "reason": raw.reason,
                    }
            except Exception as e:
                rec["raw_strategy_signal"] = {"error": str(e)}

        out["by_asset"].append(rec)

    mt5.shutdown()
    return out


def main() -> int:
    res = diagnose()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "logs" / "agent_ia_phase3"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"diagnose_hold_{ts}.json"
    out_path.write_text(json.dumps(res, indent=2, default=str), encoding="utf-8")
    sha = hashlib.sha3_256(out_path.read_bytes()).hexdigest()
    (out_dir / f"diagnose_hold_{ts}.sha3").write_text(sha + "\n", encoding="utf-8")

    print("=" * 78)
    print(f"DIAGNOSTIC: {out_path}")
    print(f"SHA3:      {sha}")
    print(f"SESSION:   {res.get('current_session')}")
    print(f"PRIORITY:  {res.get('session_config', {}).get('priority_assets')}")
    print(f"MIN_CONF:  {res.get('session_config', {}).get('min_confidence')}")
    print(f"STRATEGIES:{res.get('session_config', {}).get('active_strategies')}")
    print("-" * 78)
    print(f"{'asset':<10} {'g1_pri':<8} {'g2_md':<8} {'agent':<28} {'raw_action':<12} {'final_action':<14} reason")
    for r in res.get("by_asset", []):
        agent = r.get("gate3_agent", {})
        agent_str = f"{agent.get('strategy', '?')[:18]}({(agent.get('risk_adj_conf') or 0):.2f})"
        raw = r.get("raw_strategy_signal", {})
        fin = r.get("final_signal", {})
        print(f"{r['asset']:<10} "
              f"{str(r.get('gate1_in_priority')):<8} "
              f"{str(r.get('gate2_market_data_ok')):<8} "
              f"{agent_str:<28} "
              f"{str(raw.get('action', '-'))[:11]:<12} "
              f"{str(fin.get('action', '-'))[:13]:<14} "
              f"{(fin.get('reason') or '')[:60]}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
