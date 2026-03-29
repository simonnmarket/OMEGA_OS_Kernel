import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time
import os

print("\n" + "="*70)
print("⚙️ MACE-MAX TIER-0: LIVE TICK & M1 RECORDER DAEMON ativado")
print("📡 Status: CONECTADO À CORRETORA (RODANDO A MADRUGADA INTEIRA)")
print(f"⏰ Horário de Início (Local): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
print("\n[Aguardando fechamento da próxima barra de 1 Minuto...]")

if not mt5.initialize():
    print(f"❌ Erro fatal: Terminal MT5 não encontrado ou não acessível (Erro: {mt5.last_error()})")
    quit()

symbols = ["XAUUSD", "XAGUSD"]
os.makedirs("data_lake/live_feed", exist_ok=True)

# Habilitar ativos no Market Watch
for sym in symbols:
    if not mt5.symbol_select(sym, True):
        print(f"⚠️ Atenção: Não foi possível habilitar {sym}")

# Dicionário para armazenar o momento (timestamp) da última barra coletada
last_bar_time = {sym: 0 for sym in symbols}

def fetch_latest_bars():
    for sym in symbols:
        # Pega as últimas 2 barras fechadas (A barra 0 no index é a atual em aberto, 1 é a anterior)
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, 2)
        if rates is None or len(rates) < 2:
            continue
            
        # Analisa a barra recém-fechada (posição 0 na nossa query que vem de traz pra frente, 
        # mas copy_rates_from_pos retorna [mais antigo, mais novo]. 
        # O último (index 1) é o corrente, o penúltimo (index 0) é o anterior.
        closed_bar = rates[0]
        
        if closed_bar['time'] > last_bar_time[sym]:
            # Temos uma nova barra de M1 oficialmente Fechada!
            last_bar_time[sym] = closed_bar['time']
            dt_str = pd.to_datetime(closed_bar['time'], unit='s').strftime('%Y-%m-%d %H:%M')
            
            close_price = closed_bar['close']
            vol = closed_bar['real_volume'] if closed_bar['real_volume'] > 0 else closed_bar['tick_volume']
            
            print(f"[{dt_str}] 🔴 {sym} | C: {close_price:.3f} | V: {vol} | Nova Barra Minerada e Armazenada.")
            
            # Grava no disco
            df = pd.DataFrame([closed_bar])
            df.to_csv(f"data_lake/live_feed/{sym}_MADRUGADA_M1.csv", mode='a', header=not os.path.exists(f"data_lake/live_feed/{sym}_MADRUGADA_M1.csv"), index=False)

try:
    while True:
        fetch_latest_bars()
        # Ping a cada 5 segundos para reagir instantaneamente ao fechamento do M1
        time.sleep(5)
except KeyboardInterrupt:
    print("\n[!] Daemon encerrado manualmente. Arquivos salvos em 'data_lake/live_feed/'")
    mt5.shutdown()
