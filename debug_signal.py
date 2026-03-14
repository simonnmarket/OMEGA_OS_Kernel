import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from run_aic_v5_master import OmegaAICControllerV5
from modules.v_flow_microstructure import MacroBias

def debug_signal():
    if not mt5.initialize():
        print("MT5 Fail")
        return
    
    symbol = "XAUUSD"
    mt5.symbol_select(symbol, True)
    
    rates_m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 150)
    rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 500)
    
    if rates_m1 is None or rates_m15 is None:
        print("Data fail")
        return
        
    ohlcv_m1 = np.array([[r['open'], r['high'], r['low'], r['close'], float(r['tick_volume'])] for r in rates_m1])
    ohlcv_m15 = np.array([[r['open'], r['high'], r['low'], r['close'], float(r['tick_volume'])] for r in rates_m15])
    
    ctrl = OmegaAICControllerV5()
    
    # Analyze kernel
    kernel_state = ctrl.omega_kernel.engine_step(ohlcv_m15)
    bias = MacroBias(
        hurst=kernel_state.details.get('hfd', 0.5),
        kalman_trend=1 if ctrl.kalman_engine.execute(ohlcv_m15)['velocity'] > 0 else -1,
        horizon="DAY",
        strength=kernel_state.signal_strength
    )
    
    latest = rates_m1[-1]
    candle_dict = {
        'open': latest['open'],
        'high': latest['high'],
        'low': latest['low'],
        'close': latest['close'],
        'volume': float(latest['tick_volume'])
    }
    
    thrust = ctrl.get_thrust_vector(ohlcv_m1, candle_dict, bias)
    
    print(f"SYMBOL: {symbol}")
    print(f"HFD: {kernel_state.details.get('hfd', 0.5):.4f}")
    print(f"KERNEL BIAS: {kernel_state.bias}")
    print(f"KERNEL SCORE: {kernel_state.signal_strength*100:.1f}")
    print(f"THRUST LAUNCH: {thrust['launch']}")
    print(f"THRUST DIR: {thrust['direction']}")
    print(f"THRUST SCORE: {thrust['thrust_score']:.1f}")
    print(f"TRIGGER TYPE: {thrust['trigger_type']}")
    print(f"KALMAN BREAK: {thrust['kalman_break']}")
    
    mt5.shutdown()

if __name__ == "__main__":
    debug_signal()
