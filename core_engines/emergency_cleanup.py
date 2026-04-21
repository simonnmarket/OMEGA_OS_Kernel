import MetaTrader5 as mt5
import time

def close_all_omega_positions():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return
    
    # Target magics
    magics = [500500, 999999]
    
    positions = mt5.positions_get()
    if not positions:
        print("No open positions found.")
        mt5.shutdown()
        return
    
    closed_count = 0
    for pos in positions:
        if pos.magic in magics:
            symbol = pos.symbol
            ticket = pos.ticket
            volume = pos.volume
            order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 50,
                "magic": pos.magic,
                "comment": "OMEGA EMERGENCY CLEANUP",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"Closed {symbol} pos {ticket}")
                closed_count += 1
            else:
                # Fallback for filling mode
                request["type_filling"] = mt5.ORDER_FILLING_FOK
                result = mt5.order_send(request)
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"Closed {symbol} pos {ticket} (FOK)")
                    closed_count += 1
                else:
                    print(f"Failed to close {symbol} pos {ticket}. Code: {result.retcode}")

    print(f"\nFinalized: {closed_count} positions closed.")
    mt5.shutdown()

if __name__ == "__main__":
    close_all_omega_positions()
