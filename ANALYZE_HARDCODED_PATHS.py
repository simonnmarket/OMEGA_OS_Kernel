#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALYZE_HARDCODED_PATHS.py
Analisa arquivos .py (código ativo) em busca de paths hardcoded e gera relatório.
Ignora backups, venvs e __pycache__ para reduzir ruído.
"""

import os
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent
OUTPUT_FILE = "path_analysis_report.txt"

EXCLUDE_PATTERNS = [
    "Auditoria PARR-F",
    "inativo",
    "__pycache__",
    ".git",
    "venv",
    ".venv",
    "node_modules",
    "BACKUP",
    "BACKUPS",
    "backup",
    "archive",
    "omega_core_validation/venv_psa",
    "OMEGA_INTELLIGENCE_OS/09_INBOX/Projects/Aurora BACKUP_2025_COMPLETO",
]
PATTERNS = [
    r"[A-Z]:\\[^\\s'\"`]+",      # Windows C:\...
    r"[A-Z]:/[^\\s'\"`]+",       # Windows C:/...
    r"/(?:home|Users|opt|var|tmp)/[^\\s'\"`]+",  # Unix absolutos
    r"BAU_DO_TESOURO",
    r"OMEGA_PROJETO",
    r"OHLCV_DATA",
]


def should_skip(path: Path) -> bool:
    rel = str(path).replace("\\", "/")
    return any(skip.lower() in rel.lower() for skip in EXCLUDE_PATTERNS)


def analyze_file(path: Path):
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return findings

    for i, line in enumerate(text, 1):
        if line.strip().startswith("#"):
            continue
        for pat in PATTERNS:
            if re.search(pat, line):
                findings.append((i, line.strip(), pat))
                break
    return findings


def main():
    py_files = [p for p in ROOT.rglob("*.py") if not should_skip(p)]
    results = []

    for f in py_files:
        for line_no, content, pat in analyze_file(f):
            results.append((f, line_no, content, pat))

    lines = []
    lines.append("=" * 80)
    lines.append("RELATÓRIO DE PATHS HARDCODED - OMEGA PROJECT")
    lines.append("=" * 80)
    lines.append(f"Data: {datetime.utcnow().isoformat()}")
    lines.append(f"Raiz: {ROOT}")
    lines.append(f"Total arquivos analisados: {len(py_files)}")
    lines.append(f"Total paths hardcoded: {len(results)}")
    lines.append("=" * 80)
    lines.append("")

    by_file = {}
    for f, lno, content, pat in results:
        by_file.setdefault(f, []).append((lno, content, pat))

    for f, items in sorted(by_file.items(), key=lambda x: str(x[0])):
        lines.append(f"ARQUIVO: {f}")
        lines.append("-" * 60)
        for lno, content, pat in items:
            lines.append(f"  Linha {lno}: {content[:120]}")
        lines.append("")

    lines.append("=" * 80)
    lines.append("RECOMENDAÇÕES:")
    lines.append("1. Substituir paths absolutos por env vars (ver lista abaixo).")
    lines.append("2. Usar os.getenv(..., fallback_relativo) + validação de existência/permissão.")
    lines.append("3. Documentar env vars no README.")
    lines.append("=" * 80)

    Path(OUTPUT_FILE).write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Relatório salvo em: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
