import pandas as pd
import numpy as np
import time
import os

from modules.omega_kernel_v5_1_refined import OMEGAKernelV51Refined, KernelConfig
from modules.volume_profile import VolumeProfileEngine, VolumeConfig

def load_data():
    file_path = r"C:\OMEGA_PROJETO\OHLCV_DATA\XAUUSD_M5.csv"
    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        return None
        
    df = pd.read_csv(file_path, sep='\t')
    if len(df.columns) < 5:
        df = pd.read_csv(file_path) # Try comma
        
    # Standardize columns
    col_map = {c: c.lower().replace('<', '').replace('>', '') for c in df.columns}
    df.rename(columns=col_map, inplace=True)
    return df

def run_rigorous_test():
    print("="*80)
    print(" OMEGA TESSERACT FULL INTEGRATION - RIGOROUS BACKTEST ")
    print("="*80)
    
    df = load_data()
    if df is None: return
    
    # Aceleração para os ultimos meses para rodar rápido e ter output denso
    df = df.tail(15000).reset_index(drop=True)
    
    closes = df['close'].values
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    vols = df['tick_volume'].values if 'tick_volume' in df.columns else df.iloc[:, 5].values

    ohlcv = np.column_stack([opens, highs, lows, closes, vols])

    # Instanciando a Inteligência Ativa Isolada
    kernel = OMEGAKernelV51Refined(KernelConfig())
    vol_engine = VolumeProfileEngine(VolumeConfig())

    print(f"| Base Carregada: {len(df)} candles M5")
    print("| Motores Plugados no Pipeline: ")
    print("| -> OMEGAKernelV51Refined (Hurst, Z-Price, Z-Vol, HA Bias)")
    print("| -> VolumeProfileEngine (Wyckoff Absorption, Volume Time)")
    print("="*80)
    
    balance = 10000.0
    equity_peak = balance
    max_dd = 0.0
    
    pos = 0 # 1=Buy, -1=Sell
    entry_price = 0
    lots = 0.10
    
    wins = 0
    losses = 0
    trade_count = 0
    
    stats = {
        "kernel_vetos": 0,
        "wyckoff_absorptions_detected": 0,
        "volume_exhaustions": 0,
        "fractal_trends": 0,
        "panic_commands": 0
    }
    
    start_t = time.time()
    
    for i in range(150, len(df)-1):
        window = ohlcv[i-150:i+1] # 150 bars context
        c = closes[i]
        
        # 1. Atualizar Módulo de Profiling e Wyckoff Local
        bar_dict = {
            "close": c, "open": opens[i], "high": highs[i], "low": lows[i],
            "volume": vols[i], "hour_utc": 14 
        }
        vol_state = vol_engine.update("XAUUSD", bar_dict)
        
        wyckoff = vol_engine.check_absorption_pattern(
            "XAUUSD", closes[i], closes[i-1], vols[i], vols[i-1]
        )
        if wyckoff["is_absorption"]:
            stats["wyckoff_absorptions_detected"] += 1
            
        if vol_state.is_exhausted:
            stats["volume_exhaustions"] += 1
            
        # 2. Kernel Engine (Tier-0 Física)
        kernel_state = kernel.engine_step(window)
        regime = kernel_state.regime.name
        
        if regime == "STRUCTURAL_TREND":
            stats["fractal_trends"] += 1
        elif regime == "CHOPPY_NOISE" or regime == "INSUFFICIENT_DATA":
            stats["kernel_vetos"] += 1
        elif regime == "COMMAND_INERTIA":
            stats["panic_commands"] += 1
            
        # 3. Integração das Decisões (Decisor Tier-0)
        is_buy_signal = False
        is_sell_signal = False
        
        # Pullbacks Reversos Baseados em Wyckoff Absorption (Armadilhas Institucionais)
        if wyckoff["is_absorption"] and vol_state.flow_imbalance < 0 and wyckoff["interpretation"] == "ACCUMULATION":
            # Smart money is accumulating amidst downward price manipulation
            is_buy_signal = True
            
        elif wyckoff["is_absorption"] and vol_state.flow_imbalance > 0 and wyckoff["interpretation"] == "DISTRIBUTION":
            # Smart money is distributing in fake rally
            is_sell_signal = True
            
        # Momentum Seguro via Fractal
        elif kernel_state.is_aggressive_allowed and kernel_state.bias == "BUY" and not vol_state.is_exhausted:
            is_buy_signal = True
            
        elif kernel_state.is_aggressive_allowed and kernel_state.bias == "SELL" and not vol_state.is_exhausted:
            is_sell_signal = True

        # Posição
        if pos == 0:
            if is_buy_signal: 
                pos = 1; entry_price = c
            elif is_sell_signal: 
                pos = -1; entry_price = c
        else:
            pnl_pts = (c - entry_price) if pos == 1 else (entry_price - c)
            # Exit Logic: Reversão de viés do HA, Absorção Oposta ou Lucro grande
            exit_signal = False
            if pos == 1 and (kernel_state.bias == "SELL" or (wyckoff["is_absorption"] and wyckoff["interpretation"] == "DISTRIBUTION")):
                exit_signal = True
            elif pos == -1 and (kernel_state.bias == "BUY" or (wyckoff["is_absorption"] and wyckoff["interpretation"] == "ACCUMULATION")):
                exit_signal = True
            elif pnl_pts > 4000: # Take Profit agressivo (~400 pips)
                exit_signal = True
            elif pnl_pts < -1500: # Stop Loss técnico
                exit_signal = True
                
            if exit_signal:
                trade_count += 1
                profit = pnl_pts * lots
                balance += profit
                if profit >= 0: wins += 1
                else: losses += 1
                pos = 0
                
        # Drawdown Tracking 
        if balance > equity_peak: equity_peak = balance
        if equity_peak > 0:
            dd = (equity_peak - balance) / equity_peak
            if dd > max_dd: max_dd = dd
            
    end_t = time.time()
    
    print("\n[+] DIAGNÓSTICO ESTATÍSTICO V6 - IMPACTO DOS MÓDULOS:")
    print(f" -> Vetos por Ruído Fractal (Choppy): {stats['kernel_vetos']} barras neutralizadas.")
    print(f" -> Absorções Wyckoff (Manipulações):  {stats['wyckoff_absorptions_detected']} armadilhas detectadas e operadas contra a manada.")
    print(f" -> Exaustão de Volume (Falta de Ar):  {stats['volume_exhaustions']} vacuums abortados.")
    print(f" -> Super Fluxo (Comandos Diretos):    {stats['panic_commands']} vetores purificados pelo Tesseract.")
    print("="*80)
    print(" RESULTADO DA INTEGRAÇÃO DO ARSENAL SUPREMO:")
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
    run_rigorous_test()
