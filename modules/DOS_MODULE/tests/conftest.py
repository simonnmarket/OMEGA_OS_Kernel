"""Garante import do pacote FIN-SENSE no mesmo checkout (monorepo)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_FIN = _ROOT.parent / "FIN_SENSE_DATA_MODULE"
if _FIN.is_dir():
    sys.path.insert(0, str(_FIN))
