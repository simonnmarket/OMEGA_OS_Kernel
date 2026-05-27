"""Mutex global OMEGA — CICC remediation 20260520."""
from __future__ import annotations

import atexit
import os
from pathlib import Path

_OMEGA_ROOT = Path(os.getenv("OMEGA_ROOT", r"C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"))
GLOBAL_LOCK_PATH = _OMEGA_ROOT / "audit" / ".omega_system.lock"
_acquired = False


def _pid_alive(pid: int) -> bool:
    """Verifica se um PID está activo. Robusto em Windows e Unix."""
    if pid <= 0:
        return False
    try:
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return ctypes.get_last_error() != 87  # 87=ERROR_INVALID_PARAMETER → PID inexistente
    except Exception:
        pass
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except Exception:
        return True


def acquire_global_mutex(retry: int = 0) -> bool:
    """
    Adquire mutex de ficheiro exclusivo.
    FIX 2026-05-27: verifica se o PID no lock ainda está vivo — evita bloqueio
    permanente quando o processo anterior foi morto forçadamente (Stop-Process -Force
    não chama atexit, deixando o ficheiro lock órfão).
    """
    global _acquired
    if retry > 3:
        return False
    GLOBAL_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(GLOBAL_LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        _acquired = True
        atexit.register(release_global_mutex)
        return True
    except FileExistsError:
        pass
    # Lock existente — verificar se o dono ainda está vivo
    try:
        stale_pid = int(GLOBAL_LOCK_PATH.read_text(encoding="utf-8").strip())
    except Exception:
        # Ficheiro corrompido — remover e tentar de novo
        try:
            GLOBAL_LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            pass
        return acquire_global_mutex(retry + 1)
    if stale_pid == os.getpid():
        # Somos nós próprios (re-entrada)
        _acquired = True
        return True
    if not _pid_alive(stale_pid):
        # PID morto (processo foi killed forçadamente) — lock órfão, remover
        try:
            GLOBAL_LOCK_PATH.unlink()
        except OSError:
            pass
        return acquire_global_mutex(retry + 1)
    # PID vivo — outro processo OMEGA activo
    return False


def release_global_mutex() -> None:
    global _acquired
    if _acquired and GLOBAL_LOCK_PATH.exists():
        try:
            GLOBAL_LOCK_PATH.unlink()
        except OSError:
            pass
    _acquired = False
