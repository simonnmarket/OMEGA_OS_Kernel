#!/usr/bin/env python3
"""Gate T+30 — CEO Mandato C+A Observabilidade 20260529"""
import json, re, os, sys
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path

MARKER_TS = datetime(2026, 5, 29, 0, 3, 0)  # reinicio ~00:03 UTC (log local=UTC+1)
LOG_PATH = Path("C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/paper/omega_24x7_runner.log")

def run_gate():
    if not LOG_PATH.exists():
        print("LOG nao encontrado")
        return

    counts = {
        "executed": 0, "skipped": 0, "position_opened": 0,
        "position_closed": 0, "entries_frozen_1": 0,
        "model_dump_errors": 0, "mtf_confluence": 0,
        "ger40_lines": 0, "ukoil_lines": 0, "xagusd_lines": 0,
    }
    skip_reasons = Counter()
    samples = {"ger40": None, "ukoil+": None, "xagusd": None, "forex": None, "crypto": None}
    last_swap = None

    with open(LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if m:
                try:
                    ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                    if ts < MARKER_TS:
                        continue
                except:
                    pass

            if "model_dump" in line.lower() or "has no attribute" in line.lower():
                counts["model_dump_errors"] += 1
            if "MTF_CONFLUENCE" in line:
                counts["mtf_confluence"] += 1
            if "ENTRIES_FROZEN=1" in line:
                counts["entries_frozen_1"] += 1
            if "GER40" in line:
                counts["ger40_lines"] += 1
                if samples["ger40"] is None and "FLOW" in line:
                    samples["ger40"] = line.strip()[:250]
            if "UKOIL+" in line:
                counts["ukoil_lines"] += 1
                if samples["ukoil+"] is None and "FLOW" in line:
                    samples["ukoil+"] = line.strip()[:250]
            if "XAGUSD" in line:
                counts["xagusd_lines"] += 1
                if samples["xagusd"] is None and "FLOW" in line:
                    samples["xagusd"] = line.strip()[:250]
            if "EURUSD" in line or "GBPUSD" in line or "USDJPY" in line:
                if samples["forex"] is None and "FLOW" in line:
                    samples["forex"] = line.strip()[:250]
            if "BTCUSD" in line or "ETHUSD" in line:
                if samples["crypto"] is None and "FLOW" in line:
                    samples["crypto"] = line.strip()[:250]
            if "executed" in line and "total_signals" not in line:
                counts["executed"] += 1
            if "skipped" in line and "total_signals" not in line:
                counts["skipped"] += 1
                sr = re.search(r"\['(.*?)'\]", line)
                if sr and "SKIP" in line:
                    skip_reasons[sr.group(1)[:80]] += 1
            if "position_opened" in line:
                counts["position_opened"] += 1
                if "swap_cost_est" in line:
                    last_swap = line.strip()[:200]
            if "position_closed" in line:
                counts["position_closed"] += 1

    # JSONL trade_feedback check
    tf_path = Path("C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/paper/trade_feedback.jsonl")
    tf_opened = 0
    tf_swap = 0
    if tf_path.exists():
        with open(tf_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    row = json.loads(line)
                    ts = row.get("ts", "")
                    if ts:
                        try:
                            t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if t >= MARKER_TS and row.get("event") == "position_opened":
                                tf_opened += 1
                                if "swap_cost_est_usd" in row:
                                    tf_swap += 1
                        except:
                            pass
                except:
                    pass

    report = []
    report.append("=" * 60)
    report.append("GATE T+30 — CEO MANDATO C+A 2026-05-29")
    report.append(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    report.append(f"Marker: {MARKER_TS.isoformat()}")
    report.append("=" * 60)
    report.append("")
    report.append("[CONTAGENS]")
    for k, v in counts.items():
        report.append(f"  {k}: {v}")
    report.append(f"  trade_feedback position_opened: {tf_opened}")
    report.append(f"  trade_feedback swap_presente: {tf_swap}")
    report.append("")
    report.append("[TOP SKIP REASONS]")
    for reason, cnt in skip_reasons.most_common(10):
        report.append(f"  {cnt}x | {reason}")
    report.append("")
    report.append("[AMOSTRAS ASSET]")
    for asset, sample in samples.items():
        report.append(f"  {asset}: {sample or 'N/A'}")
    report.append("")
    report.append("[SWAP SAMPLE]")
    report.append(f"  {last_swap or 'N/A'}")
    report.append("")
    report.append("[GATES]")
    report.append(f"  model_dump_errors: {'PASS' if counts['model_dump_errors']==0 else 'FAIL'}")
    report.append(f"  ENTRIES_FROZEN=1: {'PASS' if counts['entries_frozen_1']==0 else 'FAIL'} ({counts['entries_frozen_1']})")
    report.append(f"  MTF_CONFLUENCE: {'PASS' if counts['mtf_confluence']>0 else 'CHECK'} ({counts['mtf_confluence']})")
    report.append(f"  GER40 eval: {'PASS' if counts['ger40_lines']>0 else 'FAIL'} ({counts['ger40_lines']})")
    report.append(f"  UKOIL+ eval: {'PASS' if counts['ukoil_lines']>0 else 'FAIL'} ({counts['ukoil_lines']})")
    report.append(f"  XAGUSD eval: {'PASS' if counts['xagusd_lines']>0 else 'FAIL'} ({counts['xagusd_lines']})")
    report.append(f"  swap JSONL: {'PASS' if tf_swap>0 else 'PENDING'} ({tf_swap}/{tf_opened})")
    report.append("=" * 60)

    out = "\n".join(report)
    print(out)

    # Save to forensic
    out_path = Path("C:/OMEGA_QUANTUM_LAB/SOURCE_CODE/audit/forensic/PSA_P0_REMEDIACAO_8Q_GATE_T30_20260529.txt")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out + "\n")
    print(f"\n[Saved] {out_path}")

if __name__ == "__main__":
    run_gate()
