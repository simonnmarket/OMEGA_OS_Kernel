#!/usr/bin/env python3
"""
OMEGA_AUDIT_ENGINE — inventário estático do código OMEGA (SOURCE_CODE).

Primeira passagem (CEO OIS-20260517): mapear ficheiros Python, imports prováveis,
e checksums SHA3-256 sem exigir conformidade estrita.

Uso (PowerShell, a partir de SOURCE_CODE):
  python scripts/OMEGA_AUDIT_ENGINE.py --root . --no-strict
  python scripts/OMEGA_AUDIT_ENGINE.py --root C:\\OMEGA_QUANTUM_LAB\\SOURCE_CODE --no-strict
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def sha3_file(path: Path) -> str:
    h = hashlib.sha3_256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_py_files(root: Path) -> Iterable[Path]:
    skip = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        "audit_output",
        "site-packages",
        ".tox",
        "dist-packages",
    }
    for p in root.rglob("*.py"):
        if any(part in skip for part in p.parts):
            continue
        yield p


def top_level_imports(src: str) -> list[str]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out: list[str] = []
    for n in tree.body:
        if isinstance(n, ast.Import):
            for alias in n.names:
                out.append(alias.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.append(n.module.split(".")[0])
    return sorted(set(out))


@dataclass
class FileRecord:
    path: str
    bytes: int
    sha3_256: str
    imports: list[str]
    syntax_ok: bool


def run_inventory(root: Path, strict: bool) -> dict[str, Any]:
    records: list[FileRecord] = []
    issues: list[dict[str, str]] = []
    secret_hits: list[str] = []

    secret_re = re.compile(
        r"(?i)(api[_-]?key|password|secret|bearer\s+[a-z0-9_-]{20,}|-----BEGIN [A-Z ]+PRIVATE KEY-----)"
    )

    for fp in sorted(iter_py_files(root), key=lambda x: str(x).lower()):
        rel = str(fp.relative_to(root))
        try:
            raw = fp.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            issues.append({"path": rel, "error": str(e)})
            continue
        if not strict:
            for m in secret_re.finditer(raw):
                if "example" in m.group(0).lower():
                    continue
                secret_hits.append(f"{rel}:{m.start()}")
        syn_ok = True
        try:
            ast.parse(raw)
        except SyntaxError as se:
            syn_ok = False
            issues.append({"path": rel, "error": f"syntax: {se}"})
            if strict:
                raise
        rec = FileRecord(
            path=rel,
            bytes=len(raw.encode("utf-8")),
            sha3_256=sha3_file(fp),
            imports=top_level_imports(raw),
            syntax_ok=syn_ok,
        )
        records.append(rec)

    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "root": str(root.resolve()),
        "strict": strict,
        "python_files": len(records),
        "records": [asdict(r) for r in records],
        "issues": issues,
        "secret_pattern_hits_preview": secret_hits[:200],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="OMEGA inventário de código (auditoria)")
    ap.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Raiz SOURCE_CODE (default: parent de scripts/)",
    )
    ap.add_argument(
        "--no-strict",
        action="store_true",
        help="Não falhar por sintaxe; apenas listar issues",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Pasta de saída (default: <root>/audit_output/inventory_<timestamp>)",
    )
    args = ap.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(f"ROOT inválido: {root}", file=sys.stderr)
        return 2

    strict = not args.no_strict
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir or (root / "audit_output" / f"inventory_{ts}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "inventory.json"

    payload = run_inventory(root, strict=strict)
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK inventário: {payload['python_files']} ficheiros .py")
    print(f"JSON: {out_json}")
    if payload["issues"]:
        print(f"Avisos/issues: {len(payload['issues'])} (ver inventory.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
