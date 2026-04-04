"""
Validação Tier-0: 23 tabelas, import do pacote, GATE_GLOBAL.
Executar a partir de qualquer cwd:
  python scripts/validate_hub_integrity.py
"""

from __future__ import annotations

import sys
from pathlib import Path

EXPECTED_TABLES = 23


def _pkg_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(_pkg_root()))
    from fin_sense_data_module.schemas.schema_definitions import list_tables
    from fin_sense_data_module import SCHEMA_VERSION, __version__

    tables = list_tables()
    ok = len(tables) == EXPECTED_TABLES
    print(f"package_version={__version__} schema={SCHEMA_VERSION} tables={len(tables)}")
    if not ok:
        print(f"GATE_GLOBAL: FAIL (expected {EXPECTED_TABLES} tables, got {len(tables)})")
        return 1
    print("GATE_GLOBAL: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
