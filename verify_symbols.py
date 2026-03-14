import MetaTrader5 as mt5
import pandas as pd
import os
from datetime import datetime

def check_symbols():
    if not mt5.initialize():
        print("initialize() failed")
        return
    
    requested_symbols = [
        "XAUUSD", "XAGUSD", "XAGEUR", "AUDUSD",
        "EURJPY", "GBPUSD", "USDJPY", "AUDJPY",
        "GER40", "US100", "US30", "US500", "USOIL+", "HK50",
        "BTCUSD", "ETHUSD", "DOGUSD", "SOLUSD"
    ]
    
    print("Checking availability of requested symbols...")
    available = []
    missing = []
    
    for symbol in requested_symbols:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            # Try to search or find with common suffixes
            all_symbols = mt5.symbols_get()
            found = False
            for s in all_symbols:
                if symbol == s.name or symbol in s.name:
                    available.append(s.name)
                    found = True
                    break
            if not found:
                missing.append(symbol)
        else:
            available.append(symbol)
            
    print(f"Available: {available}")
    print(f"Missing: {missing}")
    mt5.shutdown()

if __name__ == "__main__":
    check_symbols()
