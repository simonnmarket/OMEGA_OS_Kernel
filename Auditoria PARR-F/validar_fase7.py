import json, re, sys
from pathlib import Path

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    files = sorted(root.glob("omega_audit_PARRF_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    if len(files) < 5:
        print("FAIL: <5 audits"); return 2
    hx = re.compile(r"^[0-9a-f]{64}$", re.I)
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        dos = d.get("layers", {}).get("dos", {})
        errs = dos.get("errors") or []
        prov = dos.get("provenance_sha256") or ""
        ok = len(errs) == 0 and bool(hx.match(str(prov)))
        print(f"{f.name} PASS_LINE={ok}")
        if not ok: return 1
    print("PASS_FASE7: 5/5"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
