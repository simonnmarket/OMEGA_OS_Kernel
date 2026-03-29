import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import pytz
import os

artifact_dir = r"C:\Users\Lenovo\.gemini\antigravity\brain\f38157c7-ad92-48af-90ff-aabee8b9f71f"
os.makedirs(artifact_dir, exist_ok=True)

if not mt5.initialize():
    print("MT5 Init Failed")
    exit()

tz = pytz.timezone("Etc/UTC")
start_time = datetime(2026, 3, 23, 0, 0, tzinfo=tz)
end_time = datetime.now(timezone.utc)

timeframes = {
    "H4": mt5.TIMEFRAME_H4,
    "H1": mt5.TIMEFRAME_H1,
    "M15": mt5.TIMEFRAME_M15,
    "M5": mt5.TIMEFRAME_M5
}

md_output = ""

for tk, tf in timeframes.items():
    rates = mt5.copy_rates_range("XAUUSD", tf, start_time, end_time)
    if rates is None or len(rates) == 0:
        continue
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    start_t = df['time'].iloc[0]
    
    # 1. Tabela Candles
    md_output += f"### 1. TABELA COMPLETA EM CANDLES — XAUUSD ({tk})\n"
    md_output += "| T+ (Mission Time) | Dia/Hora Real | Open (O) | High (H) | Low (L) | Close (C) | Volume (V) | Status/Evento (Data Annotation) |\n"
    md_output += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    candle_rows = []
    line_rows = []
    
    for _, row in df.iterrows():
        t_plus = str(row['time'] - start_t)
        if "0 days " in t_plus:
            t_plus = t_plus.split("0 days ")[-1]
        if t_plus.startswith("00:00:00"):
            t_plus = "00:00:00"
            
        t_str = row['time'].strftime('%d/%m %H:%M')
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        v = int(row['tick_volume'])
        
        evento = "-"
        if row['time'].hour in [8,9]: evento = "Perda de Pressão Contínua"
        elif row['time'].hour == 10: evento = "Queda de Pressão (MAX Q) / Fundo Atingido"
        elif row['time'].hour == 11 and row['time'].minute == 0: evento = "MECO / Absorção (Defesa 4203.55)"
        elif row['time'].hour == 11: evento = "Ignição Altista Secundária"
        elif row['time'].hour >= 12 and row['time'].hour <= 15: evento = "Manobra RCS (Correção de Rota Nominal)"
        
        c_row = f"| T+{t_plus} | {t_str} | {o:.2f} | {h:.2f} | {l:.2f} | {c:.2f} | {v} | {evento} |\n"
        l_row = f"| T+{t_plus} | {t_str} | {c:.2f} | {evento} |\n"
        
        candle_rows.append(c_row)
        line_rows.append(l_row)
        
    md_output += "".join(candle_rows) + "\n"
    
    # 2. Tabela Linha
    md_output += f"### 2. TABELA COMPLETA COM DADOS GRÁFICO DE LINHA — XAUUSD ({tk})\n"
    md_output += "| T+ (Mission Time) | Dia/Hora Real | Variável Física (Pressão/Close) | Status/Evento (Data Annotation) |\n"
    md_output += "| :--- | :--- | :--- | :--- |\n"
    md_output += "".join(line_rows) + "\n\n"

with open(os.path.join(artifact_dir, "full_aerospace_report.md"), "w", encoding='utf-8') as f:
    f.write(md_output)

mt5.shutdown()
