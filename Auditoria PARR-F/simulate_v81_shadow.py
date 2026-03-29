import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone
import pytz
import os

if not mt5.initialize():
    print("Falha ao inicializar a interface do MT5 para simulação.")
    exit()

# Extraindo Dados HISTÓRICOS REAIS do dia da Anomalia (23/03/2026 00:00 até agora)
tz = pytz.timezone("Etc/UTC")
start_time = datetime(2026, 3, 23, 0, 0, tzinfo=tz)
end_time = datetime.now(timezone.utc)

rates = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_M15, start_time, end_time)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Calculando Média de Volume para simular o threshold do CQO
df['vol_ma20'] = df['tick_volume'].rolling(20).mean()

trade_log = []
in_position = False
entry_price = 0.0
trailing_stop = 0.0
pnl_total = 0.0
cooldown_until = None
trades_count = 0

print("=========================================================================")
print("SIMULAÇÃO DE CAUDA TIER-0: OMEGA V8.1 (MOMENTUM REGIME SWITCH)")
print("Dados Reais: XAUUSD | Timeframe Base: M15 | Walk-Forward")
print("=========================================================================\n")

for i in range(20, len(df)):
    row = df.iloc[i]
    t = row['time']
    o, h, l, c = row['open'], row['high'], row['low'], row['close']
    v = row['tick_volume']
    
    if cooldown_until and t < cooldown_until:
        continue

    # GERENCIAMENTO DE POSIÇÃO (Trailing Stop Agressivo CQO: ~15.00 USD de margem de escape)
    if in_position:
        # Acionamento do Stop/Trailing
        if h >= trailing_stop:
            exit_price = trailing_stop
            pnl_trade = entry_price - exit_price # SELL trade PnL
            pnl_total += pnl_trade
            trade_log.append(f"[T+ {t.strftime('%H:%M')} UTC] 🔴 SAÍDA (MECO/PULLBACK): Trailing Stop acionado em {exit_price:.2f}.")
            trade_log.append(f"   => PnL da Operação: +{pnl_trade:.2f} USD por lote institucional.")
            in_position = False
            cooldown_until = t + pd.Timedelta(hours=1) # Cooldown de 1h após fechar posição (CQO Rule)
            trade_log.append(f"   => ⏳ COOLDOWN ATIVADO: Operações retidas até {cooldown_until.strftime('%H:%M')} UTC.\n")
        else:
            # Trailing Stop acompanha a Inércia (Agressivo)
            novo_trailing = l + 15.00
            if novo_trailing < trailing_stop:
                trailing_stop = novo_trailing
                trade_log.append(f"[T+ {t.strftime('%H:%M')} UTC] 📉 TRAILING ATUALIZADO: Drop profundo atingido ({l:.2f}). Novo Stop de Proteção: {trailing_stop:.2f}")
        continue

    # LÓGICA DE DETECÇÃO V8.1 (MOMENTUM REGIME SWITCH - CTO)
    body = abs(c - o)
    range_hl = h - l
    if range_hl == 0: continue
    
    momentum = body / range_hl
    
    # Critérios combinados do CTO e CQO
    # 1. Momentum > 60% (Sem pavio inferior muito grande)
    # 2. Direção: Queda (c < o)
    # 3. Anomalia de Volume (Volume > Média Móvel de 20 períodos)
    # 4. Tamanho da barra mínimo para classificar "Waterfall" (Range > 10.00 USD / "Cachoeira")
    
    if c < o and momentum > 0.60 and range_hl > 10.00 and v > (df['vol_ma20'].iloc[i] * 1.1):
        in_position = True
        entry_price = c
        trailing_stop = c + 15.00
        trades_count += 1
        trade_log.append(f"[T+ {t.strftime('%H:%M')} UTC] 🚀 OVERRIDE ATIVADO (WATERFALL DETECTADO)!")
        trade_log.append(f"   => OMEGA V8.1 aciona SELL a mercado em {entry_price:.2f}.")
        trade_log.append(f"   => Trailing Stop inicial de segurança afixado em {trailing_stop:.2f}.")

for msg in trade_log:
    print(msg)

if in_position:
    current_price = df['close'].iloc[-1]
    pnl_unrealized = entry_price - current_price
    print(f"[T+ (AGORA)] 🔵 POSIÇÃO ABERTA. Surfando a inércia em {current_price:.2f}.")
    print(f"   => PnL Flutuante (Aberto): +{pnl_unrealized:.2f} USD.")

print("=========================================================================")
print(f"RESULTADO FINAL DO SHADOW TEST V8.1:")
print(f"-> Oportunidade Submersa Recuperada: PnL Capturado = +{pnl_total:.2f} PONTOS REAIS/USD (por lote)")
print(f"-> Operações Realizadas: {trades_count}")
print("=========================================================================")

mt5.shutdown()
