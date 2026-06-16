#!/usr/bin/env python3
"""
PSA Legacy Cleanup — P0-CICC-20260521
======================================
Marca os 96 deals legados (magic=0) em trade_feedback.jsonl como
legacy_unreconciled=True para que o SessionCalibrator os ignore.

Uso:
    python scripts/psa_legacy_cleanup.py [--feedback audit/paper/trade_feedback.jsonl]

Ref: PSA-EXEC-FINAL-MADRUGADA-20260521-v3 | CKO Ficheiro 4
"""
import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone


OMEGA_MAGIC = 234001
INVALID_EXIT_REASONS = {"UNKNOWN", "UNKNOWN_NO_DEAL", "UNKNOWN_NO_HISTORY"}


def main():
    parser = argparse.ArgumentParser(description="PSA Legacy Cleanup")
    parser.add_argument("--feedback", default="audit/paper/trade_feedback.jsonl",
                        help="Caminho para trade_feedback.jsonl")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mostrar mudanças sem escrever")
    args = parser.parse_args()

    src = Path(args.feedback)
    if not src.exists():
        print(f"[SKIP] {src} não encontrado — nada a limpar")
        return

    bak = src.with_suffix(".jsonl.bak")
    if not args.dry_run:
        shutil.copy2(src, bak)
        print(f"[BACKUP] {bak}")

    lines = src.read_text(encoding="utf-8").splitlines()
    total = len(lines)
    marked = 0
    errors = 0
    out_lines = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            out_lines.append(line)
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            errors += 1
            out_lines.append(line)
            continue

        is_legacy = False
        exit_r = row.get("exit_reason", "")

        # Condição legacy: magic ausente/≠234001 OU exit_reason inválido
        if row.get("entry_magic", row.get("magic", 0)) != OMEGA_MAGIC:
            is_legacy = True
        if exit_r in INVALID_EXIT_REASONS:
            is_legacy = True
        # Linhas sem campo exit_reason (schema antigo)
        if "exit_reason" not in row and row.get("event") == "position_closed":
            is_legacy = True

        if is_legacy and not row.get("legacy_unreconciled"):
            row["legacy_unreconciled"] = True
            row["legacy_ts"] = datetime.now(timezone.utc).isoformat()
            row["legacy_reason"] = f"magic_absent_or_unknown_exit_reason (pre-P0-CICC-20260521)"
            marked += 1

        out_lines.append(json.dumps(row, ensure_ascii=False))

    print(f"[CLEANUP] Total linhas: {total} | Marcadas legacy: {marked} | Erros parse: {errors}")

    cleaned_path = src.parent / "trade_feedback_cleaned.jsonl"
    if args.dry_run:
        print(f"[DRY-RUN] Seria escrito: {cleaned_path}")
        return

    cleaned_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"[OK] Escrito: {cleaned_path}")
    print(f"[NEXT] mv {cleaned_path} {src}")
    print(f"[NOTE] Backup em: {bak}")


if __name__ == "__main__":
    main()
