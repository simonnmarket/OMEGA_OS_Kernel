import MetaTrader5 as mt5
import json
if not mt5.initialize():
    print(json.dumps({"error": "init_failed"}))
    quit()
positions = mt5.positions_get()
if positions:
    res = []
    for p in positions:
        res.append({
            "symbol": p.symbol,
            "type": "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL",
            "volume": p.volume,
            "price_open": p.price_open,
            "sl": p.sl,
            "tp": p.tp,
            "profit": p.profit
        })
    print(json.dumps(res, indent=2))
else:
    print("[]")
mt5.shutdown()
