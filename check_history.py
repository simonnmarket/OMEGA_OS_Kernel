import MetaTrader5 as mt5
from datetime import datetime, timedelta

def check_history():
    if not mt5.initialize():
        print("MT5 Init Fail")
        return

    # De hoje
    from_date = datetime.now() - timedelta(days=1)
    to_date = datetime.now()
    
    deals = mt5.history_deals_get(from_date, to_date)
    if deals:
        print(f"Total deals: {len(deals)}")
        for d in deals[-10:]:
            print(f"Time: {d.time}, Symbol: {d.symbol}, Profit: {d.profit}, Comment: {d.comment}, Magic: {d.magic}")
    else:
        print("No deals found")
        
    positions = mt5.positions_get()
    print(f"Active positions: {len(positions) if positions else 0}")
    
    mt5.shutdown()

if __name__ == "__main__":
    check_history()
