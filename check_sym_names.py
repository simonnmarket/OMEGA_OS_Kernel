import MetaTrader5 as mt5

def deep_check():
    if not mt5.initialize():
        return
        
    targets = ["BTC", "ETH", "GER", "US100", "US30", "HK50", "DOG", "SOL"]
    for t in targets:
        syms = mt5.symbols_get(f"*{t}*")
        if syms:
            print(f"Search '{t}': {[s.name for s in syms]}")
        else:
            print(f"Search '{t}': No matches")
            
    mt5.shutdown()

if __name__ == "__main__":
    deep_check()
