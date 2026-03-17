
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o kernel ao path
sys.path.append(str(Path.cwd()))
from modules.omega_parr_f_engine import OmegaParrFEngine

def run_predator_long_history():
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
    
    # --- MODALIDADE PREDADOR INSTITUCIONAL ---
    initial_balance = 10000.0
    balance = initial_balance
    position_size = 0 
    entry_price = 0
    trades_count = 0
    
    # 5.0 Lotes Standard ($500 por $1 de movimento no Ouro)
    base_lots = 5.0 
    cost_per_trade = 20.0 # $20 de spread/slippage estimado para 5 lotes
    
    history = []
    points_captured = 0
    
    v_h1 = df_h1[['open','high','low','close','tick_volume']].values
    t_h1 = df_h1['time'].values
    
    print(f"🚀 INICIANDO AUDITORIA PREDADOR (H4 -> H1) | Janela: 2024 - 2026...")
    
    for i in range(50, len(df_h1)):
        current_time = pd.Timestamp(t_h1[i])
        price = v_h1[i, 3]
        
        # 1. CONFLUÊNCIA MACRO (H4)
        h4_c = df_h4[df_h4['time'] < current_time].tail(5)
        if len(h4_c) < 5: continue
        
        h4_dir = 1 if h4_c.iloc[-1]['close'] > h4_c['close'].mean() else -1
        
        # 2. TRIGGER GATILHO (H1)
        if position_size == 0:
            slice_h1 = v_h1[i-15:i+1]
            audit = engine.execute_audit(slice_h1)
            
            # Se Média Curta do H1 confirma a força do H4
            if audit['launch'] and audit['ha_bias'] == h4_dir:
                position_size = h4_dir * base_lots
                entry_price = price
                balance -= cost_per_trade 
                trades_count += 1
        
        # 3. GESTÃO DE ONDA PREDADORA
        else:
            pnl_points = (price - entry_price) * (1 if position_size > 0 else -1)
            pnl_usd = pnl_points * base_lots * 100 
            
            # Saída por reversão de Inércia no H1 (Hold the Wave)
            ha_c = (v_h1[i,0] + v_h1[i,1] + v_h1[i,2] + v_h1[i,3]) / 4.0
            ha_o = (v_h1[i-1,0] + v_h1[i-1,3]) / 2.0
            current_ha_bias = 1 if ha_c > ha_o else -1
            
            # Saída se Inércia H1 inverte OU perda de 500 pontos ($25k drawdown na posição)
            if current_ha_bias != (1 if position_size > 0 else -1) or pnl_points < -5.0:
                balance += pnl_usd
                points_captured += pnl_points
                position_size = 0
                
        history.append(balance + ((price - entry_price) * position_size * 100 if position_size != 0 else 0))

    final_val = history[-1]
    ret = ((final_val - initial_balance) / initial_balance) * 100
    max_drawdown = (max(history) - min(history)) / max(history) * 100 if history else 0
    
    print("\n" + "🏁" * 25)
    print(f"💎 RELATÓRIO DE DOMINAÇÃO OMEGA PREDATOR (2 ANOS)")
    print("🏁" * 25)
    print(f"💰 Saldo Inicial:       $ {initial_balance:,.2f}")
    print(f"💰 Saldo Final:         $ {final_val:,.2f}")
    print(f"🚀 Retorno Acumulado:   {ret:,.2f}%")
    print(f"📈 Lucro em Dólares:    $ {final_val - initial_balance:,.2f}")
    print(f"📉 Max Drawdown:         {max_drawdown:.2f}%")
    print(f"🎯 Total de Operações: {trades_count}")
    print(f"📏 Pontos Capturados:   {points_captured:,.2f} pontos")
    print(f"📅 Período Auditado:    Jul/2024 a Mar/2026")
    print("🏁" * 25)

if __name__ == "__main__":
    run_predator_long_history()
