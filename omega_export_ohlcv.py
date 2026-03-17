"""
omega_export_ohlcv.py — Export OHLCV Histórico Completo para Calibração
VERSÃO NOITE: exporta máximo histórico disponível no MT5 (até 2 anos)
Output: C:\OMEGA_PROJETO\OMEGA_OHLCV_DATA\Arquivo 1\ (estrutura compatível com volume_calibrate.py)
"""
import MetaTrader5 as mt5
import pandas as pd
import os
from datetime import datetime, timedelta, timezone

# ── Destino: pasta do volume_calibrate (estrutura já existente) ──────────────
OUTPUT_DIR = r"C:\OMEGA_PROJETO\OMEGA_OHLCV_DATA\Arquivo 1"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Ativos prioritários (XAUUSD primeiro) ────────────────────────────────────
SYMBOLS = [
    'XAUUSD',                                              # Prioridade 1 — core
    'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD',               # Forex major
    'GER40', 'US30', 'US100', 'US500',                     # Índices
    'XAGUSD', 'USOIL+', 'BTCUSD',                         # Outros
]

# ── Timeframes para calibração multi-camada ───────────────────────────────────
TIMEFRAMES = {
    'M1':  mt5.TIMEFRAME_M1,   # Camada 1: microestrutura HFT
    'M5':  mt5.TIMEFRAME_M5,   # Camada 1: fluxo direcional curto
    'M15': mt5.TIMEFRAME_M15,  # Camada 2: sinal principal OMEGA
    'H1':  mt5.TIMEFRAME_H1,   # Camada 2: regime intra-dia
    'H4':  mt5.TIMEFRAME_H4,   # Camada 3: macro direcional
    'D1':  mt5.TIMEFRAME_D1,   # Camada 3: contexto semanal
}

# ── Período: máximo histórico disponível (2 anos) ─────────────────────────────
TO_DATE   = datetime.now(timezone.utc)
FROM_DATE = TO_DATE - timedelta(days=730)  # 2 anos

# Contadores para relatório final
STATS = {'files': 0, 'bars_total': 0, 'skipped': [], 'errors': []}


def extract_and_save(symbol: str, tf_name: str, tf_mt5: int) -> dict:
    rates = mt5.copy_rates_range(symbol, tf_mt5, FROM_DATE, TO_DATE)
    if rates is None or len(rates) == 0:
        err = mt5.last_error()
        return {'status': 'NO_DATA', 'bars': 0, 'error': str(err)}

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.rename(columns={'tick_volume': 'volume'})

    cols = ['time', 'open', 'high', 'low', 'close', 'volume']
    available = [c for c in cols if c in df.columns]
    df = df[available]

    sym_dir = os.path.join(OUTPUT_DIR, symbol)
    os.makedirs(sym_dir, exist_ok=True)
    filepath = os.path.join(sym_dir, f"{symbol}_{tf_name}.csv")
    df.to_csv(filepath, index=False, float_format='%.6f')

    return {
        'status': 'OK',
        'bars':   len(df),
        'from':   df['time'].iloc[0].strftime('%Y-%m-%d'),
        'to':     df['time'].iloc[-1].strftime('%Y-%m-%d'),
        'file':   filepath,
    }


def main():
    if not mt5.initialize():
        print(f"ERRO: MT5 não inicializado: {mt5.last_error()}")
        return

    acc = mt5.account_info()
    print("=" * 70)
    print("  OMEGA — EXPORT OHLCV HISTÓRICO COMPLETO (modo noite)")
    print(f"  Conta: {acc.login} | Server: {acc.server}")
    print(f"  Período: {FROM_DATE.strftime('%Y-%m-%d')} → {TO_DATE.strftime('%Y-%m-%d')} (até 2 anos)")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Ativos: {len(SYMBOLS)} | Timeframes: {len(TIMEFRAMES)}")
    print(f"  Total combinações: {len(SYMBOLS) * len(TIMEFRAMES)}")
    print("=" * 70)

    summary = []
    combo_total = len(SYMBOLS) * len(TIMEFRAMES)
    combo_done  = 0

    for symbol in SYMBOLS:
        if not mt5.symbol_select(symbol, True):
            print(f"\n  [SKIP] {symbol}: não encontrado na corretora")
            STATS['skipped'].append(symbol)
            combo_done += len(TIMEFRAMES)
            continue

        print(f"\n  [{symbol}]")
        for tf_name, tf_mt5 in TIMEFRAMES.items():
            combo_done += 1
            pct = combo_done / combo_total * 100
            result = extract_and_save(symbol, tf_name, tf_mt5)

            if result['status'] == 'OK':
                n = result['bars']
                STATS['files']      += 1
                STATS['bars_total'] += n
                print(f"    {tf_name:4s}: {n:>7,} barras | {result['from']} → {result['to']}  [{pct:.0f}%]")
                summary.append({
                    'symbol': symbol, 'timeframe': tf_name,
                    'bars': n, 'from': result['from'], 'to': result['to'],
                    'file': result['file']
                })
            else:
                print(f"    {tf_name:4s}: SEM DADOS ({result.get('error', '')})")
                STATS['errors'].append(f"{symbol}/{tf_name}")

    # ── Índice master ─────────────────────────────────────────────────────────
    if summary:
        idx_df = pd.DataFrame(summary)
        idx_path = os.path.join(OUTPUT_DIR, "_INDEX.csv")
        idx_df.to_csv(idx_path, index=False)

    mt5.shutdown()

    # ── Relatório final ───────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  EXPORT CONCLUÍDO")
    print(f"  Ficheiros gerados:  {STATS['files']}")
    print(f"  Barras totais:      {STATS['bars_total']:,}")
    if STATS['skipped']:
        print(f"  Símbolos skip:      {', '.join(STATS['skipped'])}")
    if STATS['errors']:
        print(f"  Sem dados ({len(STATS['errors'])}):    {', '.join(STATS['errors'][:5])}")
    print()
    print("  PRÓXIMO PASSO:")
    print("  python omega_calib_run.py   ← calibração XAUUSD com dados completos")
    print("=" * 70)


if __name__ == '__main__':
    main()
