#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import hashlib

def kpis(path: Path, init_balance: float = 10000.0):
    if not path.exists():
        return {"error": "File not found"}
    
    df = pd.read_csv(path)
    fb = float(df["BALANCE"].iloc[-1])
    net = (fb / init_balance - 1) * 100
    max_dd = float(df["DD_PCT"].max())
    
    bal = df["BALANCE"]
    trades = bal.diff().fillna(0)
    trades = trades[trades != 0]
    
    win_rate = (trades[trades > 0].count() / trades.count() * 100) if trades.count() else 0.0
    pf = (trades[trades > 0].sum() / abs(trades[trades < 0].sum())) if trades[trades < 0].sum() != 0 else 0.0
    
    # SEI_EVENT: Filtrar apenas valores não-nulos para média real por evento
    sei_events = df[df["SEI_EVENT"] != 0]["SEI_EVENT"]
    sei_mean = sei_events.mean() if not sei_events.empty else 0.0
    
    launch_dist = df["LAUNCH"].value_counts().to_dict() if "LAUNCH" in df else {}
    score_dist = df["SCORE"].value_counts().to_dict() if "SCORE" in df else {}
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return {
        "final_balance": round(fb, 2),
        "net_return_pct": round(net, 2),
        "max_dd_pct": round(max_dd, 2),
        "trades": int(trades.count()),
        "win_rate_pct": win_rate,
        "profit_factor": pf,
        "sei_event_mean": sei_mean,
        "launch_dist": launch_dist,
        "score_dist": score_dist,
        "sha256": sha256_hash.hexdigest()
    }

if __name__ == "__main__":
    import json
    path = Path(r"C:\OMEGA_PROJETO\PROJETO OMEGA QUANTITATIVE FUND\AUDIT_EVIDÊNCIA_CIENTÍFICA\FULL_RECONCILED_V590.csv")
    res = kpis(path)
    print(json.dumps(res, indent=4))
