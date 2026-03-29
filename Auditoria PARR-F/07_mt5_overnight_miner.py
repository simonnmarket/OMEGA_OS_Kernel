import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os
import time

print("="*60)
print("⚙️ OMEGA V8.2 - TIER-0 OVERNIGHT MINER (DEEP EXTRACTION)")
print("📅 Data/Hora de Início:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("="*60)

def init_mt5():
    if not mt5.initialize():
        print(f"❌ Falha de Inicialização (Erro: {mt5.last_error()}). Tentando novamente em 30s...")
        time.sleep(30)
        return init_mt5()
    return True

init_mt5()

symbols = ["XAUUSD", "XAGUSD"]
os.makedirs("data_lake/deep_history", exist_ok=True)

# Mineração de trás para frente em blocos de 100.000 barras M1
chunk_size = 100000

for sym in symbols:
    print(f"\n[+] Iniciando mineração histórica profunda para: {sym}")
    mt5.symbol_select(sym, True)
    
    all_rates = []
    # Começamos de "agora" como a posição 0 na cópia por índice.
    # Como vamos acumulando, puxamos do índice atual (total recebido).
    current_pos = 0
    consecutive_empty = 0
    
    while True:
        try:
            # Re-verificar conexão
            if mt5.terminal_info() is None:
                print(f"⚠️ Conexão perdida! Reiniciando terminal...")
                init_mt5()
                
            rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, current_pos, chunk_size)
            
            if rates is None or len(rates) == 0:
                consecutive_empty += 1
                if consecutive_empty > 3:
                    print(f"[*] Limite histórico atingido para {sym} da corretora.")
                    break
                time.sleep(2)
                continue
                
            consecutive_empty = 0
            df_chunk = pd.DataFrame(rates)
            
            # Se a corretora devolver overlap ou já tivermos essas barras
            all_rates.append(df_chunk)
            current_pos += len(rates)
            
            # Formatar log visual de progresso
            oldest_time = pd.to_datetime(df_chunk['time'].iloc[0], unit='s')
            newest_time = pd.to_datetime(df_chunk['time'].iloc[-1], unit='s')
            print(f" -> {sym} Extraído: Lote {len(all_rates)} | Barras: {len(rates)} | De {oldest_time.strftime('%Y-%m-%d')} a {newest_time.strftime('%Y-%m-%d')} | Total Acumulado: {current_pos}")
            
            # Pausa cirúrgica para não sobrecarregar IPC (Inter-Process Communication DLL)
            time.sleep(1.5)
            
        except Exception as e:
            print(f"❌ Exceção no chunk: {e}. Recuperando...")
            time.sleep(10)
            init_mt5()

    # Consolidação do Ativo
    if len(all_rates) > 0:
        print(f"\n[*] Consolidando o Big Data de {sym}...")
        df_full = pd.concat(all_rates, ignore_index=True)
        # Limpar duplicados causados por overlaps
        df_full.drop_duplicates(subset=['time'], inplace=True)
        df_full.sort_values(by='time', inplace=True)
        df_full['time'] = pd.to_datetime(df_full['time'], unit='s')
        
        filename = f"data_lake/deep_history/{sym}_M1_FULL_HISTORY.parquet"
        df_full.to_parquet(filename, engine="pyarrow", compression="snappy")
        print(f"✅ {sym} Salvo com SUCESSO! Total real único: {len(df_full)} barras M1.")
        print(f"    Período: {df_full['time'].iloc[0]} até {df_full['time'].iloc[-1]}")
    else:
        print(f"⚠️ Não foi possível extrair dados profundos para {sym}.")

mt5.shutdown()
print("\n" + "="*60)
print("✅ EXTRAÇÃO OVERNIGHT FINALIZADA COM SUCESSO.")
print("📅 Data/Hora de Término:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("="*60)
