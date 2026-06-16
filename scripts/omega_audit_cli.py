#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMEGA Intelligence Audit — CLI wrapper (Windows / PowerShell).

Comando oficial (a partir da raiz SOURCE_CODE):
  python scripts/omega_audit_cli.py <comando> [opções]

Comandos:
  baseline-init     Gera audit/omega_audit/audit_baseline.json
  verify-baseline   Compara disco vs baseline (STRICT)
  inventory         Dump JSON do inventário de hashes (stdout ou --out)
  precheck          Valida pré-ciclo (lê ks_daily_anchor.json; fail-closed)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _precheck(args: argparse.Namespace) -> int:
    from modules.omega_audit import (
        default_anchor_path,
        default_baseline_path,
        verify_against_baseline,
        write_audit_report,
    )
    from modules.omega_audit.precycle_governor import run_pre_cycle_check

    anchor = Path(args.anchor) if args.anchor else default_anchor_path(ROOT)
    baseline_path = Path(args.baseline) if args.baseline else default_baseline_path(ROOT)

    if args.skip_baseline:
        bv_ok, bv_issues = True, []
    else:
        bv = verify_against_baseline(ROOT, baseline_path, strict=True)
        bv_ok, bv_issues = bv.ok, bv.issues
        if not bv_ok:
            path = write_audit_report(bv_issues, ROOT, prefix="precheck_baseline_fail")
            print(f"BLOQUEADO (baseline): {path}", file=sys.stderr)
            return 1

    account = {"equity": float(args.equity), "max_dd_allowed": float(args.max_dd)}
    signals: list[dict] = []
    if args.signals:
        signals = json.loads(Path(args.signals).read_text(encoding="utf-8"))

    result = run_pre_cycle_check(
        ROOT,
        account,
        signals,
        strict_mode=not args.no_strict,
        anchor_path=anchor,
        max_dd_allowed=float(args.max_dd),
    )
    all_issues = list(bv_issues) + result.issues
    report_path = write_audit_report(all_issues, ROOT, prefix="precheck")
    if result.allowed:
        print(f"APROVADO. Relatório: {report_path}")
        if any(i.severity == "HIGH" for i in all_issues):
            print("AVISO: issues HIGH presentes (modo não-estrito).", file=sys.stderr)
        return 0
    print(f"BLOQUEADO. Relatório: {report_path}", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="OMEGA Intelligence Audit CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_bl = sub.add_parser("baseline-init", help="Gera audit_baseline.json")
    p_bl.add_argument("--out", type=Path, default=None, help="Caminho do ficheiro baseline")

    p_vb = sub.add_parser("verify-baseline", help="Verifica hashes vs baseline")
    p_vb.add_argument("--baseline", type=Path, default=None)

    p_inv = sub.add_parser("inventory", help="Inventário de hashes")
    p_inv.add_argument("--out", type=Path, default=None)

    p_pc = sub.add_parser("precheck", help="Pré-ciclo (anchor + sinais + baseline)")
    p_pc.add_argument("--equity", type=float, required=True)
    p_pc.add_argument("--max-dd", type=float, default=0.02, dest="max_dd")
    p_pc.add_argument("--signals", type=str, default=None, help="JSON array de sinais")
    p_pc.add_argument("--anchor", type=str, default=None)
    p_pc.add_argument("--baseline", type=str, default=None)
    p_pc.add_argument("--no-strict", action="store_true", help="Não vetar só por conflito HIGH")
    p_pc.add_argument(
        "--skip-baseline",
        action="store_true",
        help="Ignorar verificação de baseline (apenas diagnóstico; não usar em produção)",
    )

    args = ap.parse_args()

    if args.cmd == "baseline-init":
        from modules.omega_audit import write_baseline

        out = write_baseline(ROOT, args.out)
        print(f"OK baseline: {out}")
        return 0

    if args.cmd == "verify-baseline":
        from modules.omega_audit import default_baseline_path, verify_against_baseline

        bp = args.baseline or default_baseline_path(ROOT)
        bv = verify_against_baseline(ROOT, bp, strict=True)
        print(json.dumps({"ok": bv.ok, "checked": bv.checked, "mismatched": bv.mismatched_paths}, indent=2))
        for i in bv.issues:
            print(f"[{i.severity}] {i.code} {i.message}", file=sys.stderr)
        return 0 if bv.ok else 1

    if args.cmd == "inventory":
        from modules.omega_audit import run_static_inventory

        data = run_static_inventory(ROOT)
        if args.out:
            args.out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"OK: {args.out}")
        else:
            print(json.dumps({"generated": data["generated"], "python_files": data["python_files"]}, indent=2))
        return 0

    if args.cmd == "precheck":
        return _precheck(args)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
