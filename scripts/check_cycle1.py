import json, glob

import os
dirs = sorted([d for d in os.listdir("logs/agent_ia_phase3/") if d.startswith("fase4_BASELINE_")], reverse=True)
path = "logs/agent_ia_phase3/" + dirs[0] + "/" if dirs else "logs/agent_ia_phase3/fase4_BASELINE_20260429_111213/"
print(f"Run dir: {dirs[0] if dirs else 'NOT FOUND'}")
files = sorted(glob.glob(path + "paper_summary_0*.json"))
if not files:
    print("Sem arquivos ainda")
    exit()

f = files[-1]
d = json.load(open(f, encoding="utf-8"))
print(f"Ciclo: {f}")
print(f"Executed: {d.get('online_stats',{}).get('executed',0)}")
print()
for r in d.get("results", []):
    em = r.get("edge_metrics", {})
    reason = em.get("reason", "")
    atr_pct = em.get("atr_pct", "")
    vol_ratio = em.get("vol_ratio", "")
    asset = r.get("asset", "")
    tf = r.get("timeframe", "")
    status = r.get("status", "")
    print(f"  {asset:8} {tf}: {status:30} atr={atr_pct} vol={vol_ratio} | {reason}")
