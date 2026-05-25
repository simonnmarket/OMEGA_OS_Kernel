"""Inventário estático + verificação contra audit_baseline.json (STRICT = veto)."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from modules.omega_audit.reporting import AuditIssue

SKIP_PARTS = frozenset(
    {
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
)


def sha3_file(path: Path) -> str:
    h = hashlib.sha3_256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_py_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        yield p


def build_hash_map(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for fp in sorted(iter_py_files(root), key=lambda x: str(x).lower()):
        rel = str(fp.relative_to(root)).replace("\\", "/")
        out[rel] = sha3_file(fp)
    return out


def default_baseline_path(source_root: Path) -> Path:
    return source_root / "audit" / "omega_audit" / "audit_baseline.json"


def write_baseline(source_root: Path, out_path: Path | None = None) -> Path:
    """Gera audit_baseline.json com mapa relativo -> SHA3-256."""
    root = source_root.resolve()
    out = out_path or default_baseline_path(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    hashes = build_hash_map(root)
    payload = {
        "version": 1,
        "generated": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "algorithm": "sha3-256",
        "hashes": hashes,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


@dataclass
class BaselineVerification:
    ok: bool
    issues: list[AuditIssue]
    checked: int
    mismatched_paths: list[str]


def verify_against_baseline(
    source_root: Path,
    baseline_path: Path,
    *,
    strict: bool = True,
) -> BaselineVerification:
    """
    Compara hashes actuais com baseline. Em strict, baseline ausente ou
    qualquer mismatch => issues CRITICAL (veto de ciclo).
    """
    issues: list[AuditIssue] = []
    root = source_root.resolve()
    if not baseline_path.exists():
        if strict:
            issues.append(
                AuditIssue(
                    "CRITICAL",
                    "STATIC_INVENTORY",
                    "audit_baseline.json ausente ou inacessível",
                    "AUD-BL-001",
                    detail={"path": str(baseline_path)},
                )
            )
        return BaselineVerification(False, issues, 0, [])

    try:
        data = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        if strict:
            issues.append(
                AuditIssue(
                    "CRITICAL",
                    "STATIC_INVENTORY",
                    f"Baseline corrompida ou ilegível: {e}",
                    "AUD-BL-002",
                    detail={"path": str(baseline_path)},
                )
            )
        return BaselineVerification(False, issues, 0, [])

    expected = data.get("hashes") or {}
    if strict and not isinstance(expected, dict):
        issues.append(
            AuditIssue(
                "CRITICAL",
                "STATIC_INVENTORY",
                "Campo 'hashes' inválido na baseline",
                "AUD-BL-003",
            )
        )
        return BaselineVerification(False, issues, 0, [])

    if strict and len(expected) == 0:
        issues.append(
            AuditIssue(
                "CRITICAL",
                "STATIC_INVENTORY",
                "Baseline vazia — veto em STRICT_MODE",
                "AUD-BL-004",
            )
        )
        return BaselineVerification(False, issues, 0, [])

    mismatched: list[str] = []
    current = build_hash_map(root)
    checked = 0
    for rel, want in expected.items():
        rel_norm = rel.replace("\\", "/")
        checked += 1
        got = current.get(rel_norm)
        if got is None:
            mismatched.append(rel_norm)
            issues.append(
                AuditIssue(
                    "CRITICAL",
                    "STATIC_INVENTORY",
                    f"Ficheiro da baseline em falta no disco: {rel_norm}",
                    "AUD-BL-005",
                    detail={"path": rel_norm},
                )
            )
            continue
        if got != want:
            mismatched.append(rel_norm)
            issues.append(
                AuditIssue(
                    "CRITICAL",
                    "STATIC_INVENTORY",
                    f"Hash mismatch: {rel_norm}",
                    "AUD-BL-006",
                    detail={"path": rel_norm, "expected_prefix": want[:16], "actual_prefix": got[:16]},
                )
            )

    ok = len([i for i in issues if i.severity == "CRITICAL"]) == 0
    return BaselineVerification(ok, issues, checked, mismatched)


def run_static_inventory(source_root: Path) -> dict[str, Any]:
    """Inventário completo (útil para CI e para regenerar baseline)."""
    root = source_root.resolve()
    hashes = build_hash_map(root)
    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "python_files": len(hashes),
        "hashes": hashes,
    }
