import json

manifest_path = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\evidencia_pre_demo\03_hashes_manifestos\MANIFEST_RUN_20260329.json"

with open(manifest_path, 'r') as f:
    m = json.load(f)

# Update DEMO_LOG to include relpath
for file in m['files']:
    if file['type'] == "DEMO_LOG":
        file['relpath'] = "Auditoria PARR-F/omega_core_validation/evidencia_demo_20260330/DEMO_LOG_SWING_TRADE_20260330.csv"

with open(manifest_path, 'w') as f:
    json.dump(m, f, indent=4)

print(f"[OK] MANIFEST UPDATED WITH RELPATH FOR DEMO_LOG")
