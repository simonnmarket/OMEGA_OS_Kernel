"""Verificação de boot CIO — CICC remediation 20260520 (teste local, sem MT5)."""
from __future__ import annotations

import logging
import os


def cio_boot_verify(logger: logging.Logger | None = None) -> bool:
    """Confirma que o dict de ordem inclui magic antes de trading."""
    log = logger or logging.getLogger("omega.cio_verify")
    magic = int(os.getenv("OMEGA_MAGIC_NUMBER", "234001"))
    lock = os.getenv("OMEGA_ROOT", r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE") + r"\audit\.omega_system.lock"
    log.info("[CIO-VERIFY] MAGIC_ENABLED = %s", magic)
    log.info("[CIO-VERIFY] MUTEX_GLOBAL = %s", lock)
    test_dict = {
        "symbol": "EURUSD",
        "magic": magic,
        "comment": "OV2|VERIFY|BOOT|H",
        "volume": 0.01,
    }
    if test_dict.get("magic") != magic:
        log.critical("[CIO-VERIFY] FAIL — magic ausente no dict teste")
        return False
    log.info("[CIO-VERIFY] PASS — dict contém magic=%s", magic)
    return True
