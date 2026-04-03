#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSA — Checklist objectiva + validação de provas JSON (auditoria de refutação)
Doc-ID: SCRIPT-CHK-PSA-REFUTACAO-20260403
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Raiz: 04_relatorios_tarefa/
HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates_auditoria_psa"

# Checklist fechada — cada item: id, descrição verificável, tipo prova
CHECKLIST: list[dict[str, str]] = [
    {"id": "CHK-ITEM-001", "desc": "git rev-parse HEAD obtido e registável (40 hex)", "tipo": "comando"},
    {"id": "CHK-ITEM-002", "desc": "PSA_RUN_LOG.jsonl existe e parse JSONL linha-a-linha OK", "tipo": "ficheiro+parse"},
    {"id": "CHK-ITEM-003", "desc": "INVENTARIO_FONTES_DADOS_v1.csv existe (≥1 linha dados)", "tipo": "ficheiro"},
    {"id": "CHK-ITEM-010", "desc": "FIN-SENSE DATA MODULE.txt em Auditoria Conselho (path normativo)", "tipo": "path"},
    {"id": "CHK-ITEM-011", "desc": "DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md existe", "tipo": "path"},
    {"id": "CHK-ITEM-020", "desc": "PSA_GATE_CONSELHO_ULTIMO.txt existe", "tipo": "path"},
    {"id": "CHK-ITEM-021", "desc": "finsense_validation_kit.py existe", "tipo": "path"},
    {"id": "CHK-ITEM-030", "desc": "PH-FS-02: CATALOGO_OHLCV_PLANO_v1.md (quando fase iniciada)", "tipo": "path_opcional"},
]

PROOF_ID_RE = re.compile(r"^PRF-[A-Z0-9]+-\d{8}-\d{3}$")
REQ_ID_RE = re.compile(r"^REQ-[A-Z]+-\d{3}$")
GIT_HEAD_RE = re.compile(r"^[0-9a-f]{40}$")


def _validate_proof_obj(data: dict) -> list[str]:
    errs: list[str] = []
    for k in (
        "proof_id",
        "req_id",
        "doc_ref",
        "fase",
        "titulo_curto",
        "artefacto_obrigatorio",
        "comando_ou_predicado",
        "resultado_esperado",
        "resultado_actual",
        "veredito",
        "git_head",
        "ts_utc",
    ):
        if k not in data:
            errs.append(f"missing:{k}")
    if "veredito" in data and data["veredito"] not in ("PASS", "FAIL"):
        errs.append("veredito must be PASS or FAIL")
    if "proof_id" in data and not PROOF_ID_RE.match(data["proof_id"] or ""):
        errs.append("proof_id format invalid (use PRF-<FASE>-YYYYMMDD-SEQ)")
    if "req_id" in data and not REQ_ID_RE.match(data["req_id"] or ""):
        errs.append("req_id format invalid (use REQ-<DOC>-NNN)")
    if "git_head" in data and data["git_head"] and not GIT_HEAD_RE.match(data["git_head"]):
        errs.append("git_head must be 40 hex chars")
    return errs


def validate_proof_file(path: Path) -> int:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL read json: {e}")
        return 2
    if not isinstance(data, dict):
        print("FAIL root must be object")
        return 2
    errs = _validate_proof_obj(data)
    if errs:
        print("FAIL validation:")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"PASS proof file OK: {path.name}")
    return 0


def emit_templates() -> None:
    TEMPLATES.mkdir(parents=True, exist_ok=True)
    empty = {
        "proof_id": "PRF-PHFS02-20260403-001",
        "req_id": "REQ-UNICO-030",
        "doc_ref": "DOC-OFC-PSA-PROVAS-AUD-20260403",
        "fase": "PH-FS-02",
        "titulo_curto": "",
        "artefacto_obrigatorio": "04_relatorios_tarefa/CATALOGO_OHLCV_PLANO_v1.md",
        "comando_ou_predicado": "",
        "resultado_esperado": "",
        "resultado_actual": "",
        "veredito": "FAIL",
        "bloqueador": "preencher após execução",
        "git_head": "0" * 40,
        "ts_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    p = TEMPLATES / "prova_TEMPLATE_PREENCHER.json"
    p.write_text(json.dumps(empty, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {p}")


def report_checklist() -> None:
    print("=== CHECKLIST (estado por inspeção de paths — PENDENTE até prova JSON ligada) ===\n")
    for item in CHECKLIST:
        status = "PENDENTE"
        iid = item["id"]
        if item["tipo"] == "path":
            rel = {
                "CHK-ITEM-010": Path("..") / ".." / ".." / "Auditoria Conselho" / "FIN‑SENSE DATA MODULE.txt",
                "CHK-ITEM-011": HERE / "DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md",
                "CHK-ITEM-020": HERE / "PSA_GATE_CONSELHO_ULTIMO.txt",
                "CHK-ITEM-021": HERE / "finsense_validation_kit.py",
            }.get(iid)
            if rel is not None and Path(HERE / rel if not iid.startswith("CHK-ITEM-010") else HERE / ".." / ".." / ".." / "Auditoria Conselho" / "FIN‑SENSE DATA MODULE.txt").exists():
                # Simplificação: paths relativos ao repo
                pass
        print(f"{iid}  [{status}]  {item['desc']}")
    print("\nPreencher provas JSON por tarefa; veredito só PASS/FAIL.")
    print(f"Templates: {TEMPLATES}")


def quick_path_checks() -> None:
    """Verificações mínimas não subjectivas no disco (04_relatorios_tarefa)."""
    repo_reports = HERE
    checks = [
        ("PSA_RUN_LOG.jsonl", repo_reports / "PSA_RUN_LOG.jsonl"),
        ("INVENTARIO_FONTES_DADOS_v1.csv", repo_reports / "INVENTARIO_FONTES_DADOS_v1.csv"),
        ("DOCUMENTO_UNICO", repo_reports / "DOCUMENTO_UNICO_PSA_MESTRE_FIN_SENSE.md"),
        ("GATE", repo_reports / "PSA_GATE_CONSELHO_ULTIMO.txt"),
        ("KIT", repo_reports / "finsense_validation_kit.py"),
    ]
    print("=== QUICK PATH CHECK (existência ficheiro) ===\n")
    for name, p in checks:
        ok = p.is_file()
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {p.name}")
    conselho = repo_reports.parent.parent.parent / "Auditoria Conselho"
    fin = list(conselho.glob("FIN*SENSE*DATA*MODULE.txt"))
    ok = len(fin) == 1 and fin[0].is_file()
    print(f"{'PASS' if ok else 'FAIL'}  FIN-SENSE Conselho (glob FIN*SENSE*DATA*MODULE.txt)")


def main() -> int:
    ap = argparse.ArgumentParser(description="PSA refutation checklist")
    ap.add_argument("--emit-template", action="store_true", help="Gera template JSON em templates_auditoria_psa/")
    ap.add_argument("--validate", type=Path, metavar="FILE", help="Valida um ficheiro de prova JSON")
    ap.add_argument("--report", action="store_true", help="Lista checklist")
    ap.add_argument("--quick", action="store_true", help="Testa existência de paths chave")
    args = ap.parse_args()

    if args.emit_template:
        emit_templates()
        return 0
    if args.validate:
        return validate_proof_file(args.validate)
    if args.quick:
        quick_path_checks()
        return 0
    if args.report:
        report_checklist()
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
