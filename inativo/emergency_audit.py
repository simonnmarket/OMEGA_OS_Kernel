import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

if not mt5.initialize():
    print('Falha MT5')
else:
    from_date = datetime.now() - timedelta(hours=24)
    to_date = datetime.now()
    deals = mt5.history_deals_get(from_date, to_date)
    
    if deals:
        df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        trades = df[(df['type'].isin([0, 1])) & (df['entry'] == 1)].copy()
        
        trades['hour'] = trades['time'].dt.strftime('%Y-%m-%d %H:00')
        hourly = trades.groupby('hour')['profit'].sum().reset_index()
        hourly['cumulative'] = hourly['profit'].cumsum()
        print('=== CRONOLOGIA DA DESTRUICAO (hora a hora) ===')
        print(hourly.to_string())
        
        print()
        print('=== VOLUME DE TRADES POR HORA ===')
        hourly_count = trades.groupby('hour').size()
        print(hourly_count.to_string())
        
        print()
        print('=== PNL POR ATIVO (24h) ===')
        asset_pnl = trades.groupby('symbol')['profit'].sum().sort_values()
        print(asset_pnl.to_string())
        
        print()
        print('Total trades: ' + str(len(trades)))
        total_pnl = trades['profit'].sum()
        print('Total lucro/perda: USD ' + str(round(total_pnl, 2)))
        
        # Verificar se o kill switch deveria ter ativado
        print()
        print('=== VERIFICACAO DO KILL SWITCH ===')
        acc = mt5.account_info()
        if acc:
            print('Balance atual: USD ' + str(acc.balance))
            print('Equity atual: USD ' + str(acc.equity))
    
    mt5.shutdown()
