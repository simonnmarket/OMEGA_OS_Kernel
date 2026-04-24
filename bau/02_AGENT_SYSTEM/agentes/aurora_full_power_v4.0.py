#!/usr/bin/env python3
"""
BAU Adapter: Aurora Agent System v4.0
Bridges main.py boot sequence to src/agent_system_original.py.
"""
import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parents[3] / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from agent_system_original import (  # noqa: F401 — re-export
    LearningDatabase,
    OllamaAgent,
    AgentCouncil,
    AuroraFullPower,
)
