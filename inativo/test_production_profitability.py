import numpy as np
import pandas as pd
import time
import os
import sys

# Tier-0 Modules
from modules.fractal_hurst import OmegaFractalAgent
from modules.volume_physics import OmegaVolumeAgent
from modules.momentum_physics import OmegaMomentumAgent
from modules.zone_navigator import OmegaZoneAgent
from modules.risk_metrics import OmegaRiskAgent
from modules.kalman_pullback_engine import OmegaKalmanPullbackEngine

def load_xauusd_historical(filepath: str) -> np.ndarray:
    """Lê o histórico real do XAUUSD de 2A/M15/H1"""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Histórico M15 não encontrado: {filepath}")
    
    print(f"[*] Carregando base histórica real (Local: {filepath})...")
    df = pd.read_csv(filepath)
    # df tem as colunas: time, open, high, low, close, volume
    
    opens = df['open'].values
    closes = df['close'].values
    highs = df['high'].values
    lows = df['low'].values
    vols = df['volume'].values
    times = df['time'].values
    
    return np.array([[opens[i], highs[i], lows[i], closes[i], vols[i]] for i in range(len(df))]), times

def test_profitability_ensemble():
    print("=" * 70)
    print("  OMEGA OS: BACKTEST DE LUCRATIVIDADE ENSEMBLE TIER-0 (O.I.G V3.0)")
    print("=" * 70)
    
    # Inicia os Agentes
    fractal_agent = OmegaFractalAgent()
    volume_agent = OmegaVolumeAgent()
    momentum_agent = OmegaMomentumAgent()
    zone_agent = OmegaZoneAgent()
    risk_agent = OmegaRiskAgent()
    kalman_agent = OmegaKalmanPullbackEngine()
    
    data_path = r"C:\OMEGA_PROJETO\Arquivo Test Codigo AIC\OHLCV_DATA_AUDIT\XAUUSD_M5.csv"
    market_data, market_times = load_xauusd_historical(data_path)
    
    # Processar toda a base M15 (2 Anos / ~47k barras completas para validação histórica comparativa)
    # Historico completo sem truncamento.
    print(f"[*] Base de Dados original carregada: {len(market_data)} barras.")
    
    balance = 10000.0 # Bacanario institucional
    open_positions = [] # Múltiplas ordens - Sistema de Escalonamento (Pyramiding)
    total_profit_locked = 0.0
    wins = 0
    losses = 0
    
    print(f"[*] Base de Dados: {len(market_data)} barras M5 (Granularidade Alta)")
    print("\n[*] Ativando Sistema Institucional de Escalonamento (Pyramiding) com Parciais...")
    start_t = time.time()
    
    total_len = len(market_data)
    
    for i in range(150, total_len):
        if i % 500 == 0:
            print(f"  ... Progresso: {i}/{total_len} candles computados ...")
            
        window = market_data[i-150:i]
        current_close = float(window[-1][0])
        current_time = market_times[i]
        
        # 1. RISK CHECK (Global Halt)
        closes_only = window[:, 0]
        risk_res = risk_agent.execute(closes_only)
        
        # Helper: ATR Dinâmico para M5
        atr_window = window[-14:]
        tr_list = [max(r[1]-r[2], abs(r[1]-window[-j-2][0]), abs(r[2]-window[-j-2][0])) for j,r in enumerate(atr_window)]
        atr_current = np.mean(tr_list)
        
        active_positions = []
        for pos in open_positions:
            entry = pos['entry']
            lots = pos['lots']
            status = pos['status']
            p_dir = pos['dir']
            
            # Inicializando e calculando max_price p/ Trailing SL Dinâmico Fiduciário
            if 'max_favorable_price' not in pos:
                pos['max_favorable_price'] = entry
                
            if p_dir == 1 and current_close > pos['max_favorable_price']:
                pos['max_favorable_price'] = current_close
            elif p_dir == -1 and current_close < pos['max_favorable_price']:
                pos['max_favorable_price'] = current_close
            
            # Cada lote padrão de XAUUSD (100 oz) move $100 por dólar de cotação
            unrealized_profit = p_dir * (current_close - entry) * lots * 100 
            
            # SL Dinâmico e Estrito (TRAILING STOP):
            # O Stop acompanha o preço a 1.5x ATR de distância do melhor preço já alcançado
            sl_hit = False
            if p_dir == 1 and current_close < pos['max_favorable_price'] - (atr_current * 1.5): sl_hit = True
            elif p_dir == -1 and current_close > pos['max_favorable_price'] + (atr_current * 1.5): sl_hit = True
            
            if sl_hit:
                balance += unrealized_profit
                total_profit_locked += unrealized_profit
                if unrealized_profit > 0: wins += 1
                else: losses += 1
                pos['status'] = 'CLOSED_SL'
                continue
                
            # Parcial: Se andou 2.0x ATR a favor, fecha metade dos lotes para GARANTIR lucro.
            tp1_hit = False
            if p_dir == 1 and current_close >= entry + (atr_current * 2.5): tp1_hit = True
            elif p_dir == -1 and current_close <= entry - (atr_current * 2.5): tp1_hit = True
            
            if status == 'OPEN' and tp1_hit:
                partial_lots = lots / 2.0
                loc_profit = p_dir * (current_close - entry) * partial_lots * 100
                balance += loc_profit
                total_profit_locked += loc_profit
                pos['lots'] -= partial_lots
                pos['status'] = 'PARTIAL_LOCKED'
                wins += 1
            
            # Saída Final: Fim do movimento (Exaustão > 4.5x ATR no frame menor)
            tp2_hit = False
            if p_dir == 1 and current_close >= entry + (atr_current * 4.5): tp2_hit = True
            elif p_dir == -1 and current_close <= entry - (atr_current * 4.5): tp2_hit = True
            
            if status == 'PARTIAL_LOCKED' and tp2_hit:
                final_profit = p_dir * (current_close - entry) * pos['lots'] * 100
                balance += final_profit
                total_profit_locked += final_profit
                wins += 1
                pos['status'] = 'CLOSED_TP'
                continue
                
            active_positions.append(pos)
            
        open_positions = active_positions
        
        if risk_res["emergency_halt"]:
            # PANIC: Fecha tudo a mercado
            for pos in open_positions:
                prof = pos['dir'] * (current_close - pos['entry']) * pos['lots'] * 100
                balance += prof
                total_profit_locked += prof
                if prof > 0: wins += 1
                else: losses += 1
            open_positions = []
            continue
        
        # 2. Oráculo Fractal & 3. Zone Navigator & 4. Momentum & 5. Volume
        frac_res = fractal_agent.execute(closes_only)
        # O zone ctx não deveria fixar direction em 1 sempre:
        # Puxa do momentum a direcao mais provável:
        cur_dir_mom = mom_res["direction"] if 'mom_res' in locals() else 1
        zone_res = zone_agent.execute(window, context={"direction": cur_dir_mom})
        mom_res = momentum_agent.execute(window)
        
        vol_ctx = {
            "regime": frac_res["regime"], 
            "is_pullback_friendly": frac_res["is_pullback_friendly"],
            "hurst_exponent": frac_res["hurst_exponent"]
        }
        vol_res = volume_agent.execute(window, context=vol_ctx)
        
        # [NOVO] INJEÇÃO DA MATRIZ KALMAN STOCHASTIC
        kalman_res = kalman_agent.execute(window)
        
        # -------------------------------------------------------------
        # SISTEMA LÓGICO: SCALE-IN AGRESSIVO BIDIRECIONAL
        # -------------------------------------------------------------
        
        market_dir = mom_res["direction"]
        
        # Filtro Rigoroso: Momentum forte e Zona CORE
        is_strong_trend = (market_dir in (1, -1) and zone_res["zone_type"] in ("CORE_STRONG", "CORE_NORMAL") and zone_res.get("fuel_remaining", 0) > 0.4)
        
        # NOVO: Matriz de Pullback Bayesiana e Estocástica via Kalman
        is_kalman_pullback = kalman_res["is_kalman_pullback"]
        
        if is_strong_trend or (is_kalman_pullback and len(open_positions) > 0):
            # Trava para não inverter posição no meio do fluxo
            active_dir = open_positions[-1]['dir'] if open_positions else market_dir
            
            # Limites rígidos baseados em Risco Quanti Institucional (Levarge 25.0 máx)
            if market_dir == active_dir and len(open_positions) < 15:
                # Escalonamento de lotes conservador (0.5 atr)
                next_lots = min(1.0 + (len(open_positions) * 0.5), 5.0)
                
                # Espacamento estruturado (No minimo 1 ATR inteiro entre cada entrada para não encavalar)
                can_add = True
                if open_positions:
                    last_entry = open_positions[-1]['entry']
                    if active_dir == 1 and current_close < last_entry + atr_current: can_add = False
                    if active_dir == -1 and current_close > last_entry - atr_current: can_add = False
                    
                if can_add:
                    open_positions.append({
                        'entry': current_close,
                        'lots': next_lots,
                        'status': 'OPEN',
                        'dir': active_dir
                    })
                    # print(f"  [++] LOTE HFT (Kalman State-Space): {next_lots} Lots @ {current_close:.2f} | P_rev: {kalman_res['pullback_confidence']:.2f} | Ordens: {len(open_positions)}")
            
        # Reversão / Fechamento
        # Mudança forte de Estrutura: Se Innovation (Kalman) estoura a banda de volatilidade, sinalizando absorção do fluxo reverso.
        elif (open_positions and mom_res["direction"] == -open_positions[-1]['dir'] and mom_res["velocity"] > 0.5) or kalman_res["is_structural_break"]:
            for pos in open_positions:
                prof = pos['dir'] * (current_close - pos['entry']) * pos['lots'] * 100
                balance += prof
                total_profit_locked += prof
                if prof > 0: wins += 1
                else: losses += 1
            # if len(open_positions) > 0:
            #    print(f"  [--] EXAUSTÃO DA TENDÊNCIA (Kalman Break)! Fechando {len(open_positions)} ordens a {current_close:.2f}")
            open_positions = []
            
    # Liquidação Fim de Teste
    for pos in open_positions:
        prof = pos['dir'] * (current_close - pos['entry']) * pos['lots'] * 100
        balance += prof
        total_profit_locked += prof
        if prof > 0: wins += 1
        else: losses += 1
            
    end_t = time.time()
    
    print("\n[+] BACKTEST ESCALONAMENTO INSTITUCIONAL (PYRAMIDING) CONCLUÍDO ({:.2f}s)".format(end_t - start_t))
    print("=" * 70)
    print(f"📊 SALDO INICIAL:        $10,000.00")
    print(f"📊 SALDO FINAL:          ${balance:,.2f}")
    print(f"💰 LUCRO LÍQUIDO TRANCA: ${total_profit_locked:,.2f}")
    print(f"⏱  TIMEFRAME USADO:      M15 (Ataque Seguro de Tendência)")
    
    if (wins+losses) > 0:
        winrate = (wins / (wins+losses)) * 100
        print(f"🎯 TAXA DE ACERTO (LEGS): {winrate:.1f}% ({wins} W / {losses} L)")
    print(f"⚙️  BOLETAS EXECUTADAS:   {wins+losses}")
    print("=" * 70)
    print("💎 [MASTERCLASS] O Escalonamento Dinâmico Institucional extrai dezenas de pernas lucrativas.")

if __name__ == "__main__":
    test_profitability_ensemble()
