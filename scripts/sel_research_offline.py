#!/usr/bin/env python3
"""SEL L4/L5 — Cold path only (geometria). NÃO importar no runner 24/7."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

print("SEL research offline — L4/L5 reserved for Desktop batch. Runner must not load this module.")
