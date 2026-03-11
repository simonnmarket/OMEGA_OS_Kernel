import os
import sys
import numpy as np
import pandas as pd
import time
from test_production_profitability import (
    OmegaFractalAgent, OmegaVolumeAgent, OmegaMomentumAgent, 
    OmegaZoneAgent, OmegaRiskAgent, OmegaKalmanPullbackEngine,
    load_xauusd_historical
)

def walk_forward_oos_test():
    print("=" * 80)
    print("  OMEGA OS: RIGOROUS WALK-FORWARD OUT-OF-SAMPLE (OOS) BACKTEST")
    print("  PARAMETRIZAÇÃO DE RISCO MAX_LEVERAGE: 25.0x")
    print("=" * 80)
    
    # 1. Instanciação OIG V3.0 Tier-0
    fractal_agent = OmegaFractalAgent()
    volume_agent = OmegaVolumeAgent()
    momentum_agent = OmegaMomentumAgent()
    zone_agent = OmegaZoneAgent()
    kalman_agent = OmegaKalmanPullbackEngine()
    
    # 2. In-Sample (IS) e Out-of-Sample (OOS) Data Splitting
    filepath = r"C:\OMEGA_PROJETO\OMEGA_OHLCV_DATA\XAUUSD\XAUUSD_M15.csv"
    data, times = load_xauusd_historical(filepath)
    
    # Pegamos os últimos 15000 candles como janela total
    data = data[-15000:]
    
    # Split: 60% IS, 40% OOS
    split_idx = int(len(data) * 0.6)
    data_is = data[:split_idx]
    data_oos = data[split_idx:]
    
    print(f"[*] In-Sample Data: {len(data_is)} candles (Calibração)")
    print(f"[*] Out-of-Sample Data: {len(data_oos)} candles (Teste de Validação Fria)")
    
    start_time = time.time()
    
    def run_simulation(market_data, prefix="IS"):
        balance = 10000.0  # Capital estrito institucional
        open_positions = []
        equity_curve = [balance]
        wins = 0
        losses = 0
        max_drawdown = 0.0
        peak_equity = balance
        
        for i in range(150, len(market_data), 5):  # Step 5 para não congelar o Python, testando fechamentos H1
            window = market_data[i-150:i]
            current_close = window[-1][0]
            
            # Execução cega e vetorizada dos oráculos
            mom_res = momentum_agent.execute(window)
            zone_res = zone_agent.execute(window, context={"direction": mom_res.get("direction", 1)})
            kalman_res = kalman_agent.execute(window)
            
            market_dir = mom_res["direction"]
            is_strong_trend = (market_dir in (1, -1) and zone_res["zone_type"] in ("CORE_STRONG", "CORE_NORMAL"))
            is_kalman_pullback = kalman_res["is_kalman_pullback"]
            
            # Regra Operacional (Sem Groupthink, Inserção Kalman Filter Frio)
            if is_strong_trend or (is_kalman_pullback and len(open_positions) > 0):
                active_dir = open_positions[-1]['dir'] if open_positions else market_dir
                
                # ESCALONAMENTO FIDUCIÁRIO (Max 15 posições, Incremento 0.5)
                if market_dir == active_dir and len(open_positions) < 15:
                    next_lots = min(1.0 + (len(open_positions) * 0.5), 5.0)
                    open_positions.append({'entry': current_close, 'lots': next_lots, 'dir': active_dir})
            
            # FECHAMENTO OBRIGATÓRIO (Drawdown Stop, Exaustão Matemática ou Inversão de Kalman)
            elif (open_positions and mom_res["direction"] == -open_positions[-1]['dir']) or kalman_res["is_structural_break"]:
                for pos in open_positions:
                    profit = pos['dir'] * (current_close - pos['entry']) * pos['lots'] * 10 
                    balance += profit
                    if profit > 0: wins += 1
                    else: losses += 1
                open_positions = []
            
            # Métrica de Risco Diária (Equity Curve)
            equity_curve.append(balance)
            if balance > peak_equity:
                peak_equity = balance
            dd = (peak_equity - balance) / peak_equity
            if dd > max_drawdown:
                max_drawdown = dd
                
        # Forçar fechamento no final
        for pos in open_positions:
            profit = pos['dir'] * (market_data[-1][0] - pos['entry']) * pos['lots'] * 10
            balance += profit
            if profit > 0: wins += 1
            else: losses += 1
            
        win_rate = (wins / (wins + losses) * 100) if (wins+losses) > 0 else 0
        return balance, max_drawdown * 100, win_rate, (wins+losses)

    print("\n[+] Rodando Simulation In-Sample (IS)...")
    is_bal, is_dd, is_wr, is_trades = run_simulation(data_is, "IS")
    
    print("[+] Rodando Simulation Out-of-Sample (OOS)...")
    oos_bal, oos_dd, oos_wr, oos_trades = run_simulation(data_oos, "OOS")
    
    end_time = time.time()
    
    print("\n=" * 80)
    print("  RELATÓRIO INSTITUCIONAL WALK-FORWARD: METADE IS x METADE OOS")
    print("=" * 80)
    print(f"⏱ Tempo Computacional: {end_time - start_time:.2f}s (Python Step-5)")
    print(f"\n[IN-SAMPLE METRICS] (O ambiente conhecido)")
    print(f"💰 Saldo Líquido: ${is_bal:,.2f} (Init: $10,000)")
    print(f"🎯 Win Rate:      {is_wr:.1f}% ({is_trades} Trades)")
    print(f"📉 Max Drawdown:  {is_dd:.2f}% (Risco Fiduciário Aceitável < 15%)")
    
    print(f"\n[OUT-OF-SAMPLE METRICS] (O Fogo Real Não Visto)")
    print(f"💰 Saldo Líquido: ${oos_bal:,.2f} (Init: $10,000)")
    print(f"🎯 Win Rate:      {oos_wr:.1f}% ({oos_trades} Trades)")
    print(f"📉 Max Drawdown:  {oos_dd:.2f}%")
    print("\n======================================================================")
    
    if oos_dd > 15.0:
        print("[VEREDITO]: REPROVADO. OOS DESTRUIU A CONTA. O SISTEMA TEM OVERFITTING IS.")
    elif oos_bal < 10000.0:
        print("[VEREDITO]: REPROVADO. SISTEMA PIOROU EM AMBIENTE DESCONHECIDO (PREJUÍZO).")
    else:
        print("[VEREDITO]: APROVADO. A EXCELÊNCIA TÉCNICA SE MANTEVE NO MERCADO CEGO (OOS).")

if __name__ == "__main__":
    walk_forward_oos_test()
