import MetaTrader5 as mt5
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timezone
import pytz
import os

artifact_dir = r"C:\Users\Lenovo\.gemini\antigravity\brain\f38157c7-ad92-48af-90ff-aabee8b9f71f"
os.makedirs(artifact_dir, exist_ok=True)

if not mt5.initialize():
    print("MT5 Init Failed")
    exit()

tz = pytz.timezone("Etc/UTC")
# Pegar a partir do inicio do dia 23
start_time = datetime(2026, 3, 23, 0, 0, tzinfo=tz)
end_time = datetime.now(timezone.utc)

timeframes = {
    "H4": mt5.TIMEFRAME_H4,
    "H1": mt5.TIMEFRAME_H1,
    "M15": mt5.TIMEFRAME_M15,
    "M5": mt5.TIMEFRAME_M5
}

md_output = ""

for tk, tf in timeframes.items():
    rates = mt5.copy_rates_range("XAUUSD", tf, start_time, end_time)
    if rates is None or len(rates) == 0:
        continue
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    md_output += f"### TABELA DE ATUAÇÃO DOS PREÇOS — XAUUSD ({tk})\n"
    md_output += "| T+ (Mission Time) | Dia/Hora Real | Open | High | Low | Close | Volume | Status/Evento (Data Annotation) |\n"
    md_output += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    start_t = df['time'].iloc[0]
    
    for _, row in df.iterrows():
        t_plus = str(row['time'] - start_t).split("0 days ")[-1] if "0 days" in str(row['time'] - start_t) else str(row['time'] - start_t)
        if t_plus.startswith("00:00:00"): t_plus = "00:00:00"
        
        t_str = row['time'].strftime('%d/%m %H:%M')
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        v = int(row['tick_volume'])
        
        # Annotations aerospaciais baseados no M15 / H1
        evento = "Nominal"
        
        if tk == "H1":
            if row['time'].hour in [1,2,3]: evento = "Órbita Inicial (Queda Estrutural)"
            if row['time'].hour in [5,6,7]: evento = "Micro-Correção de Voo (Lateralização)"
            elif row['time'].hour in [8,9]: evento = "Perda de Pressão Nível 1 e 2"
            elif row['time'].hour == 10: evento = "MAX Q (Estresse Estrutural Extremo / Fundo 4098)"
            elif row['time'].hour == 11: evento = "MECO (Absorção e Defesa. Ignition de Compra)"
            elif row['time'].hour > 11: evento = "Manobra RCS (Correção de Rota Vertical Altista)"
        
        elif tk == "M15" or tk == "M5":
            if row['time'].hour == 11 and row['time'].minute == 0:
                evento = "IGNITION SEQUENCE START"
            elif row['time'].hour == 10 and row['time'].minute in [30, 45]:
                evento = "CRITICAL PRESSURE DROP"
            
        md_output += f"| T+{t_plus} | {t_str} | {o:.2f} | {h:.2f} | {l:.2f} | {c:.2f} | {v} | {evento} |\n"
    md_output += "\n"

with open(os.path.join(artifact_dir, "telemetry_tables.md"), "w", encoding='utf-8') as f:
    f.write(md_output)

# Visuals (Line chart and Candles for H1)
rates_h1 = mt5.copy_rates_range("XAUUSD", mt5.TIMEFRAME_H1, start_time, end_time)
df_h1 = pd.DataFrame(rates_h1)
df_h1['time'] = pd.to_datetime(df_h1['time'], unit='s')

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(16, 8))

# Linha de tendência
ax.plot(df_h1['time'], df_h1['close'], marker='o', linestyle='-', color='cyan', linewidth=2, markersize=6, label='Preço (Close/Telemetry)')

# Anotações de Dados (Callouts Específicos)
for _, row in df_h1.iterrows():
    if row['time'].hour == 11:
        ax.annotate(f"MECO / DEFESA\nO: 4204.33\nH: 4270.53", 
                    xy=(row['time'], row['close']), xytext=(row['time'], row['close'] + 80),
                    arrowprops=dict(facecolor='lime', shrink=0.05, width=2, headwidth=8),
                    fontsize=10, ha='center', bbox=dict(boxstyle="round,pad=0.3", fc="green", ec="lime", lw=2, alpha=0.7))
    elif row['time'].hour == 10:
        ax.annotate(f"MAX Q (STRESS)\nL: 4098.91", 
                    xy=(row['time'], row['low']), xytext=(row['time'], row['low'] - 80),
                    arrowprops=dict(facecolor='red', shrink=0.05, width=2, headwidth=8),
                    fontsize=10, ha='center', bbox=dict(boxstyle="round,pad=0.3", fc="darkred", ec="red", lw=2, alpha=0.7))

ax.set_title("HUD de Telemetria XAUUSD (H1) - Análise de Eventos Discretos NASA/WFF", fontsize=18, color='white', pad=20)
ax.set_xlabel("Relógio da Missão (Tempo Real UTC)", fontsize=12)
ax.set_ylabel("Pressão/Altitude (Preço USD)", fontsize=12)

ax.grid(True, linestyle='--', color='gray', alpha=0.5)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# Linhas de grade finas para blocos de 6 horas
for i in range(0, 24, 6):
    val = datetime(2026, 3, 23, i, 0)
    if val >= df_h1['time'].iloc[0] and val <= df_h1['time'].iloc[-1]:
        ax.axvline(x=val, color='white', linestyle=':', alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(artifact_dir, "XAUUSD_Telemetry_Line.png"), dpi=300)
plt.close()

# Gerar Gráfico de Candles simples
fig2, ax2 = plt.subplots(figsize=(16, 8))
up = df_h1[df_h1.close >= df_h1.open]
down = df_h1[df_h1.close < df_h1.open]

width = 0.02
width2 = 0.002

ax2.bar(up.time, up.close - up.open, width, bottom=up.open, color='lime')
ax2.bar(up.time, up.high - up.close, width2, bottom=up.close, color='lime')
ax2.bar(up.time, up.open - up.low, width2, bottom=up.low, color='lime')

ax2.bar(down.time, down.close - down.open, width, bottom=down.open, color='red')
ax2.bar(down.time, down.high - down.open, width2, bottom=down.open, color='red')
ax2.bar(down.time, down.close - down.low, width2, bottom=down.low, color='red')

ax2.annotate("DEFESA INSTITUCIONAL", xy=(df_h1[df_h1['time'].dt.hour == 11]['time'].iloc[0], 4204), 
             xytext=(df_h1[df_h1['time'].dt.hour == 11]['time'].iloc[0], 4100),
             arrowprops=dict(facecolor='yellow', shrink=0.05), color='yellow', fontsize=12, ha='center')

ax2.set_title("Flight Data Recorder (Candlestick) XAUUSD - Missão 23/03/2026", fontsize=18, color='white')
ax2.grid(True, linestyle=':', color='gray', alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
plt.tight_layout()
plt.savefig(os.path.join(artifact_dir, "XAUUSD_Telemetry_Candle.png"), dpi=300)
plt.close()

mt5.shutdown()
print("Relatórios e Gráficos gerados com sucesso.")
