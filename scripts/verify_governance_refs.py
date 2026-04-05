#!/usr/bin/env python3
"""
Valida referências a DOC-OFC-* no governance/README.md contra ficheiros reais em governance/.

Uso (na raiz do repositório):
  python scripts/verify_governance_refs.py
  python scripts/verify_governance_refs.py --write-manifest

Saída: 0 = OK, 1 = erros (falha CI / pre-push).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GOV = REPO_ROOT / "governance"
README = GOV / "README.md"
MANIFEST = GOV / "MANIFESTO_DOCUMENTOS.json"

# Referência típica: `DOC-OFC-...-NNN` ou sem backticks
REF_PATTERN = re.compile(r"DOC-OFC-[A-Za-z0-9\-]+")


def stems_on_disk() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for p in sorted(GOV.glob("DOC-OFC-*.md")):
        out[p.stem] = p
    return out


def refs_in_readme(text: str) -> set[str]:
    return set(REF_PATTERN.findall(text))


def duplicate_suffix_ids(paths: list[Path]) -> list[tuple[str, list[str]]]:
    """Avisa se o mesmo sufixo -NNN aparece em mais de um ficheiro (ex.: dois -014)."""
    by_num: dict[str, list[str]] = {}
    for p in paths:
        m = re.search(r"-(\d{3})\.md$", p.name)
        if not m:
            continue
        by_num.setdefault(m.group(1), []).append(p.name)
    return [(n, names) for n, names in by_num.items() if len(names) > 1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--write-manifest",
        action="store_true",
        help="Gera/atualiza governance/MANIFESTO_DOCUMENTOS.json a partir do disco.",
    )
    args = ap.parse_args()

    if not GOV.is_dir():
        print(f"ERRO: pasta não encontrada: {GOV}", file=sys.stderr)
        return 1

    on_disk = stems_on_disk()
    errors: list[str] = []
    warnings: list[str] = []

    if not README.is_file():
        print(f"ERRO: README em falta: {README}", file=sys.stderr)
        return 1

    readme_text = README.read_text(encoding="utf-8")
    refs = refs_in_readme(readme_text)

    for stem in sorted(refs):
        if stem not in on_disk:
            errors.append(f"Referência no README sem ficheiro: `{stem}.md`")

    dup = duplicate_suffix_ids(list(on_disk.values()))
    for num, names in dup:
        warnings.append(
            f"Sufixo -{num} repetido em {len(names)} ficheiros: {', '.join(names)}"
        )

    if args.write_manifest:
        payload = {
            "version": 1,
            "description": "Lista canónica de DOC-OFC em governance/ (gerado por verify_governance_refs.py)",
            "documents": [
                {"stem": stem, "file": p.name}
                for stem, p in sorted(on_disk.items(), key=lambda x: x[0])
            ],
        }
        MANIFEST.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"OK: manifesto escrito: {MANIFEST.relative_to(REPO_ROOT)}")

    for w in warnings:
        print(f"AVISO: {w}", file=sys.stderr)

    if errors:
        for e in errors:
            print(f"ERRO: {e}", file=sys.stderr)
        print(
            "\nCorrija o README ou crie o ficheiro em governance/. "
            "Regra: cada `DOC-OFC-...` citado deve existir como .md.",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: {len(refs)} referências DOC-OFC no README verificadas; "
        f"{len(on_disk)} ficheiros DOC-OFC no disco."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
