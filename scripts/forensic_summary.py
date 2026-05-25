import json
from pathlib import Path

r = json.load(open("logs/forensic_report_20260429.json", encoding="utf-8"))

print("MELHORES CANDIDATOS NAO INTEGRADOS:")
print("-" * 72)
for name, data in r["components"].items():
    if data["not_integrated"] > 0 and data["best_candidate"]:
        b = data["best_candidate"]
        print(f"[{data['priority']}] {name}")
        print(f"  arquivo : {b['file']}")
        print(f"  tamanho : {b['size_kb']}KB  data: {b['modified']}")
        print(f"  keywords: {b['keywords_hit'][:5]}")
        print()

# Mostrar os walk_forward e pullback específicos
print("=" * 72)
print("WALK-FORWARD OOS — candidatos Python:")
for e in r.get("exclusive_nebular", []):
    if "walk" in e["file"].lower() or "oos" in e["file"].lower():
        print(f"  {e['file']:<50} {e['size_kb']:>6.1f}KB  {e['modified']}")

print("\nPULLBACK ENGINE — candidatos Python:")
for e in r.get("exclusive_nebular", []):
    if "pullback" in e["file"].lower() or "pullback" in e.get("path", "").lower():
        print(f"  {e['file']:<50} {e['size_kb']:>6.1f}KB  {e['modified']}")

print("\nCALENDARIO / NEWS — candidatos Python:")
for e in r.get("exclusive_nebular", []):
    n = e["file"].lower()
    if any(k in n for k in ["calendar", "news", "economic", "fomc", "macro"]):
        print(f"  {e['file']:<50} {e['size_kb']:>6.1f}KB  {e['modified']}")

print("\nOMEGA_OS_KERNEL modules (nebular):")
nb = Path(r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\OMEGA_OS_Kernel\modules")
if nb.exists():
    for f in nb.rglob("*.py"):
        kb = round(f.stat().st_size / 1024, 1)
        if kb > 1:
            print(f"  {f.name:<45} {kb:>6.1f}KB")
