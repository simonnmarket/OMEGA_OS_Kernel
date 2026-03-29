import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import os
import hashlib
import json
import time

print("[*] INICIANDO OMEGA V8.2 FASE 1: EXTRAÇÃO DE DADOS MT5 (M1)")

if not mt5.initialize():
    print(f"❌ Falha ao inicializar MT5. Erro: {mt5.last_error()}")
    quit()

symbols = ["XAUUSD", "XAGUSD"]  # Focando Ouro e Prata
timeframe = mt5.TIMEFRAME_M1

data_manifest = {
    "protocol": "OMEGA-V8.2-FASE1-EXTRACTION",
    "timestamp": datetime.now().isoformat(),
    "assets": {}
}

os.makedirs("data_lake", exist_ok=True)

# Vamos extrair os últimos 2.000.000 de barras (que dão cerca de 5 anos de M1 se existirem no terminal)
# O MT5 irá retornar todas as barras disponíveis até esse limite estipulado, sem erro de timezone.
bars_to_fetch = 2000000

for symbol in symbols:
    print(f"\n[+] Verificando {symbol} no terminal...")
    
    if not mt5.symbol_select(symbol, True):
        print(f"⚠️ {symbol} não encontrado no terminal MT5.")
        data_manifest["assets"][symbol] = {"status": "FAILED_UNAVAILABLE"}
        continue
    
    print(f"[*] Solicitando histórico M1 para {symbol}...")
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars_to_fetch)
    
    if rates is None or len(rates) == 0:
        print(f"❌ Nenhuma barra M1 encontrada para {symbol}. Erro: {mt5.last_error()}")
        data_manifest["assets"][symbol] = {"status": "FAILED_NO_DATA"}
        continue
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    print(f"[+] {symbol}: {len(df)} barras extraídas (Desde {df['time'].iloc[0]} até {df['time'].iloc[-1]}).")
    print(f"[*] Salvando Parquet...")
    
    filename = f"data_lake/{symbol}_M1_HISTORICO.parquet"
    df.to_parquet(filename, engine="pyarrow", compression="snappy")
    
    # Gerando SHA-256 para o Gate G-A
    hasher = hashlib.sha256()
    with open(filename, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    file_hash = hasher.hexdigest()
    
    data_manifest["assets"][symbol] = {
        "status": "SUCCESS",
        "bars_count": len(df),
        "start_date": str(df['time'].iloc[0]),
        "end_date": str(df['time'].iloc[-1]),
        "sha256": file_hash,
        "filename": filename
    }
    print(f"✅ {symbol} Parquet SHA-256: {file_hash[:16]}...")

mt5.shutdown()

print("\n[*] GERANDO DATA MANIFEST SHA-256 (GATE G-A)")
with open("data_lake/data_manifest_v82.json", "w") as f:
    json.dump(data_manifest, f, indent=4)

print("[+] FASE 1 EXTRAÇÃO CONCLUÍDA COM SUCESSO. VERIFIQUE A PASTA 'data_lake'.")
