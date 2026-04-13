import argparse
import os
import shutil
import json
import subprocess
from datetime import datetime, timezone
import pandas as pd
import matplotlib.pyplot as plt

def generate_line_chart(df, output_path, profile_name):
    plt.figure(figsize=(12, 6))
    if 'y' in df.columns:
        plt.plot(df['y'], label='Base Asset (y)', color='blue', alpha=0.7)
    if 'x' in df.columns:
        plt.plot(df['x'], label='Ref Asset (x)', color='orange', alpha=0.5)
    plt.title(f"Historico STRESS (Linha): {profile_name}")
    plt.xlabel("Index")
    plt.ylabel("Price")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def generate_candles_chart(df, output_path, profile_name, max_bars=300):
    # OHLC Sintetico derivado de y e spread
    # Open = prev y, Close = y, High = max(O,C) + spread, Low = min(O,C) - spread
    
    view_df = df.tail(max_bars).copy().reset_index(drop=True)
    if 'y' not in view_df.columns or 'spread' not in view_df.columns:
        return # Skip if columns not found
        
    view_df['Open'] = view_df['y'].shift(1).fillna(view_df['y'])
    view_df['Close'] = view_df['y']
    view_df['High'] = view_df[['Open', 'Close']].max(axis=1) + view_df['spread'].abs()
    view_df['Low'] = view_df[['Open', 'Close']].min(axis=1) - view_df['spread'].abs()
    
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_title(f"OHLC Sintético (Tail {max_bars}): {profile_name}")
    
    up = view_df[view_df.Close >= view_df.Open]
    down = view_df[view_df.Close < view_df.Open]
    
    width = 0.6
    width2 = 0.1
    
    # UP Bars
    ax.bar(up.index, up.Close - up.Open, width, bottom=up.Open, color='green')
    ax.bar(up.index, up.High - up.Close, width2, bottom=up.Close, color='green')
    ax.bar(up.index, up.Low - up.Open, width2, bottom=up.Open, color='green')
    
    # DOWN Bars
    ax.bar(down.index, down.Close - down.Open, width, bottom=down.Open, color='red')
    ax.bar(down.index, down.High - down.Open, width2, bottom=down.Open, color='red')
    ax.bar(down.index, down.Low - down.Close, width2, bottom=down.Close, color='red')
    
    plt.grid(True, alpha=0.2)
    plt.savefig(output_path)
    plt.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-days", type=int, default=730)
    parser.add_argument("--run-visualizer", action="store_true")
    args = parser.parse_args()

    base_dir = os.environ.get("OMEGA_PARRF_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Origin path of STRESS files
    src_folder = os.path.join(base_dir, "omega_core_validation", "evidencia_pre_demo", "02_logs_execucao")
    if not os.path.isdir(src_folder):
        print(f"Warning: Origin folder not found at {src_folder}. Trying alternative.")
        src_folder = os.path.join(base_dir, "Núcleo de Validação OMEGA", "evidencia_pre_demo", "02_logs_execucao")

    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    out_dir = os.path.join(base_dir, "00_PROVAS_AUDITORIA", "motor_historico_2y")
    os.makedirs(out_dir, exist_ok=True)

    profiles = ["SCALPING", "DAY_TRADE", "SWING_TRADE"]
    
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "min_days_required": args.min_days,
        "profiles": {},
        "global_pass": True
    }
    
    for p in profiles:
        filename = f"STRESS_2Y_{p}.csv"
        src_file = os.path.join(src_folder, filename)
        dst_file = os.path.join(logs_dir, filename)
        
        if os.path.isfile(src_file):
            shutil.copy2(src_file, dst_file)
        elif not os.path.isfile(dst_file):
            print(f"File {filename} not found in src nor logs.")
            report["profiles"][p] = {"error": "FILE_NOT_FOUND"}
            report["global_pass"] = False
            continue
            
        try:
            df = pd.read_csv(dst_file)
            span_days = 0
            if 'ts' in df.columns:
                df['ts'] = pd.to_datetime(df['ts'])
                span_days = (df['ts'].max() - df['ts'].min()).days
                
            gate_ok = span_days >= args.min_days
            if not gate_ok:
                report["global_pass"] = False
                
            # Generate charts
            line_png = os.path.join(out_dir, f"LINE_{p}.png")
            generate_line_chart(df, line_png, p)
            
            candle_png = os.path.join(out_dir, f"CANDLES_SYNTH_{p}.png")
            generate_candles_chart(df, candle_png, p)
            
            report["profiles"][p] = {
                "rows": len(df),
                "span_days": span_days,
                "span_gate_ok": gate_ok,
                "charts_generated": [line_png, candle_png]
            }
        except Exception as e:
            report["profiles"][p] = {"error": str(e)}
            report["global_pass"] = False

    utc_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_file = os.path.join(out_dir, f"motor_historico_report_{utc_str}.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    if args.run_visualizer:
        print("[+] Calling visualizer_tier0.py")
        subprocess.run(["python", os.path.join(base_dir, "visualizer_tier0.py")])

    print(f"Motor Histórico Completo. Gate PASS? {report['global_pass']}. Ver {report_file}")
    if not report["global_pass"]:
        exit(1)

if __name__ == "__main__":
    main()
