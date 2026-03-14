import MetaTrader5 as mt5
import sys

def get_prices():
    if not mt5.initialize():
        print("MT5 Fail")
        return
    
    symbols = ["XAUUSD", "XAGUSD", "EURUSD", "GBPUSD", "USDJPY"]
    for s in symbols:
        tick = mt5.symbol_info_tick(s)
        if tick:
            print(f"{s}: Bid={tick.bid}, Ask={tick.ask}, Last={tick.last}")
        else:
            print(f"{s}: Tick not found")
    
    mt5.shutdown()

if __name__ == "__main__":
    get_prices()
