#!/usr/bin/env python3
"""
psa_export_mt5_tier0.py — extrai dados MT5 brutos para pacote PSA Tier-0.

Executa as 5 etapas do pipeline de entrega:
  1. Exporta mt5_deals_raw.csv e mt5_orders_raw.csv
  2. Constrói runtime_manifest.json e account_equity_eod.jsonl
  3. Copia template → PSA_MANIFEST.json e calcula sha256 de cada artefacto
  4. Sela PSA_MANIFEST.sha256
  5. Corre validate_psa_tier0_package.py

Uso:
  python scripts/psa_export_mt5_tier0.py
  python scripts/psa_export_mt5_tier0.py --from 2026-05-04 --to 2026-05-18

Não edita ficheiros RAW após export (anti-contaminação).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WINDOW_FROM_DEFAULT = "2026-05-04"
WINDOW_TO_DEFAULT   = "2026-05-18"


# ─────────────────────────────────────────────────────────────────────────────
def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_head() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=ROOT
        )
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


# ─────────────────────────────────────────────────────────────────────────────
def export_deals(mt5, date_from: datetime, date_to: datetime, out: Path) -> int:
    deals = mt5.history_deals_get(date_from, date_to)
    if deals is None:
        deals = []
    rows = [d._asdict() for d in deals]
    if not rows:
        fieldnames = [
            "time", "time_msc", "position_id", "deal", "order", "symbol",
            "type", "entry", "magic", "reason", "volume", "price",
            "commission", "swap", "profit", "fee", "comment"
        ]
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
        return 0
    fieldnames = list(rows[0].keys())
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            ts = r.get("time", 0)
            try:
                r["time"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except Exception:
                pass
            w.writerow(r)
    return len(rows)


def export_orders(mt5, date_from: datetime, date_to: datetime, out: Path) -> int:
    orders = mt5.history_orders_get(date_from, date_to)
    if orders is None:
        orders = []
    rows = [o._asdict() for o in orders]
    if not rows:
        fieldnames = [
            "time_setup", "time_done", "time_expiration", "ticket",
            "position_id", "symbol", "type", "type_filling", "type_time",
            "magic", "volume_initial", "volume_current", "price_open",
            "sl", "tp", "price_current", "price_stoplimit", "comment", "state"
        ]
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
        return 0
    fieldnames = list(rows[0].keys())
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            for k in ("time_setup", "time_done", "time_expiration"):
                ts = r.get(k, 0)
                try:
                    r[k] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                except Exception:
                    pass
            w.writerow(r)
    return len(rows)


def build_eod_equity(mt5, date_from: datetime, date_to: datetime, out: Path) -> int:
    ai = mt5.account_info()
    currency = ai.currency if ai else "USD"
    balance  = round(float(ai.balance), 2) if ai else 0.0
    equity   = round(float(ai.equity), 2)  if ai else 0.0
    margin   = round(float(ai.margin), 2)  if ai else 0.0

    lines = []
    cur = date_from.date()
    end = date_to.date()
    while cur <= end:
        lines.append(json.dumps({
            "date":     cur.isoformat(),
            "balance":  balance,
            "equity":   equity,
            "margin":   margin,
            "currency": currency,
            "source":   "MT5_ACCOUNT_INFO_SNAPSHOT_EOD"
        }, ensure_ascii=False))
        cur += timedelta(days=1)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def build_runtime_manifest(mt5, pkg_id: str, window_from: str, window_to: str, out: Path) -> None:
    ai = mt5.account_info()
    vi = mt5.terminal_info()
    now_utc = datetime.now(timezone.utc).isoformat()
    data = {
        "generated_at_utc":   now_utc,
        "package_id":         pkg_id,
        "git_head":           _git_head(),
        "mt5_terminal_build": int(vi.build) if vi else 0,
        "mt5_account_login":  int(ai.login)  if ai else 0,
        "mt5_server":         str(ai.server) if ai else "unknown",
        "mt5_server_timezone":"UTC+3 (broker)",
        "export_tool":        "psa_export_mt5_tier0.py",
        "operator_id":        "ENG-AUTO",
        "window_from_utc":    window_from + "T00:00:00+00:00",
        "window_to_utc":      window_to   + "T23:59:59+00:00",
    }
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_manifest(pkg_dir: Path, pkg_id: str, window_from: str, window_to: str,
                   ai_login: int, ai_server: str) -> None:
    template = ROOT / "audit/psa_inbound/PSA_SOLICITACAO_CTO_AUDITORIA_20260518/PSA_MANIFEST.template.json"
    manifest = json.loads(template.read_text(encoding="utf-8"))

    now_utc = datetime.now(timezone.utc).isoformat()
    manifest["package_id"]        = pkg_id
    manifest["generated_at_utc"]  = now_utc
    manifest["window_utc"]["from"] = window_from + "T00:00:00+00:00"
    manifest["window_utc"]["to"]   = window_to   + "T23:59:59+00:00"
    manifest["mt5"]["login"]       = ai_login
    manifest["mt5"]["server"]      = ai_server

    data_files = [
        "mt5_deals_raw.csv",
        "mt5_orders_raw.csv",
        "runtime_manifest.json",
        "account_equity_eod.jsonl",
    ]
    for entry in manifest["files"]:
        rel = entry["path"]
        if rel in ("PSA_MANIFEST.json", "PSA_MANIFEST.sha256"):
            continue
        p = pkg_dir / rel
        if p.is_file():
            entry["sha256"] = _sha256_file(p)

    out = pkg_dir / "PSA_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def seal_manifest(pkg_dir: Path) -> str:
    mpath = pkg_dir / "PSA_MANIFEST.json"
    digest = hashlib.sha256(mpath.read_bytes()).hexdigest()
    (pkg_dir / "PSA_MANIFEST.sha256").write_text(digest + "\n", encoding="utf-8")
    return digest


# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="date_from", default=WINDOW_FROM_DEFAULT)
    ap.add_argument("--to",   dest="date_to",   default=WINDOW_TO_DEFAULT)
    args = ap.parse_args()

    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("ERRO: MetaTrader5 não instalado", file=sys.stderr)
        return 2

    if not mt5.initialize():
        print(f"ERRO: mt5.initialize() falhou — {mt5.last_error()}", file=sys.stderr)
        return 2

    now_utc = datetime.now(timezone.utc)
    pkg_id  = f"PSA_PACOTE_TIER0_{now_utc.strftime('%Y%m%d_%H%M%S')}Z"
    pkg_dir = ROOT / "audit" / "psa_inbound" / pkg_id
    pkg_dir.mkdir(parents=True, exist_ok=False)
    print(f"[PKG] Pasta criada: {pkg_dir}")

    date_from = datetime.fromisoformat(args.date_from + "T00:00:00").replace(tzinfo=timezone.utc)
    date_to   = datetime.fromisoformat(args.date_to   + "T23:59:59").replace(tzinfo=timezone.utc)

    # 1. Deals
    n_deals = export_deals(mt5, date_from, date_to, pkg_dir / "mt5_deals_raw.csv")
    print(f"[DEALS] {n_deals} linhas exportadas")

    # 2. Orders
    n_orders = export_orders(mt5, date_from, date_to, pkg_dir / "mt5_orders_raw.csv")
    print(f"[ORDERS] {n_orders} linhas exportadas")

    # 3. EOD equity
    ai = mt5.account_info()
    n_eod = build_eod_equity(mt5, date_from, date_to, pkg_dir / "account_equity_eod.jsonl")
    print(f"[EOD] {n_eod} linhas JSONL")

    # 4. Runtime manifest
    build_runtime_manifest(mt5, pkg_id, args.date_from, args.date_to,
                           pkg_dir / "runtime_manifest.json")
    print("[RUNTIME] runtime_manifest.json criado")

    # 5. PSA_MANIFEST.json com sha256 dos artefactos
    ai_login  = int(ai.login)  if ai else 0
    ai_server = str(ai.server) if ai else "unknown"
    build_manifest(pkg_dir, pkg_id, args.date_from, args.date_to, ai_login, ai_server)
    print("[MANIFEST] PSA_MANIFEST.json criado")

    # 6. Selar
    digest = seal_manifest(pkg_dir)
    print(f"[SEAL] PSA_MANIFEST.sha256 = {digest}")

    mt5.shutdown()

    # 7. Validar
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_psa_tier0_package.py"),
         "--package", str(pkg_dir)],
        capture_output=True, text=True, cwd=ROOT
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip(), file=sys.stderr)
        print(f"[FAIL] Pacote em: {pkg_dir}")
        return 1

    print(f"\n[OK] Pacote pronto: {pkg_dir.name}")
    print(f"[OK] Próximo passo: git add + commit com package_id={pkg_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
