#!/usr/bin/env python3
"""
PSA — Sincronizar MANIFEST_RUN_*.json com o disco (bytes + SHA3-256 por entrada).

Resolve desalinhamentos após edição de ficheiros rastreados pelo Tier-0.
A resolução de caminhos replica verify_tier0_psa.py (mesma árvore = mesmo resultado).

Uso:
  python psa_sync_manifest_from_disk.py
  python psa_sync_manifest_from_disk.py --dry-run
  python psa_sync_manifest_from_disk.py --set-git-commit-sha-from-head

Variável opcional: NEBULAR_KUIPER_ROOT (raiz do repo nebular-kuiper).

Nota sobre git_commit_sha:
  --set-git-commit-sha-from-head escreve o HEAD actual no manifesto.
  Após gravar, pode ser necessário commit + repetir até verify_tier0_psa.py passar
  (o HEAD muda a cada novo commit que inclui o manifesto).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_REPO = _SCRIPT_DIR.parent.parent.parent
REPO_ROOT = Path(os.environ.get("NEBULAR_KUIPER_ROOT", _DEFAULT_REPO)).resolve()

MANIFEST = _SCRIPT_DIR / "03_hashes_manifestos" / "MANIFEST_RUN_20260329.json"
LOGS_DIR = _SCRIPT_DIR / "02_logs_execucao"
RAW_DIR = _SCRIPT_DIR / "01_raw_mt5"


def _sha3_file(p: Path) -> str:
    h = hashlib.sha3_256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _resolve_path(entry: dict) -> tuple[Path, str]:
    """Retorna (path absoluto, nome para log)."""
    ftype = entry.get("type", "")
    name = entry.get("filename", "")
    if ftype == "STRESS_LOG":
        return LOGS_DIR / name, name
    if ftype == "RAW_MT5":
        return RAW_DIR / name, name
    if ftype == "DEMO_LOG":
        rel = entry.get("relpath", "")
        path = (REPO_ROOT / rel.replace("/", os.sep)).resolve() if rel else Path()
        return path, name or Path(rel).name
    path = REPO_ROOT / name
    return path, name


def _git_head() -> str:
    r = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return (r.stdout or "").strip() if r.returncode == 0 else ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Sincronizar manifesto Tier-0 com o disco (PSA).")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra alterações sem gravar o JSON.",
    )
    ap.add_argument(
        "--set-git-commit-sha-from-head",
        action="store_true",
        help="Define git_commit_sha no manifesto = saída de git rev-parse HEAD.",
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=MANIFEST,
        help="Caminho para MANIFEST_RUN_*.json",
    )
    args = ap.parse_args()

    manifest_path = args.manifest.resolve()
    if not manifest_path.is_file():
        print(f"ERRO: manifesto não encontrado: {manifest_path}", file=sys.stderr)
        return 1

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    changes: list[str] = []

    for entry in data.get("files", []):
        path, label = _resolve_path(entry)
        if not path.is_file():
            changes.append(f"[SKIP] ficheiro em falta: {path} ({label})")
            continue
        got_bytes = path.stat().st_size
        got_hash = _sha3_file(path)
        old_b = entry.get("bytes")
        old_h = (entry.get("sha3_256_full") or "").lower()
        if old_b != got_bytes or old_h != got_hash.lower():
            changes.append(
                f"[UPDATE] {label}: bytes {old_b} -> {got_bytes}; sha3 ...{old_h[-8:] if old_h else '?'} -> ...{got_hash[:8]}"
            )
        if not args.dry_run:
            entry["bytes"] = got_bytes
            entry["sha3_256_full"] = got_hash

    head = _git_head()
    if args.set_git_commit_sha_from_head:
        old_sha = data.get("git_commit_sha", "")
        if head and old_sha != head:
            changes.append(f"[UPDATE] git_commit_sha: {old_sha[:12]}... -> {head[:12]}...")
        if not args.dry_run and head:
            data["git_commit_sha"] = head

    if args.dry_run:
        print("=== DRY-RUN (nada gravado) ===")
        for line in changes:
            print(line)
        if not changes:
            print("(sem diferenças detectadas)")
        return 0

    manifest_path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK: manifesto gravado: {manifest_path}")
    for line in changes:
        print(line)
    if not changes:
        print("(nenhuma alteração de bytes/hash; git_commit_sha pode estar igual)")

    if args.set_git_commit_sha_from_head and not head:
        print("AVISO: git indisponível — git_commit_sha não actualizado.", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
