#!/usr/bin/env python3
"""
BAU Adapter: Risk Engine v4.0
Bridges main.py boot sequence to the canonical src/risk_engine.py module.
"""
import sys
from pathlib import Path

# Ensure src/ is importable
_src = str(Path(__file__).resolve().parents[3] / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from risk_engine import RiskEngine  # noqa: F401 — re-export
