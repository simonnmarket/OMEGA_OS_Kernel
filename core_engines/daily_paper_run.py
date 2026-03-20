#!/usr/bin/env python3
"""
OMEGA DAILY PAPER RUN — Script de execução diária controlada.
Roda o paper loop MT5 Tier-1, loga SHA3 do summary e grava telemetria acumulada.

Uso (executar diariamente via Task Scheduler ou manualmente):
  python core_engines\daily_paper_run.py --equity 10000 --sessions 3

Sessões: cada sessão roda 3 ciclos (MAX_POSITIONS limit) para acumular >50 retcodes
ao longo dos 7-14 dias do período de validação.
"""

import argparse
import hashlib
import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT       = Path(__file__).resolve().parent.parent
AUDIT_PAPER = ROOT / "audit" / "paper"
AUDIT_PAPER.mkdir(parents=True, exist_ok=True)

# Telemetria acumulada entre dias
TELEM_FILE = AUDIT_PAPER / "cumulative_telemetry.json"

log_file = AUDIT_PAPER / f"daily_run_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("DAILY")

TIER1 = [
    "XAUUSD", "GBPUSD", "USDJPY", "AUDUSD",
    "AUDJPY", "ETHUSD", "US500", "SOLUSD", "DOGUSD",
]


def sha3_file(path: Path) -> str:
    return hashlib.sha3_256(path.read_bytes()).hexdigest()


def load_cumulative() -> dict:
    if TELEM_FILE.exists():
        with open(TELEM_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "start_date": datetime.now(timezone.utc).isoformat(),
        "target_end":  "",
        "total_sessions": 0,
        "total_orders":   0,
        "ks_activations": 0,
        "fills":          [],
        "daily_hashes":   [],
        "retcode_counts": {},
        "slippage_pts":   [],
        "latencies_ms":   [],
        "hit_rates":      [],
    }


def save_cumulative(data: dict):
    jb = json.dumps(data, indent=2).encode("utf-8")
    data["checksum"] = hashlib.sha3_256(jb).hexdigest()
    with open(TELEM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def run_paper_session(equity: float, session_num: int) -> dict:
    log.info("── Sessão %d ──────────────────────────────", session_num)
    cmd = [
        sys.executable,
        str(ROOT / "core_engines" / "shadow_loop.py"),
        "--mode", "paper",
        "--ativos", *TIER1,
        "--timeframes", "H1", "H4",
        "--equity", str(equity),
    ]
    t0  = time.perf_counter()
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    elapsed = round(time.perf_counter() - t0, 1)
    log.info("Sessão %d concluída em %.1fs | exit=%d", session_num, elapsed, res.returncode)
    if res.returncode not in (0, 1):
        log.error("ERRO sessão %d: %s", session_num, res.stderr[:300])
    # Ler summary
    summary_f = AUDIT_PAPER / "paper_summary.json"
    if summary_f.exists():
        with open(summary_f, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(description="OMEGA Daily Paper Run")
    parser.add_argument("--equity",   type=float, default=10_000.0)
    parser.add_argument("--sessions", type=int,   default=3,
                        help="Número de sessões por execução diária (cada uma = 3 ordens)")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log.info("=" * 68)
    log.info("OMEGA DAILY PAPER RUN | %s | sessions=%d | equity=%.0f",
             today, args.sessions, args.equity)
    log.info("=" * 68)

    cumul = load_cumulative()
    if not cumul.get("target_end"):
        from datetime import timedelta
        start = datetime.now(timezone.utc)
        end   = start + timedelta(days=14)
        cumul["start_date"] = start.isoformat()
        cumul["target_end"] = end.isoformat()
        log.info("Início do período paper: %s → %s", start.date(), end.date())

    day_orders = 0
    day_ks     = 0

    for i in range(1, args.sessions + 1):
        summary = run_paper_session(args.equity, i)
        cumul["total_sessions"] += 1

        results = summary.get("results", [])
        ks      = summary.get("kill_switch", False)
        if ks:
            cumul["ks_activations"] += 1
            day_ks += 1
            log.critical("💀 KILL SWITCH na sessão %d — interrompendo dia!", i)
            break

        for r in results:
            if r.get("status") in ("MT5_PAPER_EXECUTE", "MONITOR"):
                day_orders += 1
                cumul["total_orders"] += 1
                retcode = str(r.get("retcode", ""))
                cumul["retcode_counts"][retcode] = cumul["retcode_counts"].get(retcode, 0) + 1
                if r.get("slippage_pts") is not None:
                    cumul["slippage_pts"].append(r["slippage_pts"])
                if r.get("hit_rate_134") is not None:
                    cumul["hit_rates"].append(r["hit_rate_134"])
                cumul["fills"].append({
                    "date": today, "session": i,
                    "asset": r.get("asset"), "tf": r.get("timeframe"),
                    "hit_rate": r.get("hit_rate_134"),
                    "retcode": r.get("retcode"),
                    "slip_pts": r.get("slippage_pts"),
                    "checksum": r.get("checksum"),
                })

        # Hash diário do summary
        summary_f = AUDIT_PAPER / "paper_summary.json"
        if summary_f.exists():
            h = sha3_file(summary_f)
            cumul["daily_hashes"].append({"date": today, "session": i, "sha3": h})
            log.info("SHA3 sessão %d: %s", i, h)

        time.sleep(2)  # Pausa entre sessões

    # Estatísticas acumuladas
    n_slip = max(len(cumul["slippage_pts"]), 1)
    n_hrs  = max(len(cumul["hit_rates"]), 1)
    avg_slip = sum(cumul["slippage_pts"]) / n_slip
    avg_hr   = sum(cumul["hit_rates"]) / n_hrs

    log.info("── TELEMETRIA ACUMULADA ────────────────────────────────────")
    log.info("Total sessões  : %d", cumul["total_sessions"])
    log.info("Total ordens   : %d / 50 (objetivo)", cumul["total_orders"])
    log.info("KS ativações   : %d", cumul["ks_activations"])
    log.info("Avg HR-134     : %.4f%%", avg_hr)
    log.info("Avg slippage   : %.3f pts", avg_slip)
    log.info("Retcodes dist  : %s", json.dumps(cumul["retcode_counts"]))
    log.info("Ordens hoje    : %d | KS hoje: %d", day_orders, day_ks)

    # Critério de aprovação para live
    dias_decorridos = cumul["total_sessions"] // args.sessions
    pronto_live = (
        dias_decorridos >= 7 and
        cumul["ks_activations"] == 0 and
        avg_hr >= 95.0 and
        avg_slip < 5.0 and
        cumul["total_orders"] >= 50
    )
    log.info("PRONTO_LIVE: %s (dias≥7=%s, KS=0=%s, HR≥95%%=%s, slip<5=%s, orders≥50=%s)",
             "✅ SIM" if pronto_live else "❌ NÃO",
             dias_decorridos >= 7, cumul["ks_activations"] == 0,
             avg_hr >= 95.0, avg_slip < 5.0, cumul["total_orders"] >= 50)

    save_cumulative(cumul)
    log.info("Telemetria acumulada salva: %s", TELEM_FILE)
    log.info("=" * 68)

    return 0 if day_ks == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
