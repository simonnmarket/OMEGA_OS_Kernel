"""
OMEGA — Sincronização única do ecossistema (CEO 2026-05-25).

Uma fonte de verdade para:
- Portfolio discovery (16 símbolos)
- max_positions (alinhado ao runner)
- Modo decisão IA+PSA (confluência, não motores em conflito silencioso)

Activar: OMEGA_ECOSYSTEM_UNIFIED=1 (run_omega_24x7.ps1)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

# Portfolio discovery Hantec (CEO) — US100 = NAS100 no broker
CEO_DISCOVERY_ASSETS: List[str] = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "XAUUSD", "US500", "US100",
    "BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "AVAXUSD", "ADAUSD", "LTCUSD", "BNBUSD",
]

_BROKER_ALIASES = {"NAS100": "US100", "NAS100+": "US100"}


def is_unified_mode() -> bool:
    return os.getenv("OMEGA_ECOSYSTEM_UNIFIED", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def get_unified_max_positions(default: int = 8) -> int:
    raw = os.getenv("OMEGA_MAX_POSITIONS", str(default)).strip()
    try:
        v = int(raw)
        return max(1, v) if v > 0 else default
    except ValueError:
        return default


def get_unified_portfolio(source_root: Path | None = None) -> List[str]:
    """Portfolio: env OMEGA_ECOSYSTEM_ASSETS > schedule profile > lista CEO."""
    raw = (os.getenv("OMEGA_ECOSYSTEM_ASSETS") or "").strip()
    if raw:
        parts = raw.replace(",", " ").split()
        return [_BROKER_ALIASES.get(p.strip().upper(), p.strip().upper()) for p in parts if p.strip()]

    if source_root:
        try:
            from modules.omega_asset_schedule import resolve_shadow_loop_assets

            syms, _ = resolve_shadow_loop_assets(None, source_root)
            if syms:
                return [_BROKER_ALIASES.get(s.upper(), s.upper()) for s in syms]
        except Exception:
            pass

    return list(CEO_DISCOVERY_ASSETS)


def apply_unified_session_catalog(catalog: object) -> None:
    """
    Alinha todas as sessões do SessionConfigCatalog ao portfolio e max_positions do runner.
    """
    if not is_unified_mode():
        return
    portfolio = get_unified_portfolio()
    max_pos = get_unified_max_positions()
    configs = getattr(catalog, "_configs", None)
    if not configs:
        return
    for cfg in configs.values():
        cfg.priority_assets = list(portfolio)
        cfg.max_positions = max_pos


def unified_decision_env_defaults() -> dict[str, str]:
    """Env recomendados quando ecossistema unificado (IA+PSA confluência)."""
    return {
        "OMEGA_ECOSYSTEM_UNIFIED": "1",
        "OMEGA_USE_AGENT_IA": "1",
        "OMEGA_USE_SIGNAL_FUSION": "1",
        "PSA_SHADOW_MODE": "0",
        "FUSION_MIN_CONFIDENCE": os.getenv("FUSION_MIN_CONFIDENCE", "0.55"),
        "OMEGA_LOOP_PSA_V12": "1",
    }


def write_ecosystem_manifest(source_root: Path) -> Path:
    """Manifesto auditável — prova de sincronização activa."""
    out = source_root / "audit" / "paper" / "ecosystem_unified_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "unified": is_unified_mode(),
        "portfolio": get_unified_portfolio(source_root),
        "max_positions": get_unified_max_positions(),
        "decision_env": unified_decision_env_defaults(),
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
