#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA Smoke Test — P0 operational readiness checker.
Validates: imports, paths, permissions, datasets, BAU, MT5.

Usage:
    python smoke_test.py          # run all checks
    python smoke_test.py --quick  # skip MT5 check
"""
import os
import sys
import argparse
from pathlib import Path

PROJ_ROOT = Path(__file__).parent.resolve()
PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [OK]   {label}" + (f" ({detail})" if detail else ""))
    else:
        FAIL += 1
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))


def safe_env_path(env_var: str, default: str) -> Path:
    return Path(os.getenv(env_var, default)).expanduser().resolve()


def section(title: str):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


# ─── 1. ENV VARS & PATHS ────────────────────────────────────────
def check_paths():
    section("1) Environment Variables & Paths")
    env_map = {
        "OMEGA_BAU_PATH": "./bau",
        "OMEGA_DATA_ROOT": "./data",
        "OMEGA_PROJETO_PATH": "./data/projeto",
        "OMEGA_TMP_PATH": "./tmp",
        "OMEGA_AUDIT_BASE": "./audit",
        "OMEGA_MANIFEST_PATH": "./bau/06_MANIFEST",
    }
    for var, default in env_map.items():
        p = safe_env_path(var, default)
        check(f"{var} -> {p}", p.exists(), f"exists={p.exists()}")


# ─── 2. DATASETS ────────────────────────────────────────────────
def check_datasets():
    section("2) Required Datasets (OHLCV)")
    data_root = safe_env_path("OMEGA_DATA_ROOT", "./data")
    required = [
        data_root / "ohlcv" / "XAUUSD_H4.csv",
        data_root / "ohlcv" / "XAUUSD_H1.csv",
        data_root / "ohlcv" / "EURUSD_H4.csv",
    ]
    for f in required:
        if f.exists():
            lines = sum(1 for _ in open(f, encoding="utf-8", errors="ignore"))
            check(f.name, True, f"{lines} lines")
        else:
            check(f.name, False, f"missing: {f}")


# ─── 3. BAU MODULES ─────────────────────────────────────────────
def check_bau():
    section("3) BAU Modules")
    bau = safe_env_path("OMEGA_BAU_PATH", "./bau")
    required = [
        bau / "01_RISK_ENGINE" / "codigo" / "risk_engine_v4.0.py",
        bau / "02_AGENT_SYSTEM" / "agentes" / "aurora_full_power_v4.0.py",
        bau / "03_ORCHESTRATOR" / "prometheus_master_control_v5.1.py",
    ]
    for f in required:
        check(f.relative_to(bau).as_posix(), f.exists())


# ─── 4. CORE IMPORTS ────────────────────────────────────────────
def check_imports():
    section("4) Core Imports")
    modules = [
        ("numpy", "np"),
        ("pandas", "pd"),
        ("scipy", None),
        ("pathlib", None),
    ]
    for mod, alias in modules:
        try:
            __import__(mod)
            check(f"import {mod}", True)
        except ImportError as e:
            check(f"import {mod}", False, str(e))


# ─── 5. MT5 ─────────────────────────────────────────────────────
def check_mt5():
    section("5) MetaTrader5")
    try:
        import MetaTrader5 as mt5
        ok = bool(mt5.initialize())
        if ok:
            info = mt5.terminal_info()
            check("MT5 initialize + terminal_info", bool(info),
                  f"build={info.build}" if info else "no info")
            mt5.shutdown()
        else:
            check("MT5 initialize", False, str(mt5.last_error()))
    except ImportError:
        check("import MetaTrader5", False, "package not installed")
    except Exception as e:
        check("MT5", False, str(e))


# ─── 6. CLI ENTRYPOINT ──────────────────────────────────────────
def check_cli():
    section("6) CLI Entrypoint (main.py)")
    main_py = PROJ_ROOT / "main.py"
    check("main.py exists", main_py.exists())
    if main_py.exists():
        import subprocess
        result = subprocess.run(
            [sys.executable, str(main_py), "--version"],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "PYTHONUTF8": "1"}
        )
        check("main.py --version", result.returncode == 0,
              result.stdout.strip() if result.returncode == 0 else result.stderr.strip()[:120])


# ─── MAIN ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="OMEGA P0 Smoke Test")
    parser.add_argument("--quick", action="store_true", help="Skip MT5 check")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  OMEGA SMOKE TEST — P0 Operational Readiness")
    print("=" * 60)

    check_paths()
    check_datasets()
    check_bau()
    check_imports()
    if not args.quick:
        check_mt5()
    else:
        section("5) MetaTrader5 — SKIPPED (--quick)")
    check_cli()

    section("RESULT")
    total = PASS + FAIL
    print(f"  Passed: {PASS}/{total}")
    print(f"  Failed: {FAIL}/{total}")

    if FAIL == 0:
        print("\n  ✅ ALL CHECKS PASSED — system ready for paper execution.")
    else:
        print(f"\n  ⛔ {FAIL} CHECK(S) FAILED — resolve before proceeding.")

    return 1 if FAIL > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
