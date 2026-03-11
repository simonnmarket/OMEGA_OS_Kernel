import os
import glob
import time
import pandas as pd
import numpy as np
from test_production_profitability import (
    OmegaFractalAgent, OmegaVolumeAgent, OmegaMomentumAgent, 
    OmegaZoneAgent, OmegaKalmanPullbackEngine, load_xauusd_historical
)

def run_multi_pair_validation():
    print("=" * 80)
    print("  OMEGA OS: VALIDAÇÃO HISTÓRICA MULTI-ATIVO TIER-0 (M15)")
    print("  DADOS REAIS | ALAVANCAGEM: 25.0x | AUDITORIA DE RUÍNA")
    print("=" * 80)
    
    fractal_agent = OmegaFractalAgent()
    momentum_agent = OmegaMomentumAgent()
    zone_agent = OmegaZoneAgent()
    kalman_agent = OmegaKalmanPullbackEngine()
    
    base_dir = r"C:\OMEGA_PROJETO\OMEGA_OHLCV_DATA"
    
    # Listar todos os arquivos M15 encontrados nos subdiretorios
    search_pattern = os.path.join(base_dir, "*", "*_M15.csv")
    m15_files = glob.glob(search_pattern)
    
    results = []
    
    print(f"[*] Encontrados {len(m15_files)} ativos com granularidade M15 para Auditoria.\n")
    
    for filepath in m15_files:
        asset_name = os.path.basename(os.path.dirname(filepath))
        print(f"[*] Auditando ativo: {asset_name} ...", end=" ", flush=True)
        
        try:
            data, times = load_xauusd_historical(filepath)
            # Para testes multimoeda mais ageis, pegamos no máximo as últimas 10k barras se for muito grande
            # Mas como o usuário quer os dados reais completos, vamos avaliar tudo.
            # Se for muito pesado, o script pode demorar, mas faremos o full scan com step de 5
            total_bars = len(data)
            
            balance = 10000.0
            open_positions = []
            peak_equity = balance
            max_drawdown = 0.0
            wins = 0
            losses = 0
            
            start_time = time.time()
            
            for i in range(150, total_bars, 5): 
                window = data[i-150:i]
                current_close = window[-1][0]
                
                mom_res = momentum_agent.execute(window)
                zone_res = zone_agent.execute(window, context={"direction": mom_res.get("direction", 1)})
                kalman_res = kalman_agent.execute(window)
                
                market_dir = mom_res["direction"]
                is_strong_trend = (market_dir in (1, -1) and zone_res["zone_type"] in ("CORE_STRONG", "CORE_NORMAL"))
                
                if is_strong_trend or (kalman_res["is_kalman_pullback"] and len(open_positions) > 0):
                    active_dir = open_positions[-1]['dir'] if open_positions else market_dir
                    if market_dir == active_dir and len(open_positions) < 15:
                        next_lots = min(1.0 + (len(open_positions) * 0.5), 5.0)
                        can_add = True
                        if open_positions:
                            # Uma heuristica crua: 0.1% de diferenca do preco para novas entradas parciais
                            last_entry = open_positions[-1]['entry']
                            if active_dir == 1 and current_close < last_entry * 1.001: can_add = False
                            if active_dir == -1 and current_close > last_entry * 0.999: can_add = False
                            
                        if can_add:
                            open_positions.append({'entry': current_close, 'lots': next_lots, 'dir': active_dir})
                
                # Fechamento
                elif (open_positions and mom_res["direction"] == -open_positions[-1]['dir'] and mom_res["velocity"] > 0.5) or kalman_res["is_structural_break"]:
                    for pos in open_positions:
                        # Multiplicador generico, já que cada ativo tem seu point value
                        # Usando retorno percentual em cima da banca para padronizar
                        pct_move = (current_close - pos['entry']) / pos['entry']
                        # 25x Leverage sobre o lote ficticio (representando o notional)
                        profit = pos['dir'] * pct_move * pos['lots'] * 2500.0 # Aproximacao
                        balance += profit
                        if profit > 0: wins += 1
                        else: losses += 1
                    open_positions = []
                
                if balance > peak_equity:
                    peak_equity = balance
                dd = (peak_equity - balance) / peak_equity if peak_equity > 0 else 0
                if dd > max_drawdown:
                    max_drawdown = dd
                    
            if open_positions:
                for pos in open_positions:
                    pct_move = (data[-1][0] - pos['entry']) / pos['entry']
                    profit = pos['dir'] * pct_move * pos['lots'] * 2500.0
                    balance += profit
                    if profit > 0: wins += 1
                    else: losses += 1
                    
            elaps = time.time() - start_time
            print(f"[{elaps:.1f}s] Balanço Final: ${balance:.2f} | MaxDD: {max_drawdown*100:.2f}% | Peak: ${peak_equity:.2f}")
            results.append({
                "Asset": asset_name,
                "Bars": total_bars,
                "Final_Balance": balance,
                "Peak_Equity": peak_equity,
                "Max_DD_%": max_drawdown * 100,
                "Trades": wins + losses
            })
            
        except Exception as e:
            print(f"FALHOU: {str(e)}")
            
    # Salvar resultados
    df_res = pd.DataFrame(results)
    print("\n" + "=" * 80)
    print("RESUMO DA AUDITORIA MULTI-ATIVO:")
    print(df_res.to_string(index=False))
    print("=" * 80)
    
if __name__ == "__main__":
    run_multi_pair_validation()
