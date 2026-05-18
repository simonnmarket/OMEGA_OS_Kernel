#!/usr/bin/env python3
"""
Constrói o pacote OMEGA_DIAGNOSTIC_DATA_20260518/ conforme pedido CEO v2.0.

- raw/: CSV/JSON com naming OMEGA_DIAGNOSTIC_*_20260518.*
- aggregated/: métricas derivadas
- README.md: método, issues, validação básica

Fontes: PSA_PACOTE_TIER0_20260518_204618Z, audit/paper/*, evaluation_timeline.jsonl, logs.

Uso (raiz SOURCE_CODE):
  python scripts/build_omega_diagnostic_package_20260518.py
  python scripts/build_omega_diagnostic_package_20260518.py --flow-signal-local-offset-hours 3

Opcional:
  --flow-signal-local-offset-hours N  — se o prefixo de data nos logs FlowSignal for relógio local
    broker UTC+N (naive), subtrair N horas para obter UTC (ex.: 3 para MSK/broker comum).
  --no-sem-fonte-null-proxy — não gerar linhas SEM_FONTE a partir de signal_source nulo no trade_feedback.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import subprocess
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "audit" / "psa_inbound" / "PSA_PACOTE_TIER0_20260518_204618Z"
OUT = ROOT / "audit" / "psa_inbound" / "OMEGA_DIAGNOSTIC_DATA_20260518"
RAW = OUT / "raw"
AGG = OUT / "aggregated"
SIG = RAW / "signals"

DATE0 = date(2026, 5, 4)
DATE1 = date(2026, 5, 18)

FLOW_SIGNAL_SRC_MARKERS = ("MOMENTUM", "SEM_FONTE", "SYNC_RECOVERY")

SIGNAL_CSV_FIELDS = [
    "signal_name",
    "timestamp_utc",
    "log_time_assumption",
    "log_timestamp_offset_hours_applied",
    "direction",
    "strength",
    "asset",
    "timeframe",
    "position_ticket",
    "provenance",
    "source_file",
]

REASON_MAP = {
    "0": "CLIENT",
    "1": "MOBILE",
    "2": "WEB",
    "3": "EXPERT",
    "4": "SL",
    "5": "TP",
    "6": "SO",
    "7": "ROLLOVER",
    "8": "VMARGIN",
    "9": "SPLIT",
}


def _parse_date(s: str | None) -> date | None:
    if not s or len(s) < 10:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def _in_window(d: date | None) -> bool:
    return d is not None and DATE0 <= d <= DATE1


def ts_to_utc_naive(s: str) -> str:
    if not s or not str(s).strip():
        return ""
    s = str(s).strip()
    try:
        if s.endswith("Z"):
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(s)
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return s[:19] if len(s) >= 19 else s


def git_head() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=str(ROOT),
                text=True,
            ).strip()
        )
    except Exception:
        return "UNAVAILABLE"


def flow_naive_to_utc(ts_local: str, offset_hours: float) -> str:
    """Interpreta prefixo YYYY-MM-DD HH:MM:SS do log como relógio local UTC+offset → UTC naive."""
    try:
        dt = datetime.strptime(ts_local[:19], "%Y-%m-%d %H:%M:%S")
        if offset_hours:
            dt = dt - timedelta(hours=offset_hours)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ts_local[:19]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build OMEGA_DIAGNOSTIC_DATA_20260518 package (CEO v2.0 + script review)."
    )
    p.add_argument(
        "--flow-signal-local-offset-hours",
        type=float,
        default=0.0,
        help="Naive FlowSignal log timestamps: subtract this many hours to get UTC "
        "(use e.g. 3 if the log clock is broker UTC+3). Default 0 = no adjustment.",
    )
    p.add_argument(
        "--no-sem-fonte-null-proxy",
        action="store_true",
        help="Do not emit SEM_FONTE rows inferred from NULL signal_source in trade_feedback.",
    )
    return p.parse_args()


def sl_tp_from_comment(comment: str) -> tuple[str, str]:
    c = comment or ""
    sl_m = re.search(r"\[sl\s*=\s*([^\]]+)\]", c, re.I) or re.search(
        r"\[sl\s+([^\]]+)\]", c, re.I
    )
    tp_m = re.search(r"\[tp\s*=\s*([^\]]+)\]", c, re.I) or re.search(
        r"\[tp\s+([^\]]+)\]", c, re.I
    )
    sl = sl_m.group(1).strip() if sl_m else ""
    tp = tp_m.group(1).strip() if tp_m else ""
    return sl, tp


def main(args: argparse.Namespace) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    AGG.mkdir(parents=True, exist_ok=True)
    SIG.mkdir(parents=True, exist_ok=True)

    deals_path = PKG / "mt5_deals_raw.csv"
    orders_path = PKG / "mt5_orders_raw.csv"
    runtime_src = PKG / "runtime_manifest.json"
    eod_src = PKG / "account_equity_eod.jsonl"
    tfb_src = ROOT / "audit" / "paper" / "trade_feedback.jsonl"
    eval_src = ROOT / "audit" / "paper" / "evaluation_timeline.jsonl"
    ks_src = ROOT / "audit" / "risk" / "ks_daily_state.json"

    # --- Orders: position_id -> best sl,tp
    pos_sl_tp: dict[str, tuple[str, str]] = {}
    orders_rows: list[dict[str, str]] = []
    with orders_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            orders_rows.append(row)
            pid = row.get("position_id") or ""
            sl = (row.get("sl") or "").strip()
            tp = (row.get("tp") or "").strip()
            if not pid:
                continue
            if pid not in pos_sl_tp and (sl or tp):
                pos_sl_tp[pid] = (sl, tp)
            elif pid in pos_sl_tp:
                osl, otp = pos_sl_tp[pid]
                nsl = sl or osl
                ntp = tp or otp
                if (nsl, ntp) != (osl, otp):
                    pos_sl_tp[pid] = (nsl, ntp)

    # --- Deals enriched
    out_deals = RAW / "OMEGA_DIAGNOSTIC_mt5_deals_raw_20260518.csv"
    deals_rows: list[dict[str, str]] = []
    ticket_set: set[str] = set()
    dup_tickets: list[str] = []

    with deals_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [
            "ticket",
            "position_id",
            "symbol",
            "entry",
            "profit",
            "reason",
            "reason_label",
            "timestamp_utc",
            "volume",
            "price",
            "sl",
            "tp",
            "timezone_note",
            "magic",
            "commission",
            "swap",
            "fee",
            "comment",
            "order",
        ]
        for row in reader:
            tk = row.get("ticket", "")
            if tk in ticket_set:
                dup_tickets.append(tk)
            ticket_set.add(tk)
            pid = row.get("position_id", "")
            sl, tp = pos_sl_tp.get(pid, ("", ""))
            if not sl and not tp:
                sl2, tp2 = sl_tp_from_comment(row.get("comment", ""))
                sl = sl or sl2
                tp = tp or tp2
            tsu = ts_to_utc_naive(row.get("time", ""))
            r = row.get("reason", "")
            enriched = {
                "ticket": tk,
                "position_id": pid,
                "symbol": row.get("symbol", ""),
                "entry": row.get("entry", ""),
                "profit": row.get("profit", ""),
                "reason": r,
                "reason_label": REASON_MAP.get(str(r), str(r)),
                "timestamp_utc": tsu,
                "volume": row.get("volume", ""),
                "price": row.get("price", ""),
                "sl": sl,
                "tp": tp,
                "timezone_note": "converted_from_iso8601_offset_to_utc_naive",
                "magic": row.get("magic", ""),
                "commission": row.get("commission", ""),
                "swap": row.get("swap", ""),
                "fee": row.get("fee", ""),
                "comment": row.get("comment", ""),
                "order": row.get("order", ""),
            }
            deals_rows.append(enriched)

    with out_deals.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(deals_rows)

    # --- Orders out with timestamp_utc
    out_orders = RAW / "OMEGA_DIAGNOSTIC_mt5_orders_raw_20260518.csv"
    ofields = list(orders_rows[0].keys()) if orders_rows else []
    if "timestamp_utc" not in ofields:
        ofields = ["timestamp_utc"] + ofields
    with out_orders.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=ofields)
        w.writeheader()
        for row in orders_rows:
            r2 = dict(row)
            r2["timestamp_utc"] = ts_to_utc_naive(row.get("time_done") or row.get("time_setup") or "")
            w.writerow({k: r2.get(k, "") for k in ofields})

    # Last OUT deal reason per position (for backfill)
    last_out: dict[str, tuple[str, str]] = {}
    for d in sorted(deals_rows, key=lambda x: (x.get("position_id", ""), x.get("timestamp_utc", ""))):
        if d.get("entry") == "1":
            last_out[d["position_id"]] = (d.get("reason", ""), d.get("reason_label", ""))

    # --- trade_feedback window + backfill
    out_tfb = RAW / "OMEGA_DIAGNOSTIC_trade_feedback_20260518.jsonl"
    tfb_lines_out: list[str] = []
    match_fb = 0
    unmatch_fb = 0
    unknown_before = 0
    unknown_after = 0
    sem_fb_by_position: dict[str, dict[str, str]] = {}
    sync_fb_by_position: dict[str, dict[str, str]] = {}

    for line in tfb_src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = o.get("ts") or o.get("detected_at_utc") or ""
        dkey = _parse_date(ts)
        if not _in_window(dkey):
            continue
        raw_ss = o.get("signal_source")
        if o.get("event") == "position_closed":
            tsu_fb = ts_to_utc_naive(ts)
            pt = str(o.get("position_ticket") or "").strip()
            sym = str(o.get("symbol") or "")
            tf = str(o.get("timeframe") or "")
            key_fb = pt or f"{sym}|{tsu_fb}"
            if not args.no_sem_fonte_null_proxy and raw_ss in (None, "", "SEM_FONTE"):
                if key_fb not in sem_fb_by_position:
                    sem_fb_by_position[key_fb] = {
                        "signal_name": "SEM_FONTE",
                        "timestamp_utc": tsu_fb,
                        "log_time_assumption": "trade_feedback_iso_ts_converted_to_utc_naive",
                        "log_timestamp_offset_hours_applied": "0",
                        "direction": "NA",
                        "strength": str(o.get("confidence") or o.get("result") or ""),
                        "asset": sym,
                        "timeframe": tf,
                        "position_ticket": pt,
                        "provenance": "trade_feedback:position_closed;signal_source_null_or_SEM_FONTE",
                        "source_file": "audit/paper/trade_feedback.jsonl",
                    }
            if raw_ss == "SYNC_RECOVERY" and key_fb not in sync_fb_by_position:
                sync_fb_by_position[key_fb] = {
                    "signal_name": "SYNC_RECOVERY",
                    "timestamp_utc": tsu_fb,
                    "log_time_assumption": "trade_feedback_iso_ts_converted_to_utc_naive",
                    "log_timestamp_offset_hours_applied": "0",
                    "direction": "NA",
                    "strength": str(o.get("confidence") or o.get("result") or ""),
                    "asset": sym,
                    "timeframe": tf,
                    "position_ticket": pt,
                    "provenance": "trade_feedback:position_closed;signal_source_SYNC_RECOVERY",
                    "source_file": "audit/paper/trade_feedback.jsonl",
                }
        er = o.get("exit_reason")
        if er in (None, "", "UNKNOWN"):
            unknown_before += 1
            pid = str(o.get("position_ticket", ""))
            if pid and pid in last_out:
                rc, lab = last_out[pid]
                o["exit_reason"] = lab
                o["exit_reason_mt5_code"] = rc
                o["exit_reason_backfilled"] = True
                match_fb += 1
            else:
                o["exit_reason_backfilled"] = False
                unmatch_fb += 1
        if o.get("exit_reason") in (None, "", "UNKNOWN"):
            unknown_after += 1
        o["timestamp_utc"] = ts_to_utc_naive(ts)
        if not o.get("signal_source"):
            o["signal_source"] = "NULL"
        tfb_lines_out.append(json.dumps(o, ensure_ascii=False))

    out_tfb.write_text("\n".join(tfb_lines_out) + "\n", encoding="utf-8")

    # --- ks_daily_state: snapshot as array (no history file available)
    ks_arr = []
    if ks_src.is_file():
        try:
            ks_arr = [json.loads(ks_src.read_text(encoding="utf-8"))]
        except Exception:
            ks_arr = [{"error": "parse_failed", "path": str(ks_src)}]
    (RAW / "OMEGA_DIAGNOSTIC_ks_daily_state_20260518.json").write_text(
        json.dumps(ks_arr, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- cycle exits from evaluation_timeline
    cycle_out: list[dict] = []
    for line in eval_src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("event") != "run_end":
            continue
        gen = ev.get("generated", "")
        dkey = _parse_date(gen)
        if not _in_window(dkey):
            continue
        dd_pct = None
        det = (ev.get("exit_detail") or "") + " " + (ev.get("ks_reason") or "")
        m = re.search(r"([\d.]+)\s*%", det)
        if m:
            try:
                dd_pct = float(m.group(1))
            except ValueError:
                pass
        cycle_out.append(
            {
                "timestamp_utc": ts_to_utc_naive(gen),
                "exit_reason": ev.get("exit_reason"),
                "exit_detail": ev.get("exit_detail"),
                "kill_switch": ev.get("kill_switch"),
                "dd_pct_inferred": dd_pct,
                "generated_raw": gen,
            }
        )
    (RAW / "OMEGA_DIAGNOSTIC_cycle_exit_20260518.json").write_text(
        json.dumps(cycle_out, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- runtime manifest (fix git_head to current repo)
    rt = json.loads(runtime_src.read_text(encoding="utf-8"))
    rt["git_head_at_package_export"] = rt.get("git_head")
    rt["git_head_repo_HEAD_at_build"] = git_head()
    rt["git_head_note"] = (
        "git_head_at_package_export is PSA export-time; git_head_repo_HEAD_at_build is repo when running this script."
    )
    (RAW / "OMEGA_DIAGNOSTIC_runtime_manifest_20260518.json").write_text(
        json.dumps(rt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- EOD copy + timestamp_utc
    eod_lines = []
    for line in eod_src.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        o = json.loads(line)
        o["timestamp_utc"] = f"{o.get('date', '')} 23:59:59"
        o["reliability_flag"] = "UNRELIABLE_REPEATED_VALUES"
        eod_lines.append(json.dumps(o, ensure_ascii=False))
    (RAW / "OMEGA_DIAGNOSTIC_account_equity_eod_20260518.jsonl").write_text(
        "\n".join(eod_lines) + "\n",
        encoding="utf-8",
    )

    # --- risk config snapshot (CEO keys + partial engineering snapshot)
    log_sample = {
        "risk_trade_pct": 1.0,
        "max_positions": 15,
        "dd_max_pct": 10.0,
        "comment_mark": "OV2|",
        "legacy_magic": 234001,
        "scale_magic_range": "999111-999130",
        "paper_loop_version": "OMEGA PAPER LOOP v3.0",
        "ativos_x_tf": "32 x 3",
    }
    risk_snap = {
        "sl_pct": None,
        "tp_pct": None,
        "max_dd_threshold": log_sample["dd_max_pct"],
        "position_sizing_rules": {
            "max_positions": log_sample["max_positions"],
            "risk_trade_pct": log_sample["risk_trade_pct"],
            "note": "Parsed from log banner sample only — not a full env/shadow_loop matrix.",
        },
        "kill_switch_threshold": None,
        "circuit_breaker_threshold": None,
        "source": "engineering_snapshot_20260518",
        "from_logs_sample": log_sample,
        "note": "sl_pct/tp_pct/kill_switch/circuit_breaker not resolved in this build; PSA should export effective shadow_loop.py / env values.",
    }
    (RAW / "OMEGA_DIAGNOSTIC_risk_config_20260518.json").write_text(
        json.dumps(risk_snap, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # --- Signal logs: FlowSignal (MOMENTUM / SEM_FONTE / SYNC_RECOVERY) + trade_feedback proxies
    flow_re = re.compile(
        r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}),\d+\s+\|\s+INFO\s+\|\s+\[(\S+)\s+(\w+)\]\s+FlowSignal:.*?DIR=(\w+).*\(src=([^)]+)\).*?adx=([\d.]+)",
    )
    momentum_rows: list[dict[str, str]] = []
    sem_flow_rows: list[dict[str, str]] = []
    sync_flow_rows: list[dict[str, str]] = []
    off_h = float(args.flow_signal_local_offset_hours or 0.0)
    off_s = str(off_h)
    log_paths = [ROOT / "audit" / "paper" / "omega_24x7_runner.log"]
    log_paths += sorted((ROOT / "audit" / "paper").glob("paper_loop_202605*.log"))
    seen_files = 0
    for lp in log_paths:
        if not lp.is_file():
            continue
        seen_files += 1
        try:
            txt = lp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for line in txt.splitlines():
            m = flow_re.search(line)
            if not m:
                continue
            ts_local, sym, tf, direction, src, adx = m.groups()
            dkey = _parse_date(ts_local[:10] if len(ts_local) >= 10 else "")
            if not _in_window(dkey):
                continue
            src_u = src.upper()
            if not any(marker in src_u for marker in FLOW_SIGNAL_SRC_MARKERS):
                continue
            tsu = flow_naive_to_utc(ts_local[:19], off_h)
            base_row: dict[str, str] = {
                "signal_name": src.strip(),
                "timestamp_utc": tsu,
                "log_time_assumption": (
                    "naive_log_prefix_minus_offset_hours_equals_utc"
                    if off_h
                    else "naive_log_prefix_treated_as_utc_validate_vs_broker"
                ),
                "log_timestamp_offset_hours_applied": off_s,
                "direction": direction,
                "strength": adx,
                "asset": sym,
                "timeframe": tf,
                "position_ticket": "",
                "provenance": "FlowSignal:omega_24x7_or_paper_loop",
                "source_file": str(lp.relative_to(ROOT)),
            }
            if "MOMENTUM" in src_u:
                momentum_rows.append(dict(base_row))
            if "SEM_FONTE" in src_u:
                sem_flow_rows.append(dict(base_row))
            if "SYNC_RECOVERY" in src_u:
                sync_flow_rows.append(dict(base_row))

    def write_signal_csv(name: str, rows: list[dict[str, str]], template: list[str] | None = None) -> None:
        pth = SIG / name
        keys = template or SIGNAL_CSV_FIELDS
        with pth.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in keys})

    sem_fb_rows = list(sem_fb_by_position.values())
    sync_fb_rows = list(sync_fb_by_position.values())
    sem_all = sem_flow_rows + sem_fb_rows
    sync_all = sync_flow_rows + sync_fb_rows

    write_signal_csv("OMEGA_DIAGNOSTIC_MOMENTUM_MT5_logs_20260518.csv", momentum_rows, SIGNAL_CSV_FIELDS)
    write_signal_csv("OMEGA_DIAGNOSTIC_SEM_FONTE_logs_20260518.csv", sem_all, SIGNAL_CSV_FIELDS)
    write_signal_csv("OMEGA_DIAGNOSTIC_SYNC_RECOVERY_logs_20260518.csv", sync_all, SIGNAL_CSV_FIELDS)

    # --- Aggregated: from position-level net PnL (OUT deals sum already in deals_rows group)
    pos_pnl: dict[str, dict] = defaultdict(
        lambda: {
            "pnl": 0.0,
            "symbol": "",
            "tf": "",
            "signal": "",
        }
    )
    for d in deals_rows:
        pid = d["position_id"]
        if not pid:
            continue
        pos_pnl[pid]["pnl"] += float(d.get("profit") or 0)
        if not pos_pnl[pid]["symbol"]:
            pos_pnl[pid]["symbol"] = d.get("symbol", "")
        cm = d.get("comment", "")
        if "OV2|" in cm:
            parts = cm.split("|")
            if len(parts) >= 3:
                pos_pnl[pid]["tf"] = parts[2]
    # signal from trade_feedback last for ticket
    sig_by_ticket: dict[str, str] = {}
    for line in tfb_lines_out:
        o = json.loads(line)
        if o.get("event") == "position_closed":
            sig_by_ticket[str(o.get("position_ticket"))] = str(o.get("signal_source") or "NULL")

    for pid in pos_pnl:
        pos_pnl[pid]["signal"] = sig_by_ticket.get(pid, "NULL")

    closed_positions = [(pid, v) for pid, v in pos_pnl.items() if abs(v["pnl"]) > 1e-9 or True]
    # win rate by signal / symbol / tf
    wr_key: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for pid, v in pos_pnl.items():
        pnl = v["pnl"]
        wr_key[(v["signal"], v["symbol"], v["tf"] or "NA")].append(pnl)

    wr_rows = []
    for (sig, sym, tf), pnls in sorted(wr_key.items()):
        n = len(pnls)
        wins = sum(1 for x in pnls if x > 0)
        losses = sum(1 for x in pnls if x < 0)
        gp = sum(x for x in pnls if x > 0)
        gl = abs(sum(x for x in pnls if x < 0))
        pf = (gp / gl) if gl > 1e-9 else ("NaN" if gp == 0 else "Inf")
        wr_rows.append(
            {
                "signal_source": sig,
                "symbol": sym,
                "timeframe": tf,
                "total_trades": n,
                "winning_trades": wins,
                "losing_trades": losses,
                "win_rate": round(wins / n, 6) if n else "NaN",
                "gross_profit": round(gp, 4),
                "gross_loss": round(gl, 4),
                "profit_factor": pf if isinstance(pf, str) else round(float(pf), 6),
                "avg_pnl": round(sum(pnls) / n, 6) if n else "NaN",
            }
        )
    with (AGG / "OMEGA_DIAGNOSTIC_win_rate_by_signal_20260518.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        keys = [
            "signal_source",
            "symbol",
            "timeframe",
            "total_trades",
            "winning_trades",
            "losing_trades",
            "win_rate",
            "gross_profit",
            "gross_loss",
            "profit_factor",
            "avg_pnl",
        ]
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(wr_rows)

    # profit factor by asset only
    sym_pnls: dict[str, list[float]] = defaultdict(list)
    for _, v in pos_pnl.items():
        sym_pnls[v["symbol"]].append(v["pnl"])
    pf_rows = []
    for sym, pnls in sorted(sym_pnls.items()):
        gp = sum(x for x in pnls if x > 0)
        gl = abs(sum(x for x in pnls if x < 0))
        pf = (gp / gl) if gl > 1e-9 else ("NaN" if gp == 0 else "Inf")
        pf_rows.append(
            {
                "symbol": sym,
                "total_trades": len(pnls),
                "gross_profit": round(gp, 4),
                "gross_loss": round(gl, 4),
                "profit_factor": pf if isinstance(pf, str) else round(float(pf), 6),
            }
        )
    with (AGG / "OMEGA_DIAGNOSTIC_profit_factor_by_asset_20260518.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=["symbol", "total_trades", "gross_profit", "gross_loss", "profit_factor"],
        )
        w.writeheader()
        w.writerows(pf_rows)

    # SL/TP frequency by symbol/tf from OUT deals
    st_freq: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for d in deals_rows:
        if d.get("entry") != "1":
            continue
        sym = d.get("symbol", "")
        tf = "NA"
        for pid, v in pos_pnl.items():
            if pid == d.get("position_id") and v.get("tf"):
                tf = v["tf"] or "NA"
                break
        st_freq[(sym, tf)][d.get("reason_label", "")] += 1
    sltp_rows = []
    for (sym, tf), ctr in sorted(st_freq.items()):
        sl = ctr.get("SL", 0)
        tp = ctr.get("TP", 0)
        tot = sum(ctr.values())
        sltp_rows.append(
            {
                "symbol": sym,
                "timeframe": tf,
                "sl_triggers": sl,
                "tp_triggers": tp,
                "expert_triggers": ctr.get("EXPERT", 0),
                "total_exits": tot,
                "sl_rate": round(sl / tot, 6) if tot else "NaN",
                "tp_rate": round(tp / tot, 6) if tot else "NaN",
            }
        )
    sltp_fields = [
        "symbol",
        "timeframe",
        "sl_triggers",
        "tp_triggers",
        "expert_triggers",
        "total_exits",
        "sl_rate",
        "tp_rate",
    ]
    with (AGG / "OMEGA_DIAGNOSTIC_sl_tp_trigger_frequency_20260518.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.DictWriter(f, fieldnames=sltp_fields)
        w.writeheader()
        w.writerows(sltp_rows)

    # execution quality from trade_feedback
    ex_rows: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for line in tfb_lines_out:
        o = json.loads(line)
        if o.get("event") != "position_closed":
            continue
        slip = o.get("slippage_pts")
        lat = o.get("latency_ms") or o.get("max_latency_ms")
        try:
            sp = float(slip) if slip is not None else float("nan")
        except (TypeError, ValueError):
            sp = float("nan")
        try:
            la = float(lat) if lat is not None else float("nan")
        except (TypeError, ValueError):
            la = float("nan")
        sym = o.get("symbol") or "NA"
        tz = "UTC"
        if not math.isnan(sp) or not math.isnan(la):
            ex_rows[(sym, tz)].append((sp, la))

    ex_out = []
    for (sym, tz), vals in sorted(ex_rows.items()):
        slips = [v[0] for v in vals if not math.isnan(v[0])]
        lats = [v[1] for v in vals if not math.isnan(v[1])]
        ex_out.append(
            {
                "symbol": sym,
                "timezone": tz,
                "avg_slippage": round(sum(slips) / len(slips), 4) if slips else "NaN",
                "max_slippage": round(max(slips), 4) if slips else "NaN",
                "avg_latency": round(sum(lats) / len(lats), 2) if lats else "NaN",
                "max_latency": round(max(lats), 2) if lats else "NaN",
                "rejection_rate": "NaN",
                "sample_size": len(vals),
            }
        )
    with (AGG / "OMEGA_DIAGNOSTIC_execution_quality_metrics_20260518.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        fn = [
            "symbol",
            "timezone",
            "avg_slippage",
            "max_slippage",
            "avg_latency",
            "max_latency",
            "rejection_rate",
            "sample_size",
        ]
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        w.writerows(ex_out)

    # Daily PnL by symbol for correlation
    daily_sym: dict[tuple[str, str], float] = defaultdict(float)
    for d in deals_rows:
        dk = d.get("timestamp_utc", "")[:10]
        if len(dk) < 10:
            continue
        daily_sym[(dk, d.get("symbol", "?"))] += float(d.get("profit") or 0)
    dates = sorted({k[0] for k in daily_sym.keys()})
    syms = sorted({k[1] for k in daily_sym.keys()})
    mat: dict[tuple[str, str], float] = {}

    def pearson(xs: list[float], ys: list[float]) -> float:
        if len(xs) < 2 or len(ys) < 2:
            return float("nan")
        mx = statistics.mean(xs)
        my = statistics.mean(ys)
        num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        denx = math.sqrt(sum((a - mx) ** 2 for a in xs))
        deny = math.sqrt(sum((b - my) ** 2 for b in ys))
        if denx < 1e-12 or deny < 1e-12:
            return float("nan")
        return num / (denx * deny)

    for s1 in syms:
        for s2 in syms:
            xs = [daily_sym.get((d, s1), 0.0) for d in dates]
            ys = [daily_sym.get((d, s2), 0.0) for d in dates]
            mat[(s1, s2)] = pearson(xs, ys)
    with (AGG / "OMEGA_DIAGNOSTIC_asset_correlation_matrix_20260518.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        f.write("symbol_a,symbol_b,pearson_daily_pnl,n_days\n")
        for s1 in syms:
            for s2 in syms:
                v = mat.get((s1, s2), float("nan"))
                vv = "" if isinstance(v, float) and math.isnan(v) else round(v, 6)
                f.write(f"{s1},{s2},{vv},{len(dates)}\n")

    # PnL distribution by date
    daily_tot: dict[str, float] = defaultdict(float)
    for d in deals_rows:
        dk = d.get("timestamp_utc", "")[:10]
        if len(dk) >= 10:
            daily_tot[dk] += float(d.get("profit") or 0)
    pnl_rows = [{"date": d, "daily_pnl": round(daily_tot[d], 4)} for d in sorted(daily_tot.keys())]
    with (AGG / "OMEGA_DIAGNOSTIC_pnl_distribution_20260518.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.DictWriter(f, fieldnames=["date", "daily_pnl", "pnl_histogram_bins"])
        w.writeheader()
        for r in pnl_rows:
            r2 = dict(r)
            r2["pnl_histogram_bins"] = "NA_engineering_v1"
            w.writerow(r2)

    log_file_count = seen_files
    closed_tickets: set[str] = set()
    for line in tfb_lines_out:
        ls = line.strip()
        if not ls:
            continue
        try:
            o = json.loads(ls)
        except json.JSONDecodeError:
            continue
        if o.get("event") == "position_closed":
            t = str(o.get("position_ticket") or "")
            if t:
                closed_tickets.add(t)
    deal_position_ids = {d.get("position_id", "") for d in deals_rows if d.get("position_id")}
    reconciled = sum(1 for t in closed_tickets if t in deal_position_ids)

    # --- README
    readme = f"""# OMEGA_DIAGNOSTIC_DATA_20260518

**Gerado por:** `scripts/build_omega_diagnostic_package_20260518.py`  
**Data build UTC:** {datetime.now(timezone.utc).isoformat()}  
**Pedido CEO:** `docs/requests/OMEGA_TRADING_SYSTEM_SYSTEMATIC_DECAY_DIAGNOSIS_REQUEST_v2.0_20260518.md`  
**Avaliação / gaps PSA:** `docs/requests/OMEGA_TRADING_SYSTEM_FINAL_EVALUATION_AND_NEXT_STEPS_v2.0_20260518.md`

## 1. Método de extracção

- **MT5 deals/orders:** cópia enriquecida a partir de `audit/psa_inbound/PSA_PACOTE_TIER0_20260518_204618Z/` com `timestamp_utc` (UTC naive `YYYY-MM-DD HH:MM:SS`), `sl`/`tp` via join `position_id` → `mt5_orders_raw` ou regex `\\[sl …\\]` no comentário.
- **trade_feedback:** filtro {DATE0}–{DATE1}; `exit_reason` backfill a partir do **último** deal `entry=1` do mesmo `position_id` (mapeamento MT5 → etiqueta SL/TP/EXPERT/…).
- **cycle_exit:** **{len(cycle_out)}** eventos `run_end` exportados de `audit/paper/evaluation_timeline.jsonl` com `generated` na janela **{DATE0}**–**{DATE1}** (ficheiro: `raw/OMEGA_DIAGNOSTIC_cycle_exit_20260518.json`). Campo `dd_pct_inferred` é regex sobre texto — validar com PSA quando existir série KS.
- **ks_daily_state:** apenas instantâneo disponível em `audit/risk/ks_daily_state.json` — exportado como **array JSON de 1 elemento** (série diária completa: **não disponível** sem novo export PSA).
- **Sinais (FlowSignal):** regex `FlowSignal` em `omega_24x7_runner.log` + `paper_loop_202605*.log`; aceita `src` contendo qualquer de {', '.join(FLOW_SIGNAL_SRC_MARKERS)}. Coluna `timestamp_utc` = prefixo naive do log **menos** `--flow-signal-local-offset-hours` (neste build: **{off_h}** h). Ver coluna `provenance` / `log_time_assumption` nos CSVs.
- **SEM_FONTE:** linhas `FlowSignal` com `SEM_FONTE` no `src` (**{len(sem_flow_rows)}**) + proxy a partir de `trade_feedback` `position_closed` com `signal_source` vazio/`SEM_FONTE` (**{len(sem_fb_rows)}** posições únicas por `position_ticket`){' — **desactivado** por `--no-sem-fonte-null-proxy`' if args.no_sem_fonte_null_proxy else ''}.
- **SYNC_RECOVERY:** linhas FlowSignal com `SYNC_RECOVERY` no `src` (**{len(sync_flow_rows)}**) + `trade_feedback` com `signal_source=SYNC_RECOVERY` (**{len(sync_fb_rows)}** posições únicas). Neste build: **{len(sync_all)}** linhas no CSV total; se `FlowSignal=0`, todas vêm de `trade_feedback` (dedupe por `position_ticket`).

## 1.1 Contagens verificadas (ficheiros gerados)

| Ficheiro (sob `OMEGA_DIAGNOSTIC_DATA_20260518/`) | Linhas / registos de dados |
| --- | ---: |
| `raw/OMEGA_DIAGNOSTIC_mt5_deals_raw_20260518.csv` | {len(deals_rows)} |
| `raw/OMEGA_DIAGNOSTIC_mt5_orders_raw_20260518.csv` | {len(orders_rows)} |
| `raw/OMEGA_DIAGNOSTIC_trade_feedback_20260518.jsonl` | {len(tfb_lines_out)} |
| `raw/OMEGA_DIAGNOSTIC_ks_daily_state_20260518.json` | {len(ks_arr)} elemento(s) no array JSON |
| `raw/OMEGA_DIAGNOSTIC_cycle_exit_20260518.json` | {len(cycle_out)} |
| `raw/signals/OMEGA_DIAGNOSTIC_MOMENTUM_MT5_logs_20260518.csv` | {len(momentum_rows)} |
| `raw/signals/OMEGA_DIAGNOSTIC_SEM_FONTE_logs_20260518.csv` | {len(sem_all)} |
| `raw/signals/OMEGA_DIAGNOSTIC_SYNC_RECOVERY_logs_20260518.csv` | {len(sync_all)} |
| `aggregated/OMEGA_DIAGNOSTIC_win_rate_by_signal_20260518.csv` | {len(wr_rows)} |
| `aggregated/OMEGA_DIAGNOSTIC_profit_factor_by_asset_20260518.csv` | {len(pf_rows)} |
| `aggregated/OMEGA_DIAGNOSTIC_sl_tp_trigger_frequency_20260518.csv` | {len(sltp_rows)} |
| `aggregated/OMEGA_DIAGNOSTIC_execution_quality_metrics_20260518.csv` | {len(ex_out)} |
| `aggregated/OMEGA_DIAGNOSTIC_asset_correlation_matrix_20260518.csv` | {len(syms) * len(syms) if syms else 0} |
| `aggregated/OMEGA_DIAGNOSTIC_pnl_distribution_20260518.csv` | {len(pnl_rows)} |

## 2. Issues conhecidos

- `account_equity_eod`: `reliability_flag=UNRELIABLE_REPEATED_VALUES` (valores repetidos no pacote PSA).
- `git_head`: ver `runtime_manifest` — dois campos (`git_head_at_package_export` vs `git_head_repo_HEAD_at_build`).
- **SEM_FONTE via `trade_feedback`:** `signal_source` nulo é tratado como **proxy SEM_FONTE** (convenção alinhada a scripts de auditoria internos); validar com PSA se algum fecho NULL não for SEM_FONTE.
- **`cycle_exit` `dd_pct_inferred`:** derivado por regex sobre `exit_detail` — pode falhar em formatos não previstos.
- **ks_daily_state série:** incompleta (1 snapshot).

## 3. Validação

- **Deals `ticket` duplicados:** {len(dup_tickets)} (lista: {dup_tickets[:20]}{'...' if len(dup_tickets) > 20 else ''})
- **trade_feedback backfill:** matched={match_fb}, unmatched={unmatch_fb}, unknown_before={unknown_before}, unknown_after={unknown_after}
- **Ficheiros de log escaneados (FlowSignal):** {log_file_count} ficheiros (`paper_loop_202605*.log` em `audit/paper/` + `omega_24x7_runner.log` quando existir).
- **Reconciliação `position_ticket` ↔ `position_id` em deals:** fechamentos em `trade_feedback` com ticket presente em `mt5_deals_raw.position_id`: {reconciled} / {len(closed_tickets)} (amostra na janela filtrada).

## 4. Contacto

- **PSA / Operações:** [nome do lead — preencher].
- **Engenharia OMEGA / CTO:** ajustes ao script de build (`scripts/build_omega_diagnostic_package_20260518.py`).

"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    # Save v2 request doc path reference - write the CEO doc
    print(f"OK: package written to {OUT}")


if __name__ == "__main__":
    main(parse_args())
