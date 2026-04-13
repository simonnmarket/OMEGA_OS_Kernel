import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()

    out_dir = os.path.join("00_PROVAS_AUDITORIA", "orchestrator_runs")
    os.makedirs(out_dir, exist_ok=True)
    
    success_count = 0
    results = []

    for i in range(args.runs):
        run_name = f"l07_smoke_run_{i+1:02d}"
        print(f"Executing {run_name}...")
        
        # We temporarily change audit dir for the orchestrator to dump into out_dir
        env = os.environ.copy()
        env["OMEGA_AUDIT_DIR"] = out_dir
        
        try:
            result = subprocess.run(
                ["python", "omega_orquestador_tier0_v120.py"],
                env=env,
                capture_output=True,
                text=True,
                check=False
            )
            
            # The orchestrator dumps file 'omega_audit_PARRF_<trace_id>.json'
            # We must parse output if we need to know exactly which file it was, but we can just check if exit 0
            # For strictness, if exit 0, it wasn't an ERROR
            passed = (result.returncode == 0)
            
            if passed:
                success_count += 1
                
            results.append({
                "run": i + 1,
                "exit_code": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "passed": passed
            })
            
            # Save the log of the run
            with open(os.path.join(out_dir, f"{run_name}_stdout.log"), "w", encoding="utf-8") as f:
                f.write(result.stdout)
                
        except Exception as e:
            results.append({
                "run": i + 1,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "passed": False
            })

    total_runs = args.runs
    l07_accepted = (success_count == total_runs)
    
    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_runs": total_runs,
        "success_count": success_count,
        "l07_accepted": l07_accepted,
        "details": results
    }
    
    utc_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary_path = os.path.join(out_dir, f"l07_smoke_summary_{utc_str}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
        
    print(f"L-07 Smoke Test completed. {success_count}/{total_runs} passed. Accepted? {l07_accepted}")
    
    if not l07_accepted:
        exit(1)

if __name__ == "__main__":
    main()
