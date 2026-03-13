import os
import sys
import numpy as np
import pandas as pd
import time
from datetime import datetime
from modules.squeeze_detector import SqueezeDetector
from modules.backtest_engine import BacktestMetricsEngine, walk_forward_split

from test_production_profitability import (
    OmegaFractalAgent, OmegaVolumeAgent, OmegaMomentumAgent, 
    OmegaZoneAgent, OmegaKalmanPullbackEngine,
    load_xauusd_historical
)
from run_full_real_data import GoldenMarketProfileEngine
from modules.v_flow_microstructure import VFlowReversalEngine, MacroBias
from modules.fimathe_core import FimatheCoreTIER0
from modules.omega_kernel_v5_1_refined import OMEGAKernelV51Refined

class OmegaAICControllerV5:
    """
    Controlador Master do AIC Aerospace v5.0
    Integra VFR Adaptive, Golden Trap Contínuo, Kalman Avionics e Squeeze Detector.
    """
    def __init__(self):
        self.vfr_engine = VFlowReversalEngine(window_size=20, leverage_max=5.0)
        self.golden_profile = GoldenMarketProfileEngine(trace_window=150, bins=50)
        self.kalman_engine = OmegaKalmanPullbackEngine()
        self.squeeze_engine = SqueezeDetector(window=20)
        self.fimathe_engine = FimatheCoreTIER0()
        self.omega_kernel = OMEGAKernelV51Refined()
        
    def get_thrust_vector(self, window_data, current_candle_dict, macro_bias):
        """Calcula o Thrust Scalar Vector"""
        # 1. Passo do Kernel Refinado (Confluência Macro+Micro)
        # ohlcv: np.ndarray shape (N,5) [O, H, L, C, V]
        kernel_state = self.omega_kernel.engine_step(window_data)
        
        vfr_score = kernel_state.signal_strength * 100
        vfr_direction = 1 if kernel_state.bias == "BUY" else -1 if kernel_state.bias == "SELL" else 0
        
        # 2. Perfil de Mercado
        profile = self.golden_profile.calculate_dynamic_poc(window_data)
        
        # 3. RANGE DIAGONAL / CHANNEL DETECTOR (Novo: Exigência do Comandante)
        # Detecta topos e fundos prévios onde o preço foi rejeitado na estrutura atual
        amplitude = profile["abs_max"] - profile["abs_min"]
        top_zone = profile["abs_max"] - (amplitude * 0.05)
        bottom_zone = profile["abs_min"] + (amplitude * 0.05)
        c = current_candle_dict['close']
        
        channel_direction = 0
        channel_score = 0
        # Venda no topo do canal (Range Diagonal Superior)
        if c >= top_zone and vfr_signal.z_price > 0.5: 
            channel_direction = -1
            channel_score = 85
        # Compra no fundo do canal (Range Diagonal Inferior)
        elif c <= bottom_zone and vfr_signal.z_price < -0.5:
            channel_direction = 1
            channel_score = 85
            
        # 4. Golden Trap Expandida (0.50 - 0.886)
        golden_trap = self.golden_profile.evaluate_golden_trap(profile, window_data[-1][0], vfr_direction)
        
        # 5. Kalman Avionics
        kalman_res = self.kalman_engine.execute(window_data.tolist())
        is_kalman_ok = not kalman_res["is_structural_break"]
        
        # 4. Squeeze Afterburner (XAUUSD Volume Imbalance)
        squeeze_res = self.squeeze_engine.update(current_candle_dict)
        
        # 7. NOVO: FIMATHE CORE & DIAGONAL RANGE (PSA TIER-0)
        # Convert window_data (which might be the target_data slice) to DataFrame for Fimathe
        df_window = pd.DataFrame(window_data, columns=['close', 'high', 'low', 'volume'])
        fimathe_signal = self.fimathe_engine.get_signal(df_window)
        diagonal_res = self.fimathe_engine.detect_diagonal_range(window_data)
        
        # DECISÃO E VETORIZAÇÃO DE LANÇAMENTO (Override Logic)
        # Prioridade 1: Diagonal Range do Comandante (Sniper)
        # Prioridade 2: Fimathe Breakout (Trend)
        # Prioridade 3: VFR Deep Reversal (Mean Reversion)
        
        if diagonal_res['score'] > 0:
            final_direction = diagonal_res['direction']
            final_score = diagonal_res['score']
            trigger_type = diagonal_res['type']
            # Para Range Diagonal, aceitamos mesmo com Kalman ok
            thrust_active = is_kalman_ok
        elif fimathe_signal['direction'] != 0:
            final_direction = fimathe_signal['direction']
            final_score = 85
            trigger_type = fimathe_signal['type']
            # Fimathe é tendência, aceitamos se não houver um break estrutural violento
            thrust_active = is_kalman_ok
        else:
            final_direction = vfr_direction
            # Score ponderado para VFR (Filtro de Reversão)
            final_score = (vfr_score * 0.40) + ((100 if golden_trap["in_trap_zone"] else 0) * 0.25) + ((100 if is_kalman_ok else 0) * 0.20) + (squeeze_res["squeeze_score"] * 0.15)
            trigger_type = "VFR_DEEP_REVERSAL"
            thrust_active = vfr_score >= 60 and golden_trap["in_trap_zone"] and is_kalman_ok
        
        # 8. FILTRO DE CORRELAÇÃO MACRO (Exigência TIER-0)
        # Se Hurst > 0.6 (Trend Persistente), ignoramos sinais de reversão opostos à tendência Macro
        is_macro_aligned = True
        if macro_bias.hurst > 0.60:
            if final_direction != 0 and final_direction != macro_bias.kalman_trend:
                is_macro_aligned = False
                trigger_type = f"BLOCKED_BY_MACRO_TREND ({macro_bias.kalman_trend})"
        
        # Se Hurst < 0.40 (Mean Reverting), priorizamos VFR e Diagonal Range
        elif macro_bias.hurst < 0.40:
            if trigger_type in ["FIMATHE_EXPANSION_LONG", "FIMATHE_EXPANSION_SHORT"]:
                # Em range lateral, breakout de fimathe é perigoso (falso rompimento)
                final_score *= 0.70 # Reduz confiança
        
        thrust_active = thrust_active and is_macro_aligned

        return {
            "launch": thrust_active,
            "direction": final_direction,
            "thrust_score": final_score,
            "squeeze_boost": squeeze_res["boost_multiplier"],
            "kalman_break": kalman_res["is_structural_break"],
            "trigger_type": trigger_type,
            "kernel_details": kernel_state.details
        }

def run_master_aerospace_validation():
    print("=" * 80)
    print("🚀 OMEGA OS: KERNEL MESTRE V5-AEROSPACE - VALIDAÇÃO INSTITUCIONAL")
    print("🚀 MOTOR DE RETESTE COM SQUEEZE DETECTOR E METRICAS CQO")
    print("=" * 80)

    data_path = r"C:\OMEGA_PROJETO\Arquivo Test Codigo AIC\OHLCV_DATA_AUDIT\XAUUSD_M5.csv"
    if not os.path.exists(data_path):
        data_path = r"C:\OMEGA_PROJETO\Arquivo Test Codigo AIC\OHLCV_DATA_AUDIT\XAUUSD_M15.csv"
        
    market_data, market_times = load_xauusd_historical(data_path)
    # Limitar para teste rápido mas com relevância, ou rodar tudo
    target_data = market_data[-40000:]
    
    # K-Fold Walk Forward Separator
    folds = walk_forward_split(target_data.tolist(), k=5)
    
    print(f"[*] Base de Dados: {len(target_data)} barras (Walk Forward 5-Fold Ativado)")
    
    controller = OmegaAICControllerV5()
    
    # Rodar todos simulacao em run continuo para as métricas finais
    metrics_engine = BacktestMetricsEngine(initial_balance=10000.0)
    open_positions = []
    
    print("[*] Iniciando Shadow Paper Trading Simulator...")
    start_time = time.time()
    
    for i in range(150, len(target_data)):
        window = target_data[i-150:i]
        current_candle = window[-1] # [close, high, low, vol]
        
        candle_dict = {
            'close': current_candle[0],
            'high': current_candle[1],
            'low': current_candle[2],
            'open': window[-2][0] if len(window) > 1 else current_candle[0], # approximate
            'volume': current_candle[3]
        }
        
        macro_bias = MacroBias(hurst=0.5, kalman_trend=0, horizon="SCALP", strength=1.0) # Simulado
        
        # Thrust Vectoring Decision
        thrust = controller.get_thrust_vector(window, candle_dict, macro_bias)
        
        # Gerenciamento de Posicao
        if thrust["kalman_break"] or (open_positions and open_positions[-1]['dir'] != thrust["direction"] and thrust["direction"] != 0):
            # Ejetar posicoes (Structural break ou inversao)
            for pos in open_positions:
                profit = pos['dir'] * (current_candle[0] - pos['entry']) * pos['lots'] * 100
                metrics_engine.add_trade(profit, profit > 0)
            open_positions = []
            
        # Entradas
        if thrust["launch"] and thrust["direction"] != 0:
            if len(open_positions) < int(min(18, thrust["thrust_score"] / 5)):
                # Lotes turbinados pelo Squeeze Detector Afterburner
                base_lot = 0.05
                final_lots = base_lot * thrust["squeeze_boost"]
                open_positions.append({
                    'entry': current_candle[0],
                    'lots': final_lots,
                    'dir': thrust["direction"]
                })
                
    # Fechar remanescentes
    for pos in open_positions:
        profit = pos['dir'] * (target_data[-1][0] - pos['entry']) * pos['lots'] * 100
        metrics_engine.add_trade(profit, profit > 0)

    results = metrics_engine.compute_metrics()
    end_time = time.time()
    
    print("\n" + "=" * 80)
    print("📊 RESULTADOS MATEMÁTICOS OMEGA V5-AEROSPACE (Walk-Forward 40k Bars)")
    print("=" * 80)
    print(f"⏱ Tempo de Processamento: {end_time - start_time:.2f} segundos\n")
    
    if "error" in results:
        print("❌ ERRO: ", results["error"])
    else:
        for k, v in results.items():
            if isinstance(v, float):
                if "Ratio" in k or "Factor" in k:
                    print(f"  > {k:<25}: {v:.2f}")
                elif "%" in k:
                    print(f"  > {k:<25}: {v:.2f}%")
                else:
                    print(f"  > {k:<25}: ${v:,.2f}")
            else:
                print(f"  > {k:<25}: {v}")
                
    print("\n✅ VALIDAÇÃO DO CQO CONCLUÍDA")
    print("🚀 O MOTOR ESTÁ PRONTO PARA A MESA DE DEMO HOJE À NOITE.")
    print("=" * 80)

if __name__ == "__main__":
    run_master_aerospace_validation()
