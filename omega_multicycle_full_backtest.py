
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o kernel ao path
sys.path.append(str(Path.cwd()))
from modules.omega_parr_f_engine import OmegaParrFEngine

def run_full_backtest():
    # PATHS
    h1_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_H1.csv'
    m15_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_M15.csv'
    
    # LOAD
    df_h1 = pd.read_csv(h1_path)
    df_m15 = pd.read_csv(m15_path)
    df_h1['time'] = pd.to_datetime(df_h1['time'])
    df_m15['time'] = pd.to_datetime(df_m15['time'])
    
    engine = OmegaParrFEngine()
    
    # SIMULATION VARS
    balance = 10000.0
    equity = 10000.0
    position = 0 # 1 or -1
    entry_price = 0
    trades_count = 0
    cost_per_trade = 1.5 # Points (XAUUSD Spread + Slippage)
    
    history = []
    
    # SYNC DATA
    df_m15 = df_m15.sort_values('time')
    v_m15 = df_m15[['open','high','low','close','tick_volume']].values
    t_m15 = df_m15['time'].values
    
    print(f"🚀 INICIANDO BACKTEST MULTI-CICLO (H1 -> M15)...")
    
    for i in range(50, len(df_m15)):
        current_time = pd.Timestamp(t_m15[i])
        price = v_m15[i, 3] # Close
        
        # 1. PEGAR CONTEXTO H1 (DIFERENCIAL DE PRECO)
        h1_slice = df_h1[df_h1['time'] < current_time].tail(2)
        if len(h1_slice) < 2: continue
        h1_trend = 1 if h1_slice.iloc[-1]['close'] > h1_slice.iloc[-2]['close'] else -1
        
        # 2. SE SEM POSICAO, BUSCA GATILHO M15
        if position == 0:
            slice_m15 = v_m15[i-15:i+1]
            audit = engine.execute_audit(slice_m15)
            
            # CONFLUENCIA: Gatilho M15 + Direcao H1
            if audit['launch'] and audit['ha_bias'] == h1_trend:
                position = audit['ha_bias']
                entry_price = price + (position * cost_per_trade)
                trades_count += 1
        
        # 3. GESTAO DE POSICAO (SAIDA SIMPLIFICADA POR RISCO/RETORNO OU REVERSAO)
        else:
            # PnL Flutuante
            pnl = (price - entry_price) * position
            
            # Condição de Saída: Mudança de Inércia no M15 ou PnL Alvo
            slice_m15_step = v_m15[i-5:i+1]
            # Se ha_bias reverte contra posição, sai
            ha_c = (v_m15[i,0] + v_m15[i,1] + v_m15[i,2] + v_m15[i,3]) / 4.0
            ha_o = (v_m15[i-1,0] + v_m15[i-1,3]) / 2.0
            current_ha_bias = 1 if ha_c > ha_o else -1
            
            if current_ha_bias != position or pnl < -15.0: # Stop curto de 15 pontos (~ATR M15)
                balance += pnl
                position = 0
                
        history.append(balance)

    # CALCULATE FINAL KPIs
    ret_pct = ((balance - 10000.0) / 10000.0) * 100
    
    print("\n" + "="*50)
    print(f"📊 RESULTADOS OMEGA SNIPER (M15 EX_CONFLUENCE)")
    print("="*50)
    print(f"💰 Saldo Inicial:      $ 10,000.00")
    print(f"💰 Saldo Final:        $ {balance:,.2f}")
    print(f"🚀 Lucro Líquido:       {ret_pct:.2f}%")
    print(f"🎯 Total de Operações: {trades_count}")
    print(f"💸 Custos Operacionais: $ {trades_count * cost_per_trade:,.2f} (est.)")
    print(f"📅 Período:            {df_m15.time.min()} ate {df_m15.time.max()}")
    print("="*50)

if __name__ == "__main__":
    run_full_backtest()
