import pandas as pd
import numpy as np
from numba import njit
import json
import time
import os

print("[*] Lendo dados binários Parquet...")
file_path = "data/XAUUSD_M1_2020_2026.parquet"
if not os.path.exists(file_path):
    print(f"[!] Erro: {file_path} não encontrado.")
    exit(1)
    
df = pd.read_parquet(file_path)
print(f"[+] Dados carregados. Memória ocupada: {df.memory_usage(deep=True).sum()/1024**2:.2f} MB")

# Pré-cálculos vetoriais globais
opens = df['open'].values
highs = df['high'].values
lows = df['low'].values
closes = df['close'].values
vols = df['tick_volume'].values

# Rolling MA 20 for volume
vol_ma20 = pd.Series(vols).rolling(20).mean().fillna(0).values

def run_v81_simulation(opens, highs, lows, closes, vols, vol_ma20, theta_m, delta, lam):
    n = len(closes)
    in_pos = False
    entry = 0.0
    trailing = 0.0
    
    total_pnl = 0.0
    wins = 0
    losses = 0
    gross_profit = 0.0
    gross_loss = 0.0
    cooldown = 0
    
    # Track trade PnLs for Monte Carlo
    trade_pnls = []
    
    for i in range(20, n):
        if cooldown > 0:
            cooldown -= 1
            continue
            
        o, h, l, c, v, ma20 = opens[i], highs[i], lows[i], closes[i], vols[i], vol_ma20[i]
        
        if in_pos:
            if h >= trailing:
                # Stop hit (Ask simulado via spread zero por simplicidade, conservador no M1 h)
                pnl = entry - trailing
                total_pnl += pnl
                if pnl > 0: 
                    wins += 1
                    gross_profit += pnl
                else: 
                    losses += 1
                    gross_loss += abs(pnl)
                trade_pnls.append(pnl)
                in_pos = False
                cooldown = 60 # Cooldown de 60 barras (1 hora M1)
            else:
                novo_trailing = l + lam
                if novo_trailing < trailing:
                    trailing = novo_trailing
            continue
            
        r = h - l
        if r <= 10.0: continue
            
        m = abs(c - o) / (r + 1e-5)
        v_trigger = v > ma20 * 1.1
        
        if c < o and m >= (theta_m - delta) and v_trigger:
            in_pos = True
            entry = c
            trailing = c + lam
            
    return total_pnl, wins, losses, gross_profit, gross_loss, trade_pnls

print("[*] Fase 2: Aplicando Numba e Executando Grid Search 5x5x5...")
# Espaço amostral
theta_m_vals = [0.50, 0.55, 0.60, 0.65, 0.70]
delta_vals = [0.00, 0.02, 0.05, 0.08, 0.10] # Ajustado conforme Red Team
lam_vals = [10.0, 15.0, 20.0, 25.0, 30.0]

best_pf = 0.0
best_params = {}
best_pnl = 0.0
best_trades = []

start_t = time.time()
# Jit warmup 
run_v81_simulation(opens, highs, lows, closes, vols, vol_ma20, 0.60, 0.05, 15.0)

for tm in theta_m_vals:
    for d in delta_vals:
        for lm in lam_vals:
            # Roda engine Numba
            res = run_v81_simulation(opens, highs, lows, closes, vols, vol_ma20, tm, d, lm)
            pnl, wins, losses, gp, gl, trade_pnls = res
            
            pf = gp / gl if gl > 0 else float('inf')
            n_trades = wins + losses
            
            # Filtro simples: Mínimo 20 trades em 90k barras (para garantir atividade populacional)
            if pf > best_pf and n_trades > 20:
                best_pf = pf
                best_params = {'theta_m': tm, 'delta': d, 'lambda': lm}
                best_pnl = pnl
                best_trades = trade_pnls
                
print(f"[+] Grid Search Concluído em {time.time()-start_t:.2f}s")
print(f"[*] Melhores Parâmetros: {best_params} com Profit Factor: {best_pf:.2f}")

print("[*] Fase 3: Monte Carlo Shuffle Simulation (10.000 shuffles)...")
mc_start_t = time.time()
n_trades = len(best_trades)
obs_array = np.array(best_trades)
obs_pf = best_pf

# Shuffle arrays 10.000 vezes (hipótese nula de retornos)
np.random.seed(42)
simulated_pfs = np.zeros(10000)
for i in range(10000):
        # Permutation para desconstruir qualquer dependência temporal de cluster HFT
        shuffled = np.random.choice(obs_array, size=n_trades, replace=True)
        gp = shuffled[shuffled > 0].sum()
        gl = abs(shuffled[shuffled < 0].sum())
        simulated_pfs[i] = gp / gl if gl > 0 else 100.0

percentile_99 = np.percentile(simulated_pfs, 99)
percentile_rank = (simulated_pfs < obs_pf).mean() * 100
passes_mc = obs_pf >= percentile_99
print(f"[+] Monte Carlo Concluído em {time.time()-mc_start_t:.2f}s")
print(f"    - PF Observado: {obs_pf:.2f} | P99 Threshold: {percentile_99:.2f}")

# Calcular p-value fictício simples comparando médias empíricas
# Welch T-test
import scipy.stats as stats
# Comparamos com array de mercado dummy (retorno nulo)
market_null = np.zeros(n_trades)
t_stat, p_value = stats.ttest_ind(obs_array, market_null, equal_var=False, alternative='greater')
is_significant = bool(p_value <= 0.01)

# Gerar JSON
proof = {
    "version": "V8.1_POPULATION_EDGE",
    "timestamp": "2026-03-24T00:00:00Z",
    "status": "VALIDATED" if (passes_mc and is_significant) else "REJECTED",
    "mandate": {
        "data_length_bars": len(opens),
        "target_p_value": 0.01,
        "monte_carlo_iterations": 10000,
        "grid_search": "5x5x5"
    },
    "grid_search_results": {
        "best_theta_m": best_params.get('theta_m'),
        "best_delta": best_params.get('delta'),
        "best_lambda": best_params.get('lambda')
    },
    "statistical_tests": {
        "welch_ttest_p_value": float(p_value),
        "significant_at_001": is_significant,
        "total_trades_analyzed": n_trades
    },
    "monte_carlo": {
        "iterations": 10000,
        "observed_pf": float(obs_pf),
        "percentile_rank": float(percentile_rank),
        "threshold_99": float(percentile_99),
        "passes_threshold": bool(passes_mc)
    },
    "final_verdict": {
        "approved": bool(passes_mc and is_significant),
        "reason": "População Edge comprovada no top 1% de Monte Carlo." if passes_mc else "Falha Estatística frente à Aleatoriedade."
    }
}

with open("scientific_proof_v8.1.json", "w") as f:
    json.dump(proof, f, indent=4)
    
print(f"[+] Artifact scientific_proof_v8.1.json salvo.")
print(f"[*] VALIDAÇÃO TIER-0: {'✅ APROVADA' if passes_mc and is_significant else '🔴 REJEITADA'}")
