#!/usr/bin/env python3
"""
Verificação Tier-0 — PSA (manifesto Git, ficheiros, gateway opp_cost).

Uso (na raiz nebular-kuiper ou com NEBULAR_KUIPER_ROOT):
  python verify_tier0_psa.py

Saída: código 0 se tudo OK; 1 se falha. Imprime relatório em texto.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# Raiz do repositório nebular-kuiper (evidencia_pre_demo -> Núcleo -> Auditoria PARR-F -> repo)
_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_REPO = _SCRIPT_DIR.parent.parent.parent  # .../nebular-kuiper
REPO_ROOT = Path(os.environ.get("NEBULAR_KUIPER_ROOT", _DEFAULT_REPO)).resolve()

MANIFEST = _SCRIPT_DIR / "03_hashes_manifestos" / "MANIFEST_RUN_20260329.json"
LOGS_DIR = _SCRIPT_DIR / "02_logs_execucao"
RAW_DIR = _SCRIPT_DIR / "01_raw_mt5"
GATEWAY = REPO_ROOT / "Auditoria PARR-F" / "10_mt5_gateway_V10_4_OMNIPRESENT.py"


def _sha3_file(p: Path) -> str:
    h = hashlib.sha3_256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _run_git(*args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        return ""
    return (r.stdout or "").strip()


def main() -> int:
    errors: list[str] = []
    print("=== verify_tier0_psa.py ===")
    print(f"REPO_ROOT: {REPO_ROOT}")
    print(f"MANIFEST:  {MANIFEST}")

    if not MANIFEST.is_file():
        print("FALHA: manifesto não encontrado.")
        return 1

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sha_manifest = data.get("git_commit_sha", "")
    head = _run_git("rev-parse", "HEAD")

    print("\n[1] Git HEAD vs manifest git_commit_sha")
    print(f"    HEAD:             {head}")
    print(f"    manifest:         {sha_manifest}")
    if not head or head != sha_manifest:
        errors.append("HEAD != git_commit_sha do manifesto")
    else:
        print("    OK: coincidem.")

    otype = _run_git("cat-file", "-t", sha_manifest)
    print("\n[2] git cat-file -t <sha_manifest>")
    print(f"    tipo: {otype or '(erro)'}")
    if otype != "commit":
        errors.append("git_commit_sha não resolve a objecto tipo commit")

    print("\n[3] Ficheiros do manifesto (bytes + SHA3-256)")
    for entry in data.get("files", []):
        ftype = entry.get("type", "")
        name = entry.get("filename", "")
        exp_bytes = entry.get("bytes")
        exp_hash = entry.get("sha3_256_full", "")
        if ftype == "STRESS_LOG":
            path = LOGS_DIR / name
        elif ftype == "RAW_MT5":
            path = RAW_DIR / name
        elif ftype == "DEMO_LOG":
            rel = entry.get("relpath", "")
            path = (REPO_ROOT / rel.replace("/", os.sep)).resolve() if rel else Path()
            name = name or Path(rel).name
        else:
            path = REPO_ROOT / name

        if not path.is_file():
            errors.append(f"ficheiro em falta: {path}")
            print(f"    FALTA: {name or path}")
            continue
        got_bytes = path.stat().st_size
        got_hash = _sha3_file(path)
        ok_b = exp_bytes == got_bytes
        ok_h = exp_hash.lower() == got_hash.lower()
        status = "OK" if (ok_b and ok_h) else "FALHA"
        print(f"    [{status}] {name} bytes={got_bytes} sha3={got_hash[:16]}...")
        if not ok_b:
            errors.append(f"bytes {name}: esperado {exp_bytes}, obtido {got_bytes}")
        if not ok_h:
            errors.append(f"hash {name}: manifesto != disco")

    print("\n[4] Gateway — opportunity_cost")
    if not GATEWAY.is_file():
        errors.append(f"gateway não encontrado: {GATEWAY}")
        print(f"    FALTA: {GATEWAY}")
    else:
        text = GATEWAY.read_text(encoding="utf-8", errors="replace")
        needle = "abs(y_price - (0.5 * x_price))"
        if needle in text:
            print(f"    OK: encontrado `{needle}`")
        else:
            errors.append("gateway sem fórmula opp_cost esperada (abs(y_price - (0.5 * x_price)))")
            print("    FALHA: fórmula esperada não encontrada no gateway.")

    print("\n--- RESUMO ---")
    if errors:
        print("ESTADO: FALHA")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("ESTADO: OK (Tier-0 verificação automática passou)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
