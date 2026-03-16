
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o kernel ao path
sys.path.append(str(Path.cwd()))
from modules.omega_parr_f_engine import OmegaParrFEngine

def run_triple_confluence_backtest():
    # PATHS
    h4_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_H4.csv'
    h1_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_H1.csv'
    m15_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_M15.csv'
    
    # LOAD & SYNC
    df_h4 = pd.read_csv(h4_path)
    df_h1 = pd.read_csv(h1_path)
    df_m15 = pd.read_csv(m15_path)
    
    for df in [df_h4, df_h1, df_m15]:
        df['time'] = pd.to_datetime(df['time'])
        df.sort_values('time', inplace=True)
    
    engine = OmegaParrFEngine()
    
    # SIMULATION VARS
    balance = 10000.0
    equity = 10000.0
    position = 0 # 1 (Long), -1 (Short)
    entry_price = 0
    trades_count = 0
    cost_per_trade = 1.5 # Points (Spread + Slippage)
    
    history = []
    
    # Convert to values for performance
    v_m15 = df_m15[['open','high','low','close','tick_volume']].values
    t_m15 = df_m15['time'].values
    
    print(f"🚀 INICIANDO BACKTEST TRIPLA CONFLUÊNCIA (H4 -> H1 -> M15)...")
    
    for i in range(50, len(df_m15)):
        current_time = pd.Timestamp(t_m15[i])
        price = v_m15[i, 3] # Close
        
        # 1. H4 LAYER (DIREÇÃO MACRO)
        h4_context = df_h4[df_h4['time'] < current_time].tail(5)
        if len(h4_context) < 5: continue
        # Direção baseada no fechamento atual vs média de 5 fechamentos H4
        h4_dir = 1 if h4_context.iloc[-1]['close'] > h4_context['close'].mean() else -1
        
        # 2. H1 LAYER (INTENSIDADE)
        h1_context = df_h1[df_h1['time'] < current_time].tail(3)
        if len(h1_context) < 3: continue
        # Intensidade: Se o último H1 está a favor do H4
        h1_intense = (h1_context.iloc[-1]['close'] > h1_context.iloc[-2]['close']) if h4_dir == 1 else (h1_context.iloc[-1]['close'] < h1_context.iloc[-2]['close'])
        
        # 3. M15 LAYER (SNIPER TRIGGER)
        if position == 0:
            if h1_intense: # Só busca gatilho se H4 e H1 confluem
                slice_m15 = v_m15[i-15:i+1]
                audit = engine.execute_audit(slice_m15)
                
                # Gatilho M15 a favor da confluência
                if audit['launch'] and audit['ha_bias'] == h4_dir:
                    position = h4_dir
                    entry_price = price + (position * cost_per_trade)
                    trades_count += 1
        
        # GESTÃO DE SAÍDA (Acompanhamento da Inércia M15)
        else:
            pnl = (price - entry_price) * position
            
            # Saída por reversão de Heikin-Ashi no M15 (Proteção de Lucro)
            ha_c = (v_m15[i,0] + v_m15[i,1] + v_m15[i,2] + v_m15[i,3]) / 4.0
            ha_o = (v_m15[i-1,0] + v_m15[i-1,3]) / 2.0
            current_ha_bias = 1 if ha_c > ha_o else -1
            
            # Se o M15 virar contra ou Stop Loss institucional de 30 pontos bater
            if current_ha_bias != position or pnl < -30.0:
                balance += pnl
                position = 0
                
        history.append(balance)

    # FINAL REPORT
    ret_pct = ((balance - 10000.0) / 10000.0) * 100
    mdd = (10000.0 - min(history)) / 10000.0 * 100 if history else 0
    
    print("\n" + "="*50)
    print(f"📊 RESULTADOS OMEGA TRIPLE CONFLUENCE")
    print("="*50)
    print(f"💰 Saldo Inicial:      $ 10,000.00")
    print(f"💰 Saldo Final:        $ {balance:,.2f}")
    print(f"🚀 Lucro Líquido:       {ret_pct:.2f}%")
    print(f"📉 Max Drawdown:        {max(0, mdd):.2f}%")
    print(f"🎯 Total de Operações: {trades_count}")
    print(f"💸 Custos Operacionais: $ {trades_count * cost_per_trade:,.2f}")
    print(f"📅 Período:            {df_m15.time.min()} ate {df_m15.time.max()}")
    print("="*50)

if __name__ == "__main__":
    run_triple_confluence_backtest()
