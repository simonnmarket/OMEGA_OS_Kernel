"""Configuração central (env) — sem credenciais hardcoded."""

from __future__ import annotations

import os


def get_dos_schema() -> str:
    return os.getenv("DOS_PG_SCHEMA", "dos")


def fin_sense_schema_version() -> str:
    return os.getenv("FIN_SENSE_SCHEMA_VERSION", "1.2.0")


def dos_module_version() -> str:
    from omega_dos import __version__

    return __version__
