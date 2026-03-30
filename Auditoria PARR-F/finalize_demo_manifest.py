import json
import hashlib
import os

manifest_path = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\evidencia_pre_demo\03_hashes_manifestos\MANIFEST_RUN_20260329.json"
demo_log = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\omega_core_validation\evidencia_demo_20260330\DEMO_LOG_SWING_TRADE_20260330.csv"

# SHA3-256
h = hashlib.sha3_256(open(demo_log, 'rb').read()).hexdigest()
b = os.path.getsize(demo_log)

with open(manifest_path, 'r') as f:
    m = json.load(f)

# Update GIT SHA to latest (Final Smoke Test)
m['git_commit_sha'] = '8c9d05202c2232324f657f6f132d5fef4c88b4e9'

# Append Demo Log Entry
entry = {
    "type": "DEMO_LOG",
    "filename": "DEMO_LOG_SWING_TRADE_20260330.csv",
    "bytes": b,
    "sha3_256_full": h
}

# Only append if not already there
if not any(f['filename'] == entry['filename'] for f in m['files']):
    m['files'].append(entry)

with open(manifest_path, 'w') as f:
    json.dump(m, f, indent=4)

print(f"[OK] MANIFEST UPDATED WITH DEMO LOG AND SHA: {m['git_commit_sha']}")
