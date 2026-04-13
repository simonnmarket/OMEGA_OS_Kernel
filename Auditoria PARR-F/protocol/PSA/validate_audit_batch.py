#!/usr/bin/env python3
"""
Validação em lote: audits omega_audit_*.json vs AUDIT_JSON_SCHEMA_V1.0.json (L-04).
Uso:
  pip install jsonschema
  python validate_audit_batch.py --schema Conselho/AUDIT_JSON_SCHEMA_V1.0.json \\
      --glob "00_PROVAS_AUDITORIA/orchestrator_runs/omega_audit_PARRF_*.json" --max 50
Exit: 0 = todos PASS, 1 = falha(s) ou schema inválido.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError:
    print("ERRO: instale jsonschema: pip install jsonschema", file=sys.stderr)
    raise SystemExit(2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", required=True, type=Path)
    ap.add_argument("--glob", required=True, help="Glob de ficheiros JSON a validar")
    ap.add_argument("--max", type=int, default=100)
    ap.add_argument("--csv-out", type=str, help="Saída opcional CSV")
    ap.add_argument("--json-summary", type=str, help="Saída resumo JSON")
    args = ap.parse_args()

    schema_path = args.schema.resolve()
    if not schema_path.is_file():
        print(f"ERRO: schema não encontrado: {schema_path}", file=sys.stderr)
        return 1

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)

    paths = sorted(glob.glob(args.glob, recursive=True))[: args.max]
    if not paths:
        print(f"ERRO: nenhum ficheiro para glob: {args.glob}", file=sys.stderr)
        return 1

    failures: list[tuple[str, str]] = []
    for p in paths:
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
            errs = sorted(validator.iter_errors(data), key=lambda e: e.path)
            if errs:
                msg = errs[0].message
                failures.append((p, msg))
        except Exception as e:  # noqa: BLE001
            failures.append((p, str(e)))

    pass_count = len(paths) - len(failures)
    pass_rate = pass_count / len(paths)
    
    if args.json_summary:
        import datetime
        summary = {
            "exit_ok": bool(len(failures) == 0),
            "pass_rate": pass_rate,
            "total_files": len(paths),
            "failed_files": len(failures),
            "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        with open(args.json_summary, 'w', encoding='utf-8') as fs:
            json.dump(summary, fs, indent=2)
            
    if args.csv_out:
        with open(args.csv_out, 'w', encoding='utf-8') as fc:
            fc.write("path,error_msgn")
            for p, m in failures:
                m_no_commas = m.replace(',', ';').replace('\n', ' ')
                fc.write(f'"{p}","{m_no_commas}"\n')
                
    if failures:
        print(f"FAIL: {len(failures)}/{len(paths)}")
        for path, msg in failures[:50]:
            print(f"  - {path}\n    {msg}")
        if len(failures) > 50:
            print(f"  ... +{len(failures) - 50} mais")
        return 1

    print(f"PASS: {len(paths)} ficheiro(s) conforme schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
