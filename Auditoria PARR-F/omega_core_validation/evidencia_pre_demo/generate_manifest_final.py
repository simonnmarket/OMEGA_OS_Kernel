import os
import hashlib
import json
import pandas as pd
from datetime import datetime

# PATHS
BASE_EVIDENCIA = r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\Auditoria PARR-F\Núcleo de Validação OMEGA\evidencia_pre_demo"
LOGS_DIR = os.path.join(BASE_EVIDENCIA, "02_logs_execucao")
RAW_DIR = os.path.join(BASE_EVIDENCIA, "01_raw_mt5")
MANIFEST_DIR = os.path.join(BASE_EVIDENCIA, "03_hashes_manifestos")

def get_file_hash(filepath):
    sha3 = hashlib.sha3_256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha3.update(chunk)
    return sha3.hexdigest()

def generate_manifest():
    manifest_data = {
        "run_id": f"OMEGA_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "version": "V10.4 OMNIPRESENT",
        "python_version": f"{os.sys.version}",
        "ts_audit": datetime.utcnow().isoformat() + "Z",
        "files": []
    }
    
    # Process Logs
    for f in os.listdir(LOGS_DIR):
        if f.endswith(".csv"):
            p = os.path.join(LOGS_DIR, f)
            df = pd.read_csv(p)
            f_hash = get_file_hash(p)
            
            # Row Samples for M1 Verification (M1 checklist)
            # Show first and last hash
            manifest_data["files"].append({
                "type": "STRESS_LOG",
                "filename": f,
                "row_count": len(df),
                "bytes": os.path.getsize(p),
                "sha3_256_full": f_hash,
                "first_row_sha3": df['sha3_256'].iloc[0],
                "last_row_sha3": df['sha3_256'].iloc[-1]
            })

    # Process Raw
    for f in os.listdir(RAW_DIR):
        if f.endswith(".csv"):
            p = os.path.join(RAW_DIR, f)
            f_hash = get_file_hash(p)
            manifest_data["files"].append({
                "type": "RAW_MT5",
                "filename": f,
                "bytes": os.path.getsize(p),
                "sha3_256_full": f_hash
            })
            
    # Save Manifest
    m_path = os.path.join(MANIFEST_DIR, f"MANIFEST_RUN_20260329.json")
    with open(m_path, "w", encoding="utf-8") as j:
        json.dump(manifest_data, j, indent=4)
    
    print(f"[OK] MANIFESTO GERADO: {m_path}")
    return manifest_data

if __name__ == "__main__":
    generate_manifest()
