import json
import os
import uuid
import psycopg2
from datetime import datetime, timezone

def main():
    dsn = os.environ.get("OMEGA_PG_DSN") or os.environ.get("FIN_SENSE_DSN")
    trace_id = str(uuid.uuid4())
    
    out_dir = "00_PROVAS_AUDITORIA"
    os.makedirs(out_dir, exist_ok=True)
    
    json_path = os.path.join(out_dir, f"spike_phase8_{trace_id}.json")
    txt_path = os.path.join(out_dir, f"spike_phase8_{trace_id}.txt")
    
    result = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "phase8_pass": False,
        "error": None
    }
    
    if not dsn:
        result["error"] = "NO_DSN_PROVIDED"
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2)
        with open(txt_path, "w") as f:
            f.write("ERROR: NO_DSN_PROVIDED\n")
        print("Skipped: No DSN provided.")
        return

    try:
        # Mock specific path for when the mock intercepts psycopg2, or real connection if DSN is real
        conn = psycopg2.connect(dsn)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
            if row and row[0] == 1:
                result["phase8_pass"] = True
        conn.close()
        
        with open(txt_path, "w") as f:
            f.write("CONNECTION SUCCESSFUL. Read-only spike passed.\n")
            
    except Exception as e:
        result["error"] = str(e)
        with open(txt_path, "w") as f:
            f.write(f"CONNECTION FAILED: {str(e)}\n")
            
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
        
    print(f"Spike Phase 8 execution: passed={result['phase8_pass']}")
    if not result["phase8_pass"] and result.get("error") != "NO_DSN_PROVIDED":
        exit(1)
    if result.get("error") == "NO_DSN_PROVIDED":
        print("Fase 8 pulada legalmente por falta de gate interno (DSN vazia).")
        exit(0)

if __name__ == "__main__":
    main()
