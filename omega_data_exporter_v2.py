import MetaTrader5 as mt5
import pandas as pd
import os
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
MAX_BARS = 100000

def extract_data_robust():
    if not mt5.initialize():
        print("[-] Erro ao inicializar MT5")
        return

    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    print(f"[*] Extração Robusta Iniciada em {datetime.now()}")

    for group, symbols in SYMBOLS.items():
        for symbol in symbols:
            # Garantir visibilidade e inscrição
            if not mt5.symbol_select(symbol, True):
                print(f"[!] Símbolo {symbol} não disponível ou falha ao selecionar.")
                continue
            
            for tf_label, tf_mt5 in TIMEFRAMES.items():
                # Tenta puxar a partir da posição 0 (mais recente disponível)
                # Como hoje é sábado (14/03), a posição 0 será o fechamento de sexta ou o preço atual (Crypto)
                rates = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, MAX_BARS)
                
                if rates is None or len(rates) == 0:
                    # Tenta forçar sincronização
                    mt5.symbol_select(symbol, True)
                    rates = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, MAX_BARS)
                    if rates is None or len(rates) == 0:
                        print(f"[-] {symbol} {tf_label}: Falha")
                        continue
                
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume', 'real_volume']]
                
                filename = f"{symbol}_{tf_label}.csv"
                file_path = os.path.join(TARGET_DIR, filename)
                df.to_csv(file_path, index=False)
                print(f"[+] {symbol} {tf_label}: {len(df)} bars")

    mt5.shutdown()

if __name__ == "__main__":
    extract_data_robust()
