import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

if not mt5.initialize():
    print("Falha ao inicializar MT5")
    exit()

symbol = 'XAUUSD'
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 30)

if rates is not None:
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    print(f"| Data / Hora (UTC) | Open (O) | High (H) | Low (L) | Close (C) | Volume (V) |")
    print(f"| :--- | :--- | :--- | :--- | :--- | :--- |")
    
    for index, row in df.iterrows():
        t = row['time'].strftime('%d/%m/%Y %H:%M')
        o = f"{row['open']:.2f}"
        h = f"{row['high']:.2f}"
        l = f"{row['low']:.2f}"
        c = f"{row['close']:.2f}"
        v = int(row['tick_volume'])
        print(f"| {t} | {o} | {h} | {l} | {c} | {v} |")
else:
    print(f"Falha ao acessar os dados H1 do {symbol}")

mt5.shutdown()
