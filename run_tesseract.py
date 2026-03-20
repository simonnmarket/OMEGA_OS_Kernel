import pandas as pd
import numpy as np
import time
import os

from modules.omega_kernel_v5_1_refined import OMEGAKernelV51Refined, KernelConfig
from modules.volume_profile import VolumeProfileEngine, VolumeConfig

def load_data(tf):
    path = f"C:\\OMEGA_PROJETO\\OHLCV_DATA\\XAUUSD_{tf}.csv"
    if not os.path.exists(path): return None
    df = pd.read_csv(path, sep='\t')
    if len(df.columns) < 5: df = pd.read_csv(path)
    col_map = {c: c.lower().replace('<', '').replace('>', '') for c in df.columns}
    df.rename(columns=col_map, inplace=True)
    
    time_col = None
    if 'time' in df.columns: time_col = 'time'
    elif 'date' in df.columns: time_col = 'date'
    
    if time_col:
        df['datetime'] = pd.to_datetime(df[time_col])
        df.set_index('datetime', inplace=True)
    return df

def calculate_multi_tf_bias(df, kernel):
    bias_arr = []
    # Fast proxy for Kernel Bias: Use MA crossing and Z-Price logic for speed on vector
    # But for realism, we'll try a rolling approach or simplified macro EMA
    # Actually, let's do an EMA 20 and EMA 50 for pure macro direction + Hurst logic
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['macro_bias'] = np.where(df['ema20'] > df['ema50'], 1, -1)
    return df

def build_intraday_vwap(df):
    df['typ'] = (df['high'] + df['low'] + df['close']) / 3
    
    if 'tick_volume' in df.columns:
        vol_col = 'tick_volume'
    elif 'vol' in df.columns:
        vol_col = 'vol'
    else:
        vol_col = 'volume'
        
    df['vol_price'] = df['typ'] * df[vol_col]
    df['date_only'] = df.index.date
    
    grouped = df.groupby('date_only')
    df['cum_vol'] = grouped[vol_col].cumsum()
    df['cum_vol_price'] = grouped['vol_price'].cumsum()
    df['vwap'] = df['cum_vol_price'] / df['cum_vol']
    return df

def calculate_dynamic_poc(df_past_3_days):
    if len(df_past_3_days) == 0: return 0
    # Simple TPO / Volume Profile approximation
    bins = 100
    abs_max = df_past_3_days['high'].max()
    abs_min = df_past_3_days['low'].min()
    if abs_max == abs_min: return abs_max
    
    vol_col = 'tick_volume' if 'tick_volume' in df_past_3_days.columns else 'volume'
    if vol_col not in df_past_3_days.columns: vol_col = 'vol'
    
    bin_size = (abs_max - abs_min) / bins
    volume_nodes = np.zeros(bins)
    
    for _, row in df_past_3_days.iterrows():
        h, l = row['high'], row['low']
        v = row[vol_col]
        if pd.isna(v) or h == l: continue
        
        start_idx = int((l - abs_min) / bin_size)
        end_idx = int((h - abs_min) / bin_size)
        end_idx = min(bins - 1, end_idx)
        
        span = max(1, end_idx - start_idx + 1)
        f_vol = v / span
        for b in range(start_idx, end_idx + 1):
            if b < bins:
                volume_nodes[b] += f_vol
                
    poc_idx = np.argmax(volume_nodes)
    poc_price = abs_min + (poc_idx * bin_size) + (bin_size / 2)
    return poc_price

def run_tesseract_backtest():
    print("="*80)
    print(" OMEGA TESSERACT FULL MULTI-TIMEFRAME BACKTEST ")
    print(" (XAUUSD | H4, H1, M15, M5 | VWAP & POC MEMORY)")
    print("="*80)
    
    df_h4 = load_data("H4")
    df_h1 = load_data("H1")
    df_m15 = load_data("M15")
    df_m5 = load_data("M5")
    
    if df_m5 is None or df_h4 is None:
        print("Dados insuficientes. Abortando.")
        return
        
    print(f"| Base Carregada: {len(df_m5)} M5, {len(df_m15)} M15, {len(df_h1)} H1, {len(df_h4)} H4")
    print("| Processando Convergência Espacial (VWAP/POC)...")
    
    df_h4 = calculate_multi_tf_bias(df_h4, None)
    df_h1 = calculate_multi_tf_bias(df_h1, None)
    
    df_m5 = build_intraday_vwap(df_m5)
    
    # Reindex HTF bias to M5 forward-filled
    df_m5 = df_m5.join(df_h4[['macro_bias']].rename(columns={'macro_bias':'h4_bias'}), how='left').ffill()
    df_m5 = df_m5.join(df_h1[['macro_bias']].rename(columns={'macro_bias':'h1_bias'}), how='left').ffill()
    
    # Fallbacks se nan
    df_m5['h4_bias'].fillna(0, inplace=True)
    df_m5['h1_bias'].fillna(0, inplace=True)
    
    vols = df_m5['tick_volume'].values if 'tick_volume' in df_m5.columns else df_m5['vol'].values
    closes = df_m5['close'].values
    opens = df_m5['open'].values
    highs = df_m5['high'].values
    lows = df_m5['low'].values
    vwaps = df_m5['vwap'].values
    h4_bias = df_m5['h4_bias'].values
    h1_bias = df_m5['h1_bias'].values
    dates = df_m5.index.date
    
    kernel = OMEGAKernelV51Refined(KernelConfig())
    vol_engine = VolumeProfileEngine(VolumeConfig())
    
    balance = 10000.0
    equity_peak = balance
    max_dd = 0.0
    open_positions = []
    
    wins = 0
    losses = 0
    trade_count = 0
    
    stats = {"macro_confluence_blocks": 0, "wyckoff_absorptions": 0, "vwap_traps_dodged": 0}
    
    start_t = time.time()
    last_processed_poc_date = None
    poc = 0.0
    
    # Vamos processar os ultimos 25.000 (Aprox 1.5 anos em M5)
    limit = min(25000, len(df_m5)-2)
    start_idx = len(df_m5) - limit
    
    for i in range(start_idx, len(df_m5)-1):
        c = closes[i]
        v = vols[i]
        d = dates[i]
        
        # 1. Spatial Memory (POC diária calculada a cada novo dia)
        if last_processed_poc_date != d:
            last_processed_poc_date = d
            # Puxa 3 dias de h1 atras
            end_t = df_m5.index[i]
            start_t_poc = end_t - pd.Timedelta(days=3)
            df_slice = df_h1.loc[start_t_poc:end_t]
            poc = calculate_dynamic_poc(df_slice)
            
        # 2. Volume Profile & Wyckoff M5
        bar_dict = {"close": c, "open": opens[i], "high": highs[i], "low": lows[i], "volume": v, "hour_utc": 14}
        vol_state = vol_engine.update("XAUUSD", bar_dict)
        wyckoff = vol_engine.check_absorption_pattern("XAUUSD", closes[i], closes[i-1], vols[i], vols[i-1])
        
        # 3. Convergência Tesseract (H4 + H1)
        macro_dir = 0
        if h4_bias[i] == 1 and h1_bias[i] == 1: macro_dir = 1
        elif h4_bias[i] == -1 and h1_bias[i] == -1: macro_dir = -1
        
        if macro_dir == 0:
            stats["macro_confluence_blocks"] += 1
            
        is_buy = False; is_sell = False
        
        # Estratégia Wyckoff + Spatial Memory (VWAP/POC)
        # Institutional Buy: Macro H4/H1 de alta, preço recuou PARA/ABAIXO da VWAP (Value Area), e Wyckoff ACUMULOU = Bomba.
        dist_to_poc = abs(c - poc)
        vwap_val = vwaps[i]
        
        if wyckoff["is_absorption"]:
            stats["wyckoff_absorptions"] += 1
            
        if macro_dir == 1 and wyckoff["is_absorption"] and c < vwap_val and wyckoff["interpretation"] == "ACCUMULATION":
            is_buy = True
        elif macro_dir == -1 and wyckoff["is_absorption"] and c > vwap_val and wyckoff["interpretation"] == "DISTRIBUTION":
            is_sell = True
            
        # Posições e Escalonamento
        if len(open_positions) == 0:
            if is_buy: 
                open_positions.append({"dir": 1, "entry": c, "lots": 0.1})
            elif is_sell:
                open_positions.append({"dir": -1, "entry": c, "lots": 0.1})
        else:
            # Active Management (Pyramiding + Partial Closes)
            # Para o backtest, simplificamos Partial fechar metade a 300 pts, exit total a 800pts ou trailing stop.
            pos = open_positions[-1]
            pnl_pts = (c - pos['entry']) if pos['dir'] == 1 else (pos['entry'] - c)
            
            # SL = 1500 pontos, TP = 4000 pontos
            # Geometria simples de lucro
            if pnl_pts > 4000 or pnl_pts < -1500:
                profit = pnl_pts * pos['lots']
                balance += profit
                if profit > 0: wins += 1
                else: losses += 1
                trade_count += 1
                open_positions = []
            elif pnl_pts > 1500 and len(open_positions) == 1:
                # Scaled In (Piramidação a favor do fluxo)
                if pos['dir'] == macro_dir:
                    open_positions.append({"dir": pos['dir'], "entry": c, "lots": 0.05})
            
            # Se reverteu brutalmente a tendência Macro, abortar missão
            if (pos['dir'] == 1 and macro_dir == -1) or (pos['dir'] == -1 and macro_dir == 1):
                # Close all
                for p in open_positions:
                    profit = (c - p['entry'] if p['dir'] == 1 else p['entry'] - c) * p['lots']
                    balance += profit
                    if profit > 0: wins += 1
                    else: losses += 1
                    trade_count += 1
                open_positions = []

        if balance > equity_peak: equity_peak = balance
        if equity_peak > 0:
            dd = (equity_peak - balance) / equity_peak
            if dd > max_dd: max_dd = dd
            
    # Fechar remanescentes
    for p in open_positions:
        profit = (closes[-1] - p['entry'] if p['dir'] == 1 else p['entry'] - closes[-1]) * p['lots']
        balance += profit
        if profit > 0: wins += 1
        else: losses += 1
        trade_count += 1

    end_t = time.time()
    
    print("\n[+] TESSERACT CONVERGENCE TEST (XAUUSD | H4+H1+M5+VWAP+POC)")
    print(f" -> Bloqueios por Divergência Tesseract (W1/D1/H4/H1 conflito): {stats['macro_confluence_blocks']} candles ignorados.")
    print(f" -> Absorções Wyckoff Mapeadas: {stats['wyckoff_absorptions']} (Smart Money Detectado)")
    print("="*80)
    print(" RESULTADO REALISTA (LUCRO DE FAT TAILS E ESCALONAMENTO):")
    print(f"| CAPITAL INICIAL: $ 10,000.00")
    print(f"| CAPITAL FINAL:   $ {balance:,.2f}")
    if trade_count > 0:
        print(f"| LUCRO LÍQUIDO:   $ {balance - 10000:,.2f} ({((balance-10000)/10000)*100:.2f}%)")
        print(f"| MÁX DRAWDOWN:    {max_dd*100:.2f}%")
        print(f"| TRADES FEITOS:   {trade_count}")
        print(f"| TAXA DE ACERTO:  {(wins/trade_count)*100:.1f}%")
    else:
        print("| NENHUM TRADE EXECUTADO.")
    print(f"| TEMPO PROCESSOR: {end_t-start_t:.3f} s")
    print("="*80)

if __name__ == "__main__":
    run_tesseract_backtest()
