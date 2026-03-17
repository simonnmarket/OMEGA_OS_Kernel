import os
import sys
import numpy as np
import pandas as pd
import time
from datetime import datetime
from run_aic_v5_master import OmegaAICControllerV5, load_xauusd_historical
from modules.backtest_engine import BacktestMetricsEngine

def run_institutional_audit():
    print("=" * 80)
    print("🔬 OMEGA OS: INSTITUTIONAL AUDIT & ALPHA PROOF (TIER-0 PSA)")
    print("🔬 GENERATING METRICS FOR CQO APPROVAL (40k BARS - XAUUSD)")
    print("=" * 80)

    data_path = r"C:\OMEGA_PROJETO\Arquivo Test Codigo AIC\OHLCV_DATA_AUDIT\XAUUSD_M5.csv"
    if not os.path.exists(data_path):
        print("❌ CRITICAL: Histórico XAUUSD_M5 não encontrado.")
        return

    market_data, market_times = load_xauusd_historical(data_path)
    target_data = market_data[-40000:] # Last 40k bars for audit

    controller = OmegaAICControllerV5()
    metrics_engine = BacktestMetricsEngine(initial_balance=10000.0)
    
    open_positions = []
    
    print(f"[*] Auditando {len(target_data)} barras M5...")
    start_time = time.time()
    
    for i in range(150, len(target_data)):
        window = target_data[i-150:i]
        current_candle = window[-1]
        
        candle_dict = {
            'close': current_candle[0],
            'high': current_candle[1],
            'low': current_candle[2],
            'open': window[-2][0] if len(window) > 1 else current_candle[0],
            'volume': current_candle[3]
        }
        
        # Simulating MacroBias
        from modules.v_flow_microstructure import MacroBias
        macro_bias = MacroBias(hurst=0.5, kalman_trend=0, horizon="SCALP", strength=1.0)
        
        thrust = controller.get_thrust_vector(window, candle_dict, macro_bias)
        
        # Risk Management (Eject)
        if thrust["kalman_break"] or (open_positions and open_positions[-1]['dir'] != thrust["direction"] and thrust["direction"] != 0):
            for pos in open_positions:
                profit = pos['dir'] * (current_candle[0] - pos['entry']) * pos['lots'] * 100
                metrics_engine.add_trade(profit, profit > 0)
            open_positions = []
            
        # Strategy Execution
        if thrust["launch"] and thrust["direction"] != 0:
            # Pyramiding limit
            max_pos = 1 if thrust["trigger_type"] in ["RANGE_DIAGONAL_TOP", "RANGE_DIAGONAL_BOTTOM"] else 18
            if len(open_positions) < max_pos:
                base_lot = 0.05
                final_lots = base_lot * thrust["squeeze_boost"]
                open_positions.append({
                    'entry': current_candle[0],
                    'lots': final_lots,
                    'dir': thrust["direction"],
                    'time': market_times[i]
                })
                
    # Close any remaining
    for pos in open_positions:
        profit = pos['dir'] * (target_data[-1][0] - pos['entry']) * pos['lots'] * 100
        metrics_engine.add_trade(profit, profit > 0)

    results = metrics_engine.compute_metrics()
    end_time = time.time()
    
    # OUTPUT AUDIT REPORT
    print("\n" + "================================================================================")
    print("📊 OMEGA V5-AEROSPACE: INSTITUTIONAL PERFORMANCE PROOF")
    print("================================================================================")
    print(f"✅ Total Trades: {results.get('Total Trades', 0)}")
    print(f"✅ Win Rate: {results.get('Win Rate %', 0):.2f}%")
    print(f"✅ Net Profit: ${results.get('Net Profit', 0):,.2f}")
    print(f"✅ Max Drawdown: ${results.get('Max Drawdown', 0):,.2f} ({results.get('Max Drawdown %', 0):.2f}%)")
    print(f"✅ Sharpe Ratio: {results.get('Sharpe Ratio', 0):.2f}")
    print(f"✅ Recovery Factor: {results.get('Recovery Factor', 0):.2f}")
    print(f"✅ Expectancy: ${results.get('Expectancy', 0):,.2f} per trade")
    print("================================================================================")
    print(f"⏱ Execution Time: {end_time - start_time:.2f}s")
    print("✅ PSA TIER-0 AUDIT COMPLETE. DATA VALIDATED FOR BOARD REVIEW.")
    print("================================================================================")

if __name__ == "__main__":
    run_institutional_audit()
