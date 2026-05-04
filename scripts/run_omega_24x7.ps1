# OMEGA — arranque 24/7 (MT5 tem de estar aberto e ligado à conta)
# Ajuste OMEGA_24X7_ATIVOS: apenas símbolos que existem no Market Watch (evite LINK se o broker não tiver).
$ErrorActionPreference = "Stop"
Set-Location "C:\OMEGA_QUANTUM_LAB\SOURCE_CODE"
$env:PYTHONPATH = (Get-Location).Path

# Intervalo entre ciclos (segundos)
$env:OMEGA_LOOP_INTERVAL_SEC = "30"

# paper | shadow
$env:OMEGA_24X7_MODE = "paper"

# Portfolio completo: Forex + Metals + Oils + Indices + Crypto (todos com CSVs disponíveis)
$env:OMEGA_24X7_ATIVOS = "EURUSD GBPUSD USDJPY AUDUSD NZDUSD USDCAD USDCHF EURJPY GBPJPY AUDJPY CADJPY CHFJPY XAUUSD XAGUSD UKOIL+ USOIL+ GER40 UK100 US500 BTCUSD ETHUSD SOLUSD BNBUSD LTCUSD XRPUSD ADAUSD AVAXUSD DOGUSD DOTUSD UNIUSD XLMUSD"

python -u scripts/omega_paper_loop_24x7.py `
  --timeframes H1 M15 H4 `
  --equity 10000 `
  --pre-sync-ohlcv
