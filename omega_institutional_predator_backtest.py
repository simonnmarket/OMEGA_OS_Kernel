
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Adiciona o kernel ao path
sys.path.append(str(Path.cwd()))
from modules.omega_parr_f_engine import OmegaParrFEngine

def run_institutional_predator_backtest():
    # PATHS
    h4_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_H4.csv'
    h1_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_H1.csv'
    m15_path = 'C:/OMEGA_PROJETO/OHLCV_DATA/XAUUSD_M15.csv'
    
    # LOAD
    df_h4 = pd.read_csv(h4_path)
    df_h1 = pd.read_csv(h1_path)
    df_m15 = pd.read_csv(m15_path)
    
    for df in [df_h4, df_h1, df_m15]:
        df['time'] = pd.to_datetime(df['time'])
        df.sort_values('time', inplace=True)
    
    engine = OmegaParrFEngine()
    
    # --- VARIAVEIS DE HEDGE FUND ---
    initial_balance = 10000.0
    balance = initial_balance
    equity = initial_balance
    position_size = 0 # Em Unidades (Lotes)
    entry_price = 0
    trades_count = 0
    
    # Configuração de Risco Institucional
    # 1 Lote de Ouro (100 oz) -> $1 move = $100 profit
    # Se o user fez $37k em 14k pontos ($140 move), ele usou ~2.6 lotes.
    base_lots = 5.0 # Agressividade Institucional (5 Lotes Standard)
    cost_per_lot = 15.0 # $15 de custo total por trade (Spread + Slippage p/ 5 lotes)
    
    history = []
    
    v_m15 = df_m15[['open','high','low','close','tick_volume']].values
    t_m15 = df_m15['time'].values
    
    print(f"🚀 INICIANDO PREDADOR INSTITUCIONAL OMEGA V5.19.0...")
    
    for i in range(50, len(df_m15)):
        current_time = pd.Timestamp(t_m15[i])
        price = v_m15[i, 3]
        
        # 1. H4 + H1 CONFLUENCE
        h4_c = df_h4[df_h4['time'] < current_time].tail(2)
        h1_c = df_h1[df_h1['time'] < current_time].tail(2)
        if len(h4_c) < 2 or len(h1_c) < 2: continue
        
        # Confluência Macro (H4 e H1 na mesma direção)
        h4_dir = 1 if h4_c.iloc[-1]['close'] > h4_c.iloc[-2]['close'] else -1
        h1_dir = 1 if h1_c.iloc[-1]['close'] > h1_c.iloc[-2]['close'] else -1
        
        confluence = (h4_dir == h1_dir)
        
        # 2. TRIGGER M15 (GATILHO AGRESSIVO)
        if position_size == 0:
            if confluence:
                slice_m15 = v_m15[i-15:i+1]
                audit = engine.execute_audit(slice_m15)
                
                if audit['launch'] and audit['ha_bias'] == h4_dir:
                    # ENTRADA DE PESO (5 LOTES)
                    position_size = h4_dir * base_lots
                    entry_price = price
                    balance -= cost_per_lot # Pagamento imediato do spread comercial
                    trades_count += 1
        
        # 3. GESTÃO DE ONDA (TRAILLING E REALIZAÇÃO)
        else:
            pnl = (price - entry_price) * position_size * 100 # Multiplicador de Ouro (100oz)
            
            # Realização de lucro agressiva ($10k de lucro limpo ou reversão macro)
            # Ou se o H1 reverter contra o H4 (perda de intensidade)
            if h1_dir != (1 if position_size > 0 else -1) or pnl < -2000.0:
                balance += pnl
                position_size = 0
                
        history.append(balance + ((price - entry_price) * position_size * 100 if position_size != 0 else 0))

    final_val = history[-1]
    ret = ((final_val - initial_balance) / initial_balance) * 100
    
    print("\n" + "!"*50)
    print(f"🔥 RESULTADO PREDADOR INSTITUCIONAL V5.19.0")
    print("!"*50)
    print(f"💰 Saldo Inicial:      $ {initial_balance:,.2f}")
    print(f"💰 Saldo Final:        $ {final_val:,.2f}")
    print(f"🚀 Lucro Líquido:       {ret:.2f}%")
    print(f"📈 Lucro em Dólares:   $ {final_val - initial_balance:,.2f}")
    print(f"🎯 Total de Operações: {trades_count}")
    print(f"📅 Janela de Dados:    5 Meses (Out/25 a Mar/26)")
    print("!"*50)

if __name__ == "__main__":
    run_institutional_predator_backtest()
