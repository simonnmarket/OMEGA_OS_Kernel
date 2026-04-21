
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o kernel ao path
sys.path.append(str(Path.cwd()))
from modules.omega_parr_f_engine import OmegaParrFEngine

def run_whale_hunter_audit():
    # PATHS
    h4_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_H4.csv'
    h1_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_H1.csv'
    
    # LOAD
    df_h4 = pd.read_csv(h4_path)
    df_h1 = pd.read_csv(h1_path)
    
    for df in [df_h4, df_h1]:
        df['time'] = pd.to_datetime(df['time'])
        df.sort_values('time', inplace=True)
    
    engine = OmegaParrFEngine()
    
    # --- PROTOCOLO WHALE HUNTER (50K POINTS FOCUS) ---
    initial_balance = 10000.0
    balance = initial_balance
    position_size = 0 
    entry_price = 0
    trades_count = 0
    
    # 10.0 Lotes Standard (Potência Máxima - 1000oz)
    # $1 move = $1,000 profit
    base_lots = 10.0 
    cost_per_trade = 50.0 # Spread/Slippage p/ 10 lotes
    
    history = []
    points_captured = 0
    
    v_h1 = df_h1[['open','high','low','close','tick_volume']].values
    t_h1 = df_h1['time'].values
    
    print(f"🚀 INICIANDO AUDITORIA WHALE HUNTER (MOVIMENTOS DE 50K PONTOS)...")
    
    for i in range(50, len(df_h1)):
        current_time = pd.Timestamp(t_h1[i])
        price = v_h1[i, 3]
        
        # 1. DIREÇÃO MACRO (H4)
        h4_c = df_h4[df_h4['time'] < current_time].tail(10)
        if len(h4_c) < 10: continue
        
        # Tendência H4 (Diferencial de Médias Longas)
        h4_sma = h4_context_mean = h4_c['close'].mean()
        h4_dir = 1 if h4_c.iloc[-1]['close'] > h4_sma else -1
        
        # 2. GATILHO DE ENTRADA (H1)
        if position_size == 0:
            slice_h1 = v_h1[i-15:i+1]
            audit = engine.execute_audit(slice_h1)
            
            # Confluência de Força (Thrust > 0.5 em H1 a favor do H4)
            if audit['launch'] and audit['ha_bias'] == h4_dir:
                position_size = h4_dir * base_lots
                entry_price = price
                balance -= cost_per_trade 
                trades_count += 1
                print(f"[*] ENTRY: {current_time} | Price: {price} | Bias: {h4_dir}")
        
        # 3. GESTÃO DE ONDA (WHALE HOLD)
        else:
            pnl_points = (price - entry_price) * (1 if position_size > 0 else -1)
            
            # SAÍDA APENAS SE O H4 REVERTER A TENDÊNCIA MACRO
            # Isso garante surfar os 50 mil pontos sem ser expulso pelo ruído H1
            if (h4_dir != (1 if position_size > 0 else -1)):
                pnl_usd = pnl_points * base_lots * 100 
                balance += pnl_usd
                points_captured += pnl_points
                print(f"[!] EXIT: {current_time} | Price: {price} | Points: {pnl_points:.2f} | PnL: ${pnl_usd:,.2f}")
                position_size = 0
                
        history.append(balance + ((price - entry_price) * position_size * 1000 if position_size != 0 else 0))

    final_val = history[-1]
    ret = ((final_val - initial_balance) / initial_balance) * 100
    
    print("\n" + "🐳" * 25)
    print(f"🔥 RELATÓRIO WHALE HUNTER (MODO PREDADOR TOTAL)")
    print("🐳" * 25)
    print(f"💰 Saldo Inicial:       $ {initial_balance:,.2f}")
    print(f"💰 Saldo Final:         $ {final_val:,.2f}")
    print(f"🚀 Retorno Acumulado:   {ret:,.2f}%")
    print(f"📏 Pontos Capturados:   {points_captured:,.2f} pontos")
    print(f"🎯 Total de Operações: {trades_count}")
    print(f"📅 Janela:              2024 - 2026")
    print("🐳" * 25)

if __name__ == "__main__":
    run_whale_hunter_audit()
