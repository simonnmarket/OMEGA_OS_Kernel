import pandas as pd
import numpy as np
import time
import os

from modules.volume_profile import VolumeProfileEngine, VolumeConfig
from modules.omega_kernel_v5_1_refined import OMEGAKernelV51Refined, KernelConfig

def load_data():
    file_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M5.csv"
    if not os.path.exists(file_path):
        print(f"Erro: {file_path} não encontrado.")
        return None
    df = pd.read_csv(file_path, sep='\t')
    if len(df.columns) < 5: df = pd.read_csv(file_path)
    
    col_map = {c: c.lower().replace('<', '').replace('>', '') for c in df.columns}
    df.rename(columns=col_map, inplace=True)
    return df

def build_hybrid_matrices(df):
    """
    Linha (+ Bandas de ATR + Momentum Direcional)
    Isola o ruído dos pavios através de um Vetor de Fechamento (Line Chart).
    """
    print("| [*] Calculando Vetores Híbridos (Keltner + DEMA)")
    # 1. Line Vector (Vetor Suave de Fechamento - Exclui ruído do Wick/Pavio)
    df['line_vector'] = df['close'].ewm(span=8, adjust=False).mean()
    
    # 2. True Range e ATR (Matriz de Entropia Não-Gaussiana)
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = (df['high'] - df['prev_close']).abs()
    df['tr3'] = (df['low'] - df['prev_close']).abs()
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['atr'] = df['tr'].rolling(window=20).mean()
    
    # 3. Keltner Channels (Atratores Dinâmicos)
    df['center'] = df['close'].ewm(span=30, adjust=False).mean()
    df['band_upper'] = df['center'] + (1.8 * df['atr'])
    df['band_lower'] = df['center'] - (1.8 * df['atr'])
    
    # Volume Simplificado Log
    vol_col = 'tick_volume' if 'tick_volume' in df.columns else ('vol' if 'vol' in df.columns else 'volume')
    df['vol_avg'] = df[vol_col].rolling(window=20).mean()
    df['is_vol_surge'] = df[vol_col] > (df['vol_avg'] * 1.5)
    
    df.fillna(method='bfill', inplace=True)
    return df, vol_col

def run_hybrid_backtest():
    print("="*80)
    print(" 🚀 OMEGA MOMENTUM MACRO (MODO HÍBRIDO) - HISTÓRICO COMPLETO 🚀")
    print(" (Gráfico de Linhas + Bandas Keltner ATR + Escalamento de Fat Tail) ")
    print("="*80)
    
    df = load_data()
    if df is None: return
    
    # Para o teste do Histórico Completo vamos rodar sob uma janela robusta (Total Base M5)
    # Normalmente XAUUSD M5 possui ~100k a 300k velas (Anos).
    df = df.tail(100000).reset_index(drop=True) 
    
    start_t = time.time()
    df, vol_col = build_hybrid_matrices(df)
    
    line_v = df['line_vector'].values
    upper_b = df['band_upper'].values
    lower_b = df['band_lower'].values
    closes = df['close'].values
    atr = df['atr'].values
    surge = df['is_vol_surge'].values
    
    balance = 10000.0
    equity_peak = balance
    max_dd_perc = 0.0
    
    # State Machine
    open_positions = []
    
    wins, losses, trades_closed = 0, 0, 0
    stats = {"thrust_entries": 0, "pyramid_additions": 0, "partial_takes": 0}
    
    print(f"| Executando Matrix sobre {len(df)} candles...")
    
    for i in range(50, len(df)):
        c = closes[i]
        
        # Sinais Vetoriais de Fuga (Thrust)
        buy_signal = (line_v[i] > upper_b[i]) and (line_v[i-1] <= upper_b[i-1]) and surge[i]
        sell_signal = (line_v[i] < lower_b[i]) and (line_v[i-1] >= lower_b[i-1]) and surge[i]
        
        active_dir = open_positions[0]['dir'] if open_positions else 0
        total_pnl = 0.0
        
        # Update Open Positions PnL
        alive_positions = []
        for pos in open_positions:
            pnl = (c - pos['entry']) if pos['dir'] == 1 else (pos['entry'] - c)
            total_pnl += pnl * pos['lots'] * 10.0 # Aproximação base $10 per pip por lote (Ouro usual)
            
            close_flag = False
            # Exit Logic Institucional
            if pos['dir'] == 1 and line_v[i] < df['center'].values[i]: # Perdeu gravidade central
                close_flag = True
            elif pos['dir'] == -1 and line_v[i] > df['center'].values[i]:
                close_flag = True
                
            # Stop Loss e Take Profit Rígido caso desastre
            if pnl < -(atr[i]*3.0): close_flag = True # Stop no 3x ATR (Volatilidade real)
            
            # Partial Scaling (Escala OUT)
            if not pos.get('partial_done', False) and pnl > (atr[i]*5.0): # Andou 5 ATRs maciços
                profit = (pnl * (pos['lots']/2.0) * 10.0)
                balance += profit
                pos['lots'] = pos['lots'] / 2.0
                pos['partial_done'] = True
                stats['partial_takes'] += 1
                trades_closed += 1
                if profit > 0: wins += 1
            
            # Pyramiding (Escala IN) - Apenas no Lote Base
            if not pos.get('pyramid_done', False) and pnl > (atr[i]*2.5) and len(open_positions) < 3:
                # O movimento confirmou, adicionamos peso na Tendência (Kelly)
                new_lot = pos['lots'] * 0.5
                alive_positions.append({"dir": pos['dir'], "entry": c, "lots": new_lot, 'pyramid_done': True, 'partial_done': True})
                pos['pyramid_done'] = True
                stats['pyramid_additions'] += 1
                
            if close_flag:
                profit = (pnl * pos['lots'] * 10.0)
                balance += profit
                trades_closed += 1
                if profit > 0: wins += 1
                else: losses += 1
            else:
                alive_positions.append(pos)
                
        open_positions = alive_positions
        
        # New Entries
        if len(open_positions) == 0:
            if buy_signal:
                open_positions.append({"dir": 1, "entry": c, "lots": 0.1})
                stats['thrust_entries'] += 1
            elif sell_signal:
                open_positions.append({"dir": -1, "entry": c, "lots": 0.1})
                stats['thrust_entries'] += 1
                
        # Drawdown tracker via Equity Flutuante
        current_equity = balance + total_pnl
        if current_equity > equity_peak:
            equity_peak = current_equity
        if equity_peak > 0:
            dd = (equity_peak - current_equity) / equity_peak
            if dd > max_dd_perc: max_dd_perc = dd

    # Close remaining
    for pos in open_positions:
        pnl = (closes[-1] - pos['entry']) if pos['dir'] == 1 else (pos['entry'] - closes[-1])
        balance += (pnl * pos['lots'] * 10.0)

    end_t = time.time()
    
    print("\n" + "="*80)
    print(" 📊 RESULTADO GLOBAL: MOMENTUM MACRO HÍBRIDO (FAT TAIL SCALING)")
    print("="*80)
    print(f"| 🕰️ PERÍODO:         100.000 Candles Históricos")
    print(f"| 💎 CAPITAL INICIAL: $ 10,000.00")
    print(f"| 💰 CAPITAL FINAL:   $ {balance:,.2f}")
    
    lucro = balance - 10000.0
    print(f"| 🚀 LUCRO LÍQUIDO:   $ {lucro:,.2f} ({(lucro/10000.0)*100:.2f}%)")
    print(f"| 🛡️ MÁX DRAWDOWN:    {max_dd_perc*100:.2f}%")
    print(f"| 🎯 TAXA DE ACERTO:  {(wins/max(1, trades_closed))*100:.1f}%")
    print(f"| 🔄 TRADES ATIVOS:   {trades_closed} concluídos")
    print("="*80)
    print(" 🛠️ COMPORTAMENTO FÍSICO (MOTOR GEOMÉTRICO):")
    print(f"   -> {stats['thrust_entries']} Disparos Primários de Vetor (Rompimento do Keltner + Surtos de Volume).")
    print(f"   -> {stats['pyramid_additions']} Lotes de Risco Geométrico adicionados NO FLUXO (Pyramiding).")
    print(f"   -> {stats['partial_takes']} Realizações Parciais disparadas protegendo a conta nos Picos (Scale Out).")
    print("="*80)
    print(f"Tempo de Processamento (Vetorizado): {end_t - start_t:.3f} s")

if __name__ == "__main__":
    run_hybrid_backtest()
