#!/usr/bin/env python3
"""
OMEGA — runner 24/7 para shadow_loop / paper (reinicia após cada ciclo).

- Opcionalmente corre export_ohlcv_mt5.py antes de cada ciclo (OHLCV Motor V3).
- Em falha (exit != 0 ou exceção): regista, espera com backoff exponencial e repete.
  Isto NÃO substitui kill switch / risco do paper no broker; apenas evita que o
  processo termine por erro transitório (MT5, rede, ficheiros em falta após sync).

Uso (PowerShell, a partir da raiz SOURCE_CODE):
  $env:PYTHONPATH = (Get-Location).Path
  python scripts/omega_paper_loop_24x7.py --mode paper --ativos BTCUSD ETHUSD ADAUSD --timeframes H1 M15 H4

Ou via ambiente (ativos separados por espaço ou vírgula):
  $env:OMEGA_24X7_ATIVOS = "BTCUSD ETHUSD ADAUSD XRPUSD SOLUSD AVAXUSD LTCUSD BNBUSD"
  $env:OMEGA_24X7_MODE = "paper"
  python scripts/omega_paper_loop_24x7.py

Variáveis úteis:
  OMEGA_LOOP_INTERVAL_SEC — segundos mínimos entre fim de um ciclo e início do próximo (default 10)
  OMEGA_24X7_LOG — ficheiro de log (default audit/paper/omega_24x7_runner.log)
"""
from __future__ import annotations

import argparse
import errno
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# FIX #5 (CEO 2026-05-14): Singleton lock — impede multiplas instancias simultaneas.
# Nota retcodes MT5: 10024 = TOO_MANY_REQUESTS (frequencia); 10025 = NO_CHANGES (SL/TP igual).
# Multi-processo + spam SLTP tendia a 10024; lock + noop SLTP no shadow_loop reduz ambos.
_LOCK_FILE = ROOT / "audit" / "paper" / "omega_runner.lock"

def _pid_alive(pid: int) -> bool:
    """Best-effort: True se o PID parece corresponder a um processo activo."""
    if pid <= 0:
        return False
    try:
        import psutil

        return bool(psutil.pid_exists(pid))
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
            err = ctypes.get_last_error()
            # 87 = ERROR_INVALID_PARAMETER — PID inexistente
            return err != 87
        except Exception:
            return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return True
    return True


def _acquire_singleton_lock(_retry: int = 0) -> bool:
    """
    Lock exclusivo entre instâncias do runner (CEO OIS-20260517).
    Usa criação atómica (O_EXCL) + verificação de PID para evitar corrida e lock obsoleto.
    """
    if _retry > 6:
        return False
    max_par = int(os.getenv("OMEGA_RUNNER_MAX_PARALLEL", "1"))
    if max_par != 1:
        if max_par == 0:
            print(
                "[SINGLETON] OMEGA_RUNNER_MAX_PARALLEL=0 — lock desactivado; "
                "podem existir ciclos paralelos no mesmo ficheiro de log.",
                file=sys.stderr,
                flush=True,
            )
        return True
    _LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(_LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, str(os.getpid()).encode("ascii"))
        finally:
            os.close(fd)
        return True
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    try:
        existing_pid = int(_LOCK_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        try:
            _LOCK_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        return _acquire_singleton_lock(_retry + 1)
    if existing_pid == os.getpid():
        return True
    if _pid_alive(existing_pid):
        return False
    try:
        _LOCK_FILE.unlink()
    except Exception:
        return False
    return _acquire_singleton_lock(_retry + 1)

def _release_singleton_lock() -> None:
    try:
        if _LOCK_FILE.exists():
            _LOCK_FILE.unlink()
    except Exception:
        pass
EXPORT_SCRIPT = ROOT / "scripts" / "export_ohlcv_mt5.py"
SHADOW_LOOP = ROOT / "core_engines" / "shadow_loop.py"
DEFAULT_LOG = ROOT / "audit" / "paper" / "omega_24x7_runner.log"


def _setup_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    lg = logging.getLogger("omega24x7")
    lg.setLevel(logging.INFO)
    lg.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    lg.addHandler(fh)
    lg.addHandler(sh)
    lg.propagate = False
    return lg


def _env_with_pythonpath() -> dict[str, str]:
    env = os.environ.copy()
    pp = env.get("PYTHONPATH", "")
    root_s = str(ROOT)
    if root_s not in pp.split(os.pathsep):
        env["PYTHONPATH"] = root_s if not pp else f"{root_s}{os.pathsep}{pp}"
    return env


def _parse_ativos_from_env() -> list[str] | None:
    raw = (os.getenv("OMEGA_24X7_ATIVOS") or "").strip()
    if not raw:
        return None
    parts = raw.replace(",", " ").split()
    return [p.strip() for p in parts if p.strip()]


def run_export(symbols: list[str], timeframes: list[str], bars: int, env: dict[str, str]) -> int:
    cmd = [
        sys.executable,
        "-u",
        str(EXPORT_SCRIPT),
        "--symbols",
        *symbols,
        "--timeframes",
        *timeframes,
        "--bars",
        str(bars),
        "--out-dir",
        str(ROOT / "data" / "ohlcv"),
    ]
    p = subprocess.run(cmd, cwd=str(ROOT), env=env)
    return int(p.returncode)


def run_shadow(
    mode: str,
    ativos: list[str],
    timeframes: list[str],
    equity: float,
    env: dict[str, str],
    log_path: Path | None = None,
) -> int:
    cmd = [
        sys.executable,
        "-u",
        str(SHADOW_LOOP),
        "--mode",
        mode,
        "--ativos",
        *ativos,
        "--timeframes",
        *timeframes,
        "--equity",
        str(equity),
    ]
    # ── LOG FIX 2026-05-13: capturar stdout/stderr do shadow_loop no runner log ──
    # shadow_loop.py escreve para stdout; sem captura, [M1-GATE]/[P&D] não aparecem no log
    if log_path is not None:
        try:
            proc = subprocess.Popen(
                cmd, cwd=str(ROOT), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1,
            )
            with open(log_path, "a", encoding="utf-8") as _lf:
                for _line in proc.stdout:
                    _line = _line.rstrip()
                    if _line:
                        _lf.write(_line + "\n")
                        _lf.flush()
            proc.wait()
            return int(proc.returncode)
        except Exception as _pe:
            # fallback sem captura
            pass
    p = subprocess.run(cmd, cwd=str(ROOT), env=env)
    return int(p.returncode)


def _get_mt5_equity() -> float:
    """P2-A BUG-5 FIX: Lê equity real do MT5. Evita divergência CLI vs conta real."""
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            acct = mt5.account_info()
            if acct and acct.equity > 0:
                eq = float(acct.equity)
                mt5.shutdown()
                return eq
    except Exception:
        pass
    return 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description="OMEGA 24/7 — shadow_loop com retentativas e sync OHLCV")
    ap.add_argument(
        "--mode",
        choices=["shadow", "paper"],
        default=os.getenv("OMEGA_24X7_MODE", "shadow").strip().lower() or "shadow",
    )
    ap.add_argument("--ativos", nargs="+", default=None, help="Ou defina OMEGA_24X7_ATIVOS")
    ap.add_argument("--timeframes", nargs="+", default=["H1", "M15", "H4"])
    ap.add_argument("--equity", type=float, default=float(os.getenv("OMEGA_24X7_EQUITY", "10000")))
    ap.add_argument(
        "--pre-sync-ohlcv",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Antes de cada ciclo: export_ohlcv_mt5.py para os mesmos --ativos/--timeframes",
    )
    ap.add_argument("--bars", type=int, default=12_000, help="Barras MT5 por símbolo/TF no export")
    ap.add_argument(
        "--min-interval-sec",
        type=float,
        default=float(os.getenv("OMEGA_LOOP_INTERVAL_SEC", "10")),
        help="Espera mínima após cada ciclo (sucesso ou falha) antes do próximo",
    )
    ap.add_argument("--retry-base-sec", type=float, default=30.0)
    ap.add_argument("--retry-max-sec", type=float, default=300.0)
    ap.add_argument(
        "--log-file",
        default=os.getenv("OMEGA_24X7_LOG", str(DEFAULT_LOG)),
        help="Log do runner (ficheiro + consola)",
    )
    args = ap.parse_args()

    ativos = args.ativos or _parse_ativos_from_env()
    if not ativos:
        ap.error("Indique --ativos … ou defina a variável de ambiente OMEGA_24X7_ATIVOS")

    # FIX #5: singleton lock — bloquear segunda instancia
    if not _acquire_singleton_lock():
        existing = _LOCK_FILE.read_text().strip() if _LOCK_FILE.exists() else "?"
        print(f"[SINGLETON] Runner ja activo (PID={existing}). A sair. "
              f"Para desactivar: set OMEGA_RUNNER_MAX_PARALLEL=0", flush=True)
        return 1

    log_path = Path(args.log_file)
    log = _setup_logger(log_path)

    # P1-B C1 FIX: validação de portfolio obrigatória no arranque
    ASSETS_REQUIRED = {"EURUSD", "XAUUSD", "BTCUSD"}
    current_assets = set(ativos)
    missing = ASSETS_REQUIRED - current_assets
    if missing:
        log.critical(
            "[STARTUP_BLOCK] Portfolio incompleto! Faltam: %s. "
            "Runner não inicia sem ativos obrigatórios.", missing
        )
        return 1
    log.info("[PORTFOLIO_VALID] Ativos confirmados: %s", sorted(current_assets))

    # P2-A BUG-5 FIX: equity real MT5 substitui CLI se divergência > 10%%
    if args.mode == "paper":
        real_eq = _get_mt5_equity()
        if real_eq > 0:
            divergence = abs(real_eq - args.equity) / max(args.equity, 1)
            if divergence > 0.10:
                log.warning(
                    "[EQUITY] CLI=%.2f MT5=%.2f (%.0f%% divergência) — usando MT5",
                    args.equity, real_eq, divergence * 100
                )
            args.equity = real_eq
            log.info("[EQUITY] Equity MT5 real: $%.2f", args.equity)

    env = _env_with_pythonpath()
    fail_streak = 0
    cycle = 0

    log.info(
        "ROOT=%s | mode=%s | ativos=%s | pre_sync=%s | log=%s",
        ROOT,
        args.mode,
        ativos,
        args.pre_sync_ohlcv,
        log_path,
    )

    while True:
        cycle += 1
        t0 = time.monotonic()
        rc_export = 0
        try:
            try:
                from core_engines.omega_evaluation_context import (
                    build_evaluation_context,
                    format_eval_log_line,
                )

                _runner_eval = build_evaluation_context()
                log.info(
                    "[EVAL_CONTEXT] runner_cycle=%d | %s",
                    cycle,
                    format_eval_log_line(_runner_eval),
                )
            except Exception as _ev_err:
                log.warning("[EVAL_CONTEXT] cycle=%d (skip: %s)", cycle, _ev_err)
            if args.pre_sync_ohlcv:
                log.info("ciclo %d | export OHLCV MT5…", cycle)
                rc_export = run_export(ativos, args.timeframes, args.bars, env)
                if rc_export != 0:
                    log.warning("ciclo %d | export terminou com código %d", cycle, rc_export)
                    # P1-A C2 FIX: bloquear shadow se export falhou — dados obsoletos proibidos
                    log.warning(
                        "[OHLCV] Export falhou (rc=%d) — shadow_loop SUSPENSO. Dados obsoletos proibidos.",
                        rc_export
                    )
                    _fail_log = ROOT / "audit" / "export_failures.log"
                    _fail_log.parent.mkdir(parents=True, exist_ok=True)
                    with open(_fail_log, "a") as _f:
                        import datetime as _dt
                        _f.write(f"{_dt.datetime.utcnow().isoformat()} | rc={rc_export} | ativos={ativos}\n")
                    continue  # NÃO executar shadow com dados obsoletos

            log.info("ciclo %d | shadow_loop…", cycle)
            rc = run_shadow(args.mode, ativos, args.timeframes, args.equity, env, log_path=log_path)
            # Export parcial (broker sem alguns símbolos) não deve manter backoff eterno
            if rc == 0:
                fail_streak = 0
                log.info("ciclo %d OK | shadow_rc=0 export_rc=%d", cycle, rc_export)
            else:
                fail_streak += 1
                log.warning(
                    "ciclo %d falha | shadow_rc=%d export_rc=%d streak=%d",
                    cycle,
                    rc,
                    rc_export,
                    fail_streak,
                )
        except KeyboardInterrupt:
            log.info("Interrompido pelo utilizador.")
            _release_singleton_lock()
            return 0
        except Exception as e:
            fail_streak += 1
            log.exception("ciclo %d exceção: %s", cycle, e)

        extra = 0.0
        if fail_streak > 0:
            extra = min(args.retry_max_sec, args.retry_base_sec * (2 ** min(fail_streak - 1, 6)))
        elapsed = time.monotonic() - t0
        wait = max(0.0, args.min_interval_sec - elapsed) + extra
        if wait > 0:
            log.info("aguardar %.1fs antes do próximo ciclo…", wait)
            time.sleep(wait)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        _release_singleton_lock()
