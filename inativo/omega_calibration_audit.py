import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def run_full_calibration_audit():
    if not mt5.initialize():
        print('Falha MT5')
        return None

    # EXTRAIR TUDO desde o inicio da operacao OMEGA (3 dias completos)
    from_date = datetime.now() - timedelta(days=4)
    to_date = datetime.now()
    deals = mt5.history_deals_get(from_date, to_date)
    orders = mt5.history_orders_get(from_date, to_date)

    if not deals:
        print('Sem dados')
        return

    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Entradas e Saidas
    entries = df[df['entry'] == 0].copy()
    exits = df[(df['type'].isin([0, 1])) & (df['entry'] == 1)].copy()
    
    exits['hour'] = exits['time'].dt.hour
    exits['day'] = exits['time'].dt.strftime('%Y-%m-%d')
    exits['session'] = exits['hour'].apply(lambda h: 
        'Asiatica(00-08)' if 0 <= h < 8 else 
        'Londres(08-13)' if 8 <= h < 13 else
        'NewYork(13-20)' if 13 <= h < 20 else 'Noturna(20-24)')
    
    
    print("=" * 80)
    print("OMEGA FUND: AUDITORIA DE CALIBRAGEM - TODOS OS ATIVOS (4 DIAS)")
    print("=" * 80)
    
    acc = mt5.account_info()
    if acc:
        print(f"\nSaldo Actual: USD {acc.balance:.2f}")
        print(f"Equity Actual: USD {acc.equity:.2f}")

    print("\n" + "=" * 80)
    print("ANALISE POR ATIVO: PNL, WIN RATE, HORARIO IDEAL, SESSAO IDEAL")
    print("=" * 80)
    
    results = {}
    all_symbols = exits['symbol'].unique()
    
    for sym in sorted(all_symbols):
        sym_df = exits[exits['symbol'] == sym].copy()
        if len(sym_df) < 5:
            continue
            
        total_pnl = sym_df['profit'].sum()
        wins = sym_df[sym_df['profit'] > 0]
        losses = sym_df[sym_df['profit'] < 0]
        win_rate = len(wins) / len(sym_df) * 100 if len(sym_df) > 0 else 0
        avg_win = wins['profit'].mean() if len(wins) > 0 else 0
        avg_loss = losses['profit'].mean() if len(losses) > 0 else 0
        profit_factor = abs(wins['profit'].sum() / losses['profit'].sum()) if losses['profit'].sum() != 0 else 999
        
        # Melhor hora do dia para este ativo
        hourly = sym_df.groupby('hour')['profit'].sum()
        best_hour = hourly.idxmax() if not hourly.empty else 'N/A'
        worst_hour = hourly.idxmin() if not hourly.empty else 'N/A'
        
        # Melhor sessao
        session_pnl = sym_df.groupby('session')['profit'].sum()
        best_session = session_pnl.idxmax() if not session_pnl.empty else 'N/A'
        
        # Dias positivos vs negativos
        daily_pnl = sym_df.groupby('day')['profit'].sum()
        positive_days = (daily_pnl > 0).sum()
        
        # Direcao predominante (BUY=0, SELL=1)
        buy_pnl = sym_df[sym_df['type'] == 0]['profit'].sum()
        sell_pnl = sym_df[sym_df['type'] == 1]['profit'].sum()
        dominant_dir = 'BUY' if buy_pnl > sell_pnl else 'SELL'
        dominant_pnl = max(buy_pnl, sell_pnl)
        
        results[sym] = {
            'total_pnl': total_pnl,
            'trades': len(sym_df),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'best_hour': best_hour,
            'worst_hour': worst_hour,
            'best_session': best_session,
            'dominant_direction': dominant_dir,
            'buy_pnl': buy_pnl,
            'sell_pnl': sell_pnl
        }
        
        status = "VENCEDOR" if total_pnl > 0 else "SANGRADOR"
        print(f"\n[{status}] {sym}")
        print(f"  PNL Total:        USD {total_pnl:,.2f}")
        print(f"  Total Trades:     {len(sym_df)}")
        print(f"  Win Rate:         {win_rate:.1f}%")
        print(f"  Profit Factor:    {profit_factor:.2f}")
        print(f"  Avg Win:          ${avg_win:.2f} | Avg Loss: ${avg_loss:.2f}")
        print(f"  Melhor Hora UTC:  {best_hour}H | Pior Hora UTC: {worst_hour}H")
        print(f"  Melhor Sessao:    {best_session}")
        print(f"  Dir. Dominante:   {dominant_dir} (Buy PNL: ${buy_pnl:.2f} | Sell PNL: ${sell_pnl:.2f})")

    print("\n" + "=" * 80)
    print("ANALISE POR ESTRATEGIA (MAGIC NUMBER = QUAL NUCLEO EXECUTOU)")
    print("=" * 80)
    
    # Magic numbers: 999111=Scale1, 999112=Scale2, 999113=Scale3
    magic_map = {
        999111: 'OMEGA_SCALE_Lote1 (Entrada Principal)',
        999112: 'OMEGA_SCALE_Lote2 (Confirmacao)',
        999113: 'OMEGA_SCALE_Lote3 (Momentum/Surf)',
        789012: 'BREAK_EVEN_Manager (PositionManager)',
        999999: 'Outros/Manual'
    }
    
    exits['strategy'] = exits['magic'].map(magic_map).fillna('Magic_' + exits['magic'].astype(str))
    strategy_pnl = exits.groupby('strategy').agg(
        pnl=('profit', 'sum'),
        trades=('profit', 'count'),
        avg_pnl=('profit', 'mean')
    ).sort_values(by='pnl', ascending=False)
    
    print(strategy_pnl.to_string())

    print("\n" + "=" * 80)
    print("RANKING DE ATIVOS PARA CALIBRAGEM (PRIORIDADE)")
    print("=" * 80)
    
    ranked = sorted(results.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
    print(f"\n{'ATIVO':<12} {'PNL TOTAL':>12} {'WIN RATE':>10} {'PROF.FACT':>10} {'MELHOR HR':>10} {'DIR':>6} {'DECISAO'}")
    print("-" * 80)
    for sym, r in ranked:
        decisao = "CALIBRAR AGORA" if r['profit_factor'] > 1.0 else "SUSPENDER"
        print(f"{sym:<12} ${r['total_pnl']:>11,.2f} {r['win_rate']:>9.1f}% {r['profit_factor']:>10.2f} {str(r['best_hour'])+'H UTC':>10} {r['dominant_direction']:>6} {decisao}")
    
    mt5.shutdown()
    print("\nAUDITORIA CONCLUIDA.")

if __name__ == '__main__':
    run_full_calibration_audit()
