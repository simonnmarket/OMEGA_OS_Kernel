import MetaTrader5 as mt5
import pandas as pd
import os
from datetime import datetime

# =============================================================================
# CONFIGURAÇÃO DE EXTRAÇÃO OMEGA
# =============================================================================

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
MAX_BARS = 100000 # Limite prático por timeframe para evitar travamentos

# =============================================================================

def extract_data():
    if not mt5.initialize():
        print("[-] Erro ao inicializar MT5")
        return

    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)
        print(f"[+] Diretório {TARGET_DIR} criado.")

    end_date = datetime(2026, 3, 14, 0, 0)
    print(f"[*] Iniciando extração histórica até {end_date.strftime('%Y-%m-%d %H:%M:%S')}")

    for group, symbols in SYMBOLS.items():
        for symbol in symbols:
            print(f"\n[🚀] Processando Ativo: {symbol} (Grupo {group})")
            
            # Garantir que o símbolo está visível
            mt5.symbol_select(symbol, True)
            
            for tf_label, tf_mt5 in TIMEFRAMES.items():
                print(f"   > Extraindo {tf_label}...", end=" ", flush=True)
                
                # Puxar dados históricos
                rates = mt5.copy_rates_from(symbol, tf_mt5, end_date, MAX_BARS)
                
                if rates is None or len(rates) == 0:
                    print("❌ Falha (Sem dados)")
                    continue
                
                # Converter para DataFrame
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
                # Renomear colunas para padrão institucional
                # O MT5 retorna: time, open, high, low, close, tick_volume, spread, real_volume
                df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume', 'real_volume']]
                
                # Salvar CSV
                filename = f"{symbol}_{tf_label}.csv"
                file_path = os.path.join(TARGET_DIR, filename)
                df.to_csv(file_path, index=False)
                
                print(f"✅ OK ({len(df)} candles)")

    mt5.shutdown()
    print("\n" + "="*50)
    print("✅ TAREFA DE EXTRAÇÃO CONCLUÍDA")
    print(f"📁 Localização: {TARGET_DIR}")
    print("="*50)

if __name__ == "__main__":
    extract_data()
