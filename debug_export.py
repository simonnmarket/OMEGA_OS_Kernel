import MetaTrader5 as mt5
import pandas as pd
import os
import time

def debug_export():
    if not mt5.initialize():
        print("Fail Init")
        return
        
    symbol = "XAUUSD"
    path = r"C:\OMEGA_PROJETO\OHLCV_DATA"
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created {path}")
    
    print(f"Selecting {symbol}")
    sel = mt5.symbol_select(symbol, True)
    print(f"Select result: {sel}")
    
    time.sleep(1) # Wait for sync
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    if rates is not None:
        print(f"Got {len(rates)} rates")
        df = pd.DataFrame(rates)
        f_path = os.path.join(path, "test_xauusd.csv")
        df.to_csv(f_path)
        print(f"Saved to {f_path}")
        print(f"File exists check: {os.path.exists(f_path)}")
    else:
        print("Rates is None")
        err = mt5.last_error()
        print(f"MT5 Error: {err}")

    mt5.shutdown()

if __name__ == "__main__":
    debug_export()
