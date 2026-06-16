#!/usr/bin/env python3
"""
BAU Adapter: Prometheus Orchestrator v5.1
Bridges main.py boot sequence to src/executor_original.py (PositionManager).
"""
import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parents[2] / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from executor_original import PositionManager  # noqa: F401 — re-export
