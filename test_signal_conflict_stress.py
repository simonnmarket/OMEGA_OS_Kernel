import os
import sys
import numpy as np
import pandas as pd
import time
from collections import defaultdict

# Importando os agentes do O.I.G V3.0
from test_production_profitability import (
    OmegaFractalAgent, OmegaVolumeAgent, OmegaMomentumAgent, 
    OmegaZoneAgent, OmegaRiskAgent, OmegaKalmanPullbackEngine,
    load_xauusd_historical
)

def evaluate_agent_conflict():
    print("=" * 70)
    print("  OMEGA OS: STRESS TEST DE CONFLITO DE SINAIS (TIER-0 MULTI-AGENT)")
    print("=" * 70)
    
    fractal_agent = OmegaFractalAgent()
    volume_agent = OmegaVolumeAgent()
    momentum_agent = OmegaMomentumAgent()
    zone_agent = OmegaZoneAgent()
    risk_agent = OmegaRiskAgent()
    kalman_agent = OmegaKalmanPullbackEngine()
    
    # Carregar dados
    data_path = r"C:\OMEGA_PROJETO\OMEGA_OHLCV_DATA\XAUUSD\XAUUSD_M15.csv"
    market_data, market_times = load_xauusd_historical(data_path)
    
    market_data = market_data[-5000:]
    
    total_len = len(market_data)
    
    stats = {
        "total_evaluated": 0,
        "full_consensus_long": 0,
        "full_consensus_short": 0,
        "high_conflict": 0,   # Metade diz compra, metade diz venda
        "neutral_chaos": 0,   # Maioria neutra/ranging
        "kalman_vs_momentum": 0, # Inversão de polos diretos
        "fractal_vs_volume": 0
    }
    
    start_t = time.time()
    
    print(f"[*] Escaneando {total_len} barras procurando anomalias de decisão e sobreposições...\n")
    
    for i in range(150, total_len):
        window = market_data[i-150:i]
        closes_only = window[:, 0]
        
        # 1. Fractal Bias
        frac_res = fractal_agent.execute(closes_only)
        frac_bias = 0
        if "Trending" in frac_res["regime"] and frac_res["hurst_exponent"] > 0.6:
            # Simplificando a direcao pelo close atual vs media
            media = np.mean(closes_only[-20:])
            frac_bias = 1 if closes_only[-1] > media else -1
            
        # 2. Momentum Bias
        mom_res = momentum_agent.execute(window)
        mom_bias = mom_res["direction"]
        
        # 3. Zone Bias
        zone_res = zone_agent.execute(window, context={"direction": mom_bias if mom_bias != 0 else 1})
        zone_bias = 0
        if zone_res["zone_type"] in ["CORE_STRONG", "CORE_NORMAL"]:
            zone_bias = mom_bias # Segue a tendencia
        elif zone_res["zone_type"] == "EXTREME":
            zone_bias = -mom_bias # Reversao provavel
            
        # 4. Volume Bias
        vol_ctx = {
            "regime": frac_res["regime"], 
            "is_pullback_friendly": frac_res["is_pullback_friendly"],
            "hurst_exponent": frac_res["hurst_exponent"]
        }
        vol_res = volume_agent.execute(window, context=vol_ctx)
        vol_bias = 0
        if vol_res.get("is_pullback", False):
            vol_bias = mom_bias # Confirma a tendencia dps do pullback
        elif vol_res["urgency"] == "CRITICAL":
            vol_bias = -mom_bias # Possivel absorção / reversão
            
        # 5. Kalman Bias
        kalman_res = kalman_agent.execute(window)
        kalman_bias = 0
        if kalman_res["is_kalman_pullback"]:
            kalman_bias = mom_bias # Confirma pulback favorável na direção do momentum
        elif kalman_res["is_structural_break"]:
            kalman_bias = -mom_bias # Quebra diametral oposta
            
        # Avaliar Sobreposições e Conflitos
        signals = [frac_bias, mom_bias, zone_bias, vol_bias, kalman_bias]
        longs = signals.count(1)
        shorts = signals.count(-1)
        neutrals = signals.count(0)
        
        stats["total_evaluated"] += 1
        
        if longs >= 4:
            stats["full_consensus_long"] += 1
        elif shorts >= 4:
            stats["full_consensus_short"] += 1
        elif (longs >= 2 and shorts >= 2):
            stats["high_conflict"] += 1
        elif neutrals >= 3:
            stats["neutral_chaos"] += 1
            
        # Inversão de Polos Estritos
        if (kalman_bias == 1 and mom_bias == -1) or (kalman_bias == -1 and mom_bias == 1):
            stats["kalman_vs_momentum"] += 1
            
        if (frac_bias == 1 and vol_bias == -1) or (frac_bias == -1 and vol_bias == 1):
            stats["fractal_vs_volume"] += 1

    end_t = time.time()
    
    print("[+] STRESS TEST DE POLOS DE DECISÃO CONCLUÍDO ({:.2f}s)".format(end_t - start_t))
    print("-" * 50)
    print(f"Candles validados: {stats['total_evaluated']}")
    print(f"Consenso Forte LONG (>=4 Agentes):  {stats['full_consensus_long']} vezes")
    print(f"Consenso Forte SHORT (>=4 Agentes): {stats['full_consensus_short']} vezes")
    print("-" * 50)
    print(f"⚠️ CONFLITO ALTO (2 Agentes Long vs 2 Agentes Short): {stats['high_conflict']} vezes ({(stats['high_conflict']/stats['total_evaluated'])*100:.1f}%)")
    print(f"🌫 Caos/Mercado Neutro (>3 Agentes Neutros): {stats['neutral_chaos']} vezes ({(stats['neutral_chaos']/stats['total_evaluated'])*100:.1f}%)")
    print("-" * 50)
    print("DIVERGÊNCIAS INDIRETAS (INVERSÃO DE POLOS):")
    print(f"   Kalman (State-Space) vs Momentum: {stats['kalman_vs_momentum']} divergências diretas.")
    print(f"   Fractal vs Volume (Trap/Pullback): {stats['fractal_vs_volume']} divergências diretas.")
    
    conflict_rate = (stats['high_conflict'] / stats['total_evaluated']) * 100
    print("=" * 70)
    if conflict_rate > 15.0:
        print("[ALERTA CRÍTICO] Ocorre SOBRECARGA Lógica! Mais de 15% do mercado os agentes estão brigando entre si.")
    else:
        print("[APROVADO] Baixo índice de conflito de polos. Os módulos atuam de forma SIMBIÓTICA (um complementa o outro).")

if __name__ == "__main__":
    evaluate_agent_conflict()
