"""
omega_export_htf.py — Export H1/H4/D1 usando copy_rates_from_pos
Solução: copiar por POSIÇÃO (últimas N barras) em vez de por data.
O broker limita histórico por data em M1/M5 mas não por posição em H1+.
"""
import MetaTrader5 as mt5
import pandas as pd
import os
from pathlib import Path

OUTPUT_DIR = Path(r"c:\Users\Lenovo\.gemini\antigravity\playground\nebular-kuiper\OHLCV_DATA")

SYMBOLS = [
    'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD',
    'GER40', 'US30', 'US100', 'US500',
    'XAGUSD', 'USOIL+', 'BTCUSD',
]

# H1/H4/D1 com máximo de barras por posição
TIMEFRAMES_HTF = {
    'H1':  (mt5.TIMEFRAME_H1,  99999),   # pedir tudo disponível
    'H4':  (mt5.TIMEFRAME_H4,  99999),
    'D1':  (mt5.TIMEFRAME_D1,  99999),
}

def main():
    if not mt5.initialize():
        print(f"ERRO: MT5 nao inicializado: {mt5.last_error()}")
        return

    acc = mt5.account_info()
    print("=" * 65)
    print(f"  OMEGA — EXPORT H1/H4/D1 (copy_rates_from_pos)")
    print(f"  Conta: {acc.login} | Output: {OUTPUT_DIR}")
    print("=" * 65)

    total_bars = 0
    for symbol in SYMBOLS:
        if not mt5.symbol_select(symbol, True):
            print(f"  [SKIP] {symbol}")
            continue

        sym_dir = OUTPUT_DIR / symbol
        sym_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n  [{symbol}]")

        for tf_name, (tf_mt5, count) in TIMEFRAMES_HTF.items():
            # copy_rates_from_pos: posição 0 = barra mais recente, N = todas
            rates = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, count)
            if rates is None or len(rates) == 0:
                print(f"    {tf_name:4s}: SEM DADOS ({mt5.last_error()})")
                continue

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.rename(columns={'tick_volume': 'volume'})
            cols = [c for c in ['time','open','high','low','close','volume'] if c in df.columns]
            df = df[cols]

            filepath = sym_dir / f"{symbol}_{tf_name}.csv"
            df.to_csv(filepath, index=False, float_format='%.6f')
            total_bars += len(df)
            t_start = df['time'].iloc[0].strftime('%Y-%m-%d')
            t_end   = df['time'].iloc[-1].strftime('%Y-%m-%d')
            print(f"    {tf_name:4s}: {len(df):>7,} barras | {t_start} → {t_end}")

    mt5.shutdown()
    print(f"\n{'='*65}")
    print(f"  CONCLUÍDO — {total_bars:,} barras exportadas (H1/H4/D1)")
    print(f"  Próximo: python omega_calib_run.py")
    print("=" * 65)

if __name__ == '__main__':
    main()
