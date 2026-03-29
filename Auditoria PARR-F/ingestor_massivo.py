import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import os
import time

def ingest_2y(symbol):
    print(f"[*] Ingerindo {symbol}...")
    chunks = []
    chunk_size = 50000
    p = 0
    target = 1000000
    
    while True:
        r = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, p, chunk_size)
        if r is None or len(r) == 0:
            break
        chunks.append(pd.DataFrame(r))
        p += chunk_size
        current_total = sum(len(c) for c in chunks)
        print(f"\r  {symbol}: {current_total} barras", end="")
        if current_total >= target: break
        time.sleep(0.1)
    
    if not chunks: return pd.DataFrame()
    df = pd.concat(chunks, ignore_index=True)
    print(f"\n[OK] {symbol} total: {len(df)}")
    return df

if __name__ == "__main__":
    if not mt5.initialize():
        print("Erro MT5")
        exit()
        
    df_y = ingest_2y("XAUUSD")
    df_x = ingest_2y("XAGUSD")
    mt5.shutdown()
    
    os.makedirs("RAW_2Y", exist_ok=True)
    df_y.to_csv("RAW_2Y/XAUUSD_M1_RAW.csv", index=False)
    df_x.to_csv("RAW_2Y/XAGUSD_M1_RAW.csv", index=False)
    print("\n[FINISH] Dados brutos salvos em RAW_2Y/")
