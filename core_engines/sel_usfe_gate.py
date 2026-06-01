"""SEL/USFE enforcement gate — CKO 20260601 + CEO madrugada 100% activo."""
from __future__ import annotations

import os
from typing import Any, Dict, Tuple


def _flag_on(key: str, default: str = "0") -> bool:
    return os.getenv(key, default).strip().lower() in ("1", "true", "yes", "on")


def sel_usfe_enforcement_active(live_flags: Dict[str, Any] | None = None) -> bool:
    """Master + per-layer switches. Emergency: OMEGA_SKIP_SEL_USFE_ENFORCE=1."""
    if _flag_on("OMEGA_SKIP_SEL_USFE_ENFORCE", "0"):
        return False
    if _flag_on("OMEGA_ENFORCE_SEL_USFE_GATE", "1"):
        return True
    lf = live_flags or {}
    return str(lf.get("OMEGA_ENFORCE_SEL_USFE_GATE", "0")).strip() == "1"


def evaluate_sel_usfe_gate(
    *,
    sel_audit_veto: bool,
    usfe_bias: str,
    live_flags: Dict[str, Any] | None = None,
) -> Tuple[bool, str, str]:
    """
    Returns (allowed, status_skip, message).
    allowed=False => block order.
    """
    if not sel_usfe_enforcement_active(live_flags):
        return True, "OK", ""

    lf = live_flags or {}
    sel_on = os.getenv("OMEGA_SEL_ENABLED", str(lf.get("OMEGA_SEL_ENABLED", "1"))).strip() == "1"
    usfe_block_on = os.getenv("OMEGA_USFE_BLOCK", str(lf.get("OMEGA_USFE_BLOCK", "0"))).strip() == "1"

    if sel_on and sel_audit_veto:
        return False, "SKIP_SEL_AUDIT_VETO", "SEL_AUDIT_VETO"

    bias = str(usfe_bias or "NEUTRAL").upper()
    if usfe_block_on and bias == "BLOCK":
        return False, "SKIP_USFE_BIAS_BLOCK", "USFE_BIAS_BLOCK"

    return True, "OK", ""
