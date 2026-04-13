import argparse
import json
import os
import subprocess
from datetime import datetime, timezone

def get_git_head(repo_path):
    try:
        result = subprocess.run(["git", "-C", repo_path, "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return result.stdout.strip(), None
    except Exception as e:
        return None, str(e)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-a", default=r"C:\Users\Lenovo\Desktop\OMEGA_OS_Kernel")
    parser.add_argument("--repo-b", default=r"C:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper")
    parser.add_argument("--label-a", default="desktop")
    parser.add_argument("--label-b", default="kuiper")
    args = parser.parse_args()

    head_a, err_a = get_git_head(args.repo_a)
    head_b, err_b = get_git_head(args.repo_b)

    out_dir = r"00_PROVAS_AUDITORIA"
    os.makedirs(out_dir, exist_ok=True)

    if head_a:
        with open(os.path.join(out_dir, f"ssot_HEAD_{args.label_a}.txt"), "w") as f:
            f.write(head_a + "\n")
    if head_b:
        with open(os.path.join(out_dir, f"ssot_HEAD_{args.label_b}.txt"), "w") as f:
            f.write(head_b + "\n")

    parity_match = (head_a == head_b) and (head_a is not None)
    
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo_a": {"label": args.label_a, "path": args.repo_a, "head": head_a, "error": err_a},
        "repo_b": {"label": args.label_b, "path": args.repo_b, "head": head_b, "error": err_b},
        "parity_match": parity_match
    }
    
    utc_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = os.path.join(out_dir, f"ssot_parity_report_{utc_str}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(json.dumps(report, indent=2))

    if os.environ.get("OMEGA_REQUIRE_GIT_PARITY") == "1" and not parity_match:
        print("ERROR: Git parity match failed!")
        exit(1)

if __name__ == "__main__":
    main()
