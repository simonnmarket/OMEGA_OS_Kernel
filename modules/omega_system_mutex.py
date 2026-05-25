"""Mutex global OMEGA — CICC remediation 20260520."""
from __future__ import annotations

import atexit
import os
from pathlib import Path

_OMEGA_ROOT = Path(os.getenv("OMEGA_ROOT", r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"))
GLOBAL_LOCK_PATH = _OMEGA_ROOT / "audit" / ".omega_system.lock"
_acquired = False


def acquire_global_mutex() -> bool:
    global _acquired
    try:
        GLOBAL_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(GLOBAL_LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        _acquired = True
        atexit.register(release_global_mutex)
        return True
    except FileExistsError:
        return False


def release_global_mutex() -> None:
    global _acquired
    if GLOBAL_LOCK_PATH.exists() and _acquired:
        try:
            GLOBAL_LOCK_PATH.unlink()
        except OSError:
            pass
    _acquired = False
