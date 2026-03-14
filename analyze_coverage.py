import pandas as pd
import os
from datetime import datetime

def analyze_all_files():
    path = r"C:\OMEGA_PROJETO\OHLCV_DATA"
    files = [f for f in os.listdir(path) if f.endswith(".csv")]
    
    report = []
    
    for f in files:
        if "_" not in f: continue
        parts = f.replace(".csv", "").split("_")
        symbol = parts[0]
        tf = parts[1]
        
        try:
            df = pd.read_csv(os.path.join(path, f), usecols=['time'])
            start = pd.to_datetime(df['time'].iloc[0])
            end = pd.to_datetime(df['time'].iloc[-1])
            duration = end - start
            
            report.append({
                "Symbol": symbol,
                "TF": tf,
                "Start": start.strftime('%Y-%m-%d'),
                "End": end.strftime('%Y-%m-%d'),
                "Days": duration.days,
                "Bars": len(df)
            })
        except:
            continue
            
    df_report = pd.DataFrame(report)
    
    # Resumo por Timeframe (Média de cobertura)
    summary = df_report.groupby('TF')['Days'].mean().reset_index()
    print("\n=== COBERTURA MÉDIA POR TIMEFRAME (TODOS OS ATIVOS) ===")
    for _, row in summary.iterrows():
        days = row['Days']
        if days > 365:
            print(f"{row['TF']}: aprox. {days/365:.1f} anos")
        elif days > 7:
            print(f"{row['TF']}: aprox. {days/7:.1f} semanas ({int(days)} dias)")
        else:
            print(f"{row['TF']}: {int(days)} dias")

    print("\n=== DETALHE DOS GRUPOS (DIÁRIO D1) ===")
    d1_data = df_report[df_report['TF'] == 'D1']
    for _, row in d1_data.iterrows():
        print(f"{row['Symbol']}: {row['Days']/365:.1f} anos (Início: {row['Start']})")

if __name__ == "__main__":
    analyze_all_files()
