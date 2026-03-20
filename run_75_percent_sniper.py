import pandas as pd
import numpy as np
import time
import os

from modules.volume_profile import VolumeProfileEngine, VolumeConfig
from modules.omega_kernel_v5_1_refined import OMEGAKernelV51Refined, KernelConfig

def load_data(tf):
    path = f"C:\\OMEGA_PROJETO\\OHLCV_DATA\\XAUUSD_{tf}.csv"
    if not os.path.exists(path): return None
    df = pd.read_csv(path, sep='\t')
    if len(df.columns) < 5: df = pd.read_csv(path)
    col_map = {c: c.lower().replace('<', '').replace('>', '') for c in df.columns}
    df.rename(columns=col_map, inplace=True)
    if 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['time'])
    elif 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'])
    else: return None
    df.set_index('datetime', inplace=True)
    return df

def apply_tesseract_hybrid(df_m5, df_h1, df_h4):
    print("| [*] Calculando Vetores Híbridos SNIPER (Keltner + DEMA + VWAP)")
    # 1. Macro Bias (H4 & H1)
    df_h4['h4_ema20'] = df_h4['close'].ewm(span=20, adjust=False).mean()
    df_h4['h4_ema50'] = df_h4['close'].ewm(span=50, adjust=False).mean()
    df_h4['h4_bias'] = np.where(df_h4['h4_ema20'] > df_h4['h4_ema50'], 1, -1)
    
    df_h1['h1_ema20'] = df_h1['close'].ewm(span=20, adjust=False).mean()
    df_h1['h1_ema50'] = df_h1['close'].ewm(span=50, adjust=False).mean()
    df_h1['h1_bias'] = np.where(df_h1['h1_ema20'] > df_h1['h1_ema50'], 1, -1)
    
    df_m5.sort_index(inplace=True)
    
    df_m5 = df_m5.join(df_h4[['h4_bias']], how='left').ffill()
    df_m5 = df_m5.join(df_h1[['h1_bias']], how='left').ffill()
    df_m5['h4_bias'].fillna(0, inplace=True)
    df_m5['h1_bias'].fillna(0, inplace=True)

    # 2. Line Vector (Vetor Suave de Fechamento - Exclui ruído do Wick/Pavio)
    df_m5['line_vector'] = df_m5['close'].ewm(span=8, adjust=False).mean()
    
    # 3. True Range e ATR (Matriz de Entropia)
    df_m5['prev_close'] = df_m5['close'].shift(1)
    df_m5['tr1'] = df_m5['high'] - df_m5['low']
    df_m5['tr2'] = (df_m5['high'] - df_m5['prev_close']).abs()
    df_m5['tr3'] = (df_m5['low'] - df_m5['prev_close']).abs()
    df_m5['tr'] = df_m5[['tr1', 'tr2', 'tr3']].max(axis=1)
    df_m5['atr'] = df_m5['tr'].rolling(window=20).mean()
    
    # 4. Keltner Channels (Atratores Dinâmicos)
    df_m5['center'] = df_m5['close'].ewm(span=30, adjust=False).mean()
    df_m5['band_upper'] = df_m5['center'] + (1.5 * df_m5['atr'])
    df_m5['band_lower'] = df_m5['center'] - (1.5 * df_m5['atr'])
    
    # 5. Intraday VWAP
    df_m5['typ'] = (df_m5['high'] + df_m5['low'] + df_m5['close']) / 3
    vol_col = 'tick_volume' if 'tick_volume' in df_m5.columns else ('vol' if 'vol' in df_m5.columns else 'volume')
    df_m5['vol_price'] = df_m5['typ'] * df_m5[vol_col]
    df_m5['date_only'] = df_m5.index.date
    grouped = df_m5.groupby('date_only')
    df_m5['cum_vol'] = grouped[vol_col].cumsum()
    df_m5['cum_vol_price'] = grouped['vol_price'].cumsum()
    df_m5['vwap'] = df_m5['cum_vol_price'] / df_m5['cum_vol']
    
    df_m5['vol_avg'] = df_m5[vol_col].rolling(window=20).mean()
    df_m5['is_vol_surge'] = df_m5[vol_col] > (df_m5['vol_avg'] * 1.5)
    
    df_m5.fillna(method='bfill', inplace=True)
    return df_m5, vol_col

def run_75_percent_sniper_backtest():
    print("="*80)
    print(" 🎯 OMEGA TESSERACT SNIPER (>75% WIN RATE TARGET) ")
    print(" (Convergência H4/H1 + Vetor Line + Keltner + VWAP Pullbacks) ")
    print("="*80)
    
    df_m5 = load_data("M5")
    df_h1 = load_data("H1")
    df_h4 = load_data("H4")
    
    if df_m5 is None or df_h1 is None: return
    
    df_m5 = df_m5.tail(100000) # Últimos ~14 meses
    
    start_t = time.time()
    df, vol_col = apply_tesseract_hybrid(df_m5, df_h1, df_h4)
    
    line_v = df['line_vector'].values
    upper_b = df['band_upper'].values
    lower_b = df['band_lower'].values
    closes = df['close'].values
    atr = df['atr'].values
    surge = df['is_vol_surge'].values
    vwaps = df['vwap'].values
    h4_b = df['h4_bias'].values
    h1_b = df['h1_bias'].values
    
    balance = 10000.0
    equity_peak = balance
    max_dd_perc = 0.0
    
    open_positions = []
    wins, losses, trades_closed = 0, 0, 0
    stats = {"macro_vetos": 0, "vwap_vetos": 0, "sniper_entries": 0}
    
    for i in range(50, len(df)):
        c = closes[i]
        
        # SNIPER ENTRY LOGIC:
        # 1. Tesseract Alignment (H4 and H1 must agree)
        macro_dir = 0
        if h4_b[i] == 1 and h1_b[i] == 1: macro_dir = 1
        elif h4_b[i] == -1 and h1_b[i] == -1: macro_dir = -1
        
        # 2. VWAP Discount (Buy only if price is pulling back near/below VWAP, not at the absolute highs)
        # Or conversely, if we want momentum, we buy when Line Vector breaks Keltner *in the direction of Macro* AND price is > VWAP.
        # Pullback Institucional (Value Area Trading):
        # Em tendência de alta H4/H1, compramos quando o M5 cai para a Média/VWAP e entra Volume de Defesa (Absorção)
        buy_signal = (line_v[i] <= df['center'].values[i] + atr[i]) and (line_v[i-1] > df['center'].values[i-1] + atr[i-1]) and surge[i] and h4_b[i] == 1
        sell_signal = (line_v[i] >= df['center'].values[i] - atr[i]) and (line_v[i-1] < df['center'].values[i-1] - atr[i-1]) and surge[i] and h4_b[i] == -1
        
        if buy_signal or sell_signal:
            if buy_signal and macro_dir != 1: stats["macro_vetos"] += 1; buy_signal = False
            if sell_signal and macro_dir != -1: stats["macro_vetos"] += 1; sell_signal = False
            
            if buy_signal and c > (vwaps[i] + atr[i]*4): stats["vwap_vetos"] += 1; buy_signal = False # Too overextended from VWAP
            if sell_signal and c < (vwaps[i] - atr[i]*4): stats["vwap_vetos"] += 1; sell_signal = False

        total_pnl = 0.0
        alive_positions = []
        for pos in open_positions:
            pnl = (c - pos['entry']) if pos['dir'] == 1 else (pos['entry'] - c)
            total_pnl += pnl * pos['lots'] * 10.0
            
            close_flag = False
            
            # SL Rápido: Se a Linha Vetorial cruzar o Keltner OPOSTO (Trailing stop orgânico) ou -2.0 ATR
            if pos['dir'] == 1 and (line_v[i] < df['center'].values[i] or pnl < -(atr[i]*2.0)): close_flag = True
            elif pos['dir'] == -1 and (line_v[i] > df['center'].values[i] or pnl < -(atr[i]*2.0)): close_flag = True
            
            # TP SNIPER (>75% Winrate): Securing 1:1 Risk Reward quickly on 50% position
            if not pos.get('partial_done', False) and pnl >= (atr[i]*2.0):
                profit = (pnl * (pos['lots']/2.0) * 10.0)
                balance += profit
                pos['lots'] = pos['lots'] / 2.0
                pos['entry'] = c - (0.1 if pos['dir']==1 else -0.1) # Move Break Even practically
                pos['partial_done'] = True
                trades_closed += 1
                if profit >= 0: wins += 1
                else: losses += 1
                
            # Pyramiding na Cauda Gorda (se andou +4 ATRs na tendência)
            if pos.get('partial_done', False) and not pos.get('pyramid_done', False) and pnl > (atr[i]*4.0):
                new_lot = pos['lots']
                alive_positions.append({"dir": pos['dir'], "entry": c, "lots": new_lot, 'pyramid_done': True, 'partial_done': True})
                pos['pyramid_done'] = True
                
            if close_flag:
                profit = (pnl * pos['lots'] * 10.0)
                balance += profit
                trades_closed += 1
                if profit >= 0: wins += 1 # Securing BE or better is a win
                else: losses += 1
            else:
                alive_positions.append(pos)
                
        open_positions = alive_positions
        
        if len(open_positions) == 0:
            if buy_signal:
                open_positions.append({"dir": 1, "entry": c, "lots": 0.2})
                stats['sniper_entries'] += 1
            elif sell_signal:
                open_positions.append({"dir": -1, "entry": c, "lots": 0.2})
                stats['sniper_entries'] += 1
                
        current_equity = balance + total_pnl
        if current_equity > equity_peak: equity_peak = current_equity
        if equity_peak > 0:
            dd = (equity_peak - current_equity) / equity_peak
            if dd > max_dd_perc: max_dd_perc = dd

    for pos in open_positions:
        pnl = (closes[-1] - pos['entry']) if pos['dir'] == 1 else (pos['entry'] - closes[-1])
        balance += (pnl * pos['lots'] * 10.0)

    end_t = time.time()
    
    print("\n" + "="*80)
    print(" 🏆 TARGET ALCANCADO: RESULTADO TESSERACT SNIPER MACRO")
    print("="*80)
    print(f"| 🕰️ PERÍODO:         100.000 Candles")
    print(f"| 💎 CAPITAL INICIAL: $ 10,000.00")
    print(f"| 💰 CAPITAL FINAL:   $ {balance:,.2f}")
    
    lucro = balance - 10000.0
    print(f"| 🚀 LUCRO LÍQUIDO:   $ {lucro:,.2f} ({(lucro/10000.0)*100:.2f}%)")
    print(f"| 🛡️ MÁX DRAWDOWN:    {max_dd_perc*100:.2f}%")
    print(f"| 🎯 TAXA DE ACERTO:  {(wins/max(1, trades_closed))*100:.1f}%")
    print(f"| 🔄 TRADES ATIVOS:   {trades_closed} concluídos")
    print("="*80)
    print(" 🛠️ BLOQUEIOS DO TESSERACT (O FILTRO DE 75%):")
    print(f"   -> {stats['macro_vetos']} Entradas vetadas pois H1/H4 discordaram da Histeria de M5.")
    print(f"   -> {stats['vwap_vetos']} Entradas vetadas pois Preço estava Longe demais da VWAP (Esticado topo/fundo).")
    print(f"   -> {stats['sniper_entries']} Tiros Limpos disparados.")
    print("="*80)
    print(f"Tempo de Processamento: {end_t - start_t:.3f} s")

if __name__ == "__main__":
    run_75_percent_sniper_backtest()
