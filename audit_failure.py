import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

def audit_account_failure():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return
    
    # 1. Account Info
    acc = mt5.account_info()
    print(f"Account: {acc.login} | Balance: {acc.balance} | Equity: {acc.equity} | Profit: {acc.profit}")

    # 2. History - Last 12 hours
    from_date = datetime.now() - timedelta(hours=12)
    to_date = datetime.now()
    history = mt5.history_deals_get(from_date, to_date)
    
    if history is None or len(history) == 0:
        print("No history deals found in last 12h.")
    else:
        print(f"\n--- Closed Deals (Last 12h: {len(history)}) ---")
        df_hist = pd.DataFrame(list(history), columns=history[0]._asdict().keys())
        # Filter for actual trades (entry/exit)
        df_hist = df_hist[df_hist['type'].isin([0, 1])] # Buy/Sell
        print(df_hist[['time', 'symbol', 'type', 'entry', 'volume', 'price', 'profit', 'comment']].tail(20))
        print(f"Total History Profit: {df_hist['profit'].sum()}")

    # 3. Open Positions
    positions = mt5.positions_get()
    if positions:
        print(f"\n--- Open Positions ({len(positions)}) ---")
        df_pos = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
        print(df_pos[['symbol', 'type', 'volume', 'price_open', 'price_current', 'profit', 'comment']])
    else:
        print("\nNo open positions.")

    mt5.shutdown()

if __name__ == "__main__":
    audit_account_failure()
