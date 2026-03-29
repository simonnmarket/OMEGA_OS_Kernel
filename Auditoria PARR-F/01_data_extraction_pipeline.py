import MetaTrader5 as mt5
import pandas as pd
import pytz
from datetime import datetime
import os
import sys

def main():
    print("[*] Iniciando Pipeline de Ingestão Massiva de Dados (Tier-0)")
    
    # Inicializa MT5
    if not mt5.initialize():
        print(f"[!] Falha na inicialização do MT5: {mt5.last_error()}")
        sys.exit(1)
        
    symbol = "XAUUSD"
    # Adicionando explicitamente ao Market Watch para evitar "Invalid params"
    if not mt5.symbol_select(symbol, True):
        print(f"[!] Falha ao selecionar {symbol} no Market Watch.")
        mt5.shutdown()
        sys.exit(1)
        
    timeframe = mt5.TIMEFRAME_M1
    
    # Extraindo as últimas velas M1 compatíveis com a memória do terminal
    n_bars_to_fetch = 90_000
    print(f"[*] Solicitando {n_bars_to_fetch} velas M1 de {symbol}...")
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars_to_fetch)
    
    if rates is None or len(rates) == 0:
        print("[!] Nenhum dado retornado. O histórico XAUUSD M1 está disponível no terminal MT5?")
        print(f"    Erro API: {mt5.last_error()}")
        mt5.shutdown()
        sys.exit(1)
    # Conversão Numpy -> Pandas DataFrame veloz
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    
    n_candles = len(df)
    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    print(f"[+] Extração em RAM concluída com sucesso.")
    print(f"    - Total de Velas: {n_candles:,}")
    print(f"    - Memória Estimada (RAM): {memory_mb:.2f} MB")
    
    # Criação do diretório e salvamento contíguo em Parquet (Fast I/O)
    out_dir = "data"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "XAUUSD_M1_2020_2026.parquet")
    
    print(f"[*] Gravando dados no disco no formato binário colunar (Engine: PyArrow, Snappy)...")
    
    # Salva com compressão para evitar overhead de I/O em leitura futura
    df.to_parquet(out_file, engine='pyarrow', compression='snappy')
    print(f"[+] Arquivo persistido em disco: {out_file}")
    
    file_size_mb = os.path.getsize(out_file) / (1024 * 1024)
    print(f"    - Tamanho no Disco (Parquet Snappy): {file_size_mb:.2f} MB")
    
    mt5.shutdown()
    print("\n[✓] FASE 1 - THE FOUNDATION: CLARA E EXECUTADA.")
    print("[*] Aguardando comando para inicializar o Gerador de Ruído e Numba Cython.")

if __name__ == "__main__":
    main()
