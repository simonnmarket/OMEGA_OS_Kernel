import MetaTrader5 as mt5
import pandas as pd
import os
import time
from datetime import datetime

# Lista exata do Comandante
raw_symbols = [
    "XAUUSD", "USOL+", "USDJPY", "US500", "US100", "US30", 
    "SOLUSD", "HK50", "GER40", "GBPUSD", "ETHUSD", "DOGUSD", 
    "BTCUSD", "AUDUSD", "AUDJPY"
]

timeframes = {
    "W1": (mt5.TIMEFRAME_W1, 2000),
    "D1": (mt5.TIMEFRAME_D1, 5000),
    "H4": (mt5.TIMEFRAME_H4, 15000),
    "H1": (mt5.TIMEFRAME_H1, 50000),
    "M15": (mt5.TIMEFRAME_M15, 150000),
    "M5": (mt5.TIMEFRAME_M5, 300000),
    "M1": (mt5.TIMEFRAME_M1, 500000)
}

save_dir = r"C:\OMEGA_PROJETO\OHLCV_DATA"

def find_actual_symbol(symbol):
    # Tratamento de sufixos de corretora ou nomes difusos
    info = mt5.symbol_info(symbol)
    if info is not None: return symbol
    
    # Tentativas de fallback
    fallbacks = [symbol+".", symbol+"!", symbol+"_m"]
    if symbol == "USOL+": fallbacks.extend(["USOil", "USOUSD", "XTIUSD"])
    if symbol == "DOGUSD": fallbacks.extend(["DOGEUSD"])
    
    for f in fallbacks:
        if mt5.symbol_info(f) is not None: return f
    return None

def download_data():
    print("="*80)
    print(" 📥 OMEGA SYSTEM - DOWNLOADER MASSIVO DE HISTÓRICO INSTITUCIONAL 📥 ")
    print("="*80)
    
    if not mt5.initialize():
        print("❌ FALHA: MetaTrader 5 não está aberto ou conectável.")
        return
        
    os.makedirs(save_dir, exist_ok=True)
    
    for sym in raw_symbols:
        real_sym = find_actual_symbol(sym)
        if not real_sym:
            print(f"⚠️ AVISO: Símbolo '{sym}' não localizado no terminal (verifique o Market Watch).")
            continue
            
        print(f"\n[*] Sincronizando Ativo: {real_sym} ...")
        for tf_name, (mt5_tf, amount) in timeframes.items():
            rates = mt5.copy_rates_from_pos(real_sym, mt5_tf, 0, amount)
            
            # Auto-redução dinâmica se a corretora não tiver 500.000 barras na memória
            if rates is None or len(rates) == 0:
                steps = [100000, 50000, 10000, 5000, 1000]
                for step in steps:
                    rates = mt5.copy_rates_from_pos(real_sym, mt5_tf, 0, step)
                    if rates is not None and len(rates) > 0:
                        break
            
            if rates is None or len(rates) == 0:
                print(f"  -> Falha absoluta no download de {tf_name}. Histórico não disponível no terminal.")
                continue
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Estrutura Círurgica: Duas Pastas Físicas e Separadas
            folder_candle = os.path.join(save_dir, "grafico_candle")
            folder_linha = os.path.join(save_dir, "grafico_linha")
            os.makedirs(folder_candle, exist_ok=True)
            os.makedirs(folder_linha, exist_ok=True)
            
            # Formato 1: Gráfico de Candles (Original Completo OHLCV)
            file_candle = os.path.join(folder_candle, f"{sym.replace('+','')}_{tf_name}.csv")
            df.to_csv(file_candle, index=False, float_format='%.5f')
            
            # Formato 2: Gráfico de Linha (Apenas Tempo e Preço Limpo)
            df_linha = df[['time', 'close']].copy()
            df_linha.rename(columns={'close': 'linha'}, inplace=True)
            file_linha = os.path.join(folder_linha, f"{sym.replace('+','')}_{tf_name}.csv")
            df_linha.to_csv(file_linha, index=False, float_format='%.5f')
            
            print(f"  -> {tf_name} Salvo: {len(df)} barras | Separado em [grafico_candle] e [grafico_linha]")
            
    mt5.shutdown()
    print("\n" + "="*80)
    print("✅ DOWNLOAD COMPLETO. BANCO DE DADOS PREPARADO PARA TESTES EM ESCALA.")
    print("="*80)

if __name__ == "__main__":
    download_data()
