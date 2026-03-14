import MetaTrader5 as mt5
import pandas as pd
import os
import time
from datetime import datetime

SYMBOLS = {
    "A": ["XAUUSD", "XAGUSD", "XAGEUR", "AUDUSD"],
    "B": ["EURJPY", "GBPUSD", "USDJPY", "AUDJPY"],
    "C": ["GER40", "US100", "US30", "US500", "USOIL+", "HK50"],
    "D": ["BTCUSD", "ETHUSD", "DOGUSD", "SOLUSD"]
}

TIMEFRAMES = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1
}

TARGET_DIR = r"C:\OMEGA_PROJETO\OHLCV_DATA"
MAX_BARS = 10000 # Reduzindo para 10k para ser mais rápido e evitar timeouts de sync

def fetch_with_retry(symbol, tf, bars, retries=5):
    for i in range(retries):
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
        if rates is not None and len(rates) > 0:
            return rates
        # Se falhou, tenta selecionar novamente e esperar
        mt5.symbol_select(symbol, True)
        time.sleep(2) # Espera o terminal baixar o histórico
    return None

def extract_data_v3():
    if not mt5.initialize():
        print("[-] Erro ao inicializar MT5")
        return

    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    print(f"[*] Extração V3 Iniciada em {datetime.now()}")

    for group, symbols in SYMBOLS.items():
        for symbol in symbols:
            print(f"\n[🚀] Sincronizando {symbol}...")
            if not mt5.symbol_select(symbol, True):
                print(f"[!] {symbol} INDISPONÍVEL.")
                continue
            
            for tf_label, tf_mt5 in TIMEFRAMES.items():
                rates = fetch_with_retry(symbol, tf_mt5, MAX_BARS)
                
                if rates is not None:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume', 'real_volume']]
                    
                    filename = f"{symbol}_{tf_label}.csv"
                    file_path = os.path.join(TARGET_DIR, filename)
                    df.to_csv(file_path, index=False)
                    print(f"   ✅ {tf_label}: {len(df)} candles")
                else:
                    print(f"   ❌ {tf_label}: FALHA")

    mt5.shutdown()

if __name__ == "__main__":
    extract_data_v3()
