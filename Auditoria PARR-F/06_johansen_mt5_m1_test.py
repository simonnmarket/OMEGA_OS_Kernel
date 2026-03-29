import pandas as pd
import json
import os
from statsmodels.tsa.vector_ar.vecm import coint_johansen

print("[*] FASE 1: TESTE DE CO-INTEGRAÇÃO (JOHANSEN) - DADOS M1 REAIS (MT5)")

file_xau = "data_lake/XAUUSD_M1_HISTORICO.parquet"
file_xag = "data_lake/XAGUSD_M1_HISTORICO.parquet"

if not os.path.exists(file_xau) or not os.path.exists(file_xag):
    print("❌ Falha: Dados Parquet não encontrados no data_lake.")
    exit(1)

df_xau = pd.read_parquet(file_xau)
df_xag = pd.read_parquet(file_xag)

# Alinhar dados pelo tempo (caso haja furos de liquidez)
df_xau.set_index('time', inplace=True)
df_xag.set_index('time', inplace=True)

df_pair = pd.DataFrame({
    'XAUUSD': df_xau['close'],
    'XAGUSD': df_xag['close']
}).dropna()

print(f"[+] Registros alinhados: {len(df_pair)} barras M1 simultâneas.")

print("[*] Executando Teste de Johansen...")
# det_order=0 (sem constante pre-determinada no vector/trend)
coint_test = coint_johansen(df_pair, det_order=0, k_ar_diff=1)
trace = coint_test.lr1[0]
cv_95 = coint_test.cvt[0, 1]
cointegrated = bool(trace > cv_95)

results = {
    "protocol": "Johansen_M1_Test",
    "data_source": "MetaTrader 5 Literal (M1 Raw)",
    "bars_analyzed": len(df_pair),
    "start_date": str(df_pair.index[0]),
    "end_date": str(df_pair.index[-1]),
    "trace_statistic": float(trace),
    "critical_value_95%": float(cv_95),
    "cointegrated": cointegrated,
    "conclusion": "Ouro e Prata CO-INTEGRADOS no M1" if cointegrated else "Sem cointegração estável nesta janela M1."
}

with open("data_lake/johansen_m1_results.json", "w") as f:
    json.dump(results, f, indent=4)

if cointegrated:
    print(f"✅ SUCESSO! Cointegração validada: Trace={trace:.2f} > CV_95={cv_95:.2f}")
else:
    print(f"❌ FALHA! Não há cointegração: Trace={trace:.2f} < CV_95={cv_95:.2f}")

print("[+] Resultados gravados em data_lake/johansen_m1_results.json")
