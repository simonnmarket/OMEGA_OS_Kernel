#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 OMEGA BRIDGE RUNNER — Opção B (Runner Dedicado)
=============================================================================
ID      : BRIDGE-RUNNER-001
Versão  : 1.0.0
Data    : 2026-05-17
Decisão : Conselho OMEGA — 17/05/2026

ARQUITECTURA (Opção B aprovada):
  shadow_loop.py  ──────────────────────────────────────────────────────────
    (execução MT5 nativa — fonte de verdade, não alterada)
                                │
                                │ escreve OMEGA_SIGNAL.<SYMBOL>.json
                                ▼
  audit/bridge/signals/     ←── pasta monitorizada por este runner
                                │
                                ▼
  ComponentEngine.execute_signal()   ←── omega_execution_bridge_v2_2.py
                                │
                                ▼
  AIRequest.<SYMBOL>.json  →  MT5 Common Files  ←  EA MQL5 (obrigatório)
                                │
                                ▼
  AIResponse.<SYMBOL>.json  ←  EA MQL5 escreve resposta
                                │
                                ▼
  audit/bridge/bridge_runner.jsonl  (log de auditoria)

PRÉ-REQUISITO OBRIGATÓRIO:
  EA MQL5 activo a ler AIRequest e escrever AIResponse em Common Files.
  Sem EA, este runner apenas valida a escrita atómica (teste de ficheiro).

OPÇÃO A (FUTURO — condicionada):
  Requer desenho aprovado + OMEGA_FILE_BRIDGE_AFTER_DECISION=1 +
  regra anti-duplicação mt5_send_order por ticket/ciclo.
  O B6 no shadow_loop NÃO avança sem desenho assinado pelo Conselho.

INICIAR:
  python scripts/omega_bridge_runner.py
  python scripts/omega_bridge_runner.py --mql5-dir "C:\\...\\Common\\Files"
  python scripts/omega_bridge_runner.py --dry-run      # sem escrita MT5
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.omega_execution_bridge_v2_2 import ComponentEngine, BridgeConfig

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [BRIDGE_RUNNER] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("OMEGA.BRIDGE_RUNNER")

# ── Caminhos default ───────────────────────────────────────────────────────
_ROOT         = Path(__file__).parent.parent
_SIGNAL_DIR   = _ROOT / "audit" / "bridge" / "signals"
_AUDIT_JSONL  = _ROOT / "audit" / "bridge" / "bridge_runner.jsonl"
_KS_FILE      = _ROOT / "audit" / "risk" / "ks_daily_state.json"

# ── Constantes ─────────────────────────────────────────────────────────────
SIGNAL_GLOB       = "OMEGA_SIGNAL.*.json"
POLL_INTERVAL_S   = float(os.getenv("OMEGA_BRIDGE_POLL_S", "1.0"))
MAX_SIGNAL_AGE_S  = float(os.getenv("OMEGA_BRIDGE_MAX_SIGNAL_AGE_S", "30.0"))


def _append_audit(record: dict) -> None:
    """Append de linha ao JSONL de auditoria do bridge."""
    try:
        _AUDIT_JSONL.parent.mkdir(parents=True, exist_ok=True)
        with open(_AUDIT_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception as e:
        log.error("Falha ao escrever audit JSONL: %s", e)


def _load_signal(path: Path) -> dict | None:
    """Lê e valida um ficheiro de sinal. Retorna None se inválido."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        required = {"symbol", "action", "confidence"}
        if not required.issubset(data.keys()):
            log.warning("[SKIP] %s — campos em falta: %s", path.name, required - set(data.keys()))
            return None
        if data.get("action", "").upper() not in ("BUY", "SELL"):
            log.warning("[SKIP] %s — action inválida: %s", path.name, data.get("action"))
            return None
        return data
    except Exception as e:
        log.error("[SKIP] %s — JSON inválido: %s", path.name, e)
        return None


def _signal_too_old(path: Path) -> bool:
    """Descarta sinais mais antigos que MAX_SIGNAL_AGE_S (evitar execução de sinais obsoletos)."""
    try:
        age = time.time() - path.stat().st_mtime
        if age > MAX_SIGNAL_AGE_S:
            log.warning("[STALE] %s — sinal com %.0fs (máx: %.0fs) — descartado",
                        path.name, age, MAX_SIGNAL_AGE_S)
            return True
    except Exception:
        pass
    return False


def process_signal(path: Path, engine: ComponentEngine, dry_run: bool) -> None:
    """Processa um único ficheiro de sinal."""
    sig = _load_signal(path)
    if sig is None:
        path.unlink(missing_ok=True)
        return

    if _signal_too_old(path):
        path.unlink(missing_ok=True)
        _append_audit({
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "signal_stale",
            "file": path.name,
            "symbol": sig.get("symbol"),
        })
        return

    symbol     = str(sig["symbol"]).upper()
    action     = str(sig["action"]).upper()
    confidence = float(sig.get("confidence", 0.0))
    volume     = float(sig.get("volume", 0.01))
    voltage    = float(sig.get("voltage", 0.0))
    components = int(sig.get("components_fired", 0) or 0)

    log.info("[SIGNAL] %s %s conf=%.3f vol=%.4f components=%d%s",
             symbol, action, confidence, volume, components,
             " [DRY-RUN]" if dry_run else "")

    if dry_run:
        path.unlink(missing_ok=True)
        _append_audit({
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "dry_run",
            "symbol": symbol,
            "action": action,
            "confidence": confidence,
        })
        return

    state = engine.execute_signal(
        symbol=symbol,
        action=action,
        confidence=confidence,
        volume=volume,
        voltage=voltage,
        components_fired=components,
    )

    record = {
        "ts":                datetime.now(timezone.utc).isoformat(),
        "event":             "bridge_executed",
        "symbol":            symbol,
        "action":            action,
        "confidence":        confidence,
        "is_valid":          state.is_valid,
        "direction":         state.direction,
        "strength":          round(state.strength, 4),
        "atomic_write_ok":   state.atomic_write_success,
        "feedback_received": state.feedback_received,
        "write_latency_us":  state.write_latency_us,
        "exec_latency_us":   state.execution_latency_us,
        "ks_passed":         state.ks_check_passed,
        "warning":           state.warning,
    }
    _append_audit(record)

    if state.warning:
        log.warning("[%s] %s", symbol, state.warning)
    if state.is_valid:
        log.info("[%s] OK — write=%.0fµs total=%.0fµs feedback=%s",
                 symbol, state.write_latency_us, state.execution_latency_us,
                 "YES" if state.feedback_received else "NO (timeout)")
    else:
        log.error("[%s] FALHA — is_valid=False ks=%s", symbol, state.ks_check_passed)

    path.unlink(missing_ok=True)


def run(args: argparse.Namespace) -> None:
    """Loop principal do runner dedicado (Opção B)."""
    _SIGNAL_DIR.mkdir(parents=True, exist_ok=True)
    _AUDIT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    mql5_dir = args.mql5_dir or ""
    regime   = args.regime or "default"

    engine = ComponentEngine.from_config(
        regime,
        mql5_data_dir=mql5_dir,
        require_ks_check=(not args.no_ks),
        ks_anchor_file=str(_KS_FILE),
    )

    log.info("=" * 64)
    log.info("OMEGA BRIDGE RUNNER v1.0.0 — Opção B (Runner Dedicado)")
    log.info("Signal dir : %s", _SIGNAL_DIR)
    log.info("MQL5 dir   : %s", engine._data_dir)
    log.info("Regime     : %s | Timeout: %.1fs", regime, engine._cfg.response_timeout_s)
    log.info("KS check   : %s | Dry-run: %s", not args.no_ks, args.dry_run)
    log.info("Audit JSONL: %s", _AUDIT_JSONL)
    if args.dry_run:
        log.warning("[DRY-RUN] Modo activo — AIRequest NÃO será escrito")
    if not mql5_dir:
        log.warning("[AVISO] --mql5-dir não definido — a usar APPDATA\\MetaQuotes\\Terminal\\Common\\Files")
    log.info("=" * 64)

    _append_audit({
        "ts":    datetime.now(timezone.utc).isoformat(),
        "event": "runner_start",
        "regime": regime,
        "mql5_dir": str(engine._data_dir),
        "dry_run": args.dry_run,
    })

    # ── Graceful shutdown ──────────────────────────────────────────────────
    _running = [True]

    def _stop(sig, frame):
        log.info("[SHUTDOWN] Sinal %s recebido — a terminar...", sig)
        _running[0] = False

    signal.signal(signal.SIGINT,  _stop)
    signal.signal(signal.SIGTERM, _stop)

    processed = 0
    while _running[0]:
        signals = sorted(_SIGNAL_DIR.glob(SIGNAL_GLOB))
        for sig_path in signals:
            if not _running[0]:
                break
            process_signal(sig_path, engine, dry_run=args.dry_run)
            processed += 1
        if not signals:
            time.sleep(POLL_INTERVAL_S)

    _append_audit({
        "ts":        datetime.now(timezone.utc).isoformat(),
        "event":     "runner_stop",
        "processed": processed,
    })
    log.info("Runner terminado. Sinais processados: %d", processed)


def _self_test() -> bool:
    """Verificação rápida de arranque (sem EA, sem ficheiro MT5)."""
    import tempfile
    log.info("[SELF-TEST] Iniciando...")
    errors = []

    with tempfile.TemporaryDirectory() as tmpdir:
        sig_dir = Path(tmpdir) / "signals"
        sig_dir.mkdir()

        sig_file = sig_dir / "OMEGA_SIGNAL.XAUUSD.json"
        sig_file.write_text(json.dumps({
            "symbol": "XAUUSD", "action": "BUY",
            "confidence": 0.85, "volume": 0.01,
            "voltage": 2.5, "components_fired": 3,
        }), encoding="utf-8")

        eng = ComponentEngine.from_config("metal", mql5_data_dir=tmpdir, require_ks_check=False)

        sig = _load_signal(sig_file)
        if sig is None:
            errors.append("T01: load_signal devolveu None")
        if _signal_too_old(sig_file):
            errors.append("T02: sinal fresco marcado como stale")

        process_signal(sig_file, eng, dry_run=True)
        if sig_file.exists():
            errors.append("T03: ficheiro não foi removido após dry-run")

    if errors:
        for e in errors:
            log.error("[SELF-TEST] %s", e)
        return False
    log.info("[SELF-TEST] All self-tests PASSED — BridgeRunner v1.0.0")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OMEGA Bridge Runner v1.0.0 — Opção B (runner dedicado)"
    )
    parser.add_argument("--mql5-dir", default="",
                        help="Pasta MT5 Common Files (default: APPDATA\\MetaQuotes\\Terminal\\Common\\Files)")
    parser.add_argument("--regime", default="default",
                        choices=["default", "forex", "crypto", "metal"],
                        help="Regime de execução (default: default)")
    parser.add_argument("--no-ks", action="store_true",
                        help="Desactivar Kill Switch check (só testes)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry-run: processa sinais mas NÃO escreve AIRequest")
    parser.add_argument("--self-test", action="store_true",
                        help="Executar self-test e sair")
    args = parser.parse_args()

    if args.self_test:
        sys.exit(0 if _self_test() else 1)

    run(args)


if __name__ == "__main__":
    main()
