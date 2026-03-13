import MetaTrader5 as mt5
import pandas as pd

def check_current_positions():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return
    
    positions = mt5.positions_get()
    if positions is None:
        print("No positions found.")
    else:
        print(f"Total positions: {len(positions)}")
        df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
        print(df[['symbol', 'type', 'volume', 'price_open', 'price_current', 'sl', 'tp', 'magic', 'comment']])
        
    mt5.shutdown()

if __name__ == "__main__":
    check_current_positions()
